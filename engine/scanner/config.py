"""me/ klasöründen worker'ları ve kaynak ayarlarını okur."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # PyYAML yoksa basit ayrıştırıcı
    yaml = None


def _scalar(v: str):
    v = v.strip()
    if v in ("", "~", "null"):
        return None
    if v.startswith("[") and v.endswith("]"):
        return [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v.strip("'\"")


def _mini_yaml(text: str) -> dict:
    """PyYAML yokken frontmatter için yeterli alt küme: girintiyle iç içe map'ler,
    `- madde` listeleri, satır içi `[a, b]` listeleri ve skaler değerler."""
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"\s+#.*$", "", raw).rstrip()
        if line.strip() and not line.lstrip().startswith("#"):
            lines.append((len(line) - len(line.lstrip()), line.strip()))

    def block(i: int, ind: int):
        """i. satırdan başlayıp girintisi `ind` olan bloğu ayrıştırır → (değer, sonraki i)."""
        if i < len(lines) and lines[i][1].startswith("- "):
            out = []
            while i < len(lines) and lines[i][0] == ind and lines[i][1].startswith("- "):
                out.append(_scalar(lines[i][1][2:]))
                i += 1
            return out, i
        out: dict = {}
        while i < len(lines) and lines[i][0] == ind:
            key, _, val = lines[i][1].partition(":")
            i += 1
            if val.strip():
                out[key.strip()] = _scalar(val)
            elif i < len(lines) and (lines[i][0] > ind or (lines[i][0] == ind and lines[i][1].startswith("- "))):
                out[key.strip()], i = block(i, lines[i][0])
            else:
                out[key.strip()] = None
        return out, i

    root, _ = block(0, lines[0][0]) if lines else ({}, 0)
    return root


def read_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return {}
    body = m.group(1)
    return (yaml.safe_load(body) if yaml else _mini_yaml(body)) or {}


def worker_defaults(vault: Path) -> dict:
    p = vault / "me" / "profile" / "preferences.md"
    return dict((read_frontmatter(p).get("worker_varsayılanları") if p.exists() else None) or {})


def load_workers(vault: Path, *, only_active: bool = True) -> list[dict]:
    workers = []
    today = date.today().isoformat()
    defaults = worker_defaults(vault)
    common_excl = list(defaults.pop("ortak_hariç_başlık", None) or [])
    for p in sorted((vault / "me" / "workers").glob("*.md")):
        if p.name.lower() == "readme.md":
            continue
        fm = read_frontmatter(p)
        if not fm:
            continue
        for k, v in defaults.items():  # worker'da yoksa ya da boşsa varsayılan
            if fm.get(k) in (None, "", [], {}):
                fm[k] = v
        fm.setdefault("ad", p.stem)
        fm["_path"] = str(p)
        state = str(fm.get("durum") or "").strip()
        resume = fm.get("duraklatma_bitişi")
        if state != "aktif" and resume and str(resume) <= today:
            state = "aktif"  # duraklatma süresi doldu
        fm["_aktif"] = state == "aktif"
        for k in ("roller", "kaynaklar", "hariç_başlık", "şirket_kökleri"):
            v = fm.get(k)
            fm[k] = [v] if isinstance(v, str) else list(v or [])
        fm["hariç_başlık"] += [x for x in common_excl if x not in fm["hariç_başlık"]]
        if fm["_aktif"] or not only_active:
            workers.append(fm)
    return workers


def load_sources(vault: Path) -> dict:
    p = vault / "me" / "sources.json"
    if not p.exists():
        return {"watchlist": [], "feeds": {}, "max_age_days": 14}
    return json.loads(p.read_text(encoding="utf-8"))
