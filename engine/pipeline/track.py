#!/usr/bin/env python3
"""HRVault başvuru takibi.

Kullanım (vault kökünden):
  python3 engine/pipeline/track.py list   [--all] [--json]       # başvuru tablosu (iptal hariç; --all ile dahil)
  python3 engine/pipeline/track.py due    [--today YYYY-MM-DD]   # takip tarihi gelenler
  python3 engine/pipeline/track.py stats                          # dönüşüm: worker ve puan bandına göre
  python3 engine/pipeline/track.py set <başvuru> <durum> [--not "…"] [--sebep "…"] [--takip-gün 10]

Durumlar: hazırlandı → başvuruldu → görüldü → mülakat → teklif | ret | sessiz | iptal.
`iptal` için --sebep zorunludur (learn kullanır). `başvuruldu` yapılınca başvuru ve takip tarihi yazılır.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from pipeline import records  # noqa: E402

ACTIVE = {"başvuruldu", "görüldü"}
RESPONDED = {"görüldü", "mülakat", "teklif", "ret"}
POSITIVE = {"mülakat", "teklif"}


def _d(s) -> date | None:
    try:
        return date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def _workers(fm) -> list[str]:
    w = fm.get("worker") or ""
    return [x.strip() for x in (w if isinstance(w, list) else str(w).split(",")) if x.strip()] or ["?"]


def cmd_list(a) -> int:
    rows = []
    today = date.today()
    for d, fm in records.all_apps():
        st = str(fm.get("durum") or "")
        if st == "iptal" and not a.all:
            continue
        sent = _d(fm.get("başvuru_tarihi"))
        rows.append({"klasör": d.name, "tarih": str(sent or ""), "şirket": fm.get("şirket"), "rol": fm.get("rol"),
                     "worker": ", ".join(_workers(fm)), "puan": fm.get("uygunluk_puanı"), "ats": fm.get("ats_eşleşme"),
                     "durum": st, "gün": (today - sent).days if sent else None, "takip": str(fm.get("takip_tarihi") or "")})
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    print(f"{'tarih':10}  {'durum':10} {'gün':>3}  {'puan':>4}  şirket — rol  [worker]")
    for r in sorted(rows, key=lambda r: (r["tarih"] or "9999", r["şirket"] or "")):
        print(f"{r['tarih'] or '—':10}  {r['durum']:10} {'' if r['gün'] is None else r['gün']:>3}  "
              f"{r['puan'] or '?':>4}  {r['şirket']} — {str(r['rol'])[:60]}  [{r['worker']}]")
    return 0


def cmd_due(a) -> int:
    today = _d(a.today) if a.today else date.today()
    due, stale = [], []
    for d, fm in records.all_apps():
        st = str(fm.get("durum") or "")
        t = _d(fm.get("takip_tarihi"))
        if st in ACTIVE and t and t <= today:
            due.append((t, d, fm))
        if st == "hazırlandı":
            stale.append((d, fm))
    if not due and not stale:
        print("Takip tarihi gelen başvuru yok.")
        return 0
    for t, d, fm in sorted(due, key=lambda x: x[0]):
        late = (today - t).days
        print(f"TAKİP  {fm.get('şirket')} — {fm.get('rol')} · takip {t} ({late} gün geçti) · {d.name}")
        print("       öneri: kısa bir takip mesajı ya da `set … sessiz`")
    for d, fm in stale:
        print(f"BEKLİYOR  {fm.get('şirket')} — {fm.get('rol')} · hazırlandı ama gönderilmedi · {d.name}")
    return 0


def cmd_stats(_a) -> int:
    apps = [fm for _, fm in records.all_apps() if str(fm.get("durum")) not in ("hazırlandı", "iptal", "")]
    cancelled = [fm for _, fm in records.all_apps() if str(fm.get("durum")) == "iptal"]
    if not apps:
        print("Gönderilmiş başvuru yok.")
        return 0

    def line(label, group):
        n = len(group)
        resp = sum(str(f.get("durum")) in RESPONDED for f in group)
        pos = sum(str(f.get("durum")) in POSITIVE for f in group)
        return f"  {label:28} {n:>3} başvuru · cevap {resp} ({100 * resp // n}%) · mülakat+ {pos} ({100 * pos // n}%)"

    print(f"Toplam gönderilen: {len(apps)} · iptal: {len(cancelled)}")
    print(line("hepsi", apps))
    by_w = defaultdict(list)
    for f in apps:
        for w in _workers(f):
            by_w[w].append(f)
    print("Worker'a göre (çok worker'lı başvuru her birinde sayılır):")
    for w, g in sorted(by_w.items(), key=lambda x: -len(x[1])):
        print(line(w, g))
    bands = defaultdict(list)
    for f in apps:
        try:
            p = int(str(f.get("uygunluk_puanı")).strip())
            bands["85+" if p >= 85 else "70–84" if p >= 70 else "60–69" if p >= 60 else "<60"].append(f)
        except ValueError:
            bands["puansız"].append(f)
    print("Puan bandına göre (eşiği kalibre etmek için):")
    for b in ("85+", "70–84", "60–69", "<60", "puansız"):
        if bands.get(b):
            print(line(b, bands[b]))
    no_reason = [f for f in cancelled if str(f.get("iptal_sebebi") or "belirtilmedi") == "belirtilmedi"]
    if no_reason:
        print(f"Not: {len(no_reason)} iptalin sebebi belirtilmemiş — learn için kişiye sor.")
    return 0


def cmd_set(a) -> int:
    if a.durum not in records.STATES:
        sys.exit(f"Geçersiz durum: {a.durum}. Geçerli: {', '.join(records.STATES)}")
    if a.durum == "iptal" and not a.sebep:
        sys.exit("iptal için --sebep gerekli (kişiye sor; learn bu sebebi kullanır).")
    d = records.app_dir(a.app)
    today = date.today()
    fields = {"durum": a.durum, "son_güncelleme": today.isoformat()}
    if a.durum == "başvuruldu":
        fm = records.read(d)
        fields["başvuru_tarihi"] = fm.get("başvuru_tarihi") or today.isoformat()
        fields["takip_tarihi"] = (today + timedelta(days=a.takip_gün)).isoformat()
    if a.durum == "iptal":
        fields["iptal_sebebi"] = a.sebep
    if a.durum in ("ret", "teklif", "sessiz", "iptal"):
        fields["takip_tarihi"] = ""
    note = a.durum + (f" — {a.sebep}" if a.sebep else "") + (f" — {a.not_}" if a.not_ else "")
    records.update(d, fields, history=note)
    print(f"ok {d.name}: {a.durum}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="HRVault başvuru takibi")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("--all", action="store_true", help="iptalleri de göster")
    ls.add_argument("--json", action="store_true")
    du = sub.add_parser("due")
    du.add_argument("--today")
    sub.add_parser("stats")
    s = sub.add_parser("set")
    s.add_argument("app")
    s.add_argument("durum")
    s.add_argument("--sebep")
    s.add_argument("--not", dest="not_")
    s.add_argument("--takip-gün", dest="takip_gün", type=int, default=10)
    a = ap.parse_args()
    return {"list": cmd_list, "due": cmd_due, "stats": cmd_stats, "set": cmd_set}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
