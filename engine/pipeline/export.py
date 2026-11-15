#!/usr/bin/env python3
"""HRVault export — paylaşılabilir paket ve kişisel veri sızıntısı taraması.

Kullanım (vault kökünden):
  python3 engine/pipeline/export.py lint [dosya…]        # paylaşılan katmanı tara (1: bulgu, 2: tarama yapılamadı)
  python3 engine/pipeline/export.py lint --hook          # commit öncesi: profil boşsa yalnızca genel kurallar
  python3 engine/pipeline/export.py allow <dosya> <satır> --gerekce "…"   # gözden_geçir bulgusuna izin
  python3 engine/pipeline/export.py ids                  # kimliği olmayan knowledge/ maddelerine `k:` ekle
  python3 engine/pipeline/export.py build                # prova: tara, hazırlık klasöründe kur, yeniden tara
  python3 engine/pipeline/export.py build --reviewed [--dest KLASÖR] [--zip]
  python3 engine/pipeline/export.py build --knowledge-only [--reviewed]   # yalnızca yeni/değişen öğrenimler
  python3 engine/pipeline/export.py verify <paket>       # paketi me/ olmadan doğrula
  python3 engine/pipeline/export.py merge <bilgi-paketi> # gelen öğrenimleri kimliğe göre birleştir
  python3 engine/pipeline/export.py install-hook         # .git/hooks/pre-commit

İlkeler: beyaz liste (manifest), kapalı başarısızlık (desen yoksa "temiz" denmez), düzeltme kaynakta.
Desenler `me/` içinden okunur ve hiçbir yere yazılmaz; raporlar yalnızca ekrana basılır.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import unicodedata
import zipfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from scanner import config  # noqa: E402

VAULT = HERE.parent.parent
TEXT_EXT = {".md", ".py", ".json", ".txt", ".yml", ".yaml", ".toml", ".cfg", ".sh", ""}
MIN_PATTERNS = 5
ENGEL, GOZDEN, BILGI = "engel", "gözden_geçir", "bilgi"


class ScanError(Exception):
    """Tarama yapılamadı — sonuç "temiz" sayılmaz (çıkış kodu 2)."""


# ------------------------------------------------------------------ metin katlama
_TR = str.maketrans({"ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g", "ü": "u", "Ü": "u",
                     "ö": "o", "Ö": "o", "ç": "c", "Ç": "c", "ß": "s", "æ": "a", "ø": "o"})


def fold(s: str) -> str:
    """Küçük harf, Türkçe ve aksanlı karakterler düz Latin'e. Uzunluk korunur (satır eşlemesi için)."""
    out = []
    for ch in s.translate(_TR):
        d = unicodedata.normalize("NFKD", ch)
        base = "".join(c for c in d if not unicodedata.combining(c)) or ch
        out.append(base[0].lower() if base else ch)
    return "".join(out)


def _term_regex(term: str) -> re.Pattern | None:
    """`Acme Robotics` → acme[ayraç]?robotics; kelime sınırlı. Slug ve bitişik yazımı da yakalar."""
    toks = re.findall(r"[a-z0-9]+", fold(term))
    if not toks:
        return None
    return re.compile(r"(?<![a-z0-9])" + r"[\s\-_./]{0,2}".join(map(re.escape, toks)) + r"(?![a-z0-9])")


# ------------------------------------------------------------------ manifest
def _glob_re(g: str) -> re.Pattern:
    out, i = "", 0
    while i < len(g):
        if g.startswith("**/", i):
            out += r"(?:.*/)?"; i += 3
        elif g.startswith("**", i):
            out += r".*"; i += 2
        elif g[i] == "*":
            out += r"[^/]*"; i += 1
        elif g[i] == "?":
            out += r"[^/]"; i += 1
        else:
            out += re.escape(g[i]); i += 1
    return re.compile("^" + out + "$")


def load_manifest(vault: Path) -> dict:
    p = vault / "engine" / "export" / "manifest.json"
    if not p.exists():
        raise ScanError("engine/export/manifest.json yok")
    m = json.loads(p.read_text(encoding="utf-8"))
    m["_kopyala"] = [_glob_re(g) for g in m.get("kopyala", [])]
    m["_asla"] = [_glob_re(g) for g in m.get("asla", [])]
    return m


KAPSAM_LINE = re.compile(r"\*\*kapsam:\*\*\s*([^\s—–-]+)")


def regional_stems(vault: Path) -> dict[str, str]:
    """Başlığında `**kapsam:** <ülke>` taşıyan adaptör ve site notları → {ad: ülke}."""
    out = {}
    for d in (vault / "engine" / "adapters", vault / "knowledge" / "sites"):
        for p in sorted(d.glob("*.md")) if d.exists() else []:
            if p.name == "README.md":
                continue
            mm = KAPSAM_LINE.search("\n".join(p.read_text(encoding="utf-8").splitlines()[:12]))
            if mm and fold(mm.group(1)) not in ("kuresel", "genel"):
                out[p.stem] = mm.group(1)
    return out


def regional_paths(stem: str) -> set[str]:
    return {f"engine/adapters/{stem}.md", f"engine/scanner/sources/{stem}.py", f"knowledge/sites/{stem}.md"}


def excluded_regional(vault: Path, m: dict) -> dict[str, str]:
    """Manifest `bölgesel_adaptörler: false` ise pakete girmeyecek bölgesel adaptörler."""
    return {} if m.get("bölgesel_adaptörler", True) else regional_stems(vault)


def regional_patterns(vault: Path, m: dict) -> list:
    """Dışlanan bölgesel adaptörün adı paylaşılan katmanda geçmemeli (pakette kırık atıf ve bölge izi olur)."""
    return [Pattern(s, "dışlanan bölgesel adaptöre atıf", ENGEL, _term_regex(s)) for s in excluded_regional(vault, m)]


def classify_files(vault: Path, m: dict) -> tuple[list[str], list[str]]:
    """→ (pakete girecek yollar, tanınmayan yollar). `asla` her zaman kazanır; dışlanan bölgesel adaptörler de girmez."""
    keep, unknown = [], []
    skip = set().union(*[regional_paths(s) for s in excluded_regional(vault, m)])
    for root, dirs, files in os.walk(vault):
        rel_root = Path(root).relative_to(vault).as_posix()
        dirs[:] = [d for d in dirs if not (rel_root == "." and d in ("me", ".git"))]
        for f in files:
            rel = f if rel_root == "." else f"{rel_root}/{f}"
            if rel in skip or any(r.match(rel) for r in m["_asla"]):
                continue
            (keep if any(r.match(rel) for r in m["_kopyala"]) else unknown).append(rel)
    return sorted(keep), sorted(unknown)


# ------------------------------------------------------------------ desenler (me/ → bellek)
@dataclass
class Pattern:
    term: str
    kind: str
    level: str
    rx: re.Pattern


STOP = {"remote", "freelance", "senior", "junior", "university", "universitesi", "gmbh", "inc", "ltd", "the",
        "group", "global", "team", "company", "online", "none", "yok", "evet", "hayir", "worldwide", "europe",
        "contract", "part", "full", "time", "lead", "manager", "engineer", "developer", "consultant", "proje",
        "project", "present", "bugun", "self", "employed", "serbest", "linkedin", "github", "google", "claude"}

DATA_FILES = ("engine/export/manifest.json", "engine/export/countries.json")  # beyan edilmiş genel adlar
COUNTRY_ALIASES = [set(g) for g in json.loads((HERE.parent / "export" / "countries.json").read_text(encoding="utf-8"))]


def _strip_comments(t: str) -> str:
    return re.sub(r"<!--.*?-->", "", t, flags=re.S)


def _read(p: Path) -> str:
    return _strip_comments(p.read_text(encoding="utf-8")) if p.exists() else ""


def _kv(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        mm = re.match(r"^\s*-\s*([A-Za-zÇĞİÖŞÜçğıöşü_ -]+?):\s*(.*)$", line)
        if mm:
            out[mm.group(1).strip().lower()] = re.sub(r"\s+#.*$", "", mm.group(2)).strip()
    return out


def _heading_names(h: str) -> tuple[list[str], list[str]]:
    """`Rol | Alt başlık — Şirket (2020-01 – 2023-05) · Şehir, Ülke` → (ad adayları, konum parçaları)."""
    h = re.sub(r"\([^)]*\d{4}[^)]*\)", " ", h)        # tarih parantezleri
    head, _, loc = h.partition(" · ")
    head = re.sub(r",?\s*\b(19|20)\d{2}\b.*$", " ", head)
    clean = lambda xs: [re.sub(r"[\"“”()]", "", x).strip() for x in xs if x.strip()]  # noqa: E731
    return clean(re.split(r"\s+[—–|/]\s+|\s+-\s+|,\s+", head)), clean(re.split(r"[,·/]", loc))


def collect_patterns(vault: Path, platforms: set[str] = frozenset(), generic: set[str] = frozenset()) -> list[Pattern]:
    me = vault / "me"
    if not me.exists():
        raise ScanError("me/ yok — kişisel desen üretilemez")
    seen: dict[str, Pattern] = {}

    def add(term, kind: str, level: str, *, min_len: int = 4):
        term = str(term or "").strip().strip("\"'`")
        f = fold(term)
        if len(re.sub(r"[^a-z0-9]", "", f)) < min_len or f in STOP or f in generic or f.startswith("<"):
            return
        if f in platforms and level == ENGEL:
            level = GOZDEN  # herkese açık platform adı: motorun kendi konusu olabilir
        rx = _term_regex(term)
        if rx and (f not in seen or (level == ENGEL and seen[f].level != ENGEL)):
            seen[f] = Pattern(term, kind, level, rx)

    prof = me / "profile"
    ans = _kv(_read(prof / "answers.md"))
    cvkv = _kv(_read(prof / "cv-master.md"))

    for name in (ans.get("full_name"), cvkv.get("ad soyad")):
        if name:
            add(name, "isim", ENGEL)
            for part in name.split():
                add(part, "isim", ENGEL, min_len=3)
    for mail in (ans.get("email"), cvkv.get("e-posta")):
        if mail and "@" in mail:
            add(mail, "e-posta", ENGEL)
            add(mail.split("@")[0], "e-posta", ENGEL, min_len=5)
    for url in (ans.get("linkedin_url"), cvkv.get("linkedin"), ans.get("portfolio_url"), cvkv.get("portfolyo")):
        if not url:
            continue
        mm = re.search(r"linkedin\.com/in/([^/?#\s]+)", url)
        if mm:
            add(mm.group(1), "profil adresi", ENGEL)
        else:
            host = re.sub(r"^https?://(www\.)?", "", url).strip("/")
            if not re.match(r"(github|gitlab|medium|behance|dribbble|notion|linkedin)\.", host):
                add(host.split("/")[0], "profil adresi", ENGEL)
            if "/" in host:
                add(host.rstrip("/").split("/")[-1], "profil adresi", ENGEL, min_len=5)
    def add_loc(part: str):
        add(part, "konum", GOZDEN, min_len=3)
        for group in COUNTRY_ALIASES:
            if fold(part.strip()) in group:
                for alias in group:
                    add(alias, "konum", GOZDEN, min_len=3)

    for loc in (ans.get("location"), cvkv.get("lokasyon")):
        for part in re.split(r"[,/()]", loc or ""):
            add_loc(part)

    # işveren / okul / proje adları
    cv = _read(prof / "cv-master.md")
    for h in re.findall(r"^### (.+)$", cv, re.M):
        names, locs = _heading_names(h)
        for i, n in enumerate(names):
            add(n, "CV başlığı", GOZDEN if i == 0 and len(names) > 1 else ENGEL, min_len=5)
        for n in locs:
            add_loc(n)
    ev = _read(prof / "evidence-bank.md")
    for b in re.findall(r"\*\*\[(.+?)\]\*\*", ev):
        names, locs = _heading_names(b)
        for i, n in enumerate(names):
            add(n, "kanıt kaynağı", GOZDEN if i == 0 else ENGEL, min_len=5)
        for n in locs:
            add_loc(n)
    for mm in re.finditer(r"(?:öneri(?:yi)? yazan|önerən|recommend\w* by|kimden|öneren)\s*[:—-]\s*([^\n,;(]+)", ev, re.I):
        add(mm.group(1), "üçüncü kişi", ENGEL)

    # şirketler: takip listesi, kara liste, başvurular, kararlar
    try:
        src = json.loads((me / "sources.json").read_text(encoding="utf-8")) if (me / "sources.json").exists() else {}
    except json.JSONDecodeError as e:
        raise ScanError(f"me/sources.json okunamadı: {e}")
    for w in src.get("watchlist", []) or []:
        add(w.get("company") if isinstance(w, dict) else w, "takip edilen şirket", ENGEL)
        if isinstance(w, dict) and w.get("token"):
            add(w["token"], "takip edilen şirket", ENGEL, min_len=5)
    pp = prof / "preferences.md"
    prefs = config.read_frontmatter(pp) if pp.exists() else {}
    for c in ((prefs.get("kara_liste") or {}).get("şirketler")) or []:
        add(c, "kara liste", ENGEL)
    apps = me / "pipeline" / "applications"
    if apps.exists():
        for d in apps.iterdir():
            a = d / "application.md"
            if a.exists():
                add((config.read_frontmatter(a) or {}).get("şirket"), "başvurulan şirket", ENGEL)
    dj = me / "pipeline" / "decisions.jsonl"
    if dj.exists():
        for line in dj.read_text(encoding="utf-8").splitlines():
            try:
                add(json.loads(line).get("şirket"), "değerlendirilen şirket", GOZDEN)
            except json.JSONDecodeError:
                continue

    # worker ve tanım adları, roller (dolaylı)
    wd = me / "workers"
    if wd.exists():
        for p in wd.glob("*.md"):
            if p.name.lower() == "readme.md":
                continue
            fm = config.read_frontmatter(p) or {}
            add(p.stem, "worker adı", GOZDEN, min_len=6)
            roles = fm.get("roller") or []
            for r in ([roles] if isinstance(roles, str) else roles):
                if len(str(r).split()) >= 2:      # tek kelimelik rol ("analyst") herkesin kelimesidir
                    add(r, "aranan rol", GOZDEN, min_len=6)
    for mm in re.finditer(r"^### T\d+:\s*(.+)$", _read(prof / "job-definitions.md"), re.M):
        add(mm.group(1), "iş tanımı", GOZDEN, min_len=6)

    pats = list(seen.values())
    if not any(p.kind == "isim" for p in pats) or not any(p.kind == "e-posta" for p in pats):
        raise ScanError("profilde isim ya da e-posta yok — kişisel desen üretilemez")
    if len(pats) < MIN_PATTERNS:
        raise ScanError(f"yalnızca {len(pats)} desen üretildi (en az {MIN_PATTERNS})")
    return pats


def patterns_for(vault: Path, m: dict) -> list[Pattern]:
    adapters = {p.stem for p in (vault / "engine" / "adapters").glob("*.md")}
    return collect_patterns(vault, {fold(x) for x in m.get("platform_adları", [])} | adapters,
                            {fold(x) for x in m.get("genel_kelimeler", [])})


def personal_numbers(vault: Path) -> tuple[set[str], set[str]]:
    """→ (telefonun rakamları, ücret rakamları). Yalnızca bellekte."""
    prof = vault / "me" / "profile"
    ans = _kv(_read(prof / "answers.md")) | {k: v for k, v in _kv(_read(prof / "cv-master.md")).items() if k == "telefon"}
    phones = set()
    for k in ("phone", "telefon"):
        d = re.sub(r"\D", "", ans.get(k, ""))
        if len(d) >= 9:
            phones.add(d[-9:])
    money = set()
    for k in ("salary_expectation_annual", "hourly_rate"):
        for n in re.findall(r"\d[\d.,]*\d|\d", ans.get(k, "")):
            d = re.sub(r"\D", "", n)
            if len(d) >= 2:
                money.add(d)
    return phones, money


NARRATIVE = ("cv-master.md", "evidence-bank.md", "goals.md", "career-analysis.md", "linkedin-notes.md",
             "linkedin-final.md", "linkedin-plan.md")
SHINGLE = 6


def _shingles(text: str) -> set[tuple]:
    out = set()
    for line in text.splitlines():
        w = re.findall(r"[a-z0-9]+", fold(line))
        for i in range(len(w) - SHINGLE + 1):
            out.add(tuple(w[i:i + SHINGLE]))
    return out


def personal_shingles(vault: Path) -> set[tuple]:
    """Kişinin anlatı dosyalarındaki 6 kelimelik parmak izleri; şablon metni çıkarılmış."""
    prof = vault / "me" / "profile"
    mine = set()
    for name in NARRATIVE:
        if (prof / name).exists():
            mine |= _shingles(_read(prof / name))
    ans = _kv(_read(prof / "answers.md"))
    for k in ("about_me", "why_this_role_template"):
        mine |= _shingles(ans.get(k, ""))
    tpl = set()
    for p in (vault / "engine" / "templates").rglob("*.md"):
        tpl |= _shingles(p.read_text(encoding="utf-8"))
    return mine - tpl


# ------------------------------------------------------------------ genel kurallar (kişiden bağımsız)
GENERIC = [
    ("e-posta", ENGEL, re.compile(r"[\w.+-]+@(?!example\.|ornek\.)[\w-]+\.[a-z]{2,}", re.I)),
    ("telefon", ENGEL, re.compile(r"(?<![\w/])\+\d{1,3}[\s().-]{0,2}\d[\d\s().-]{6,}\d")),
    ("kullanıcı yolu", ENGEL, re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\Users\\)[\w.-]+")),
    ("LinkedIn profili", ENGEL, re.compile(r"linkedin\.com/in/(?!<)[\w%-]{3,}")),
    ("IBAN", ENGEL, re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}\b")),
    ("ücret rakamı", GOZDEN, re.compile(r"[$€₺£]\s?\d|\d\s?(?:USD|EUR|TRY|TL|GBP)\b")),
]
FULL_DATE = re.compile(r"\[\d{4}-\d{2}-\d{2}\]")
IDENTITY_KEYS = ("full_name", "email", "phone", "location", "linkedin_url", "portfolio_url",
                 "salary_expectation_annual", "hourly_rate")


@dataclass
class Finding:
    level: str
    kind: str
    file: str
    line: int
    text: str

    def key(self) -> str:
        return hashlib.sha1(f"{self.file}|{self.kind}|{self.text.strip()}".encode()).hexdigest()[:16]


def scan_text(rel: str, text: str, pats: list[Pattern], phones=(), money=(), shingles=()) -> list[Finding]:
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        fl = fold(line)
        snip = line.strip()[:160]
        for p in pats:
            if p.rx.search(fl):
                out.append(Finding(p.level, p.kind, rel, i, snip))
        for kind, level, rx in GENERIC:
            if rx.search(line):
                out.append(Finding(level, kind, rel, i, snip))
        if phones or money:
            for run in re.findall(r"\d[\d\s().-]{5,}\d", line):
                d = re.sub(r"\D", "", run)
                if any(ph in d for ph in phones):
                    out.append(Finding(ENGEL, "telefon", rel, i, snip))
            for mm in re.finditer(r"(?<![\w.-])\d[\d.,]*\d(?![\w-])", line):
                d = re.sub(r"\D", "", mm.group())
                near = re.search(r"[$€₺£]\s?$", line[:mm.start()]) or \
                    re.match(r"\s?(?:[$€₺£]|USD|EUR|TRY|TL|GBP|k\b|\s?/\s?(?:saat|hour|hr|yıl|year))", line[mm.end():])
                if d in money and (len(d) >= 5 or near):
                    out.append(Finding(ENGEL, "kişinin ücret rakamı", rel, i, snip))
        if shingles:
            w = re.findall(r"[a-z0-9]+", fl)
            if any(tuple(w[j:j + SHINGLE]) in shingles for j in range(len(w) - SHINGLE + 1)):
                out.append(Finding(GOZDEN, "profilden cümle", rel, i, snip))
    return out


def template_findings(vault: Path, m: dict) -> list[Finding]:
    """`me` şablonu boş olmalı: kimlik alanları, kara liste, takip listesi."""
    out = []
    tpl = vault / m.get("me_şablonu", "engine/templates/me")
    a = tpl / "profile" / "answers.md"
    if a.exists():
        for i, line in enumerate(a.read_text(encoding="utf-8").splitlines(), 1):
            mm = re.match(r"^\s*-\s*([a-z_]+):\s*(.*)$", line)
            if mm and mm.group(1) in IDENTITY_KEYS and re.sub(r"(^|\s+)#.*$", "", mm.group(2)).strip():
                out.append(Finding(ENGEL, "şablonda dolu alan", a.relative_to(vault).as_posix(), i, mm.group(1)))
    s = tpl / "sources.json"
    if s.exists() and json.loads(s.read_text(encoding="utf-8")).get("watchlist"):
        out.append(Finding(ENGEL, "şablonda dolu alan", s.relative_to(vault).as_posix(), 1, "watchlist"))
    p = tpl / "profile" / "preferences.md"
    if p.exists():
        fm = config.read_frontmatter(p) or {}
        if any((fm.get("kara_liste") or {}).get(k) for k in ("şirketler", "sektörler", "anahtar_kelimeler")):
            out.append(Finding(ENGEL, "şablonda dolu alan", p.relative_to(vault).as_posix(), 1, "kara_liste"))
        for k in ("ülkeler", "yer", "ilan_dilleri"):
            if (fm.get("worker_varsayılanları") or {}).get(k):
                out.append(Finding(ENGEL, "şablonda dolu alan", p.relative_to(vault).as_posix(), 1, k))
        if fm.get("cv_dili"):
            out.append(Finding(ENGEL, "şablonda dolu alan", p.relative_to(vault).as_posix(), 1, "cv_dili"))
    return out


def load_allow(vault: Path) -> dict:
    p = vault / "engine" / "export" / "allow.json"
    return {x["anahtar"]: x for x in json.loads(p.read_text(encoding="utf-8")).get("izinler", [])} if p.exists() else {}


def lint(vault: Path, *, only: list[str] | None = None, generic_only: bool = False) -> dict:
    """→ {bulgular, izinli, dosya_sayısı, desen_sayısı}. Tarama yapılamıyorsa ScanError."""
    m = load_manifest(vault)
    keep, unknown = classify_files(vault, m)
    if generic_only:
        pats, phones, money, sh = [], set(), set(), set()
    else:
        pats = patterns_for(vault, m)
        phones, money = personal_numbers(vault)
        sh = personal_shingles(vault)
    pats = pats + regional_patterns(vault, m)
    findings = [Finding(ENGEL, "tanınmayan dosya (manifestte yok)", u, 0, "") for u in unknown]
    targets = keep
    if only:
        want = {Path(o).resolve() for o in only}
        targets = [k for k in keep if (vault / k).resolve() in want]
        findings = [f for f in findings if (vault / f.file).resolve() in want]
    full_dates = 0
    for rel in targets:
        p = vault / rel
        if p.suffix.lower() not in TEXT_EXT:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as e:
            raise ScanError(f"{rel} okunamadı: {e}")
        own = rel in DATA_FILES
        findings += scan_text(rel, text, [] if own else pats, phones, money, () if own else sh)
        for f in scan_text(rel, rel, pats):          # dosya ve klasör adları da içeriktir
            findings.append(Finding(f.level, f"{f.kind} (dosya adında)", rel, 0, rel))
        if rel.startswith("knowledge/"):
            full_dates += len(FULL_DATE.findall(text))
    if not only:
        findings += template_findings(vault, m)
    allow = load_allow(vault)
    open_, allowed = [], []
    seen = set()
    for f in findings:
        k = (f.level, f.kind, f.file, f.line)
        if k in seen:
            continue
        seen.add(k)
        (allowed if f.level == GOZDEN and f.key() in allow else open_).append(f)
    return {"bulgular": open_, "izinli": allowed, "dosyalar": keep, "desen_sayısı": len(pats),
            "bölgesel": excluded_regional(vault, m),
            "tam_tarih": full_dates, "manifest": m}


def blocking(findings: list[Finding]) -> list[Finding]:
    return [f for f in findings if f.level in (ENGEL, GOZDEN)]


def print_report(r: dict, *, title: str = "Sızıntı taraması") -> None:
    b = r["bulgular"]
    n_e = sum(f.level == ENGEL for f in b)
    n_g = sum(f.level == GOZDEN for f in b)
    print(f"{title}: {len(r['dosyalar'])} dosya · {r['desen_sayısı']} kişisel desen · "
          f"engel {n_e} · gözden_geçir {n_g} · izinli {len(r['izinli'])}")
    for level in (ENGEL, GOZDEN):
        rows = [f for f in b if f.level == level]
        if rows:
            print(f"\n[{level}]")
            for f in rows:
                loc = f"{f.file}:{f.line}" if f.line else f.file
                print(f"  {loc} · {f.kind}" + (f" · {f.text}" if f.text else ""))
    if r.get("tam_tarih"):
        print(f"\n[bilgi] knowledge/ içinde {r['tam_tarih']} tarih var; pakette kaldırılır, dayanak sayıları yuvarlanır.")
    if r.get("bölgesel"):
        print(f"\n[bilgi] pakete girmeyecek bölgesel adaptörler: "
              + ", ".join(f"{s} ({c})" for s, c in sorted(r["bölgesel"].items())))
    if not blocking(b):
        print("Temiz.")
    elif n_e:
        print("\nengel bulguları kaynakta düzeltilmeden paket oluşmaz (istisna yok).")
    if n_g:
        print("gözden_geçir: genelleştir ya da kişinin onayıyla `export.py allow <dosya> <satır> --gerekce …`.")


# ------------------------------------------------------------------ knowledge/ maddeleri
ENTRY_HEAD = re.compile(r"^- \*\*(?:\[(\d{4}-\d{2}(?:-\d{2})?)\]\s*)?(.+?)\*\*(?:\s*`k:([a-z0-9-]+)`)?\s*$")
DAYANAK = re.compile(r"_dayanak:\s*(.*?)\s*·\s*güven:\s*(düşük|orta|yüksek)([^_]*)_")
LEVELS = ["düşük", "orta", "yüksek"]


def slug(s: str, words: int = 6) -> str:
    return "-".join(re.findall(r"[a-z0-9]+", fold(s))[:words])


def parse_entries(text: str, stem: str = "") -> list[dict]:
    """→ [{id, tarih, başlık, bölüm, start, end, gövde, dayanak, güven}] (satır indeksleri 0 tabanlı, end hariç)."""
    lines = text.splitlines()
    out, section, i = [], "", 0
    while i < len(lines):
        if lines[i].startswith("## "):
            section = lines[i][3:].strip()
        mm = ENTRY_HEAD.match(lines[i])
        if not mm:
            i += 1
            continue
        j = i + 1
        while j < len(lines) and (lines[j].startswith("  ") or (not lines[j].strip() and j + 1 < len(lines)
                                                                 and lines[j + 1].startswith("  "))):
            j += 1
        body = "\n".join(lines[i + 1:j])
        d = DAYANAK.search(body)
        out.append({"id": mm.group(3) or "", "tarih": mm.group(1) or "", "başlık": mm.group(2).strip(), "bölüm": section,
                    "start": i, "end": j, "gövde": body, "dayanak": d.group(1) if d else "",
                    "güven": d.group(2) if d else "", "özet": _body_hash(body)})
        i = j
    return out


def _body_hash(body: str) -> str:
    core = DAYANAK.sub("", body)
    return hashlib.sha1(" ".join(fold(core).split()).encode()).hexdigest()[:16]


def knowledge_files(root: Path) -> list[Path]:
    k = root / "knowledge"
    return sorted(p for p in k.rglob("*.md") if p.name != "README.md") if k.exists() else []


def assign_ids(vault: Path) -> int:
    used = {e["id"] for p in knowledge_files(vault) for e in parse_entries(p.read_text(encoding="utf-8")) if e["id"]}
    n = 0
    for p in knowledge_files(vault):
        lines = p.read_text(encoding="utf-8").splitlines()
        changed = False
        for e in parse_entries("\n".join(lines)):
            if e["id"]:
                continue
            base = f"{p.stem}-{slug(e['başlık'])}"
            kid, c = base, 2
            while kid in used:
                kid, c = f"{base}-{c}", c + 1
            used.add(kid)
            lines[e["start"]] = lines[e["start"]].rstrip() + f" `k:{kid}`"
            changed, n = True, n + 1
        if changed:
            p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return n


def baseline_of(root: Path) -> dict:
    out = {}
    for p in knowledge_files(root):
        for e in parse_entries(p.read_text(encoding="utf-8")):
            if e["id"]:
                out[e["id"]] = {"dosya": p.relative_to(root).as_posix(), "özet": e["özet"], "dayanak": e["dayanak"]}
    return out


DATE = re.compile(r"\b20\d\d-\d\d(?:-\d\d)?\b")


def strip_dates(text: str) -> str:
    """Madde başlığındaki `[YYYY-MM-DD]` ve tarih içeren parantezler ("doğrulandı 2026-01-02") silinir:
    motorun ne zaman kullanıldığı paketten okunmasın."""
    text = re.sub(r"^(\s*- \*\*)\[\d{4}-\d{2}(?:-\d{2})?\]\s*", r"\1", text, flags=re.M)
    text = re.sub(r"[ \t]*\((?:[^()\n]*?\s)?20\d\d-\d\d(?:-\d\d)?(?:\s[^()\n]*)?\)", "", text)
    return text


def round_counts(day: str) -> str:
    """`10 form` → `çok sayıda form`, `5 ilan` → `birkaç ilan`, `1 oturum` → `tek oturum`: kuralın dayanağı kalır,
    kişinin ne kadar etkinlik yaptığı okunmaz. Kullanıcı sayıları ("+1 kullanıcı") kişisel değildir, kalır."""
    def r(mm: re.Match) -> str:
        n, unit = int(mm.group(2)), mm.group(3)
        if unit.startswith("kullanıcı"):
            return mm.group(0)
        return f"{mm.group(1)}{'tek' if n == 1 else 'birkaç' if n < 10 else 'çok sayıda'} {unit}"
    return re.sub(r"(^|[\s(,])~?(\d+)\s+([^\W\d_][\w-]*)", r, day)


def neutralize_knowledge(text: str) -> str:
    """Pakete girerken: tarih silinir, dayanak sayıları yuvarlanır, tek kişilik gözlemde güven en fazla orta olur,
    devralınan dayanak düzleşir."""
    text = strip_dates(text)

    def cap(mm: re.Match) -> str:
        day, lvl, rest = mm.group(1), mm.group(2), mm.group(3)
        day = round_counts(re.sub(r"devralındı \((.*?)\)\s*\+\s*", r"\1 + ", day))
        if lvl == "yüksek" and not re.search(r"genel bilgi|API notu|kullanıcı", day):
            lvl = "orta"
        return f"_dayanak: {day} · güven: {lvl}{rest}_"
    return DAYANAK.sub(cap, text)


# ------------------------------------------------------------------ build
FIXED = (2000, 1, 1, 0, 0, 0)   # paketteki tüm dosyaların tarihi: dışa aktarma günü de okunmasın


def _fixed_time() -> float:
    return datetime(*FIXED).timestamp()


def _write(dst: Path, data: bytes, ts: float) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)          # yalnızca içerik: öznitelik, sahiplik, tarih taşınmaz
    os.utime(dst, (ts, ts))


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def version(vault: Path) -> str:
    p = vault / "engine" / "VERSION"
    return p.read_text(encoding="utf-8").strip() if p.exists() else "0"


def stage(vault: Path, r: dict, *, knowledge_only: bool = False) -> Path:
    m, ts = r["manifest"], _fixed_time()
    st = Path(tempfile.mkdtemp(prefix="hrvault-export-"))
    if knowledge_only:
        base_p = vault / "knowledge" / ".baseline.json"
        base = json.loads(base_p.read_text(encoding="utf-8")) if base_p.exists() else {}
        n = 0
        for p in knowledge_files(vault):
            text = p.read_text(encoding="utf-8")
            lines = text.splitlines()
            fresh = [e for e in parse_entries(text) if e["id"] and
                     (e["id"] not in base or base[e["id"]]["özet"] != e["özet"] or base[e["id"]]["dayanak"] != e["dayanak"])]
            if not fresh:
                continue
            out, sec = [f"# {p.stem} — öğrenimler", ""], None
            for e in fresh:
                if e["bölüm"] != sec:
                    sec = e["bölüm"]
                    out += [f"## {sec or 'Öğrenimler'}"]
                out += lines[e["start"]:e["end"]]
            _write(st / p.relative_to(vault), neutralize_knowledge("\n".join(out) + "\n").encode(), ts)
            n += len(fresh)
        if not n:
            shutil.rmtree(st)
            raise ScanError("baseline'dan beri yeni ya da değişen öğrenim yok")
    else:
        for rel in r["dosyalar"]:
            data = (vault / rel).read_bytes()
            if rel.startswith("knowledge/") and rel.endswith(".md") and not rel.endswith("README.md"):
                data = neutralize_knowledge(data.decode("utf-8")).encode()
            elif rel.startswith("engine/adapters/") and rel.endswith(".md"):
                data = strip_dates(data.decode("utf-8")).encode()
            _write(st / rel, data, ts)
        tpl = vault / m.get("me_şablonu", "engine/templates/me")
        for p in sorted(tpl.rglob("*")):
            if p.is_file() and p.name != ".DS_Store":
                _write(st / "me" / p.relative_to(tpl), p.read_bytes(), ts)
        _write(st / "knowledge" / ".baseline.json",
               (json.dumps(baseline_of(st), ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode(), ts)
    return st


def package_files(root: Path) -> dict:
    """Paketin dosyaları (EXPORT.json ve paket bir git deposuysa `.git/` hariç)."""
    return {p.relative_to(root).as_posix(): _sha(p.read_bytes())
            for p in sorted(root.rglob("*")) if p.is_file() and p.name != "EXPORT.json"
            and p.relative_to(root).parts[0] != ".git"}


def rescan_stage(vault: Path, st: Path) -> list[Finding]:
    """Hazırlık klasörünü kişinin desenleriyle yeniden tara (me/ şablonu dahil)."""
    m = load_manifest(vault)
    pats = patterns_for(vault, m) + regional_patterns(vault, m)
    phones, money = personal_numbers(vault)
    sh = personal_shingles(vault)
    allow = load_allow(vault)
    out = []
    for p in sorted(st.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(st).as_posix()
        if p.name in (".DS_Store",) or p.suffix == ".pyc" or "__pycache__" in rel or rel.startswith(".git/"):
            out.append(Finding(ENGEL, "yasak dosya pakette", rel, 0, ""))
            continue
        if p.suffix.lower() in TEXT_EXT:
            # baseline yalnızca knowledge/ maddelerinden türetilir (kimlik, dayanak): oradaki her eşleşmenin
            # kaynağı bir madde satırıdır ve orada zaten değerlendirilir. Genel kurallar yine uygulanır.
            own = rel in DATA_FILES or rel == "knowledge/.baseline.json"
            for f in scan_text(rel, p.read_text(encoding="utf-8"), [] if own else pats, phones, money, () if own else sh):
                if not (f.level == GOZDEN and f.key() in allow):
                    out.append(f)
    return out


def cmd_build(a) -> int:
    vault = VAULT
    r = lint(vault)
    print_report(r)
    if blocking(r["bulgular"]):
        return 1
    st = stage(vault, r, knowledge_only=a.knowledge_only)
    try:
        again = blocking(rescan_stage(vault, st))
        if again:
            print("\nHazırlık klasöründe bulgu (paket oluşmadı):")
            for f in again:
                print(f"  [{f.level}] {f.file}:{f.line} · {f.kind} · {f.text}")
            return 1
        files = package_files(st)
        kn = [f for f in files if f.startswith("knowledge/") and f.endswith(".md")]
        if not a.reviewed:
            last_p = vault / "me" / "pipeline" / "exports.json"
            last = (json.loads(last_p.read_text(encoding="utf-8")).get("bilgi_özetleri", {}) if last_p.exists() else {})
            todo = [f for f in kn if last.get(f) != files[f]]
            print(f"\nProva tamam: {len(files)} dosya, betik taraması temiz. Paket OLUŞMADI.")
            print("Anlam okuması bekleyen dosyalar (son export'tan beri değişen):")
            for f in todo or ["(yok)"]:
                print(f"  {f}")
            print("Okuma bitip kişi raporu onaylayınca: `export.py build --reviewed`.")
            return 0
        kind = "bilgi" if a.knowledge_only else "tam"
        default = vault.parent / f"HRVault-{'knowledge' if a.knowledge_only else 'share'}-{date.today().isoformat()}"
        dest = Path(a.update or a.dest).expanduser().resolve() if (a.update or a.dest) else default
        if dest == vault.resolve() or vault.resolve() in dest.parents:
            print("Paket vault'un içine yazılmaz.")
            return 2
        if a.update:
            if not (dest.is_dir() and (dest / "EXPORT.json").exists()):
                print(f"{dest} önceki bir paket değil (EXPORT.json yok); --update yalnızca paket klasörüne yazar.")
                return 2
        elif dest.exists():
            print(f"{dest} zaten var. Üzerine yazılmaz; başka `--dest` ver, paket deposunu güncellemek için `--update`.")
            return 2
        info = {"hrvault_sürümü": version(vault), "tür": kind,
                "dosyalar": files,
                "tarama": {"dosya": len(r["dosyalar"]), "engel": 0, "gözden_geçir": 0, "izinli": len(r["izinli"])},
                "bilgi_maddeleri": sorted(baseline_of(st))}
        _write(st / "EXPORT.json", (json.dumps(info, ensure_ascii=False, indent=1) + "\n").encode(), _fixed_time())
        if a.update:
            # Paket deposu: `.git` kalır, geri kalan her şey yeni paketle değişir (silinen dosyalar da silinir).
            for p in dest.iterdir():
                if p.name != ".git":
                    shutil.rmtree(p) if p.is_dir() else p.unlink()
            for p in st.iterdir():
                shutil.move(str(p), str(dest / p.name))
            shutil.rmtree(st)
        else:
            shutil.move(str(st), str(dest))
        st = None
        print(f"\nPaket: {dest} · {len(files)} dosya · sürüm {info['hrvault_sürümü']}")
        if a.zip:
            z = dest.with_suffix(".zip")
            with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
                for p in sorted(dest.rglob("*")):
                    if p.is_file():
                        zi = zipfile.ZipInfo(f"{dest.name}/{p.relative_to(dest).as_posix()}", FIXED)
                        zi.compress_type = zipfile.ZIP_DEFLATED
                        zi.external_attr = 0o644 << 16
                        zf.writestr(zi, p.read_bytes())
            print(f"Zip: {z}")
        if not a.knowledge_only:
            rec = vault / "me" / "pipeline" / "exports.json"
            rec.parent.mkdir(parents=True, exist_ok=True)
            rec.write_text(json.dumps({"son": date.today().isoformat(), "sürüm": info["hrvault_sürümü"],
                                       "bilgi_özetleri": {f: files[f] for f in kn}}, ensure_ascii=False, indent=1) + "\n",
                           encoding="utf-8")
        return cmd_verify(argparse.Namespace(paket=str(dest)))
    finally:
        if st and st.exists():
            shutil.rmtree(st, ignore_errors=True)


# ------------------------------------------------------------------ verify
def verify(pkg: Path) -> list[str]:
    """Paketi me/ olmadan doğrula → sorun listesi (boşsa geçerli)."""
    issues = []
    ej = pkg / "EXPORT.json"
    if not ej.exists():
        return ["EXPORT.json yok — bu klasör onaylanmış bir paket değil"]
    info = json.loads(ej.read_text(encoding="utf-8"))
    actual = package_files(pkg)
    if not (pkg / "me").exists():
        # Paket bir git deposundan alındıysa me/ yoktur (.gitignore); `profile.py init` onu şablondan kurar.
        info["dosyalar"] = {f: h for f, h in info["dosyalar"].items() if not f.startswith("me/")}
    for f in sorted(set(actual) - set(info["dosyalar"])):
        issues.append(f"listede olmayan dosya: {f}")
    for f, h in info["dosyalar"].items():
        if f not in actual:
            issues.append(f"eksik dosya: {f}")
        elif actual[f] != h:
            issues.append(f"paketlendikten sonra değişmiş: {f}")
    for f in actual:
        name = f.rsplit("/", 1)[-1]
        if name == ".DS_Store" or f.endswith(".pyc") or "__pycache__" in f or f.startswith(".git/") \
                or name in ("settings.local.json", "allow.json") or f.endswith((".pdf", ".zip")):
            issues.append(f"yasak dosya: {f}")
        p = pkg / f
        if p.suffix.lower() in TEXT_EXT:
            try:
                text = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                issues.append(f"okunamayan dosya: {f}")
                continue
            for x in scan_text(f, text, []):
                if x.level == ENGEL:
                    issues.append(f"{x.file}:{x.line} · {x.kind}")
    for f in actual:
        if (f.startswith("knowledge/") or f.startswith("engine/adapters/")) and f.endswith(".md") \
                and DATE.search((pkg / f).read_text(encoding="utf-8")):
            issues.append(f"tarih kalmış: {f}")
    mp = pkg / "engine" / "export" / "manifest.json"
    if mp.exists() and json.loads(mp.read_text(encoding="utf-8")).get("bölgesel_adaptörler", True) is False:
        for s, c in regional_stems(pkg).items():
            issues.append(f"bölgesel adaptör pakette ({c}): {s}")
    if info.get("tür") == "tam":
        tpl = pkg / "engine" / "templates" / "me"
        tfiles = {p.relative_to(tpl).as_posix(): _sha(p.read_bytes()) for p in tpl.rglob("*") if p.is_file()}
        mfiles = {f[3:]: h for f, h in actual.items() if f.startswith("me/")}
        if (pkg / "me").exists() and tfiles != mfiles:
            issues.append("me/ boş şablonla aynı değil")
        for x in template_findings(pkg, {"me_şablonu": "engine/templates/me"}):
            issues.append(f"{x.file} · {x.kind}: {x.text}")
    blob = json.dumps(info, ensure_ascii=False)
    if re.search(r"(?:/Users/|/home/|\\Users\\)\w|@", blob):
        issues.append("EXPORT.json içinde yol ya da adres var")
    return issues


def cmd_verify(a) -> int:
    pkg = Path(a.paket).expanduser()
    issues = verify(pkg)
    if issues:
        print(f"Paket GEÇERSİZ ({len(issues)} sorun):")
        for i in issues:
            print(f"  - {i}")
        return 1
    print("Paket doğrulandı: dosyalar listeyle aynı, me/ boş şablon, genel kurallar temiz.")
    return 0


# ------------------------------------------------------------------ merge
def _bump(level: str) -> str:
    return LEVELS[min(LEVELS.index(level) + 1, 2)] if level in LEVELS else "orta"


def merge(vault: Path, pkg: Path) -> dict:
    res = {"eklendi": [], "güçlendi": [], "çelişki": [], "aynı": []}
    for src in knowledge_files(pkg):
        rel = src.relative_to(pkg)
        dst = vault / rel
        inc_text = src.read_text(encoding="utf-8")
        inc_lines = inc_text.splitlines()
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(f"# {src.stem} — öğrenimler\n\n## Öğrenimler\n", encoding="utf-8")
        for e in parse_entries(inc_text):
            if not e["id"]:
                continue
            text = dst.read_text(encoding="utf-8")
            lines = text.splitlines()
            mine = {x["id"]: x for x in parse_entries(text)}
            block = inc_lines[e["start"]:e["end"]]
            if e["id"] in mine:
                cur = mine[e["id"]]
                if cur["özet"] != e["özet"]:
                    if f"k:{e['id']}-gelen" in text:
                        continue
                    block[0] = block[0].replace(f"`k:{e['id']}`", f"`k:{e['id']}-gelen`")
                    lines[cur["end"]:cur["end"]] = block
                    res["çelişki"].append(e["id"])
                elif e["dayanak"] and e["dayanak"] not in cur["dayanak"]:
                    for i in range(cur["start"], cur["end"]):
                        d = DAYANAK.search(lines[i])
                        if d:
                            new = f"_dayanak: {d.group(1)} · +1 kullanıcı ({e['dayanak']}) · güven: {_bump(d.group(2))}{d.group(3)}_"
                            lines[i] = lines[i][:d.start()] + new + lines[i][d.end():]
                    res["güçlendi"].append(e["id"])
                else:
                    res["aynı"].append(e["id"])
                    continue
            else:
                heads = [i for i, l in enumerate(lines) if l.startswith("## ") and l[3:].strip() == e["bölüm"]]
                if heads:
                    at = heads[0] + 1
                    while at < len(lines) and not lines[at].startswith("## "):
                        at += 1
                    while at > 0 and not lines[at - 1].strip():
                        at -= 1
                    lines[at:at] = block
                else:
                    lines += ["", f"## {e['bölüm'] or 'Öğrenimler'}"] + block
                res["eklendi"].append(e["id"])
            dst.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return res


def cmd_merge(a) -> int:
    pkg = Path(a.paket).expanduser()
    issues = verify(pkg)
    if issues:
        print("Paket doğrulanamadı; birleştirilmedi:")
        for i in issues:
            print(f"  - {i}")
        return 1
    res = merge(VAULT, pkg)
    print(f"Birleştirildi: eklendi {len(res['eklendi'])} · güçlendi {len(res['güçlendi'])} · "
          f"çelişki {len(res['çelişki'])} · aynı {len(res['aynı'])}")
    for k in res["çelişki"]:
        print(f"  çelişki: k:{k} — ikisi de duruyor (`k:{k}-gelen`); kişiye sor, birini seç ya da birleştir.")
    return 0


# ------------------------------------------------------------------ diğer komutlar
def cmd_lint(a) -> int:
    generic = False
    if a.hook:
        try:
            patterns_for(VAULT, load_manifest(VAULT))
        except ScanError as e:
            generic = True
            print(f"[uyarı] {e}; yalnızca genel kurallar uygulanıyor.")
    r = lint(VAULT, only=a.dosya or None, generic_only=generic)
    print_report(r)
    return 1 if blocking(r["bulgular"]) else 0


def cmd_allow(a) -> int:
    r = lint(VAULT)
    rel = Path(a.dosya).as_posix()
    hits = [f for f in r["bulgular"] if f.file == rel and f.line == a.satır]
    if not hits:
        print("O satırda açık bulgu yok.")
        return 1
    if any(f.level == ENGEL for f in hits):
        print("engel bulgusuna izin verilemez; kaynakta düzelt.")
        return 1
    p = VAULT / "engine" / "export" / "allow.json"
    data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"izinler": []}
    for f in hits:
        data["izinler"].append({"anahtar": f.key(), "dosya": f.file, "tür": f.kind,
                                "gerekçe": a.gerekce, "tarih": date.today().isoformat()})
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(hits)} izin eklendi (satır değişirse izin düşer).")
    return 0


def cmd_ids(_a) -> int:
    print(f"{assign_ids(VAULT)} maddeye kimlik eklendi.")
    return 0


def cmd_install_hook(_a) -> int:
    g = VAULT / ".git"
    if not g.exists():
        print(".git yok; önce `git init`.")
        return 1
    dst = g / "hooks" / "pre-commit"
    dst.parent.mkdir(exist_ok=True)
    shutil.copyfile(VAULT / "engine" / "export" / "pre-commit", dst)
    dst.chmod(0o755)
    print("pre-commit kuruldu: her commit'ten önce `export.py lint --hook` çalışır.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="HRVault export")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("lint"); s.add_argument("dosya", nargs="*"); s.add_argument("--hook", action="store_true")
    s = sub.add_parser("allow"); s.add_argument("dosya"); s.add_argument("satır", type=int)
    s.add_argument("--gerekce", required=True)
    sub.add_parser("ids")
    s = sub.add_parser("build"); s.add_argument("--dest"); s.add_argument("--reviewed", action="store_true")
    s.add_argument("--zip", action="store_true"); s.add_argument("--knowledge-only", action="store_true")
    s.add_argument("--update", metavar="PAKET", help="önceki paket klasörünü (ör. git deposu) yerinde güncelle; .git korunur")
    s = sub.add_parser("verify"); s.add_argument("paket")
    s = sub.add_parser("merge"); s.add_argument("paket")
    sub.add_parser("install-hook")
    a = ap.parse_args()
    fn = {"lint": cmd_lint, "allow": cmd_allow, "ids": cmd_ids, "build": cmd_build, "verify": cmd_verify,
          "merge": cmd_merge, "install-hook": cmd_install_hook}[a.cmd]
    try:
        return fn(a)
    except ScanError as e:
        print(f"TARAMA YAPILAMADI: {e}\nSonuç \"temiz\" değildir; paket oluşmaz.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
