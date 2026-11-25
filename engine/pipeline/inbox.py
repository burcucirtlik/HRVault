#!/usr/bin/env python3
"""HRVault onay listesi.

Kullanım (vault kökünden):
  python3 engine/pipeline/inbox.py filter   [--scan YYYY-MM-DD]
  python3 engine/pipeline/inbox.py rate     <id|sıra> (--json '{...}' | --drop SEBEP) [--scan …]
  python3 engine/pipeline/inbox.py render   [--scan YYYY-MM-DD]
  python3 engine/pipeline/inbox.py mark     [--approve 1,3] [--reject '2=sebep' …] [--date …]
  python3 engine/pipeline/inbox.py decisions [--date YYYY-MM-DD] [--record]
  python3 engine/pipeline/inbox.py log [--json]

Akış: scan skill'i ilanları sınıflandırır → `filter` kesin kuralları uygular →
score skill'i kalanları puanlar (`rate`) → `render` günlük onay listesini yazar →
kişi işaretler (dosyada ya da sohbette → `mark`) → `decisions` apply ve learn'e verir.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from scanner import config  # noqa: E402
from scanner.common import company_blocked  # noqa: E402
from scanner.scan import _fold, dedupe_key  # noqa: E402,F401

VAULT = HERE.parent.parent
PIPE = VAULT / "me" / "pipeline"

SCAM = re.compile(
    r"telegram|whats\s?app|signal app|"
    r"(?:pay|purchase|buy)\b.{0,40}\b(?:training|equipment|starter kit|software|fee)|"
    r"registration fee|processing fee|"
    r"send you a check|deposit (?:the|a) check|cashier'?s check|"
    r"bank account (?:number|details)|social security number|\bSSN\b|passport (?:number|copy)",
    re.I,
)


# ------------------------------------------------------------------ yardımcılar
def _today() -> str:
    return date.today().isoformat()


def _scan_path(day: str | None) -> Path:
    return PIPE / "scans" / f"{day or _today()}.json"


def _inbox_path(day: str | None) -> Path:
    return PIPE / "inbox" / f"{day or _today()}.md"


def _load(p: Path):
    if not p.exists():
        sys.exit(f"Dosya yok: {p.relative_to(VAULT)}")
    return json.loads(p.read_text(encoding="utf-8"))


def _save(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _prefs() -> dict:
    p = VAULT / "me" / "profile" / "preferences.md"
    return config.read_frontmatter(p) if p.exists() else {}


def _find(jobs: list, ref: str):
    j = next((x for x in jobs if x["id"] == ref), None)
    if j is None and ref.isdigit() and 0 < int(ref) <= len(jobs):
        j = jobs[int(ref) - 1]
    return j


def _applications() -> list[dict]:
    out = []
    for p in (PIPE / "applications").glob("*/application.md"):
        fm = config.read_frontmatter(p)
        if fm:
            out.append(fm)
    return out


# ------------------------------------------------------------------ filter
def cmd_filter(a) -> int:
    """Kesin kurallar: kara liste, mevcut başvuru. Dolandırıcılık kalıplarını eleme değil
    uyarı olarak işaretler; kararı score skill'i verir."""
    p = _scan_path(a.scan)
    data = _load(p)
    prefs = _prefs()
    kl = prefs.get("kara_liste") or {}
    bad_companies = [_fold(x) for x in kl.get("şirketler") or [] if x]
    bad_words = [x for x in kl.get("anahtar_kelimeler") or [] if x]

    apps = _applications()
    applied_links = {str(ap.get("ilan_linki") or "") for ap in apps} - {""}
    applied_keys = {dedupe_key(str(ap.get("şirket") or ""), str(ap.get("rol") or "")) for ap in apps}

    unclassified, dropped, flagged, ready = 0, Counter(), 0, []
    for i, j in enumerate(data["jobs"], 1):
        if "elendi" in j:
            continue
        if "sınıf" not in j:
            unclassified += 1
            continue
        comp = _fold(j.get("company", ""))
        text = f"{j.get('title', '')}\n{j.get('description', '')}"
        reason = None
        if company_blocked(j.get("company", ""), kl.get("şirketler") or []):
            reason = "kara liste: şirket"
        elif any(re.search(rf"\b{re.escape(w)}\b", text, re.I) for w in bad_words):
            reason = "kara liste: anahtar kelime"
        elif "skor" not in j and (j.get("url") in applied_links or j.get("key") in applied_keys):
            # Puanlanmış ilan filtreyi zaten geçmiştir; başvurusu bu listeden yapılmış olabilir.
            # Yeniden çalışan filter onu "zaten başvuruldu" diye eleyip puanını silmemeli.
            reason = "zaten başvuruldu"
        if reason:
            j["elendi"] = reason
            j.pop("skor", None)
            dropped[reason.split(":")[0]] += 1
            continue
        hits = sorted({m.group(0).strip() for m in SCAM.finditer(text)})
        if hits:
            j["scam_sinyal"] = hits[:5]
            flagged += 1
        if "skor" not in j:
            ready.append((i, j))
    _save(p, data)

    print(f"Filtre · {p.relative_to(VAULT)}")
    if unclassified:
        print(f"  ! sınıflandırılmamış {unclassified} ilan var — önce scan skill'i (brief/annotate)")
    for r, n in dropped.items():
        print(f"  elendi: {r} · {n}")
    if flagged:
        print(f"  dolandırıcılık kalıbı geçen {flagged} ilan işaretlendi (score skill'i karar verir)")
    print(f"Puanlanacak: {len(ready)}")
    for i, j in ready:
        s = j["sınıf"]
        warn = f" · ⚠ {', '.join(j['scam_sinyal'])}" if j.get("scam_sinyal") else ""
        print(f"  {i:3}. [{','.join(j['workers'])}] {j['company']} — {j['title']} · "
              f"{s.get('tip', '?')}/{s.get('yer', '?')}{warn}")
    return 0


# ------------------------------------------------------------------ rate
def cmd_rate(a) -> int:
    p = _scan_path(a.scan)
    data = _load(p)
    j = _find(data["jobs"], a.ref)
    if j is None:
        print("İlan bulunamadı.")
        return 1
    if a.drop:
        j["elendi"] = a.drop
        j.pop("skor", None)
    else:
        try:
            skor = json.loads(a.json)
        except (TypeError, json.JSONDecodeError) as e:
            print(f"--json geçerli JSON olmalı: {e}")
            return 1
        if not isinstance(skor.get("puan"), (int, float)) or not 0 <= skor["puan"] <= 100:
            print("`puan` 0–100 arası sayı olmalı.")
            return 1
        j["skor"] = skor
        j.pop("elendi", None)
    _save(p, data)
    print(f"ok {j['id']}: " + (f"elendi ({a.drop})" if a.drop else f"puan {j['skor']['puan']}"))
    return 0


# ------------------------------------------------------------------ inbox biçimi
ITEM = re.compile(r"^## (?P<head>.+?)\n(?P<body>.*?)(?=^## |^---\s*$|\Z)", re.S | re.M)


def parse_inbox(text: str) -> list[dict]:
    items = []
    for m in ITEM.finditer(text):
        body = m.group("body")
        idm = re.search(r"<!--\s*id:\s*(\S+)\s*-->", body)
        if not idm:
            continue
        num = re.match(r"(\d+)", m.group("head"))
        retm = re.search(r"^- ret:[ \t]*(.*)$", body, re.M)
        items.append({
            "no": int(num.group(1)) if num else None,
            "id": idm.group(1),
            "baslik": m.group("head").strip(),
            "onay": bool(re.search(r"^- \[[xX]\] onay", body, re.M)),
            "ret": (retm.group(1).strip() if retm else ""),
        })
    return items


def _fmt_item(no: int, j: dict, keep: dict | None) -> str:
    s, k = j.get("sınıf") or {}, j.get("skor") or {}
    yer = s.get("yer") or j.get("workplace") or "?"
    if s.get("ülke_kısıtı"):
        yer += f" ({', '.join(s['ülke_kısıtı'])})"
    facts = [f"worker: {', '.join(j['workers'])}", f"tip: {s.get('tip', '?')}", f"yer: {yer}"]
    if s.get("saat"):
        facts.append(f"saat: {s['saat']}/hafta")
    facts.append(f"ücret: {s.get('ücret') or j.get('salary') or '?'}")
    links = f"kaynak: {j['source']} · [ilan]({j['url']})"
    if j.get("apply_url") and j["apply_url"] != j["url"]:
        links += f" · [başvuru]({j['apply_url']})"
    warns = list(k.get("uyarılar") or [])
    if s.get("belirsiz"):
        warns.append("belirsiz: " + ", ".join(s["belirsiz"]))
    lines = [
        f"## {no} · {k.get('puan', '?')} · {j['title']} — {j['company']}",
        f"<!-- id: {j['id']} -->",
        f"- [{'x' if keep and keep['onay'] else ' '}] onay",
        "- " + " · ".join(facts),
        f"- {links}",
        f"- **neden uygun:** {k.get('gerekçe', '')}",
    ]
    if k.get("eksikler"):
        lines.append(f"- **eksikler:** {', '.join(k['eksikler'])}")
    if warns:
        lines.append(f"- **uyarılar:** {'; '.join(warns)}")
    lines.append(f"- ret: {keep['ret'] if keep else ''}".rstrip())
    return "\n".join(lines)


# ------------------------------------------------------------------ render
def cmd_render(a) -> int:
    day = a.scan or _today()
    data = _load(_scan_path(day))
    prefs = _prefs()
    min_puan = int(prefs.get("min_uygunluk_puanı") or 0)
    cap = int(prefs.get("onay_listesi_üst_sınır") or 20)

    jobs = data["jobs"]
    scored = [j for j in jobs if "skor" in j and "elendi" not in j]
    below = [j for j in scored if j["skor"]["puan"] < min_puan]
    shown = sorted((j for j in scored if j["skor"]["puan"] >= min_puan),
                   key=lambda j: -j["skor"]["puan"])
    overflow = shown[cap:]
    shown = shown[:cap]
    pending = [j for j in jobs if "skor" not in j and "elendi" not in j]

    # mevcut işaretleri koru; eski sıra korunur, yeniler sona eklenir
    ip = _inbox_path(day)
    old = {x["id"]: x for x in parse_inbox(ip.read_text(encoding="utf-8"))} if ip.exists() else {}
    old_order = list(old)
    shown.sort(key=lambda j: (old_order.index(j["id"]) if j["id"] in old else len(old_order), -j["skor"]["puan"]))
    lost = [x for x in old.values() if (x["onay"] or x["ret"]) and x["id"] not in {j["id"] for j in shown}]

    reasons = Counter(re.split(r"[;:(]", j["elendi"])[0].strip() for j in jobs if "elendi" in j)
    meta = data.get("meta", {})
    head = [
        "---",
        f"tarih: {day}",
        f"aktif_worker: [{', '.join(meta.get('aktif_worker', []))}]",
        f"taranan: {len(jobs)}",
        f"elenen: {sum(reasons.values()) + len(below)}",
        f"onaya_sunulan: {len(shown)}",
        f"güncelleme: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "---",
        f"# Onay listesi — {day}",
        "",
        "> Başvurmak istediklerini `[x]` yap. Reddettiklerine `ret:` ile kısa sebep yazarsan",
        "> motor tercihlerini öğrenir. Sonra Claude'a \"onaylananlara başvur\" de.",
        "> Sohbetten de olur: \"1 ve 3'e başvur, 2'yi reddet: çok kıdemli\".",
        "",
    ]
    if pending:
        head += [f"> ⚠ {len(pending)} ilan henüz puanlanmadı; liste eksik olabilir.", ""]
    body = [_fmt_item(n, j, old.get(j["id"])) for n, j in enumerate(shown, 1)]
    if not shown:
        body = ["_Bugün eşiği geçen ilan yok._"]

    tail = ["", "---", "<details><summary>Elenenler ve eşik altı</summary>", ""]
    for r, n in reasons.most_common():
        tail.append(f"- {r}: {n}")
    if below:
        tail.append(f"- puan < {min_puan}: {len(below)}")
        for j in sorted(below, key=lambda j: -j["skor"]["puan"])[:10]:
            tail.append(f"  - {j['skor']['puan']} · {j['title']} — {j['company']} ([ilan]({j['url']}))")
    if overflow:
        tail.append(f"- üst sınır ({cap}) dışında kalan: {len(overflow)}")
    tail += ["", "</details>", ""]

    ip.parent.mkdir(parents=True, exist_ok=True)
    ip.write_text("\n".join(head) + "\n" + "\n\n".join(body) + "\n" + "\n".join(tail), encoding="utf-8")
    print(f"Yazıldı: {ip.relative_to(VAULT)} · onaya sunulan {len(shown)} · eşik altı {len(below)}"
          f" · elenen {sum(reasons.values())} · puanlanmamış {len(pending)}")
    for x in lost:
        print(f"  ! işaretli ilan listeden düştü: {x['baslik']} ({x['id']})")
    return 0


# ------------------------------------------------------------------ mark
def cmd_mark(a) -> int:
    ip = _inbox_path(a.date)
    if not ip.exists():
        print(f"Onay listesi yok: {ip.relative_to(VAULT)}")
        return 1
    text = ip.read_text(encoding="utf-8")
    approve = {int(x) for x in (a.approve or "").replace(" ", "").split(",") if x}
    reject = {}
    for r in a.reject or []:
        no, _, why = r.partition("=")
        reject[int(no)] = why.strip() or "—"

    def fix(m: re.Match) -> str:
        head, body = m.group("head"), m.group("body")
        num = re.match(r"(\d+)", head)
        n = int(num.group(1)) if num else None
        if n in approve:
            body = re.sub(r"^- \[[ xX]\] onay", "- [x] onay", body, flags=re.M)
            body = re.sub(r"^- ret:.*$", "- ret:", body, flags=re.M)
        if n in reject:
            body = re.sub(r"^- \[[ xX]\] onay", "- [ ] onay", body, flags=re.M)
            body = re.sub(r"^- ret:.*$", f"- ret: {reject[n]}", body, flags=re.M)
        return f"## {head}\n{body}"

    known = {x["no"] for x in parse_inbox(text)}
    missing = (approve | set(reject)) - known
    if missing:
        print(f"Listede olmayan numara: {sorted(missing)}")
        return 1
    ip.write_text(ITEM.sub(fix, text), encoding="utf-8")
    print(f"ok · onay: {sorted(approve) or '-'} · ret: {sorted(reject) or '-'}")
    return 0


# ------------------------------------------------------------------ decisions
def cmd_decisions(a) -> int:
    day = a.date or _today()
    ip = _inbox_path(day)
    if not ip.exists():
        print(f"Onay listesi yok: {ip.relative_to(VAULT)}")
        return 1
    items = parse_inbox(ip.read_text(encoding="utf-8"))
    sp = _scan_path(day)
    jobs = {j["id"]: j for j in json.loads(sp.read_text(encoding="utf-8"))["jobs"]} if sp.exists() else {}

    def info(x):
        j = jobs.get(x["id"], {})
        return {"no": x["no"], "id": x["id"], "şirket": j.get("company"), "rol": j.get("title"),
                "worker": j.get("workers"), "puan": (j.get("skor") or {}).get("puan"),
                "url": j.get("url"), "apply_url": j.get("apply_url"), "kaynak": j.get("source")}

    out = {
        "tarih": day,
        "onaylanan": [info(x) for x in items if x["onay"]],
        "reddedilen": [info(x) | {"sebep": x["ret"]} for x in items if x["ret"] and not x["onay"]],
        "bekleyen": [x["no"] for x in items if not x["onay"] and not x["ret"]],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))

    if a.record:
        last = latest_decisions()
        new = []
        for kind, rows in (("onay", out["onaylanan"]), ("ret", out["reddedilen"])):
            for r in rows:
                prev = last.get(r["id"])
                if prev and prev["karar"] == kind and prev.get("sebep", "") == r.get("sebep", ""):
                    continue  # aynı karar zaten kayıtlı
                new.append({"tarih": day, "zaman": datetime.now().isoformat(timespec="seconds"), "karar": kind, **r})
        if new:
            with DECISIONS.open("a", encoding="utf-8") as f:
                for r in new:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"kaydedildi: {len(new)} yeni karar → {DECISIONS.relative_to(VAULT)}", file=sys.stderr)
    return 0


DECISIONS = PIPE / "decisions.jsonl"


def read_decisions() -> list[dict]:
    """decisions.jsonl satırları, yazılma sırasıyla. Bozuk satır atlanır."""
    rows = []
    if DECISIONS.exists():
        for line in DECISIONS.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(r, dict) and r.get("id") and r.get("karar"):
                rows.append(r)
    return rows


def latest_decisions() -> dict[str, dict]:
    """İlan id'si → son karar. Günlük yalnızca eklenir; aynı ilan için sonraki satır öncekini geçersiz kılar.
    Sıra numarası (`no`) yalnızca o günün listesindeki konumdur, anahtar değildir."""
    out: dict[str, dict] = {}
    for r in read_decisions():
        out[r["id"]] = r
    return out


def cmd_log(a) -> int:
    """Her ilan için geçerli (son) kararı göster."""
    rows = sorted(latest_decisions().values(), key=lambda r: (r.get("tarih", ""), r.get("zaman", "")))
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    c = Counter(r["karar"] for r in rows)
    print(f"Geçerli kararlar: {len(rows)} · " + " · ".join(f"{k}: {v}" for k, v in c.items()))
    for r in rows:
        why = f" — {r['sebep']}" if r.get("sebep") else ""
        print(f"  {r.get('tarih', '?')} · {r['karar']:6} · {r.get('puan') or '?':>3} · {r.get('şirket')} — {r.get('rol')}{why}")
    return 0


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser(description="HRVault onay listesi")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("filter", help="kesin kuralları uygula, puanlanacakları listele")
    f.add_argument("--scan")
    r = sub.add_parser("rate", help="ilana puan yaz veya ele")
    r.add_argument("ref")
    r.add_argument("--json", help='{"puan":78,"gerekçe":"…","eksikler":["…"],"uyarılar":["…"]}')
    r.add_argument("--drop", metavar="SEBEP")
    r.add_argument("--scan")
    n = sub.add_parser("render", help="günlük onay listesini yaz")
    n.add_argument("--scan")
    m = sub.add_parser("mark", help="sohbetten gelen onay/ret kararlarını listeye işle")
    m.add_argument("--approve", help="virgülle numaralar, ör. 1,3,5")
    m.add_argument("--reject", action="append", help="'no=sebep', tekrar edilebilir")
    m.add_argument("--date")
    d = sub.add_parser("decisions", help="onaylanan / reddedilen ilanları JSON olarak ver")
    d.add_argument("--date")
    d.add_argument("--record", action="store_true", help="me/pipeline/decisions.jsonl'a ekle (learn için)")
    lg = sub.add_parser("log", help="her ilan için geçerli (son) kararı göster")
    lg.add_argument("--json", action="store_true")
    a = ap.parse_args()
    return {"filter": cmd_filter, "rate": cmd_rate, "render": cmd_render,
            "mark": cmd_mark, "decisions": cmd_decisions, "log": cmd_log}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
