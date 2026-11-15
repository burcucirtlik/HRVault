#!/usr/bin/env python3
"""HRVault tarayıcı.

Kullanım (vault kökünden):
  python3 engine/scanner/scan.py run [--dry-run] [--all] [--max-age 14]
  python3 engine/scanner/scan.py brief [--scan YYYY-MM-DD] [--all]
  python3 engine/scanner/scan.py show <id|sıra> [--scan YYYY-MM-DD] [--full]
  python3 engine/scanner/scan.py annotate <id|sıra> (--json '{...}' | --drop SEBEP) [--workers a,b]
  python3 engine/scanner/scan.py detect <kariyer-sayfası-veya-ilan-url> [--add "Şirket Adı"]

`run` aktif worker'ların kaynaklarından ilanları çeker, rol anahtar kelimeleriyle
başlıktan ön-eleme yapar, tekrarları birleştirir, daha önce görülenleri atlar ve
me/pipeline/scans/YYYY-MM-DD.json dosyasına yazar. Çalışma tipi / yer / saat
sınıflandırması ve puanlama bu betikte değil; scan ve score skill'lerinde yapılır.

Yalnızca standart kütüphane kullanır (PyYAML varsa onu tercih eder).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from scanner import config  # noqa: E402
from scanner.common import age_days, http_get, http_json  # noqa: E402
from scanner.sources import ALL, ATS, FEEDS  # noqa: E402

VAULT = HERE.parent.parent
NON_SCANNABLE = {"linkedin": "LinkedIn otomatik taranmaz; iş alarmı e-postaları veya kişinin verdiği linklerle çalışılır (engine/adapters/linkedin.md)."}


# ------------------------------------------------------------------ yardımcılar
def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def dedupe_key(company: str, title: str) -> str:
    c = re.sub(r"\b(inc|llc|ltd|gmbh|corp|co|the)\b", "", _fold(company)).strip()
    t = re.sub(r"\s*\b(remote|hybrid|m f d|f m d|w m d)\b", "", _fold(title)).strip()
    return f"{c}|{t}"


def role_matches(title: str, role: str) -> bool:
    """Rolün tüm kelimeleri başlıkta kelime başı olarak geçiyor mu (çoğul ekine izin verir)."""
    t = _fold(title)
    words = _fold(role).split()
    # Kısa kelimeler (ai, ml, qa…) önek olarak eşleşirse gürültü yapar: "ai" → "aircraft". Bunlar tam kelime (+ çoğul) eşleşir.
    def hit(w: str) -> bool:
        pat = rf"\b{re.escape(w)}s?\b" if len(w) <= 3 else rf"\b{re.escape(w)}"
        return bool(re.search(pat, t))
    return bool(words) and all(hit(w) for w in words)


def excluded(title: str, phrase: str) -> bool:
    """Hariç başlık kontrolü: kelimeler tam eşleşir (+ çoğul). Önek eşleşmesi burada tehlikeli:
    "intern" → "internal", "international" ilanlarını da eler."""
    t = _fold(title)
    words = _fold(phrase).split()
    return bool(words) and all(re.search(rf"\b{re.escape(w)}(s|es)?\b", t) for w in words)


YER = {"remote": "remote", "uzaktan": "remote", "hybrid": "hybrid", "hibrit": "hybrid",
       "onsite": "onsite", "on-site": "onsite", "ofis": "onsite", "office": "onsite"}


def workplace_ok(declared: str, allowed: list) -> bool:
    """Kaynak yeri açıkça beyan ettiyse ve worker o yeri istemiyorsa ele.
    Beyan yoksa geçir; asıl karar scan skill'inin ilan metnini okumasında."""
    if not declared or not allowed:
        return True
    return declared in {YER.get(str(x).lower(), str(x).lower()) for x in allowed}


OPEN_LOC = ("worldwide", "anywhere", "global", "remote")


def location_ok(job, allowed: list) -> bool:
    """Akış kaynaklarında konum alanı *adayın* bulunması gereken yeri belirtir (Himalayas
    locationRestrictions, Remotive candidate_required_location, WWR region…). Worker'ın
    `ülkeler` listesiyle hiç kesişmiyorsa ele. Başlıktaki "Worldwide" bu alanı geçersiz kılmaz.
    ATS kaynaklarında konum ofis yeridir; orada karar scan skill'inde."""
    if job.source not in FEEDS or not allowed:
        return True
    loc = _fold(job.location)
    if not loc or any(re.search(rf"\b{w}\b", loc) for w in OPEN_LOC):
        return True
    # kelime sınırıyla: "EU" kısaltması "Sint Eustatius" içinde eşleşmesin
    return any(_fold(str(a)) and re.search(rf"\b{re.escape(_fold(str(a)))}\b", loc) for a in allowed)


# Adayın bulunması gereken yeri kısıtlayan bölge/ülke adları (katlanmış). Worker'ın `ülkeler` listesiyle
# kesişmiyorsa ilan elenir. AB ülkeleri burada yok: "EU/Europe" izni olan worker'da yanlış eleme yapmasın;
# onların kararı scan skill'inde.
RESTRICTED = [
    "united states", "u s a", "u s", "usa", "us", "north america", "americas", "latam", "latin america",
    "canada", "mexico", "brazil", "argentina", "colombia", "chile", "peru",
    "united kingdom", "u k", "uk", "england", "scotland", "wales",
    "india", "pakistan", "bangladesh", "sri lanka", "philippines", "indonesia", "singapore", "malaysia",
    "japan", "china", "hong kong", "korea", "taiwan", "vietnam", "thailand", "apac", "asia pacific",
    "australia", "new zealand", "anz", "uae", "united arab emirates", "dubai", "abu dhabi", "saudi arabia",
    "ksa", "qatar", "bahrain", "kuwait", "oman", "israel", "egypt", "nigeria", "kenya", "south africa",
    "turkey", "turkiye",
]
_RESTRICTED_RE = re.compile(r"\b(?:" + "|".join(re.escape(x) for x in sorted(RESTRICTED, key=len, reverse=True)) + r")\b")
OPEN_WORDS = re.compile(r"\b(?:worldwide|anywhere|global|globally)\b")


def region_ok(text: str, allowed: list) -> bool:
    """Metin (başlık ya da ATS konum alanı) kısıtlayıcı bir bölge adıyor ve worker'ın izinli yerlerinden
    hiçbirini ya da "worldwide" gibi açık bir ifadeyi içermiyorsa False. Ör. "Remote - US" → False,
    "Mentor (US, Canada, Europe)" → True (Europe izinli)."""
    if not allowed:
        return True
    t = _fold(text)
    if not _RESTRICTED_RE.search(t):
        return True
    if OPEN_WORDS.search(t):
        return True
    return any(_fold(str(a)) and re.search(rf"\b{re.escape(_fold(str(a)))}\b", t) for a in allowed)


def ats_location_ok(job, allowed: list) -> bool:
    """ATS konum alanı çoğunlukla ofis yeridir. Kısıtlayıcı bölge + ("remote" yazıyor ya da ilan remote
    beyan etmiyor) → aday o bölgede olmalı, ele. Remote beyanlı ve konum yalnızca bir ülke ise (merkez ofis
    olabilir) karar scan skill'inde."""
    if region_ok(job.location, allowed):
        return True
    return job.workplace == "remote" and "remote" not in _fold(job.location)


# Dil uzmanlığı ilanları ("Dutch Audio Specialist", "Kazakh Language Specialist"):
# başlıktaki dil worker'ın `diller` listesinde yoksa elenir.
LANGS = {
    "english": "en", "turkish": "tr", "german": "de", "french": "fr", "spanish": "es", "italian": "it",
    "portuguese": "pt", "dutch": "nl", "flemish": "nl", "swedish": "sv", "norwegian": "no", "danish": "da",
    "finnish": "fi", "icelandic": "is", "polish": "pl", "czech": "cs", "slovak": "sk", "hungarian": "hu",
    "romanian": "ro", "bulgarian": "bg", "greek": "el", "serbian": "sr", "croatian": "hr", "bosnian": "bs",
    "slovenian": "sl", "ukrainian": "uk", "russian": "ru", "belarusian": "be", "lithuanian": "lt",
    "latvian": "lv", "estonian": "et", "albanian": "sq", "macedonian": "mk", "welsh": "cy", "irish": "ga",
    "basque": "eu", "catalan": "ca", "galician": "gl", "arabic": "ar", "hebrew": "he", "persian": "fa",
    "farsi": "fa", "dari": "fa", "urdu": "ur", "hindi": "hi", "bengali": "bn", "bangla": "bn",
    "punjabi": "pa", "gujarati": "gu", "marathi": "mr", "tamil": "ta", "telugu": "te", "kannada": "kn",
    "malayalam": "ml", "nepali": "ne", "sinhala": "si", "chinese": "zh", "mandarin": "zh", "cantonese": "zh",
    "japanese": "ja", "korean": "ko", "vietnamese": "vi", "thai": "th", "indonesian": "id", "malay": "ms",
    "tagalog": "tl", "filipino": "tl", "swahili": "sw", "amharic": "am", "somali": "so", "oromo": "om",
    "yoruba": "yo", "igbo": "ig", "hausa": "ha", "zulu": "zu", "xhosa": "xh", "afrikaans": "af",
    "kinyarwanda": "rw", "fulah": "ff", "wolof": "wo", "kazakh": "kk", "uzbek": "uz", "tajik": "tg",
    "kyrgyz": "ky", "azerbaijani": "az", "azeri": "az", "georgian": "ka", "armenian": "hy", "mongolian": "mn",
    "maori": "mi", "samoan": "sm", "hawaiian": "haw", "kabuverdianu": "kea", "haitian creole": "ht",
}
_LANG_RE = re.compile(r"\b(" + "|".join(sorted(LANGS, key=len, reverse=True)) + r")\b")
_LANG_ROLE = re.compile(r"\b(?:language|linguist|linguistic|speaker|speaking|native|fluent|bilingual|audio|voice|"
                        r"annotat\w*|transcri\w*|translat\w*|locali[sz]\w*|rater|evaluat\w*|specialist|expert|"
                        r"writer|tutor|trainer|reviewer)\b")


def language_ok(title: str, langs: list) -> bool:
    """Başlık bir dil uzmanlığı istiyorsa (dil adı + dil/uzman kelimesi) ve o dil worker'da yoksa False."""
    if not langs:
        return True
    t = _fold(title)
    names = _LANG_RE.findall(t)
    if not names or not _LANG_ROLE.search(t):
        return True
    have = {str(x).lower() for x in langs}
    return any(LANGS[n] in have for n in names)


def _scans_dir() -> Path:
    d = VAULT / "me" / "pipeline" / "scans"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _load_json(p: Path, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def _write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


# ------------------------------------------------------------------ run
def cmd_run(a) -> int:
    from pipeline.profile import definitions  # geç import: döngüsel bağımlılığı önler
    approved = {d["id"] for d in definitions(VAULT / "me" / "profile" / "job-definitions.md")
                if d["durum"] == "onaylandı"}
    all_active = config.load_workers(VAULT)
    workers = [w for w in all_active if str(w.get("tanım") or "").strip() in approved]
    for w in all_active:
        if w not in workers:
            print(f"Atlandı: {w['ad']} — onaylı bir iş tanımına bağlı değil (coach §4–5).")
    if not workers:
        print("Taranacak worker yok. Tarama yalnızca onaylanmış iş tanımlarına bağlı aktif worker'larla çalışır "
              "(coach skill'i: analiz → iş tanımları → onay → worker).")
        return 1
    src_cfg = config.load_sources(VAULT)
    max_age = a.max_age if a.max_age is not None else src_cfg.get("max_age_days", 14)

    wanted = {s for w in workers for s in w["kaynaklar"]}
    queries = sorted({r for w in workers for r in w["roller"]})
    if not queries:
        print("Uyarı: aktif worker'larda `roller` boş; başlık ön-elemesi yapılamaz. Worker'a rol ekleyin.")
        return 1

    notes, stats, fetched = [], {}, []
    for s in sorted(wanted - set(ALL)):
        notes.append(f"{s}: " + NON_SCANNABLE.get(s, "bilinmeyen kaynak, adaptörü yok."))

    # ATS kaynakları önce: doğrudan başvuru linki verdikleri için tekrarlarda tercih edilir
    for name in [s for s in ATS if s in wanted] + [s for s in FEEDS if s in wanted]:
        mod = ALL[name]
        ctx = {
            "watchlist": [w for w in src_cfg.get("watchlist", []) if w.get("ats") == name],
            "feed": (src_cfg.get("feeds") or {}).get(name) or {},
            "queries": queries,
        }
        if name in ATS and not ctx["watchlist"]:
            notes.append(f"{name}: takip listesinde bu ATS'yi kullanan şirket yok (detect --add ile eklenir).")
            continue
        regional = getattr(mod, "KAPSAM", "küresel") != "küresel"
        if name in FEEDS and (ctx["feed"].get("enabled") is False or (regional and ctx["feed"].get("enabled") is not True)):
            notes.append(f"{name}: me/sources.json içinde kapalı" + (" (bölgesel kaynak, açıkça açılmalı)." if regional else "."))
            continue
        try:
            jobs = mod.fetch(ctx)
            stats[name] = {"çekilen": len(jobs)}
            fetched += jobs
        except Exception as e:  # bir kaynağın hatası taramayı durdurmaz
            stats[name] = {"hata": f"{type(e).__name__}: {e}"[:200]}

    # yaş + worker eşleşmesi
    kept = []
    for j in fetched:
        ad = age_days(j.published)
        # Yaş filtresi yalnızca akış kaynaklarına uygulanır. Şirket kariyer sayfalarındaki (ATS) ilanlar
        # aylarca açık kalır; panoda duruyorsa ilan açıktır.
        if j.source in FEEDS and max_age and ad is not None and ad > max_age:
            continue
        for w in workers:
            if j.source not in w["kaynaklar"]:
                continue
            if any(excluded(j.title, x) for x in w["hariç_başlık"]):
                continue
            if not workplace_ok(j.workplace, w.get("yer") or []):
                continue
            allowed = w.get("ülkeler") or []
            if not location_ok(j, allowed):
                continue
            # Başlıkta kısıtlayıcı bölge ("- India", "U.S. Remote") ve ATS'de konum alanı (ofis/aday yeri)
            if not region_ok(j.title, allowed) or (j.source in ATS and not ats_location_ok(j, allowed)):
                continue
            if not language_ok(j.title, w.get("diller") or []):
                continue
            hits = [r for r in w["roller"] if role_matches(j.title, r)]
            # Takip listesi (ATS) ilanlarında geniş eşleşme: worker'ın kelime köklerinden biri başlıkta geçerse yeter.
            # Liste kişinin seçtiği şirketlerle sınırlı olduğu için gürültü kabul edilebilir; karar sınıflandırma/puanlamada.
            if j.source in ATS:
                hits += [f"kök:{k}" for k in w.get("şirket_kökleri") or [] if role_matches(j.title, k)]
            if hits:
                j.workers.append(w["ad"])
                j.matched += [h for h in hits if h not in j.matched]
        if j.workers:
            kept.append(j)

    # tekrar birleştirme
    by_key: dict[str, object] = {}
    for j in kept:
        k = dedupe_key(j.company, j.title)
        if k in by_key:
            first = by_key[k]
            first.also_on.append(j.url)
            first.workers += [x for x in j.workers if x not in first.workers]
        else:
            by_key[k] = j

    # daha önce görülenler
    seen_p = VAULT / "me" / "pipeline" / "seen.json"
    seen = _load_json(seen_p, {})
    today = date.today().isoformat()
    # Görülme kaydı süresizse yeniden açılan ilan bir daha hiç görünmez; süresi dolan kayıt düşer.
    ttl = int(src_cfg.get("seen_süresi_gün") or 90)
    seen = {k: v for k, v in seen.items() if (date.today() - date.fromisoformat(str(v)[:10])).days <= ttl}
    new = {k: j for k, j in by_key.items() if a.all or k not in seen}

    for s in stats.values():
        s.setdefault("eşleşen", 0)
    for j in new.values():
        stats.setdefault(j.source, {}).setdefault("eşleşen", 0)
        stats[j.source]["eşleşen"] += 1

    out_p = _scans_dir() / f"{today}.json"
    existing = _load_json(out_p, {"jobs": []})
    have = {x["id"] for x in existing["jobs"]}
    jobs_out = existing["jobs"] + [j.to_dict() | {"key": k} for k, j in new.items() if j.id not in have]
    result = {
        "meta": {
            "tarih": today,
            "çalışma_zamanı": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "aktif_worker": [w["ad"] for w in workers],
            "roller": queries,
            "max_age_days": max_age,
            "kaynaklar": stats,
            "notlar": notes,
            "toplam_ilan": len(jobs_out),
        },
        "jobs": jobs_out,
    }
    if not a.dry_run:
        _write_json(out_p, result)
        for k in new:
            seen.setdefault(k, today)
        _write_json(seen_p, seen)

    # özet
    print(f"Tarama {today} · worker: {', '.join(result['meta']['aktif_worker'])} · roller: {', '.join(queries)}")
    for name, s in stats.items():
        print(f"  {name:15} " + " · ".join(f"{k}: {v}" for k, v in s.items()))
    for n in notes:
        print(f"  not: {n}")
    print(f"Yeni ilan: {len(new)}" + (" (dry-run, kaydedilmedi)" if a.dry_run else f" → {out_p.relative_to(VAULT)}"))
    pos = {x["id"]: i for i, x in enumerate(jobs_out, 1)}
    for j in new.values():
        i, ad = pos.get(j.id, 0), age_days(j.published)
        print(f"  {i:3}. [{','.join(j.workers)}] {j.company} — {j.title} · {j.workplace or '?'} · {j.location[:40] or '?'}"
              f" · {j.source}{' +' + str(len(j.also_on)) if j.also_on else ''} · {'' if ad is None else f'{ad:.0f}g'}")
    return 0


# ------------------------------------------------------------------ show / brief / annotate
def _scan_path(day: str | None) -> Path:
    return _scans_dir() / f"{day or date.today().isoformat()}.json"


def _find_job(jobs: list, ref: str):
    j = next((x for x in jobs if x["id"] == ref), None)
    if j is None and ref.isdigit() and 0 < int(ref) <= len(jobs):
        j = jobs[int(ref) - 1]
    return j


SIGNAL = re.compile(
    r"(hours?\s*(?:per|/|a|each)\s*week|\b\d{1,2}\s*(?:-|–|to)?\s*\d{0,2}\s*h(?:ou)?rs?\b|part[- ]time|full[- ]time|"
    r"contract|freelance|temporary|fixed[- ]term|internship|"
    r"remote|hybrid|on[- ]?site|in[- ]office|days? (?:a|per) week|relocat|"
    r"time ?zone|\b(?:EST|EDT|PST|PDT|CET|CEST|GMT|UTC)\b|overlap|"
    r"visa|sponsor|authori[sz]ed to work|work permit|based in|located in|must (?:reside|live)|residen|"
    r"salary|compensation|per hour|/hr\b|hourly|[$€£]\s?\d|"
    r"years? of experience|\d\+? years|fluent|native|english|turkish|german)",
    re.I,
)


NOISE = re.compile(r"privacy (?:policy|notice)|equal opportunity|https?://\S+$|^to apply", re.I)


def signal_lines(text: str, limit: int = 8, width: int = 180) -> list[str]:
    out, seen = [], set()
    for line in re.split(r"(?<=[.!?])\s+|\n", text or ""):
        line = line.strip(" -•\t")
        if len(line) < 12 or not SIGNAL.search(line) or NOISE.search(line):
            continue
        k = line[:60].lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(line[:width] + ("…" if len(line) > width else ""))
        if len(out) >= limit:
            break
    return out


def cmd_brief(a) -> int:
    """Sınıflandırma için kompakt görünüm: beyan edilen alanlar + açıklamadan sinyal cümleleri."""
    p = _scan_path(a.scan)
    if not p.exists():
        print(f"Tarama dosyası yok: {p.relative_to(VAULT)}")
        return 1
    jobs = _load_json(p, {"jobs": []})["jobs"]
    for i, j in enumerate(jobs, 1):
        if not a.all and ("sınıf" in j or "elendi" in j):
            continue
        print(f"### {i}. {j['company']} — {j['title']}  [{j['id']}]")
        print(f"worker: {', '.join(j['workers'])} · beyan: {j.get('workplace') or '?'} / {j.get('employment_type') or '?'}"
              f" · yer: {j.get('location') or '?'} · ücret: {j.get('salary') or '?'}")
        for line in signal_lines(j.get("description", "")):
            print(f"  · {line}")
        print()
    return 0


def cmd_annotate(a) -> int:
    """scan skill'inin sınıflandırma sonucunu ilana yazar."""
    p = _scan_path(a.scan)
    data = _load_json(p, None)
    if not data:
        print(f"Tarama dosyası yok: {p.relative_to(VAULT)}")
        return 1
    j = _find_job(data["jobs"], a.ref)
    if j is None:
        print("İlan bulunamadı.")
        return 1
    if a.drop:
        j["elendi"] = a.drop
        j.pop("sınıf", None)
    else:
        try:
            j["sınıf"] = json.loads(a.json)
        except (TypeError, json.JSONDecodeError) as e:
            print(f"--json geçerli JSON olmalı: {e}")
            return 1
        j.pop("elendi", None)
    if a.workers:
        j["workers"] = [w.strip() for w in a.workers.split(",") if w.strip()]
    _write_json(p, data)
    print(f"ok {j['id']}: " + (f"elendi ({a.drop})" if a.drop else "sınıflandırıldı"))
    return 0


def cmd_show(a) -> int:
    p = _scan_path(a.scan)
    if not p.exists():
        print(f"Tarama dosyası yok: {p.relative_to(VAULT)}")
        return 1
    jobs = _load_json(p, {"jobs": []})["jobs"]
    j = _find_job(jobs, a.ref)
    if j is None:
        print("İlan bulunamadı.")
        return 1
    desc = j.pop("description")
    for k, v in j.items():
        if v not in ("", [], None):
            print(f"{k}: {v}")
    print("\n" + (desc if a.full else desc[:3000] + ("\n…(--full)" if len(desc) > 3000 else "")))
    return 0


# ------------------------------------------------------------------ detect
PATTERNS = [
    ("greenhouse", r"(?:boards|job-boards)\.greenhouse\.io/embed/job_board(?:/js)?\?for=([A-Za-z0-9_-]+)"),
    ("greenhouse", r"boards-api\.greenhouse\.io/v1/boards/([A-Za-z0-9_-]+)"),
    ("greenhouse", r"(?:boards|job-boards)(?:\.eu)?\.greenhouse\.io/(?!embed)([A-Za-z0-9_-]+)"),
    ("lever", r"jobs\.(?:eu\.)?lever\.co/([A-Za-z0-9_.-]+)"),
    ("ashby", r"jobs\.ashbyhq\.com/([A-Za-z0-9_.%-]+)"),
]
VERIFY = {
    "greenhouse": lambda t: len(http_json(f"https://boards-api.greenhouse.io/v1/boards/{t}/jobs")["jobs"]),
    "lever": lambda t: len(http_json(f"https://api.lever.co/v0/postings/{t}?mode=json")),
    "ashby": lambda t: len(http_json(f"https://api.ashbyhq.com/posting-api/job-board/{t}")["jobs"]),
}


def _find(text: str):
    for ats, pat in PATTERNS:
        m = re.search(pat, text)
        if m:
            return ats, m.group(1)
    return None


def cmd_detect(a) -> int:
    hit = _find(a.url)
    if not hit:
        try:
            page = http_get(a.url).decode("utf-8", "ignore")
        except Exception as e:
            print(f"Sayfa açılamadı: {e}")
            return 1
        hit = _find(page)
    if not hit:
        print("Greenhouse / Lever / Ashby izi bulunamadı. Şirket başka bir ATS kullanıyor olabilir "
              "(Workable, SmartRecruiters, Personio…) — adaptörü henüz yok.")
        return 2
    ats, token = hit
    try:
        n = VERIFY[ats](token)
    except Exception as e:
        print(f"{ats} / {token} bulundu ama API doğrulanamadı: {e}")
        return 1
    print(json.dumps({"ats": ats, "token": token, "açık_ilan": n}, ensure_ascii=False))
    if a.add:
        p = VAULT / "me" / "sources.json"
        cfg = _load_json(p, None) or _load_json(VAULT / "engine/templates/me/sources.json", {})
        wl = cfg.setdefault("watchlist", [])
        if any(w.get("ats") == ats and w.get("token") == token for w in wl):
            print("Zaten takip listesinde.")
        else:
            wl.append({"company": a.add, "ats": ats, "token": token})
            _write_json(p, cfg)
            print(f"Takip listesine eklendi: {a.add} ({ats}/{token})")
    return 0


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser(description="HRVault tarayıcı")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="aktif worker'lar için tara")
    r.add_argument("--dry-run", action="store_true", help="dosya yazma, seen.json'u güncelleme")
    r.add_argument("--all", action="store_true", help="daha önce görülenleri de dahil et")
    r.add_argument("--max-age", type=int, default=None, help="gün; 0 = sınırsız")
    s = sub.add_parser("show", help="taranmış bir ilanı göster")
    s.add_argument("ref", help="ilan id'si (kaynak:id) veya listedeki sıra")
    s.add_argument("--scan", help="tarama tarihi (YYYY-MM-DD), varsayılan bugün")
    s.add_argument("--full", action="store_true")
    b = sub.add_parser("brief", help="sınıflandırılmamış ilanların kompakt görünümü")
    b.add_argument("--scan", help="tarama tarihi (YYYY-MM-DD), varsayılan bugün")
    b.add_argument("--all", action="store_true", help="sınıflandırılmışları da göster")
    n = sub.add_parser("annotate", help="ilana sınıflandırma sonucu yaz veya ele")
    n.add_argument("ref", help="ilan id'si veya sıra")
    n.add_argument("--json", help='ör. \'{"tip":"part-time","yer":"remote","ülke_kısıtı":["US"],"saat":20,"ücret":"…","dil":["en"],"kıdem":"mid","belirsiz":[]}\'')
    n.add_argument("--drop", metavar="SEBEP", help="ilanı sebebiyle ele")
    n.add_argument("--workers", help="eşleşen worker listesini düzelt (virgülle)")
    n.add_argument("--scan", help="tarama tarihi (YYYY-MM-DD), varsayılan bugün")
    d = sub.add_parser("detect", help="bir şirketin ATS'sini ve token'ını bul")
    d.add_argument("url")
    d.add_argument("--add", metavar="ŞİRKET", help="bulunursa me/sources.json takip listesine ekle")
    a = ap.parse_args()
    return {"run": cmd_run, "show": cmd_show, "brief": cmd_brief, "annotate": cmd_annotate,
            "detect": cmd_detect}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
