#!/usr/bin/env python3
"""Başvuru klasöründeki cv.md / cover-letter.md → metin tabanlı, tek sütun PDF.

Kullanım (vault kökünden):
  python3 engine/pipeline/render_pdf.py <başvuru-klasörü|adı> [--cv-only | --letter-only] [--html]

Kural: her başvurunun CV'si ve ön yazısı (md + PDF) o başvurunun klasöründe saklanır.
Bu betik yalnızca me/pipeline/applications/ altındaki klasörlere yazar ve PDF adlarını
application.md'ye (`cv_pdf`, `ön_yazı_pdf`) işler.

PDF için yüklü Chrome/Chromium kullanılır (HRVAULT_CHROME ile yol verilebilir). Yalnızca standart kütüphane.
"""
from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from pipeline import records  # noqa: E402

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
]
# Windows: Chrome ve Edge'in olağan kurulum yerleri (ortam değişkenleri yalnızca Windows'ta tanımlı).
for _env in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
    _base = os.environ.get(_env)
    if _base:
        CHROME_CANDIDATES += [os.path.join(_base, "Google", "Chrome", "Application", "chrome.exe"),
                              os.path.join(_base, "Microsoft", "Edge", "Application", "msedge.exe")]
CHROME_CANDIDATES += ["chrome", "msedge"]

# ATS dostu: tek sütun, tablo/ikon yok, iletişim bilgisi gövdede, sistem yazı tipi.
CSS = """
@page { size: A4; margin: 16mm 17mm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 10.3pt; line-height: 1.38; color: #111; }
h1 { font-size: 19pt; margin: 0 0 2pt; }
h1 + p { margin-top: 0; color: #333; }
h2 { font-size: 11.5pt; text-transform: uppercase; letter-spacing: .04em; border-bottom: 1px solid #999;
     padding-bottom: 2pt; margin: 12pt 0 5pt; }
h3 { font-size: 10.6pt; margin: 8pt 0 2pt; }
p { margin: 3pt 0; }
ul { margin: 2pt 0 4pt; padding-left: 14pt; }
li { margin: 1.5pt 0; }
a { color: inherit; text-decoration: none; }
h2, h3 { break-after: avoid; }
li { break-inside: avoid; }
"""


def _inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    return s


def md_to_html(md: str, title: str) -> str:
    """CV/ön yazı için yeterli Markdown alt kümesi: başlıklar, madde listeleri, paragraflar, kalın/italik, link."""
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    out, para, in_list = [], [], False

    def flush():
        nonlocal para
        if para:
            out.append("<p>" + "<br>".join(_inline(x) for x in para) + "</p>")
            para = []

    for raw in md.splitlines():
        line = raw.rstrip()
        m = re.match(r"^(#{1,3})\s+(.*)$", line)
        li = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m or li or not line.strip() or re.match(r"^-{3,}$", line.strip()):
            flush()
        if not li and in_list:
            out.append("</ul>")
            in_list = False
        if m:
            n = len(m.group(1))
            out.append(f"<h{n}>{_inline(m.group(2))}</h{n}>")
        elif li:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_inline(li.group(1))}</li>")
        elif line.strip() and not re.match(r"^-{3,}$", line.strip()):
            para.append(line.strip())
    flush()
    if in_list:
        out.append("</ul>")
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title>'
            f"<style>{CSS}</style></head><body>{''.join(out)}</body></html>")


def chrome() -> str:
    env = os.environ.get("HRVAULT_CHROME")
    for c in ([env] if env else []) + CHROME_CANDIDATES:
        path = c if os.path.isabs(c) else shutil.which(c)
        if path and os.path.exists(path):
            return path
    sys.exit("Chrome/Chromium bulunamadı. HRVAULT_CHROME ortam değişkeniyle yolunu ver.")


def to_pdf(html_text: str, out: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "doc.html"
        src.write_text(html_text, encoding="utf-8")
        cmd = [chrome(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
               f"--user-data-dir={tmp}/profile", f"--print-to-pdf={out}", src.as_uri()]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode != 0 or not out.exists():
            sys.exit(f"PDF üretilemedi: {r.stderr.strip()[-400:]}")


def person_name(md: str) -> str:
    m = re.search(r"^#\s+(.+)$", re.sub(r"<!--.*?-->", "", md, flags=re.S), re.M)
    return re.sub(r"[^\w]+", "_", m.group(1).strip()).strip("_") if m else "CV"


def main() -> int:
    ap = argparse.ArgumentParser(description="cv.md / cover-letter.md → PDF (başvuru klasörüne)")
    ap.add_argument("app", help="başvuru klasörü ya da adının benzersiz parçası")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--cv-only", action="store_true")
    g.add_argument("--letter-only", action="store_true")
    ap.add_argument("--html", action="store_true", help="PDF yanında HTML'i de bırak (kontrol için)")
    ap.add_argument("--force", action="store_true", help="gönderilmiş başvurunun PDF'inin üzerine yaz")
    a = ap.parse_args()

    d = records.app_dir(a.app)
    if records.APPS.resolve() not in d.resolve().parents:
        sys.exit("Yalnızca me/pipeline/applications/ altındaki başvuru klasörlerine yazılır.")
    cv_md = d / "cv.md"
    name = person_name(cv_md.read_text(encoding="utf-8")) if cv_md.exists() else "CV"
    jobs = []
    if not a.letter_only:
        if not cv_md.exists():
            sys.exit(f"{d.name}/cv.md yok — önce tailor CV'yi bu klasöre yazmalı.")
        jobs.append(("cv_pdf", cv_md, d / f"{name}_CV.pdf"))
    if not a.cv_only and (d / "cover-letter.md").exists():
        jobs.append(("ön_yazı_pdf", d / "cover-letter.md", d / f"{name}_Cover_Letter.pdf"))
    state = str(records.read(d).get("durum") or "")
    sent = state not in ("", "hazırlandı")
    fields = {}
    for field, src, out in jobs:
        if sent and out.exists() and not a.force:
            # Gönderilmiş belge kanıttır: işverenin elindeki sürümle aynı kalmalı.
            sys.exit(f"{out.name} gönderilmiş bir başvuruya ait (durum: {state}); üzerine yazılmaz. "
                     "Gerçekten gerekiyorsa --force.")
        page = md_to_html(src.read_text(encoding="utf-8"), out.stem.replace("_", " "))
        if a.html:
            out.with_suffix(".html").write_text(page, encoding="utf-8")
        to_pdf(page, out)
        fields[field] = out.name
        print(f"Yazıldı: {out.relative_to(records.VAULT)} ({out.stat().st_size // 1024} KB)")
    if fields:
        fields["cv"] = "cv.md"
        if "ön_yazı_pdf" in fields:
            fields["ön_yazı"] = "cover-letter.md"
        records.update(d, fields)
    return 0


if __name__ == "__main__":
    sys.exit(main())
