#!/usr/bin/env python3
"""ATS anahtar kelime eşleşmesi — tekrarlanabilir ölçüm.

Kullanım (vault kökünden):
  python3 engine/pipeline/ats.py <başvuru> --required "Python; prompt engineering|prompting; LLM" \
                                           [--preferred "Zapier; Airflow"] [--record]

Anahtar kelimeleri tailor skill'i ilandan çıkarır (zorunlu / tercih edilen). `a|b` eş anlamlıdır:
CV'de biri geçerse eşleşir. Ölçüm başvuru klasöründeki cv.md üzerinde yapılır (büyük/küçük harf ve
aksan duyarsız, kelime sınırıyla). Puan: zorunlu ×2, tercih ×1 ağırlıklı yüzde.
`--record` sonucu application.md → `ats_eşleşme` alanına yazar.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from pipeline import records  # noqa: E402


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9+#.]+", " ", s)


def found(text: str, term: str) -> bool:
    """`term` (eş anlamlılar `|` ile) metinde kelime sınırıyla geçiyor mu."""
    for alt in term.split("|"):
        w = fold(alt).strip()
        if w and re.search(rf"(?<![a-z0-9]){re.escape(w)}(?![a-z0-9])", text):
            return True
    return False


def split(s: str | None) -> list[str]:
    return [x.strip() for x in re.split(r"[;\n]", s or "") if x.strip()]


def measure(cv_text: str, required: list[str], preferred: list[str]) -> dict:
    t = " " + fold(cv_text) + " "
    req = {k: found(t, k) for k in required}
    pref = {k: found(t, k) for k in preferred}
    total = 2 * len(req) + len(pref)
    got = 2 * sum(req.values()) + sum(pref.values())
    return {
        "yüzde": round(100 * got / total) if total else None,
        "zorunlu": f"{sum(req.values())}/{len(req)}",
        "tercih": f"{sum(pref.values())}/{len(pref)}",
        "eşleşen": [k for k, v in {**req, **pref}.items() if v],
        "eksik_zorunlu": [k for k, v in req.items() if not v],
        "eksik_tercih": [k for k, v in pref.items() if not v],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="CV ↔ ilan anahtar kelime eşleşmesi")
    ap.add_argument("app", help="başvuru klasörü ya da adının benzersiz parçası")
    ap.add_argument("--required", required=True, help="noktalı virgülle; eş anlamlı için a|b")
    ap.add_argument("--preferred", default="")
    ap.add_argument("--record", action="store_true", help="application.md → ats_eşleşme")
    a = ap.parse_args()
    d = records.app_dir(a.app)
    cv = d / "cv.md"
    if not cv.exists():
        sys.exit(f"{d.name}/cv.md yok.")
    text = re.sub(r"<!--.*?-->", "", cv.read_text(encoding="utf-8"), flags=re.S)
    r = measure(text, split(a.required), split(a.preferred))
    print(json.dumps(r, ensure_ascii=False, indent=2))
    if a.record and r["yüzde"] is not None:
        records.update(d, {"ats_eşleşme": f"{r['yüzde']}% (zorunlu {r['zorunlu']}, tercih {r['tercih']})"})
        print(f"kaydedildi → {d.name}/application.md", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
