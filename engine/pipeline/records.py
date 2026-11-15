"""Başvuru kayıtları (me/pipeline/applications/<klasör>/application.md) için ortak yardımcılar."""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from scanner import config  # noqa: E402

VAULT = HERE.parent.parent
APPS = VAULT / "me" / "pipeline" / "applications"
STATES = ["hazırlandı", "başvuruldu", "görüldü", "mülakat", "teklif", "ret", "sessiz", "iptal"]


def app_dir(ref: str) -> Path:
    """Klasör yolu, klasör adı ya da adın benzersiz bir parçası → başvuru klasörü."""
    p = Path(ref)
    if (p / "application.md").exists():
        return p.resolve()
    if (APPS / ref / "application.md").exists():
        return APPS / ref
    hits = [d for d in APPS.glob("*/") if ref.lower() in d.name.lower() and (d / "application.md").exists()]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        sys.exit(f"Başvuru bulunamadı: {ref}")
    sys.exit(f"Birden çok başvuru eşleşti: {', '.join(d.name for d in hits)}")


def read(d: Path) -> dict:
    fm = config.read_frontmatter(d / "application.md")
    return {k: ("" if v is None else v) for k, v in fm.items()}


def update(d: Path, fields: dict, history: str | None = None) -> None:
    """Frontmatter alanlarını yerinde günceller (satır yorumlarını korur), yoksa ekler.
    `history` verilirse "Durum geçmişi" bölümüne tarihli satır ekler."""
    p = d / "application.md"
    t = p.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    if not m:
        sys.exit(f"Frontmatter yok: {p}")
    lines = m.group(1).split("\n")
    for k, v in fields.items():
        v = "" if v is None else str(v)
        for i, line in enumerate(lines):
            if re.match(rf"^{re.escape(k)}:", line):
                comment = re.search(r"\s+#.*$", line)
                lines[i] = f"{k}: {v}".rstrip() + (comment.group(0) if comment else "")
                break
        else:
            lines.append(f"{k}: {v}".rstrip())
    body = t[m.end():]
    if history:
        entry = f"- {date.today().isoformat()} · {history}"
        if "## Durum geçmişi\n" in body:
            body = body.replace("## Durum geçmişi\n", f"## Durum geçmişi\n{entry}\n", 1)
        else:
            body += f"\n## Durum geçmişi\n{entry}\n"
    p.write_text("---\n" + "\n".join(lines) + "\n---\n" + body, encoding="utf-8")


def all_apps() -> list[tuple[Path, dict]]:
    return [(p.parent, read(p.parent)) for p in sorted(APPS.glob("*/application.md"))]
