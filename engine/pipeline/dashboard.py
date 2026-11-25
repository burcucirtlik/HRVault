#!/usr/bin/env python3
"""HRVault paneli — tarama, onay listesi ve başvuruların tek sayfalık özeti.

Kullanım (vault kökünden):
  python3 engine/pipeline/dashboard.py            # me/dashboard.html yazar
  python3 engine/pipeline/dashboard.py --open     # yazar ve varsayılan tarayıcıda açar

Sayfa `me/` içindeki kayıtlardan üretilir ve `me/dashboard.html` olarak yalnızca bu bilgisayarda kalır (me/ git'e ve pakete
girmez). Bağımsızdır: dışarıdan yazı tipi, betik ya da görsel yüklemez, internetsiz açılır. Kaynaklardan gelen her metin
(ilan başlığı, şirket adı, sebep) HTML olarak kaçışlanır; bağlantılar yalnızca http(s) ise tıklanabilir.

Boş bir kurulumda da çalışır: en üstteki kurulum kartı profilin hangi coach aşamasında olduğunu ve sıradaki adımı gösterir;
tercihler, iş tanımları, worker'lar ve taramalar eklendikçe bölümler dolar.

Bölümler: kurulum, son tarama (onay listesine girenler, elenenler ve eşik altı — en fazla 20, sebepleriyle), başvurular (bekleyen,
gönderilen; ATS yüzdesi ve %90'a ulaşmak için eksik kelimeler), ret gelenler, kaynak bazında tarama sayıları,
taranan kaynaklar ve kriterler.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import webbrowser
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from pipeline import profile  # noqa: E402
from pipeline.ats import MIN_ATS  # noqa: E402
from scanner import config  # noqa: E402
from scanner.scan import dedupe_key  # noqa: E402

VAULT = HERE.parent.parent
MAX_DROPPED = 20
SENT = ("başvuruldu", "görüldü", "mülakat", "teklif", "sessiz")
STATE_LABEL = {"hazırlandı": "hazırlandı", "başvuruldu": "gönderildi", "görüldü": "görüldü", "mülakat": "mülakat",
               "teklif": "teklif", "ret": "ret", "sessiz": "sessiz", "iptal": "iptal"}


# ------------------------------------------------------------------ veri
def _json(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default
    except (json.JSONDecodeError, OSError):
        return default


def latest_scan(me: Path) -> tuple[str, dict]:
    files = sorted(p for p in (me / "pipeline" / "scans").glob("*.json") if re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.stem))
    if not files:
        return "", {"meta": {}, "jobs": []}
    return files[-1].stem, _json(files[-1], {"meta": {}, "jobs": []})


def latest_decisions(me: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    p = me / "pipeline" / "decisions.jsonl"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(r, dict) and r.get("id"):
                out[r["id"]] = r
    return out


def ats_pct(raw) -> int | None:
    m = re.match(r"\s*~?\s*(\d+)\s*%", str(raw or ""))
    return int(m.group(1)) if m else None


def ats_need(raw) -> int | None:
    """'79% (zorunlu 5/5, tercih 1/4)' → %90'a ulaşmak için gereken ek ağırlık puanı (zorunlu kelime 2, tercih 1)."""
    m = re.search(r"zorunlu (\d+)/(\d+), tercih (\d+)/(\d+)", str(raw or ""))
    if not m:
        return None
    rg, rt, pg, pt = map(int, m.groups())
    got, total = 2 * rg + pg, 2 * rt + pt
    return max(0, -(-MIN_ATS * total // 100) - got) if total else None


def _split(s) -> list[str]:
    return [x.strip() for x in re.split(r"[;\n]", str(s or "")) if x.strip()]


def _history(text: str) -> list[tuple[str, str, str]]:
    """application.md → [(tarih, durum, not)] (Durum geçmişi, yeniden eskiye)."""
    out = []
    for m in re.finditer(r"^- (\d{4}-\d{2}-\d{2}) · ([^\s—(]+)\s*(?:[—(]\s*(.*))?$", text, re.M):
        out.append((m.group(1), m.group(2).strip(), (m.group(3) or "").strip().rstrip(")")))
    return out


def applications(me: Path) -> list[dict]:
    out = []
    for p in sorted((me / "pipeline" / "applications").glob("*/application.md")):
        fm = config.read_frontmatter(p) or {}
        text = p.read_text(encoding="utf-8")
        hist = _history(text)
        st = str(fm.get("durum") or "")
        ret_note = next((n for d, s, n in hist if s == "ret"), "")
        ret_date = next((d for d, s, n in hist if s == "ret"), "")
        out.append({
            "klasör": p.parent.name,
            "şirket": str(fm.get("şirket") or ""), "rol": str(fm.get("rol") or ""),
            "durum": st, "tarih": str(fm.get("başvuru_tarihi") or "")[:10],
            "uygunluk": str(fm.get("uygunluk_puanı") or "").split()[0] if str(fm.get("uygunluk_puanı") or "").strip() else "",
            "ats_raw": str(fm.get("ats_eşleşme") or ""), "ats": ats_pct(fm.get("ats_eşleşme")),
            "ats_need": ats_need(fm.get("ats_eşleşme")),
            "eksik_zorunlu": _split(fm.get("ats_eksik_zorunlu")), "eksik_tercih": _split(fm.get("ats_eksik_tercih")),
            "kaynak": str(fm.get("kaynak") or ""), "link": str(fm.get("ilan_linki") or ""),
            "ilan_id": str(fm.get("ilan_id") or ""), "worker": str(fm.get("worker") or ""),
            "iptal_sebebi": str(fm.get("iptal_sebebi") or ""),
            "yöntem": str(fm.get("başvuru_yöntemi") or ""),
            "terim_listesi": (p.parent / "ats-terimler.json").exists(),
            "ret_tarihi": ret_date, "ret_notu": ret_note,
            "son": hist[0] if hist else ("", st, ""),
        })
    return out


def _round_robin(groups: dict[str, list], limit: int) -> list:
    """Her sebepten sırayla birer ilan: ilk 20'de tek bir sebep baskın olmasın."""
    out, lists = [], [list(v) for _, v in sorted(groups.items(), key=lambda kv: -len(kv[1]))]
    while len(out) < limit and any(lists):
        for lst in lists:
            if lst and len(out) < limit:
                out.append(lst.pop(0))
    return out


REASON_GROUPS = [   # (grup, kalıp) — yalnızca özet için; satırda sebebin tamamı görünür
    ("tekrar / zaten başvuruldu", r"tekrar|zaten başvuruldu|aynı ilan"),
    ("aynı şirkette bekleme süresi", r"aynı şirket"),
    ("kara liste", r"kara liste"),
    ("dil (ilan dili ya da dil şartı)", r"ilan dili|almanca|dil şartı|^dil\b|dil/ses|dil:|ispanyolca|asturyaca"),
    ("ücret alt sınırın altında", r"ücret"),
    ("konum / ofis / hibrit", r"konum|ofis|hibrit|yer belirsiz|yalnızca abd|yalnızca i|kuzey amerika|north america|ülkeye bağlı|abd"),
    ("kıdem uyumsuz", r"kıdem|junior|\d+\+ yıl"),
    ("alan uzmanlığı şartı", r"alan uzmanl|sme|alan uyumsuz|alan şartı|istihbarat|veri mühendisliği|alanı"),
    ("rol uyumsuz (kod, altyapı, satış, ürün)", r"kod yoğun|altyapı|satış|ürün yönetimi|fde|mühendislik yöneticisi|öğrenci|okul"),
    ("ilan metni alınamadı", r"metni alınamadı"),
]


def reason_key(r: str) -> str:
    s = str(r).replace("İ", "i").lower()
    for name, pat in REASON_GROUPS:
        if re.search(pat, s):
            return name
    return re.split(r"[;:(]", s)[0].strip() or "—"


STALE_DAYS = 7


def source_status(me: Path, src_cfg: dict, today) -> list[dict]:
    """Her kaynağın en son ne zaman, nasıl tarandığı. Betik kaynakları tarama özetinden (meta.kaynaklar), tarayıcıyla ya da
    elle okunanlar `scan.py kaydet` kayıtlarından (meta.elle_okumalar) ve tarama dosyasına eklenen ilanlardan okunur."""
    from scanner.sources import ATS, FEEDS
    last: dict[str, dict] = {}

    def put(key, day, n, how, note=""):
        cur = last.get(key)
        if cur and cur["tarih"] == day and cur["yöntem"] != "betik":   # aynı gün birden çok elle okuma: topla
            cur["ilan"] = (cur["ilan"] or 0) + (n or 0)
            cur["yöntem"] = ", ".join(dict.fromkeys([cur["yöntem"], how]))
            cur["not"] = cur["not"] or note
        elif not cur or day >= cur["tarih"]:
            last[key] = {"tarih": day, "ilan": n, "yöntem": how, "not": note}
    for f in sorted((me / "pipeline" / "scans").glob("*.json")):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", f.stem):
            continue
        d = _json(f, {})
        meta, jobs = d.get("meta") or {}, d.get("jobs") or []
        by_src = Counter(j.get("source") for j in jobs)
        for s, st in (meta.get("kaynaklar") or {}).items():
            st = st or {}
            put(s, f.stem, st.get("eşleşen", by_src.get(s, 0)), "betik", st.get("uyarı") or st.get("hata") or "")
        for r in meta.get("elle_okumalar") or []:
            s, how = r.get("kaynak", "?"), str(r.get("yöntem") or "")
            key = "linkedin:arama" if s == "linkedin" and "arama" in how else "linkedin:link" if s == "linkedin" else s
            put(key, f.stem, r.get("ilan", 0), how, r.get("not", ""))

    feeds, manual = src_cfg.get("feeds") or {}, src_cfg.get("elle_kaynaklar") or {}
    n_watch = len(src_cfg.get("watchlist") or [])
    rows = []
    ats_last = max((last[s] for s in ATS if s in last), key=lambda x: x["tarih"], default=None)
    rows.append(("Şirket kariyer sayfaları", f"betik · Greenhouse / Lever / Ashby API · {n_watch} şirket", ats_last,
                 sum(last[s]["ilan"] for s in ATS if s in last and last[s]["tarih"] == (ats_last or {}).get("tarih")), True, ""))
    for s, mod in FEEDS.items():
        cfg = feeds.get(s) or {}
        regional = getattr(mod, "KAPSAM", "küresel") != "küresel"   # bölgesel akış yalnızca açıkça açılınca taranır
        on = cfg.get("enabled") is True if regional else cfg.get("enabled") is not False
        rows.append((s, "betik · bölgesel akış" if regional else "betik · açık akış", last.get(s),
                     (last.get(s) or {}).get("ilan"), on, "" if on else "me/sources.json'da kapalı"))
    # Betiği olmayan kaynaklar kişinin ayarından (me/sources.json → elle_kaynaklar): notu "taranmaz" diyorsa yalnızca link/e-postayla çalışır.
    passive_names = set()
    for s, note in manual.items():
        link_only = bool(re.search(r"taranmaz|yalnızca (iş alarmı|e-posta|link)", str(note), re.I))
        if link_only:
            passive_names.add(s)
        rows.append((s, "yalnızca senin linklerin / alarm e-postası" if link_only else "tarayıcıyla (kişinin isteğiyle, düşük hacim)",
                     last.get(s), (last.get(s) or {}).get("ilan"), True, (last.get(s) or {}).get("not") or str(note or "")))
    rows.append(("linkedin · arama", "tarayıcıyla, senin oturumunla (düşük hacim)", last.get("linkedin:arama"),
                 (last.get("linkedin:arama") or {}).get("ilan"), True, "LinkedIn otomasyonu yasaklıyor: yalnızca isteğinle"))
    rows.append(("linkedin · tekil link", "senin verdiğin ilan linkleri", last.get("linkedin:link"),
                 (last.get("linkedin:link") or {}).get("ilan"), True, ""))
    out = []
    for name, how, rec, n, on, note in rows:
        age = (today - datetime.fromisoformat(rec["tarih"]).date()).days if rec else None
        passive = name in passive_names or name == "linkedin · tekil link"   # yalnızca kişi link verince çalışır: "eski" sayılmaz
        out.append({"ad": name, "yöntem": how, "tarih": rec["tarih"] if rec else "", "gün": age, "ilan": n, "açık": on,
                    "not": note or (rec or {}).get("not", ""), "pasif": passive,
                    "eski": (age is None or age > STALE_DAYS) and on and not passive})
    return out


def collect(vault: Path = VAULT) -> dict:
    me = vault / "me"
    prefs = config.read_frontmatter(me / "profile" / "preferences.md") if (me / "profile" / "preferences.md").exists() else {}
    min_puan = int(prefs.get("min_uygunluk_puanı") or 0)
    day, scan = latest_scan(me)
    jobs, meta = scan.get("jobs", []), scan.get("meta", {})

    passed = sorted((j for j in jobs if "skor" in j and "elendi" not in j and j["skor"].get("puan", 0) >= min_puan),
                    key=lambda j: -j["skor"]["puan"])
    below = [j for j in jobs if "skor" in j and "elendi" not in j and j["skor"].get("puan", 0) < min_puan]
    dropped = [j for j in jobs if "elendi" in j]
    reasons = Counter(reason_key(j["elendi"]) for j in dropped)
    if below:
        reasons[f"uygunluk puanı < {min_puan}"] = len(below)
    groups: dict[str, list] = defaultdict(list)
    for j in dropped:
        groups[reason_key(j["elendi"])].append({"j": j, "sebep": j["elendi"]})
    for j in sorted(below, key=lambda j: -j["skor"]["puan"]):
        groups[f"uygunluk puanı < {min_puan}"].append({"j": j, "sebep": f"uygunluk puanı {j['skor']['puan']} < {min_puan}"})
    sample = _round_robin(groups, MAX_DROPPED)

    # kaynak bazında: betiğin sayıları (meta) + tarama dosyasındaki akıbet
    per = defaultdict(Counter)
    for j in jobs:
        c = per[j.get("source") or "?"]
        c["dosyada"] += 1
        c["elenen"] += "elendi" in j
        c["puanlanan"] += "skor" in j and "elendi" not in j
        c["listede"] += j in passed
    src_stats = meta.get("kaynaklar") or {}
    sources = []
    for name in sorted(set(per) | set(src_stats), key=lambda n: (-per[n]["listede"], -per[n]["dosyada"], n)):
        s = src_stats.get(name) or {}
        sources.append({"ad": name, **{k: s.get(k) for k in ("çekilen", "eski", "kara_liste", "dil_dışı", "eşleşen", "uyarı", "hata")},
                        **dict(per[name])})

    apps = [a for a in applications(me) if "başvuru değil" not in a["yöntem"]]   # ör. platform profil eki
    dec = latest_decisions(me)
    # Onaylanıp hazırlanmamış ilan yalnızca taze ise bekler: eski onaylar çoğunlukla sonradan vazgeçilmiş ya da ilanı kapanmıştır.
    fresh_days = int(_json(me / "sources.json", {}).get("max_age_days") or 7)
    cutoff = (datetime.now().date() - timedelta(days=fresh_days)).isoformat()
    app_ids = {a["ilan_id"] for a in apps if a["ilan_id"]}
    app_keys = {dedupe_key(a["şirket"], a["rol"]) for a in apps}
    approved_waiting = [r for r in dec.values() if r.get("karar") == "onay" and str(r.get("tarih") or "") >= cutoff
                        and r["id"] not in app_ids
                        and dedupe_key(str(r.get("şirket") or ""), str(r.get("rol") or "")) not in app_keys]

    src_cfg = _json(me / "sources.json", {})
    workers = config.load_workers(vault, only_active=False) if (me / "workers").exists() else []
    defaults = config.worker_defaults(vault)
    return {
        "üretildi": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "kurulum": profile.check(vault),
        "tarama": {"tarih": day, "zaman": meta.get("çalışma_zamanı", ""), "toplam": len(jobs), "min_puan": min_puan,
                   "geçen": passed, "elenen_sayı": len(dropped) + len(below), "sebepler": reasons.most_common(),
                   "örnek_elenen": sample, "notlar": meta.get("notlar") or [],
                   "yaş": meta.get("max_age_days"), "yaş_kapsam": meta.get("max_age_kapsam")},
        "kaynaklar": sources,
        "kaynak_durumu": source_status(me, _json(me / "sources.json", {}), datetime.now().date()),
        "başvurular": apps,
        "onaylı_bekleyen": approved_waiting,
        "ayar": {"kaynak": src_cfg, "workers": workers, "varsayılan": defaults, "tercih": prefs},
    }


# ------------------------------------------------------------------ HTML
def e(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def link(url, text) -> str:
    u = str(url or "")
    if re.match(r"^https?://", u):
        return f'<a href="{e(u)}" target="_blank" rel="noopener noreferrer">{e(text)}</a>'
    return e(text)


def band(p) -> str:
    try:
        p = int(p)
    except (TypeError, ValueError):
        return "none"
    return "hi" if p >= 75 else "mid" if p >= 60 else "lo"


def score(p, title="uygunluk puanı") -> str:
    return f'<span class="score {band(p)}" title="{e(title)}">{e(p) if p not in (None, "") else "—"}</span>'


def chips(items, cls="") -> str:
    return "".join(f'<span class="chip {cls}">{e(x)}</span>' for x in items) or '<span class="muted">—</span>'


def _term(x: str) -> str:
    return x.split("|")[0].strip()


def ats_cell(a: dict, missing: bool = True) -> str:
    p = a["ats"]
    if p is None:
        return '<span class="muted">ölçülmedi</span>'
    approx = a["ats_raw"].strip().startswith("~")
    w = max(0, min(100, p))
    need = a["ats_need"]
    note = ("kapıyı geçer" if p >= MIN_ATS else (f"%{MIN_ATS} için +{need} ağırlık puanı" if need else f"%{MIN_ATS} altı"))
    if a["durum"] == "hazırlandı" and not a.get("terim_listesi"):
        note += " · eski ölçüm: terim listesi kayıtlı değil, göndermeden önce yeniden ölçülmeli"
    out = (f'<div class="ats"><div class="bar"><span class="fill {"ok" if p >= MIN_ATS else "low"}" style="width:{w}%"></span>'
           f'<span class="gate" style="left:{MIN_ATS}%"></span></div>'
           f'<span class="num">{"~" if approx else ""}%{p}</span><span class="muted small">{e(note)}</span></div>')
    if missing and (a["eksik_zorunlu"] or a["eksik_tercih"]):
        out += ('<div class="miss"><span class="small muted">eksik:</span> '
                + chips([_term(x) for x in a["eksik_zorunlu"]], "req") * bool(a["eksik_zorunlu"])
                + (chips([_term(x) for x in a["eksik_tercih"]]) if a["eksik_tercih"] else "") + "</div>")
    return out


CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#1d2330;--muted:#677084;--line:#e3e6ec;--soft:#f0f2f6;--accent:#3b5bdb;
--hi:#1f8a4c;--hi-bg:#e3f4ea;--mid:#9a6a00;--mid-bg:#fdf1d6;--lo:#b4372c;--lo-bg:#fbe6e3;--none-bg:#eceef2;
--chip:#eef1f6;--warn:#8a5a00;--shadow:0 1px 2px rgba(20,30,50,.06),0 2px 8px rgba(20,30,50,.04)}
@media (prefers-color-scheme:dark){:root{--bg:#12151b;--card:#1a1f27;--ink:#e6e9ef;--muted:#98a1b3;--line:#2a313c;--soft:#202632;
--accent:#8ea8ff;--hi:#6fd49a;--hi-bg:#163323;--mid:#f0c060;--mid-bg:#3a2f12;--lo:#ff8f80;--lo-bg:#3a1a17;--none-bg:#262c37;
--chip:#252c38;--warn:#f0c060;--shadow:none}}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
header{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
.top{display:flex;align-items:center;gap:16px;flex-wrap:wrap;padding:12px 0}
.top h1{font-size:17px;margin:0;font-weight:650;letter-spacing:-.01em}
.top .meta{color:var(--muted);font-size:12.5px}
nav{display:flex;gap:4px;flex-wrap:wrap;margin-left:auto}
nav a{padding:5px 10px;border-radius:7px;color:var(--muted);font-size:13px}nav a:hover{background:var(--soft);color:var(--ink);text-decoration:none}
main{padding:20px 0 48px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:22px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;box-shadow:var(--shadow)}
.kpi .v{font-size:24px;font-weight:650;letter-spacing:-.02em}.kpi .l{color:var(--muted);font-size:12.5px}
section{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin-bottom:18px;box-shadow:var(--shadow);scroll-margin-top:70px}
section>h2{font-size:15.5px;margin:0 0 4px;font-weight:650}section>p.sub{margin:0 0 14px;color:var(--muted);font-size:13px}
h3{font-size:13.5px;margin:18px 0 8px;font-weight:650}
.tbl{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:13.2px}
th{text-align:left;font-weight:600;color:var(--muted);font-size:12px;border-bottom:1px solid var(--line);padding:7px 8px;white-space:nowrap}
td{border-bottom:1px solid var(--line);padding:9px 8px;vertical-align:top}tr:last-child td{border-bottom:0}
td .t{font-weight:600}td .c{color:var(--muted)}
.score{display:inline-block;min-width:34px;text-align:center;font-weight:700;border-radius:7px;padding:2px 7px;font-variant-numeric:tabular-nums}
.score.hi{color:var(--hi);background:var(--hi-bg)}.score.mid{color:var(--mid);background:var(--mid-bg)}.score.lo{color:var(--lo);background:var(--lo-bg)}.score.none{color:var(--muted);background:var(--none-bg)}
.chip{display:inline-block;background:var(--chip);border-radius:6px;padding:1px 7px;margin:2px 4px 2px 0;font-size:12px}
.chip.req{box-shadow:inset 0 0 0 1px var(--lo)}.chip.src{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11.5px}
.warn{color:var(--warn);font-size:12.3px;margin-top:4px}
.muted{color:var(--muted)}.small{font-size:12px}
.pill{display:inline-block;border-radius:999px;padding:1px 9px;font-size:12px;font-weight:600;background:var(--soft);color:var(--muted)}
.pill.ret{background:var(--lo-bg);color:var(--lo)}.pill.ok{background:var(--hi-bg);color:var(--hi)}.pill.wait{background:var(--mid-bg);color:var(--mid)}
.ats{display:grid;grid-template-columns:110px minmax(0,1fr);gap:2px 8px;align-items:center}
.ats .bar{position:relative;height:8px;border-radius:5px;background:var(--soft);overflow:visible}
.ats .fill{position:absolute;left:0;top:0;bottom:0;border-radius:5px}.ats .fill.ok{background:var(--hi)}.ats .fill.low{background:var(--lo)}
.ats .gate{position:absolute;top:-3px;bottom:-3px;width:2px;background:var(--ink);opacity:.55}
.ats .num{font-weight:700;font-variant-numeric:tabular-nums}.ats .small{grid-column:1/-1}
details{border:1px solid var(--line);border-radius:10px;margin-top:14px;background:var(--soft)}
summary{cursor:pointer;padding:10px 14px;font-weight:600;list-style:none;display:flex;align-items:center;gap:8px}
summary::-webkit-details-marker{display:none}summary:before{content:"▸";color:var(--muted);transition:transform .15s}
details[open] summary:before{transform:rotate(90deg)}
details .inner{padding:4px 14px 14px;background:var(--card);border-top:1px solid var(--line);border-radius:0 0 10px 10px}
.reasons{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 6px}.reasons .chip b{font-variant-numeric:tabular-nums}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
dl{display:grid;grid-template-columns:max-content 1fr;gap:6px 14px;margin:0;font-size:13.2px}dt{color:var(--muted)}dd{margin:0}
.empty{color:var(--muted);padding:10px 0}
td.role{min-width:160px;max-width:300px}td.atscol{min-width:220px;max-width:380px;width:42%}.miss{margin-top:6px;line-height:1.9}
td .t,td .c{overflow-wrap:anywhere}
footer{color:var(--muted);font-size:12px;text-align:center;padding:10px 0 30px}
.steps{list-style:none;display:flex;flex-wrap:wrap;gap:6px 18px;padding:0;margin:6px 0 12px}
.steps li{display:flex;align-items:center;gap:7px;color:var(--muted);font-size:13px}
.steps .dot{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:var(--soft);font-size:11.5px;font-weight:700}
.steps li.done{color:var(--ink)}.steps li.done .dot{background:var(--hi-bg);color:var(--hi)}
.steps li.now{color:var(--ink);font-weight:650}.steps li.now .dot{background:var(--accent);color:#fff}
.setup.compact{padding:10px 18px}.setup.compact .steps{margin:0}.setup.compact details{margin-top:8px}
.setup ul{margin:6px 0;padding-left:18px}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;background:var(--soft);padding:1px 5px;border-radius:5px}
@media (max-width:640px){.wrap{padding:0 12px}section{padding:14px}nav{margin-left:0}}
"""


def _table(head: list[str], rows: list[str], empty: str) -> str:
    if not rows:
        return f'<p class="empty">{e(empty)}</p>'
    return ('<div class="tbl"><table><thead><tr>' + "".join(f"<th>{e(h)}</th>" for h in head) + "</tr></thead><tbody>"
            + "".join(rows) + "</tbody></table></div>")


def _job_title(j: dict) -> str:
    return f'<div class="t">{link(j.get("url"), j.get("title", ""))}</div><div class="c">{e(j.get("company", ""))}</div>'


STAGES = ["1 · Tanışma", "2 · Kanıt", "3 · Analiz", "4 · İş tanımları", "5 · Worker'lar", "6 · Tamamlama"]
STAGE_HINT = {
    "1 · Tanışma": "LinkedIn profilin okunur, güçlü yanların, çekincelerin, hayalindeki iş, çalışma biçimin ve konumun konuşulur.",
    "2 · Kanıt": "Her yetkinliğe somut bir kanıt bağlanır (en az 5). CV ve puanlama yalnızca kanıtı olanı kullanır.",
    "3 · Analiz": "Kanıtlı güçler, açıklar ve erişilebilir pazar üzerine kariyer analizi yazılır.",
    "4 · İş tanımları": "3–6 iş tanımı önerilir; senin onayladıkların taranır.",
    "5 · Worker'lar": "Her onaylı tanımdan bir arama profili (worker) kurulur: roller, çalışma tipi, yer, ücret.",
    "6 · Tamamlama": "İlan ve CV dilleri, form cevapları, kaynaklar ve kara liste tamamlanır.",
}


def setup_card(k: dict) -> str:
    """Kurulum ilerlemesi: aşamalar, eksikler ve sıradaki adım. Kurulum tamamsa tek satıra iner."""
    if not k.get("me", True):
        return ('<section id="kurulum" class="setup"><h2>Kurulum</h2><p class="sub">Bu vault henüz bir kişi için kurulmadı.</p>'
                '<p><b>Sıradaki adım:</b> Claude Code\'da <code>/coach</code> yaz. Kariyer koçu profilini kurar; panel her adımda dolar.</p></section>')
    stage = k.get("aşama", "")
    done_n = len(STAGES) if stage == "tamam" else (STAGES.index(stage) if stage in STAGES else 0)
    steps = "".join(
        f'<li class="{"done" if i < done_n else "now" if i == done_n else ""}"><span class="dot">{"✓" if i < done_n else i + 1}</span>'
        f'<span>{e(s.split(" · ", 1)[1])}</span></li>' for i, s in enumerate(STAGES))
    eksik = k.get("eksikler") or []
    if stage == "tamam":
        more = (f'<details><summary>Tamamlanabilecek {len(eksik)} küçük eksik</summary><div class="inner"><ul class="small">'
                + "".join(f"<li>{e(x)}</li>" for x in eksik) + "</ul></div></details>") if eksik else ""
        return f'<section id="kurulum" class="setup compact"><ol class="steps">{steps}</ol>{more}</section>'
    ready = k.get("hazır")
    nxt = ("Profil taramaya hazır; kalan aşamaları uygun bir anda tamamla. Tarama için <code>/scan</code>."
           if ready else "Claude Code'da <code>/coach</code> yaz; kaldığın yerden devam eder. Profil hazır olunca tarama açılır.")
    return (f'<section id="kurulum" class="setup"><h2>Kurulum — {e(stage)}</h2>'
            f'<p class="sub">{e(STAGE_HINT.get(stage, ""))}</p><ol class="steps">{steps}</ol>'
            f'<p><b>Sıradaki adım:</b> {nxt}</p>'
            + (f'<details open><summary>Eksikler ({len(eksik)})</summary><div class="inner"><ul class="small">'
               + "".join(f"<li>{e(x)}</li>" for x in eksik[:12]) + "</ul></div></details>" if eksik else "")
            + "</section>")


def render(d: dict) -> str:
    t, apps = d["tarama"], d["başvurular"]
    sent = [a for a in apps if a["durum"] in SENT]
    rejected = [a for a in apps if a["durum"] == "ret"]
    waiting = [a for a in apps if a["durum"] == "hazırlandı"]
    passed = t["geçen"]

    kpis = [(t["toplam"], "son taramada eşleşen"), (len(passed), "onay listesinde"), (t["elenen_sayı"], "elenen / eşik altı"),
            (len(waiting) + len(d["onaylı_bekleyen"]), "bekleyen başvuru"), (len(sent), "gönderilen"), (len(rejected), "ret")]
    kpi_html = "".join(f'<div class="kpi"><div class="v">{e(v)}</div><div class="l">{e(l)}</div></div>' for v, l in kpis)

    # --- son tarama
    rows = []
    for j in passed:
        k, s = j["skor"], j.get("sınıf") or {}
        yer = s.get("yer") or j.get("workplace") or "?"
        warns = "".join(f'<div class="warn">⚠ {e(w)}</div>' for w in (k.get("uyarılar") or [])[:3])
        rows.append(f'<tr><td>{score(k.get("puan"))}</td><td>{_job_title(j)}<div class="small muted" style="margin-top:3px">'
                    f'{e(k.get("gerekçe", ""))}</div>{warns}</td>'
                    f'<td><span class="chip src">{e(j.get("source"))}</span><div class="small muted">{e(s.get("tip", "?"))} · {e(yer)}</div></td>'
                    f'<td>{chips(k.get("eksikler") or [])}</td></tr>')
    passed_tbl = _table(["Puan", "İlan", "Kaynak · tip/yer", "Profil eksikleri (kanıt yok)"], rows,
                        "Bu taramada eşiği geçen ilan yok." if t["tarih"] else
                        "Henüz tarama yok. Profil hazır olunca Claude Code'da /scan yaz; ilanlar burada görünür.")
    reasons = "".join(f'<span class="chip">{e(r)} <b>{n}</b></span>' for r, n in t["sebepler"])
    drows = [f'<tr><td>{_job_title(x["j"])}</td><td><span class="chip src">{e(x["j"].get("source"))}</span></td>'
             f'<td>{e(x["sebep"])}</td></tr>' for x in t["örnek_elenen"]]
    dropped_html = "" if not t["elenen_sayı"] else (f'<details><summary>Elenenler ve eşik altı — {t["elenen_sayı"]} ilan '
                    f'<span class="muted small">(ilk {min(MAX_DROPPED, t["elenen_sayı"])} gösteriliyor, her sebepten sırayla)</span></summary>'
                    f'<div class="inner"><div class="reasons">{reasons}</div>'
                    + _table(["İlan", "Kaynak", "Neden"], drows, "Elenen ilan yok.") + "</div></details>")
    notes = "".join(f'<div class="warn">⚠ {e(n)}</div>' for n in t["notlar"] if re.search(r"uyarı|429|okunmadı|hata", str(n), re.I))

    # --- başvurular
    def app_row(a, with_state=True):
        state = a["durum"]
        cls = "ret" if state == "ret" else "ok" if state in ("mülakat", "teklif") else "wait" if state == "hazırlandı" else ""
        return (f'<tr><td class="role"><div class="t">{link(a["link"], a["rol"])}</div><div class="c">{e(a["şirket"])}</div></td>'
                + (f'<td><span class="pill {cls}">{e(STATE_LABEL.get(state, state))}</span>'
                   f'<div class="small muted">{e(a["tarih"] or "—")}</div></td>' if with_state else "")
                + f'<td>{score(a["uygunluk"])}</td><td class="atscol">{ats_cell(a)}</td></tr>')
    wait_rows = [app_row(a) for a in waiting]
    wait_rows += [f'<tr><td><div class="t">{link(r.get("url"), r.get("rol", ""))}</div><div class="c">{e(r.get("şirket", ""))}</div></td>'
                  f'<td><span class="pill wait">onaylandı</span><div class="small muted">{e(r.get("tarih", ""))}</div></td>'
                  f'<td>{score(r.get("puan"))}</td><td class="atscol"><span class="muted">hazırlanmadı</span></td></tr>'
                  for r in d["onaylı_bekleyen"]]
    head = ["Rol · şirket", "Durum", "Uygunluk", "ATS · eksik kelimeler"]
    apps_html = ("<h3>Bekleyenler</h3>" + _table(head, wait_rows, "Bekleyen başvuru yok.")
                 + "<h3>Gönderilenler</h3>" + _table(head, [app_row(a) for a in sorted(sent, key=lambda a: a["tarih"], reverse=True)],
                                                      "Gönderilmiş başvuru yok."))

    rej_rows = [f'<tr><td class="role"><div class="t">{link(a["link"], a["rol"])}</div><div class="c">{e(a["şirket"])}</div>'
                f'<div class="small muted" style="margin-top:4px">{e(a["ret_notu"] or "sebep bildirilmedi")}</div></td>'
                f'<td class="small">{e(a["tarih"] or "—")} →<br>{e(a["ret_tarihi"] or "—")}</td><td>{score(a["uygunluk"])}</td>'
                f'<td class="atscol">{ats_cell(a)}</td></tr>' for a in rejected]
    rej_html = _table(["Rol · şirket · not", "Gönderim → ret", "Uygunluk", "ATS · eksik kelimeler"], rej_rows, "Ret gelen başvuru yok.")

    # --- kaynaklar
    def n(v):
        return "—" if v in (None, "") else e(v)
    def script_cell(s):
        parts = [(s.get("çekilen"), "çekildi"), (s.get("eski"), f"eski (> {t['yaş'] or '?'} gün)"),
                 (s.get("kara_liste"), "kara liste"), (s.get("dil_dışı"), "dil dışı")]
        txt = " · ".join(f"<b>{e(v)}</b> {e(l)}" for v, l in parts if v not in (None, "", 0))
        return txt or '<span class="muted">elle eklendi</span>'
    src_rows = [f'<tr><td><span class="chip src">{e(s["ad"])}</span>' + (f'<div class="warn">⚠ {e(s["uyarı"])}</div>' if s.get("uyarı") else "")
                + (f'<div class="warn">⚠ hata: {e(s["hata"])}</div>' if s.get("hata") else "")
                + f'</td><td class="small">{script_cell(s)}</td><td>{n(s.get("dosyada", 0))}</td><td>{n(s.get("elenen", 0))}</td>'
                f'<td>{n(s.get("puanlanan", 0))}</td><td><b>{n(s.get("listede", 0))}</b></td></tr>' for s in d["kaynaklar"]]
    src_html = _table(["Kaynak", "Betik", "Eşleşen", "Elenen", "Puanlanan", "Listede"],
                      src_rows, "Bu taramada kaynak bilgisi yok.")

    # --- kaynak durumu
    def when(s):
        if not s["açık"]:
            return '<span class="pill">kapalı</span>'
        if not s["tarih"]:
            return '<span class="pill">link gelince</span>' if s["pasif"] else '<span class="pill wait">hiç taranmadı</span>'
        ago = "bugün" if s["gün"] == 0 else "dün" if s["gün"] == 1 else f'{s["gün"]} gün önce'
        return (f'<div>{e(s["tarih"])}</div><span class="pill {"wait" if s["eski"] else "ok"}">{e(ago)}</span>')
    st_rows = [f'<tr><td><span class="t">{e(s["ad"])}</span><div class="small muted">{e(s["yöntem"])}</div></td>'
               f'<td>{when(s)}</td><td>{"—" if s["ilan"] in (None, "") or not s["tarih"] else e(s["ilan"])}</td>'
               f'<td class="small">{e(s["not"]) or "<span class=muted>—</span>"}</td></tr>' for s in d["kaynak_durumu"]]
    status_html = _table(["Kaynak · yöntem", "Son tarama", "O gün gelen", "Not"], st_rows, "Kaynak yok.")
    stale = [s["ad"] for s in d["kaynak_durumu"] if s["eski"]]

    # --- bilgi
    a = d["ayar"]
    src, defaults, prefs = a["kaynak"], a["varsayılan"], a["tercih"]
    feeds = src.get("feeds") or {}
    feed_rows = "".join(f'<span class="chip {"" if (v or {}).get("enabled") else "muted"}">{e(k)}: {"açık" if (v or {}).get("enabled") else "kapalı"}</span>'
                        for k, v in feeds.items() if not k.startswith("_") and isinstance(v, dict))
    wl = defaultdict(list)
    for w in src.get("watchlist") or []:
        wl[w.get("ats", "?")].append(w.get("company", w.get("token", "")))
    wl_html = "".join(f'<div style="margin:4px 0"><span class="chip src">{e(k)}</span> {e(", ".join(v))}</div>' for k, v in sorted(wl.items()))
    manual = ", ".join((src.get("elle_kaynaklar") or {}).keys())
    kr = defaults.get("kısmi_remote") or {}
    kr_txt = (f'{", ".join(kr.get("tipler") or [])} · en az %{kr.get("min_remote_yüzde")} remote · yerinde: {", ".join(kr.get("şehirler") or [])}'
              if kr.get("tipler") else "yok")
    kl = prefs.get("kara_liste") or {}
    crit = [
        ("Yer", ", ".join(defaults.get("yer") or []) or "—"),
        ("Kısmi remote istisnası", kr_txt),
        ("İzinli ülke / bölge", ", ".join(defaults.get("ülkeler") or []) or "—"),
        ("İlan dili", ", ".join(defaults.get("ilan_dilleri") or []) or "—"),
        ("Haftalık saat", "–".join(str(x) for x in (defaults.get("haftalık_saat") or {}).values()) or "—"),
        ("Tazelik", f'son {src.get("max_age_days", "?")} gün içinde açılan ya da yeniden yayımlanan · kapsam: {src.get("max_age_kapsam", "akışlar")}'),
        ("Daha önce görülen", f'{src.get("seen_süresi_gün", 90)} gün boyunca tekrar gösterilmez'),
        ("Onay listesi eşiği", f'uygunluk ≥ {prefs.get("min_uygunluk_puanı", "?")} · en fazla {prefs.get("onay_listesi_üst_sınır", "?")} ilan'),
        ("ATS kapısı", f"%{MIN_ATS} altı gönderilmez (sabit kural)"),
        ("Kara liste", f'{len(kl.get("şirketler") or [])} şirket ({", ".join(kl.get("şirketler") or [])}) · {len(kl.get("anahtar_kelimeler") or [])} anahtar kelime'),
        ("Başlıkta hariç", ", ".join(defaults.get("ortak_hariç_başlık") or []) or "—"),
    ]
    crit_html = "<dl>" + "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in crit) + "</dl>"
    wrows = []
    for w in a["workers"]:
        active = w.get("_aktif")
        mu = w.get("min_ücret") or {}
        wrows.append(f'<tr><td><span class="t">{e(w.get("ad"))}</span><div class="small muted">{e(w.get("tanım", ""))}</div></td>'
                     f'<td><span class="pill {"ok" if active else ""}">{"aktif" if active else "duraklatıldı"}</span></td>'
                     f'<td class="small">{e(", ".join(w.get("çalışma_tipi") or []))}</td>'
                     f'<td class="small">{e(mu.get("tutar", "—"))} {e(mu.get("para_birimi", ""))} {e(mu.get("birim", ""))}</td>'
                     f'<td><details style="margin:0;background:transparent;border:0"><summary style="padding:0;font-weight:500">'
                     f'{len(w.get("roller") or [])} rol</summary><div class="small" style="padding-top:6px">{chips(w.get("roller") or [])}'
                     f'<div class="muted" style="margin-top:6px">hariç: {e(", ".join(w.get("hariç_başlık") or []))}</div></div></details></td></tr>')
    workers_html = _table(["Worker · iş tanımı", "Durum", "Çalışma tipi", "Ücret alt sınırı", "Roller"], wrows,
                          "Henüz worker yok: iş tanımlarını onayladığında coach her biri için bir arama profili kurar.")
    info_html = (f'<div class="grid2"><div><h3>Taranan kaynaklar</h3><div style="margin-bottom:8px">{feed_rows or "<span class=muted>—</span>"}</div>'
                 f'<div class="small muted">Şirket kariyer sayfaları (takip listesi, {sum(len(v) for v in wl.values())} şirket):</div>{wl_html or "<span class=muted>—</span>"}'
                 f'<div class="small muted" style="margin-top:8px">Elle / tarayıcıyla okunan: {e(manual or "—")}</div></div>'
                 f'<div><h3>Tarama kriterleri</h3>{crit_html}</div></div><h3>Worker\'lar (arama profilleri)</h3>{workers_html}')

    nav = "".join(f'<a href="#{i}">{e(l)}</a>' for i, l in
                  [("tarama", "Son tarama"), ("basvurular", "Başvurular"), ("retler", "Retler"), ("kaynaklar", "Kaynaklar"), ("bilgi", "Bilgi")])
    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HRVault paneli</title><style>{CSS}</style></head><body>
<header><div class="wrap top"><h1>HRVault paneli</h1><span class="meta">son tarama {e(t["tarih"] or "—")} · üretildi {e(d["üretildi"])}</span><nav>{nav}</nav></div></header>
<main class="wrap">
{setup_card(d.get("kurulum") or {})}
<div class="kpis">{kpi_html}</div>
<section id="tarama"><h2>Son tarama{" — " + e(t["tarih"]) if t["tarih"] else ""}</h2>
<p class="sub">Onay listesine giren ilanlar (uygunluk ≥ {e(t["min_puan"])}). Puan profildeki kanıta göre; ATS ölçümü başvuru hazırlanırken yapılır.</p>
{notes}{passed_tbl}{dropped_html}</section>
<section id="basvurular"><h2>Başvurular</h2>
<p class="sub">ATS: ilandan çıkarılan kelimelerin CV'de ölçülen eşleşmesi; dikey çizgi %{MIN_ATS} kapısı. Eksik kelimelerde kırmızı çerçeve
zorunlu şart (+2 ağırlık), diğerleri tercih (+1). Kanıtı olan eksik CV'ye eklenir, olmayan eklenmez.</p>
{apps_html}</section>
<section id="retler"><h2>Ret gelenler</h2><p class="sub">Yüksek ATS'li bir başvurunun reddi çoğu zaman kelimeden değil başka bir eleyiciden gelir (form cevapları, konum, kıdem).</p>
{rej_html}</section>
<section id="kaynaklar"><h2>Kaynaklar</h2>
<p class="sub">Her kaynağın en son ne zaman tarandığı. Betik kaynakları her taramada okunur; tarayıcıyla okunanlar ve LinkedIn yalnızca
senin isteğinle. {f'{STALE_DAYS} günden uzun süredir taranmayan: ' + e(", ".join(stale)) + '.' if stale else ''}</p>
{status_html}
<h3>Son taramanın kaynak dökümü — {e(t["tarih"] or "—")}</h3>
<p class="sub">"Betik": kaynaktan çekilen ve yaş, kara liste ya da ilan dili yüzünden otomatik elenen ilanlar. Sağdaki sütunlar rollerle
eşleşen ilanların akıbeti: sınıflandırmada elenen, puanlanan, onay listesine giren.</p>
{src_html}</section>
<section id="bilgi"><h2>Bilgi: kaynaklar ve tarama kriterleri</h2>{info_html}</section>
<footer>Bu sayfa <code>me/</code> içindeki kayıtlardan üretildi ve yalnızca bu bilgisayarda durur. Yeniden üret:
<code>python3 engine/pipeline/dashboard.py</code></footer>
</main></body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser(description="HRVault paneli (me/dashboard.html)")
    ap.add_argument("--out", default=str(VAULT / "me" / "dashboard.html"))
    ap.add_argument("--open", action="store_true", help="yazdıktan sonra varsayılan tarayıcıda aç")
    a = ap.parse_args()
    out = Path(a.out).resolve()
    if (VAULT / "me").resolve() not in out.parents:
        sys.exit("Panel kişisel veri içerir; yalnızca me/ altına yazılır.")
    if not (VAULT / "me").exists():
        # Panel me/'yi kendisi kurmaz: kurulum coach'un işi (profile.py init). Kişiye yolu göster.
        print("me/ yok: bu vault henüz kurulmadı. Claude Code'da /coach yaz (ya da `python3 engine/pipeline/profile.py init`),\n"
              "sonra paneli yeniden üret. Panel kurulumun her adımında dolar.")
        return 1
    out.write_text(render(collect(VAULT)), encoding="utf-8")
    print(f"Yazıldı: {out.relative_to(VAULT)} ({out.stat().st_size // 1024} KB)")
    if a.open:
        webbrowser.open(out.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
