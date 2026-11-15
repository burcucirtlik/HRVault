"""Himalayas — herkese açık arama API'si. Rol anahtar kelimeleriyle arar (sayfa başı 20 ilan)."""
import time
import urllib.error
from urllib.parse import urlencode

from ..common import Job, html_to_text, http_json, to_iso

SEARCH = "https://himalayas.app/jobs/api/search"
DELAY_S = 1.0      # istekler arası bekleme; arka arkaya istekler 429 (Too Many Requests) döndürüyor
BACKOFF_S = 15     # 429 gelirse bir kez bu kadar bekleyip tekrar dene


def _job(j) -> Job:
    sal = ""
    if j.get("minSalary") or j.get("maxSalary"):
        sal = f"{j.get('minSalary', '')}–{j.get('maxSalary', '')} {j.get('currency', '')} {j.get('salaryPeriod', '')}".strip()
    return Job(
        source="himalayas",
        native_id=j.get("guid") or j.get("applicationLink", ""),
        company=j.get("companyName", ""),
        title=j.get("title", ""),
        url=j.get("guid") or j.get("applicationLink", ""),
        apply_url=j.get("applicationLink", ""),
        location=", ".join(j.get("locationRestrictions") or []) or "Worldwide",
        workplace="remote",
        employment_type=j.get("employmentType", ""),
        salary=sal,
        published=to_iso(j.get("pubDate")),
        tags=(j.get("seniority") or []) + (j.get("categories") or [])[:5],
        description=html_to_text(j.get("description")) or j.get("excerpt", ""),
    )


def fetch(ctx) -> list[Job]:
    pages = int((ctx.get("feed") or {}).get("pages", 1))
    out: dict[str, Job] = {}
    first = True
    for q in ctx.get("queries") or []:
        for page in range(1, pages + 1):
            if not first:
                time.sleep(DELAY_S)
            first = False
            url = SEARCH + "?" + urlencode({"q": q, "page": page})
            try:
                data = http_json(url)
            except urllib.error.HTTPError as e:
                if e.code != 429:
                    raise
                time.sleep(BACKOFF_S)
                try:
                    data = http_json(url)
                except urllib.error.HTTPError as e2:
                    if e2.code == 429 and out:
                        return list(out.values())  # kısmi sonuç, taramayı düşürme
                    raise
            batch = data.get("jobs") or []
            for j in batch:
                job = _job(j)
                out[job.native_id] = job
            if len(batch) < 20:
                break
    return list(out.values())
