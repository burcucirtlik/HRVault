#!/usr/bin/env python3
"""Öğrenme raporu — tarama, karar ve başvuru kayıtlarından "neyi değiştirmeli" sorusunun verisi.

Kullanım (vault kökünden):
  python3 engine/pipeline/learn.py rapor     [--gün 30]   # üçü birden
  python3 engine/pipeline/learn.py verim     [--gün 30]   # rol kelimesi / kaynak / worker hunisi
  python3 engine/pipeline/learn.py elemeler  [--gün 30]   # tekrar eden eleme sebepleri ve kaynağı olan kelimeler
  python3 engine/pipeline/learn.py bekleyen  [--sessiz-gün 30]

Huni (her ilan bir kez sayılır; çok kelimeyle eşleşen ilan her kelimede sayılır):
  betik → kaldı (sınıflandırma + kesin kurallardan sonra) → listede (puan ≥ min_uygunluk_puanı) → onay → başvuru → cevap
Bu betik **karar vermez**: gürültülü kelime, ölü rol ve tekrar eden eleme sebebi önerisi üretir. Worker, rol, kara liste
değişikliği kişinin onayıyla yapılır (mode / coach skill'leri). Okur, yazmaz.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from pipeline import inbox, records  # noqa: E402
from scanner import config  # noqa: E402
from scanner.common import fold  # noqa: E402
from scanner.scan import dedupe_key  # noqa: E402

VAULT = HERE.parent.parent
PIPE = VAULT / "me" / "pipeline"
STAGES = ["betik", "kaldı", "listede", "onay", "başvuru", "cevap"]
SENT = {"başvuruldu", "görüldü", "mülakat", "teklif", "ret", "sessiz"}
RESPONDED = {"görüldü", "mülakat", "teklif", "ret"}
# Kurala bağlı ya da tekrar niteliğinde sebepler: kişiye yeni filtre önermek için anlamsız.
RULE_REASONS = re.compile(r"^(?:kara liste|zaten başvuruldu|tekrar|aynı şirket|atlandı)", re.I)
NOISY_MIN = 8      # bu kadar ilan getirip listeye %5'ten azını sokan kelime gürültü adayıdır
NOISY_RATE = 0.05
CLUSTER_MIN = 3    # learn skill'inin "3+ tekrar" kuralı


# ------------------------------------------------------------------ veri
def _rank(j: dict) -> int:
    return 0 if "elendi" in j else 2 if "skor" in j else 1


def load_jobs(pipe: Path, days: int) -> list[dict]:
    """Tarama dosyalarındaki ilanlar (son `days` gün; 0 = hepsi). Aynı id birden çok dosyadaysa en ileri gittiği kayıt
    tutulur: sonraki taramada "zaten başvuruldu" diye elenen kopya, puanlanmış ilk kaydı silmemeli."""
    since = (date.today() - timedelta(days=days)).isoformat() if days else ""
    out: dict[str, dict] = {}
    for p in sorted((pipe / "scans").glob("*.json")):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.stem) or p.stem < since:
            continue
        for j in json.loads(p.read_text(encoding="utf-8")).get("jobs", []):
            prev = out.get(j["id"])
            if prev is None or _rank(j) >= _rank(prev):
                out[j["id"]] = j | {"_tarih": p.stem}
    return list(out.values())


def reason_key(r: str) -> str:
    """Eleme sebebinin ilk parçası: "dil/ses uzmanlığı (…); …" → "dil/ses uzmanlığı"."""
    # "İ".lower() birleşik nokta bırakır ("i̇ngiltere")
    return re.split(r"[;:(]", str(r))[0].strip().replace("İ", "i").lower()


def scan_count(pipe: Path, days: int) -> int:
    since = (date.today() - timedelta(days=days)).isoformat() if days else ""
    return sum(1 for p in (pipe / "scans").glob("*.json")
               if re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.stem) and p.stem >= since)


def _manual(kw: str) -> bool:
    """Rol değil, elle ekleme işareti ("linkedin-arama", "(elle)")."""
    return kw.startswith(("linkedin", "("))


# ------------------------------------------------------------------ huni
def stage_of(j: dict, decisions: dict, apps_by_id: dict, min_puan: int, apps_by_key: dict | None = None) -> list[str]:
    """İlanın geçtiği aşamalar. Başvuru önce ilan id'siyle, bulunamazsa şirket+rol anahtarıyla eşlenir
    (elle hazırlanan başvurularda `ilan_id` başka kaynağın id'si olabiliyor)."""
    st = ["betik"]
    app = apps_by_id.get(j["id"]) or (apps_by_key or {}).get(j.get("key") or "")
    sent = bool(app) and str(app.get("durum")) in SENT
    # Gönderilmiş başvuru, sonradan eklenen "zaten başvuruldu" etiketinden güçlü kanıttır.
    if "elendi" in j and not sent:
        return st
    st.append("kaldı")
    try:
        app_puan = int(str((app or {}).get("uygunluk_puanı") or "").split()[0])
    except (ValueError, IndexError):
        app_puan = -1
    if max((j.get("skor") or {}).get("puan", -1), app_puan) >= min_puan:
        st.append("listede")
    if (decisions.get(j["id"]) or {}).get("karar") == "onay" or sent:
        st.append("onay")
    if sent:
        st.append("başvuru")
        if str(app.get("durum")) in RESPONDED | {"mülakat", "teklif"}:
            st.append("cevap")
    return st


def funnel(jobs: list[dict], decisions: dict, apps: list[dict], min_puan: int) -> dict[str, dict]:
    """→ {"kelime": {anahtar: Counter}, "kaynak": …, "worker": …}."""
    apps_by_id = {str(a.get("ilan_id")): a for a in apps if a.get("ilan_id")}
    apps_by_key = {dedupe_key(str(a.get("şirket") or ""), str(a.get("rol") or "")): a for a in apps}
    out = {"kelime": defaultdict(Counter), "kaynak": defaultdict(Counter), "worker": defaultdict(Counter)}
    for j in jobs:
        st = stage_of(j, decisions, apps_by_id, min_puan, apps_by_key)
        keys = {"kelime": j.get("matched") or ["(elle)"], "kaynak": [j.get("source") or "?"],
                "worker": j.get("workers") or ["?"]}
        for dim, ks in keys.items():
            for k in ks:
                out[dim][k].update(st)
    return out


def noisy(by_kw: dict, jobs: list[dict], min_n: int = NOISY_MIN) -> list[tuple[str, int, list, int]]:
    """Çok ilan getirip listeye pek sokamayan kelimeler → (kelime, ilan, en sık eleme sebepleri, listede)."""
    out = []
    for kw, c in by_kw.items():
        if c["betik"] >= min_n and c["listede"] <= NOISY_RATE * c["betik"] and not _manual(kw):
            why = Counter(reason_key(j["elendi"]) for j in jobs if kw in (j.get("matched") or []) and "elendi" in j)
            out.append((kw, c["betik"], why.most_common(2), c["listede"]))
    return sorted(out, key=lambda x: -x[1])


def dead_roles(workers: list[dict], by_kw: dict) -> dict[str, list[str]]:
    """Aktif worker'larda olup penceredeki taramalarda hiç ilan getirmeyen roller, worker'a göre."""
    out = {}
    for w in workers:
        dead = [r for r in w.get("roller") or [] if by_kw.get(r, Counter())["betik"] == 0]
        if dead:
            out[w["ad"]] = dead
    return out


# ------------------------------------------------------------------ elemeler
def drop_clusters(jobs: list[dict], min_n: int = CLUSTER_MIN) -> list[dict]:
    """Tekrar eden eleme sebepleri; her biri için ilanları getiren kelimeler ve örnek başlıklar."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for j in jobs:
        if "elendi" in j:
            k = reason_key(j["elendi"])
            if k and not RULE_REASONS.match(k):
                groups[k].append(j)
    out = []
    for k, js in groups.items():
        if len(js) < min_n:
            continue
        kws = Counter(m for j in js for m in (j.get("matched") or ["(elle)"]))
        top, n = kws.most_common(1)[0]
        out.append({"sebep": k, "sayı": len(js), "kelimeler": kws.most_common(3),
                    "örnek": [j.get("title", "") for j in js[:2]],
                    # Sebebin çoğu tek kelimeden geliyorsa düzeltme yeri o kelimedir.
                    "öneri": (f"elle eklenen ilanlar ({top}): eklemeden önce bu sebebi kontrol et"
                              if n / len(js) >= 0.6 and _manual(top) else
                              f"'{top}' rolünü gözden geçir (bu sebebin {n}/{len(js)} ilanı ondan)"
                              if n / len(js) >= 0.6 else
                              "ortak başlık kalıbı varsa worker hariç_başlık'a, metin kalıbıysa kara listeye eklemeyi öner")})
    return sorted(out, key=lambda x: -x["sayı"])


# ------------------------------------------------------------------ bekleyenler
def pending(decisions: dict, apps: list[tuple[str, dict]], learnings: str, today: date,
            silent_days: int = 30) -> list[str]:
    """learn'in kişiye sorması ya da işlemesi gerekenler."""
    out = []
    for r in decisions.values():
        sebep = str(r.get("sebep") or "")
        if r.get("karar") == "ret" and (not sebep.strip() or "belirtilmedi" in sebep):
            out.append(f"sebepsiz ret kararı: {r.get('şirket')} — {r.get('rol')} ({r.get('tarih')}) → kişiye bir kez sor")
    lf = fold(learnings)
    for name, fm in apps:
        st = str(fm.get("durum") or "")
        who = f"{fm.get('şirket')} — {fm.get('rol')}"
        if st == "iptal" and str(fm.get("iptal_sebebi") or "belirtilmedi").strip() in ("", "belirtilmedi"):
            out.append(f"sebepsiz iptal: {who} → kişiye bir kez sor")
        if st in ("ret", "mülakat", "teklif") and fold(str(fm.get("şirket") or "")) not in lf:
            out.append(f"sonuç öğrenime işlenmemiş ({st}): {who} → me/learnings.md "
                       f"'{'Ne işe yaradı' if st != 'ret' else 'Ne işe yaramadı'}'")
        sent = str(fm.get("başvuru_tarihi") or "")[:10]
        if st in ("başvuruldu", "görüldü") and sent:
            try:
                age = (today - date.fromisoformat(sent)).days
            except ValueError:
                continue
            if age >= silent_days:
                out.append(f"sessiz adayı ({age} gün cevap yok): {who} → track.py set {name} sessiz")
    return out


# ------------------------------------------------------------------ çıktı
def _row(label: str, c: Counter) -> str:
    return f"  {label[:34]:34} " + " · ".join(f"{s} {c[s]}" for s in STAGES)


def _context(days: int):
    prefs = config.read_frontmatter(VAULT / "me" / "profile" / "preferences.md") \
        if (VAULT / "me" / "profile" / "preferences.md").exists() else {}
    min_puan = int(prefs.get("min_uygunluk_puanı") or 0)
    jobs = load_jobs(PIPE, days)
    dec = inbox.latest_decisions()
    apps = records.all_apps()
    return jobs, dec, apps, min_puan


def cmd_verim(a) -> int:
    jobs, dec, apps, min_puan = _context(a.gün)
    if not jobs:
        print("Pencerede tarama yok.")
        return 0
    f = funnel(jobs, dec, [fm for _, fm in apps], min_puan)
    n_scans = scan_count(PIPE, a.gün)
    print(f"## Verim — son {a.gün or 'tüm'} gün · {n_scans} tarama · {len(jobs)} ilan · liste eşiği {min_puan}")
    if n_scans < 5:
        print("  (az tarama: rol çıkarma / değiştirme önerilerini kesin karar sayma)")
    for dim in ("kaynak", "worker"):
        print(f"{dim.capitalize()}:")
        for k, c in sorted(f[dim].items(), key=lambda x: -x[1]["betik"]):
            print(_row(k, c))
    print("Rol kelimesi (en çok ilan getiren 15):")
    for k, c in sorted(f["kelime"].items(), key=lambda x: -x[1]["betik"])[:15]:
        print(_row(k, c))
    nz = noisy(f["kelime"], jobs)
    if nz:
        print(f"Gürültü adayları ({NOISY_MIN}+ ilan, listeye %{int(NOISY_RATE * 100)}'ten az) — rolü çıkarmayı ya da "
              "daraltmayı kişiye öner:")
        for kw, n, why, listed in nz:
            print(f"  - {kw}: {n} ilan, listede {listed} · elenme: " + ", ".join(f"{r} {c}" for r, c in why))
    dead = dead_roles(config.load_workers(VAULT), f["kelime"])
    if dead:
        total = sum(len(v) for v in dead.values())
        print(f"Hiç ilan getirmeyen roller ({total}) — çok özelse genel bir başlıkla değiştirmeyi öner:")
        for w, rs in dead.items():
            print(f"  - {w}: {', '.join(rs)}")
    return 0


def cmd_elemeler(a) -> int:
    jobs, *_ = _context(a.gün)
    cl = drop_clusters(jobs)
    print(f"## Tekrar eden eleme sebepleri ({CLUSTER_MIN}+) — son {a.gün or 'tüm'} gün")
    if not cl:
        print("  yok")
    for c in cl:
        print(f"- {c['sebep']}: {c['sayı']} · kelimeler: " + ", ".join(f"{k} {n}" for k, n in c["kelimeler"]))
        print(f"    örnek: {' | '.join(t[:60] for t in c['örnek'])}")
        print(f"    öneri: {c['öneri']}")
    return 0


def cmd_bekleyen(a) -> int:
    _, dec, apps, _ = _context(0)
    lp = VAULT / "me" / "learnings.md"
    items = pending(dec, [(d.name, fm) for d, fm in apps], lp.read_text(encoding="utf-8") if lp.exists() else "",
                    date.today(), a.sessiz_gün)
    print("## Bekleyen öğrenimler")
    for x in items or ["yok"]:
        print(f"- {x}")
    return 0


def cmd_rapor(a) -> int:
    for f in (cmd_verim, cmd_elemeler, cmd_bekleyen):
        f(a)
        print()
    print("Bu rapor öneri üretir; worker / rol / kara liste değişikliği kişinin onayıyla yapılır.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="HRVault öğrenme raporu")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("rapor", "verim", "elemeler", "bekleyen"):
        p = sub.add_parser(name)
        p.add_argument("--gün", type=int, default=30, help="tarama penceresi; 0 = hepsi")
        p.add_argument("--sessiz-gün", dest="sessiz_gün", type=int, default=30)
    a = ap.parse_args()
    return {"rapor": cmd_rapor, "verim": cmd_verim, "elemeler": cmd_elemeler, "bekleyen": cmd_bekleyen}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
