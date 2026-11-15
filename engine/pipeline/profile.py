#!/usr/bin/env python3
"""HRVault profil kontrolü.

Kullanım (vault kökünden):
  python3 engine/pipeline/profile.py init      # me/ yoksa şablondan kur (varsa dokunmaz)
  python3 engine/pipeline/profile.py check     # neyin dolu, neyin eksik olduğunu raporla
  python3 engine/pipeline/profile.py check --json
  python3 engine/pipeline/profile.py doctor    # ortam ön koşulları (Python, Chrome, ağ, git)
  python3 engine/pipeline/profile.py gate      # oturum başı tek satır durum (SessionStart hook'u)

coach ilerlemeyi takip etmek, score ise profilin puanlamaya hazır olup olmadığını
anlamak için kullanır.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from scanner import config  # noqa: E402

VAULT = HERE.parent.parent
ME = VAULT / "me"
TEMPLATE = VAULT / "engine" / "templates" / "me"

# answers.md içinde boş kalırsa coach'un sorması gereken alanlar
ANSWERS_CORE = [
    "full_name", "email", "location", "linkedin_url",
    "work_authorization", "requires_sponsorship", "earliest_start_date",
    "timezone", "currency",
]
ANSWERS_BY_TYPE = {
    "full-time": ["salary_expectation_annual", "notice_period"],
    "part-time": ["hourly_rate", "availability_hours_per_week"],
    "freelance": ["hourly_rate", "availability_hours_per_week"],
    "contract": ["hourly_rate", "availability_hours_per_week"],
}


def cmd_init(_a) -> int:
    if ME.exists():
        missing = []
        for src in TEMPLATE.rglob("*"):
            dst = ME / src.relative_to(TEMPLATE)
            if not dst.exists():
                if src.is_dir():
                    dst.mkdir(parents=True, exist_ok=True)
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                missing.append(str(dst.relative_to(VAULT)))
        print("me/ zaten var." + (f" Eksik şablon dosyaları eklendi: {', '.join(missing)}" if missing else ""))
        return 0
    shutil.copytree(TEMPLATE, ME)
    print("me/ şablondan kuruldu.")
    return 0


# ------------------------------------------------------------------ ayrıştırıcılar
def _strip_comments(t: str) -> str:
    return re.sub(r"<!--.*?-->", "", t, flags=re.S)


def answers(path: Path) -> dict:
    out = {}
    if not path.exists():
        return out
    for line in _strip_comments(path.read_text(encoding="utf-8")).splitlines():
        m = re.match(r"^\s*-\s*([a-z_]+):\s*(.*)$", line)
        if m:
            val = re.sub(r"(?:^|\s+)#.*$", "", m.group(2)).strip()
            out[m.group(1)] = val
    return out


def cv_status(path: Path) -> dict:
    t = _strip_comments(path.read_text(encoding="utf-8")) if path.exists() else ""
    name = re.search(r"^- Ad Soyad:[ \t]*(\S.*)$", t, re.M)
    roles = [h for h in re.findall(r"^### (.+)$", t, re.M) if "Rol — Şirket" not in h and "Bölüm — Okul" not in h]
    bullets = [b for b in re.findall(r"^- (.+)$", t, re.M)
               if not re.match(r"(Ad Soyad|E-posta|Telefon|Lokasyon|LinkedIn|Portfolyo|Madde)", b)]
    summary = re.search(r"^## Özet[ \t]*\n(.*?)(?=^## |\Z)", t, re.S | re.M)
    return {
        "ad": bool(name and name.group(1).strip()),
        "özet": bool(summary and summary.group(1).strip()),
        "deneyim_başlığı": len(roles),
        "madde": len(bullets),
    }


def evidence_status(path: Path) -> dict:
    t = _strip_comments(path.read_text(encoding="utf-8")) if path.exists() else ""
    sections = re.split(r"^## ", t, flags=re.M)
    res = {"hard": [], "soft": [], "vaka": 0, "kanıtsız": []}
    for sec in sections:
        title, _, body = sec.partition("\n")
        kind = "hard" if title.lower().startswith("hard") else "soft" if title.lower().startswith("soft") else \
            "vaka" if title.lower().startswith("vaka") else None
        if not kind:
            continue
        for sk in re.split(r"^### ", body, flags=re.M)[1:]:
            name, _, sbody = sk.partition("\n")
            name = name.strip()
            if name.startswith("<") or name.startswith("vaka-01: <"):
                continue
            if kind == "vaka":
                res["vaka"] += 1
                continue
            proofs = [p for p in re.findall(r"^\s+- \*\*\[(.+?)\]\*\*\s*(.+)$", sbody, re.M)
                      if "Rol/Proje" not in p[0] and "Durum, yıl" not in p[0]]
            res[kind].append(name)
            if not proofs:
                res["kanıtsız"].append(name)
    return res


def sections(path: Path) -> dict:
    """`## Başlık` → gövde (yorumlar çıkarılmış). Boş liste satırları (`- alan:`) boş sayılır."""
    t = _strip_comments(path.read_text(encoding="utf-8")) if path.exists() else ""
    out = {}
    for h, body in re.findall(r"^## (.+?)\n(.*?)(?=^## |\Z)", t, re.S | re.M):
        out[h.strip()] = re.sub(r"^- [^:\n]+:[ \t]*$", "", body.strip(), flags=re.M).strip()
    return out


def definitions(path: Path) -> list[dict]:
    """job-definitions.md → [{id, ad, durum, tür, worker}]"""
    t = _strip_comments(path.read_text(encoding="utf-8")) if path.exists() else ""
    out = []
    for m in re.finditer(r"^### (T\d+):\s*(.+?)\n(.*?)(?=^### |\Z)", t, re.S | re.M):
        body = m.group(3)
        field = lambda k: (re.search(rf"^- {k}:[ \t]*([^#\n]*)", body, re.M) or [None, ""])[1].strip()  # noqa: E731
        out.append({"id": m.group(1), "ad": m.group(2).strip(), "durum": field("durum") or "önerildi",
                    "tür": field("tür"), "worker": field("worker")})
    return out


GOALS_CORE = ["Hayalimdeki iş ve sektör", "Nasıl çalışmak istiyorum"]


def check() -> dict:
    if not ME.exists():
        return {"hazır": False, "me": False, "eksikler": ["me/ yok — `profile.py init`"]}
    workers = config.load_workers(VAULT, only_active=False)
    active = [w for w in workers if w["_aktif"]]
    ans = answers(ME / "profile" / "answers.md")
    cv = cv_status(ME / "profile" / "cv-master.md")
    ev = evidence_status(ME / "profile" / "evidence-bank.md")
    prefs_p = ME / "profile" / "preferences.md"
    prefs = config.read_frontmatter(prefs_p) if prefs_p.exists() else {}

    types = {t for w in active for t in (w.get("çalışma_tipi") or [])}
    need = ANSWERS_CORE + sorted({k for t in types for k in ANSWERS_BY_TYPE.get(t, [])})
    empty_answers = [k for k in need if not ans.get(k)]

    defs = definitions(ME / "profile" / "job-definitions.md")
    approved = {d["id"] for d in defs if d["durum"] == "onaylandı"}

    worker_issues, worker_soft = [], []
    for w in active:
        if str(w.get("tanım") or "").strip() not in approved:
            worker_issues.append(f"{w['ad']}: onaylı bir iş tanımına bağlı değil (tanım: {w.get('tanım') or '-'})")
        miss = [k for k in ("roller", "çalışma_tipi", "yer") if not w.get(k)]
        if miss:
            worker_issues.append(f"{w['ad']}: {', '.join(miss)}")
        mu = w.get("min_ücret") or {}
        if not (isinstance(mu, dict) and mu.get("tutar")):
            worker_soft.append(f"{w['ad']}: min_ücret (opsiyonel, ücret filtresi çalışmaz)")

    eksik = []
    if not cv["ad"] or cv["deneyim_başlığı"] == 0:
        eksik.append("cv-master: kişisel bilgi veya deneyim boş")
    if not cv["özet"]:
        eksik.append("cv-master: özet boş")
    n_proofed = len(ev["hard"]) + len(ev["soft"]) - len(ev["kanıtsız"])
    if n_proofed < 5:
        eksik.append(f"kanıt bankası: kanıtlı yetkinlik {n_proofed} (en az 5 önerilir)")
    if ev["kanıtsız"]:
        eksik.append(f"kanıt bankası: kanıtsız yetkinlik — {', '.join(ev['kanıtsız'][:8])}")
    if empty_answers:
        eksik.append(f"answers: boş — {', '.join(empty_answers)}")
    if not active:
        eksik.append("aktif worker yok")
    eksik += [f"worker {x}" for x in worker_issues + worker_soft]
    g = ME / "profile" / "goals.md"
    goals = sections(g)
    empty_goals = [h for h, b in goals.items() if not b]
    if not g.exists():
        eksik.append("goals.md yok — `profile.py init`")
    elif empty_goals:
        eksik.append(f"goals: boş — {', '.join(empty_goals)}")
    analysis = sections(ME / "profile" / "career-analysis.md")
    analysis_done = bool(analysis.get("Profil özeti"))
    if not analysis_done:
        eksik.append("kariyer analizi yapılmadı (career-analysis.md)")
    pending = [d["id"] for d in defs if d["durum"] == "önerildi"]
    if not defs:
        eksik.append("iş tanımı yok (job-definitions.md)")
    elif not approved:
        eksik.append("onaylanmış iş tanımı yok")
    if pending:
        eksik.append(f"onay bekleyen iş tanımı: {', '.join(pending)}")
    # Duraklatılmış worker da tanımı karşılar: tanım bilerek beklemeye alınmıştır, eksik sayılmaz.
    linked = {str(w.get("tanım") or "").strip() for w in workers}
    linked_active = {str(w.get("tanım") or "").strip() for w in active}
    no_worker = sorted(approved - linked)
    paused_defs = sorted((approved & linked) - linked_active)
    if no_worker:
        eksik.append(f"worker'ı olmayan onaylı tanım: {', '.join(no_worker)}")
    if not (ME / "sources.json").exists():
        eksik.append("sources.json yok — `profile.py init`")
    # İlan dili: arayüz dili Türkçe olsa da aranan ilanların dili ayrı bir karardır; kişiye sorulur.
    job_langs = (prefs.get("worker_varsayılanları") or {}).get("ilan_dilleri") or []
    if not job_langs:
        eksik.append("ilan dilleri seçilmedi (preferences → worker_varsayılanları.ilan_dilleri) — coach sorar")
    if not prefs.get("cv_dili"):
        eksik.append("CV dilleri seçilmedi (preferences → cv_dili) — coach sorar")

    # coach aşaması: ilk eksik olan
    goals_ok = g.exists() and all(goals.get(h) for h in GOALS_CORE)
    cv_ok = cv["ad"] and cv["deneyim_başlığı"] > 0
    good_workers = [w for w in active if not any(x.startswith(w["ad"] + ":") for x in worker_issues)]
    if not cv_ok or not goals_ok:
        stage = "1 · Tanışma"
    elif n_proofed < 5:
        stage = "2 · Kanıt"
    elif not analysis_done:
        stage = "3 · Analiz"
    elif not approved or pending:
        stage = "4 · İş tanımları"
    elif no_worker or not good_workers:
        stage = "5 · Worker'lar"
    elif empty_answers or not job_langs or not prefs.get("cv_dili"):
        stage = "6 · Tamamlama"
    else:
        stage = "tamam"

    # tarama/puanlama için asgari: CV, 5 kanıtlı yetkinlik, hedeflerin çekirdeği,
    # en az bir onaylı iş tanımı ve ona bağlı sorunsuz bir aktif worker
    ready = bool(cv_ok and n_proofed >= 5 and goals_ok and approved and good_workers and job_langs)
    return {
        "hazır": bool(ready),
        "sürüm": engine_version(),
        "ilan_dilleri": job_langs,
        "aşama": stage,
        "tanımlar": {k: [d["id"] for d in defs if d["durum"] == k] for k in ("onaylandı", "önerildi", "reddedildi")},
        "cv": cv,
        "kanıt": {"hard": len(ev["hard"]), "soft": len(ev["soft"]), "kanıtlı": n_proofed,
                  "kanıtsız": ev["kanıtsız"], "vaka": ev["vaka"]},
        "answers_boş": empty_answers,
        "worker": {"toplam": len(workers), "aktif": [w["ad"] for w in active], "sorunlu": worker_issues,
                   "duraklatılmış_tanım": paused_defs},
        "kara_liste_şirket": len(((prefs.get("kara_liste") or {}).get("şirketler")) or []),
        "eksikler": eksik,
    }


def cmd_check(a) -> int:
    r = check()
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    print(f"Profil {'HAZIR' if r['hazır'] else 'HAZIR DEĞİL'} (tarama ve puanlama için) · motor {engine_version()}")
    if r.get("aşama"):
        print(f"  Coach aşaması: {r['aşama']}")
    if r.get("cv"):
        c, k, w = r["cv"], r["kanıt"], r["worker"]
        print(f"  CV: deneyim {c['deneyim_başlığı']} · madde {c['madde']} · özet {'var' if c['özet'] else 'yok'}")
        print(f"  Kanıt bankası: hard {k['hard']} · soft {k['soft']} · kanıtlı {k['kanıtlı']} · vaka {k['vaka']}")
        t = r["tanımlar"]
        print(f"  İş tanımları: onaylı {len(t['onaylandı'])} · bekleyen {len(t['önerildi'])} · reddedilen {len(t['reddedildi'])}")
        print(f"  Worker: {w['toplam']} · aktif: {', '.join(w['aktif']) or '-'}")
        if w["duraklatılmış_tanım"]:
            print(f"  Duraklatılmış tanım: {', '.join(w['duraklatılmış_tanım'])}")
        print(f"  Kara listede şirket: {r['kara_liste_şirket']}")
    if r["eksikler"]:
        print("Eksikler:")
        for e in r["eksikler"]:
            print(f"  - {e}")
    return 0


def engine_version() -> str:
    p = VAULT / "engine" / "VERSION"
    return p.read_text(encoding="utf-8").strip() if p.exists() else "?"


def cmd_gate(_a) -> int:
    """Oturum başında bağlama eklenen tek satır. Asla hata vermez (hook oturumu engellememeli)."""
    try:
        r = check()
        if not r.get("me", True):
            msg = ("me/ yok: bu vault henüz bir kişi için kurulmadı. Kişi ne isterse istesin önce bunu söyle ve "
                   "/coach ile kuruluma başlamayı öner (`profile.py init`, `profile.py doctor`).")
        elif not r["hazır"]:
            msg = (f"profil HAZIR DEĞİL · coach aşaması: {r['aşama']}. scan / score / apply çalıştırma; önce durumu "
                   "söyle ve /coach ile kaldığı yerden devam etmeyi öner.")
        elif r["aşama"] != "tamam":
            msg = f"profil hazır · coach aşaması: {r['aşama']} (eksik: {'; '.join(r['eksikler'][:3])}). Uygun bir anda tamamlamayı öner."
        else:
            msg = "profil hazır."
        print(f"HRVault {engine_version()} · {msg}")
    except Exception as e:  # noqa: BLE001
        print(f"HRVault durumu okunamadı ({type(e).__name__}); `python3 engine/pipeline/profile.py check` çalıştır.")
    return 0


def cmd_doctor(a) -> int:
    """Ortam ön koşulları. Her satır: durum · ne · eksikse hangi adımı etkiler."""
    rows = []  # (ok: True | False | None(uyarı), ad, not)
    v = sys.version_info
    rows.append((v >= (3, 9), f"Python {v.major}.{v.minor}", "" if v >= (3, 9) else "3.9+ gerekir; hiçbir betik çalışmaz"))
    try:
        from pipeline import render_pdf
        cands = ([os.environ["HRVAULT_CHROME"]] if os.environ.get("HRVAULT_CHROME") else []) + render_pdf.CHROME_CANDIDATES
        found = next((p for p in ((c if os.path.isabs(c) else shutil.which(c)) for c in cands) if p and os.path.exists(p)), None)
    except Exception:  # noqa: BLE001
        found = None
    rows.append((bool(found) or None, "Chrome / Chromium (PDF)",
                 "" if found else "bulunamadı; CV/ön yazı PDF'i üretilemez — başvuru adımına kadar kurman yeterli "
                                  "(ya da HRVAULT_CHROME ile yolunu ver)"))
    try:
        probe = VAULT / ".hrvault-write-test"
        probe.write_text("x", encoding="utf-8")
        probe.unlink()
        rows.append((True, "Vault'a yazma izni", ""))
    except OSError:
        rows.append((False, "Vault'a yazma izni", "yok; profil ve başvuru kayıtları yazılamaz"))
    if (VAULT / ".git").exists():
        ign = subprocess.run(["git", "-C", str(VAULT), "check-ignore", "-q", "me"], capture_output=True).returncode == 0
        rows.append((ign, "me/ git'te yok sayılıyor", "" if ign else "`.gitignore`'a `/me/` ekle; kişisel veri commit'lenebilir"))
        hook = (VAULT / ".git" / "hooks" / "pre-commit").exists()
        rows.append((hook or None, "Commit öncesi sızıntı taraması", "" if hook else "kurulu değil — `python3 engine/pipeline/export.py install-hook`"))
    else:
        rows.append((True, "Git deposu yok", "me/ zaten hiçbir yere gönderilmiyor"))
    if a.offline:
        rows.append((None, "Ağ erişimi", "atlandı (--offline)"))
    else:
        try:
            req = urllib.request.Request("https://remotive.com/api/remote-jobs?limit=1", headers={"User-Agent": "hrvault-doctor"})
            urllib.request.urlopen(req, timeout=10).read(64)
            rows.append((True, "Ağ erişimi (ilan akışı)", ""))
        except Exception as e:  # noqa: BLE001
            rows.append((None, "Ağ erişimi (ilan akışı)", f"istek başarısız ({type(e).__name__}); tarama çalışmayabilir"))
    rows.append((None, "Tarayıcı eklentisi (Claude in Chrome)", "betikle denetlenemez; LinkedIn profilini okumak ve form doldurmak "
                 "için gerekir. Yoksa LinkedIn 'Save to PDF' çıktısı kullanılır"))
    mark = {True: "✓", False: "✗", None: "!"}
    print(f"HRVault {engine_version()} — ortam kontrolü")
    for ok, name, note in rows:
        print(f"  {mark[ok]} {name}" + (f" — {note}" if note else ""))
    bad = [r for r in rows if r[0] is False]
    print("Engelleyen sorun yok." if not bad else f"{len(bad)} engelleyen sorun var.")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="HRVault profil")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="me/ yoksa şablondan kur; varsa eksik şablon dosyalarını ekle")
    c = sub.add_parser("check", help="profil eksiklerini raporla")
    c.add_argument("--json", action="store_true")
    d = sub.add_parser("doctor", help="ortam ön koşullarını denetle")
    d.add_argument("--offline", action="store_true")
    sub.add_parser("gate", help="oturum başı tek satır durum")
    a = ap.parse_args()
    return {"init": cmd_init, "check": cmd_check, "doctor": cmd_doctor, "gate": cmd_gate}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
