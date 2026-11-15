"""Remotive — herkese açık API. Koşul: Remotive'i kaynak olarak belirt, ilanları yeniden yayınlama."""
from urllib.parse import urlencode

from ..common import Job, html_to_text, http_json, to_iso

API = "https://remotive.com/api/remote-jobs"


def fetch(ctx) -> list[Job]:
    params = {k: v for k, v in (ctx.get("feed") or {}).items() if k in ("category",)}
    data = http_json(API + ("?" + urlencode(params) if params else ""))
    return [
        Job(
            source="remotive",
            native_id=str(j["id"]),
            company=j.get("company_name", ""),
            title=j.get("title", ""),
            url=j.get("url", ""),
            apply_url=j.get("url", ""),
            location=j.get("candidate_required_location", ""),
            workplace="remote",
            employment_type=j.get("job_type", ""),
            salary=j.get("salary", ""),
            published=to_iso(j.get("publication_date")),
            tags=j.get("tags") or [],
            description=html_to_text(j.get("description")),
        )
        for j in data.get("jobs", [])
    ]
