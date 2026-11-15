"""Remote OK — herkese açık API. Koşul: Remote OK'u kaynak olarak belirt ve ilan linkini koru."""
from ..common import Job, html_to_text, http_json, to_iso

API = "https://remoteok.com/api"


def fetch(ctx) -> list[Job]:
    data = http_json(API)
    out = []
    for j in data:
        if "id" not in j or "position" not in j:  # ilk eleman yasal not
            continue
        sal = ""
        if j.get("salary_min") or j.get("salary_max"):
            sal = f"{j.get('salary_min', '')}–{j.get('salary_max', '')} USD yıllık"
        out.append(Job(
            source="remoteok",
            native_id=str(j["id"]),
            company=j.get("company", ""),
            title=j.get("position", ""),
            url=j.get("url", ""),
            apply_url=j.get("apply_url", "") or j.get("url", ""),
            location=j.get("location", ""),
            workplace="remote",
            salary=sal,
            published=to_iso(j.get("date") or j.get("epoch")),
            tags=j.get("tags") or [],
            description=html_to_text(j.get("description")),
        ))
    return out
