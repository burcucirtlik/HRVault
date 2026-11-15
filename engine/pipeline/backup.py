#!/usr/bin/env python3
"""me/ klasörünün tarihli zip yedeği. me/ git'e girmez; tek kopyası budur.

Kullanım (vault kökünden):
  python3 engine/pipeline/backup.py [--dest KLASÖR] [--keep 30]

Hedef: --dest, yoksa preferences.md → `yedek_klasörü`, o da yoksa vault'un yanındaki `HRVault-yedek/`.
Hedefi bir bulut eşitleme klasörü (iCloud Drive, Dropbox…) yapmak makine kaybına karşı korur.
`--keep` en yeni N yedeği tutar, eskileri siler.
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from scanner import config  # noqa: E402

VAULT = HERE.parent.parent
ME = VAULT / "me"


def main() -> int:
    ap = argparse.ArgumentParser(description="me/ yedeği")
    ap.add_argument("--dest")
    ap.add_argument("--keep", type=int, default=30)
    a = ap.parse_args()
    if not ME.exists():
        sys.exit("me/ yok.")
    prefs_p = ME / "profile" / "preferences.md"
    prefs = config.read_frontmatter(prefs_p) if prefs_p.exists() else {}
    dest = Path(a.dest or prefs.get("yedek_klasörü") or VAULT.parent / "HRVault-yedek").expanduser()
    if VAULT.resolve() in dest.resolve().parents or dest.resolve() == VAULT.resolve():
        sys.exit("Yedek vault'un içine yazılmaz (export ile birlikte paylaşılabilir).")
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / f"me-{datetime.now().strftime('%Y-%m-%d_%H%M')}.zip"
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(ME.rglob("*")):
            if p.is_file() and p.name != ".DS_Store":
                z.write(p, p.relative_to(VAULT))
                n += 1
    old = sorted(dest.glob("me-*.zip"))[:-a.keep] if a.keep > 0 else []
    for p in old:
        p.unlink()
    print(f"Yedek: {out} · {n} dosya · {out.stat().st_size // 1024} KB" + (f" · {len(old)} eski yedek silindi" if old else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
