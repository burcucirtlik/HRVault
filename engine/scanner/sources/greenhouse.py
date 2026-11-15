from ..common import Job, html_to_text, http_json, norm_workplace, to_iso

API = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"


def fetch_board(company: str, token: str) -> list[Job]:
    data = http_json(API.format(token=token))
    jobs = []
    for j in data.get("jobs", []):
        meta = {m.get("name"): m.get("value") for m in j.get("metadata") or [] if m}
        jobs.append(Job(
            source="greenhouse",
            native_id=str(j["id"]),
            company=j.get("company_name") or company,
            title=j.get("title", ""),
            url=j.get("absolute_url", ""),
            apply_url=j.get("absolute_url", ""),
            location=(j.get("location") or {}).get("name", ""),
            workplace=norm_workplace(meta.get("Location Type") or meta.get("Workplace Type")),
            employment_type=str(meta.get("Employment Type") or meta.get("Employment type") or ""),
            published=to_iso(j.get("first_published") or j.get("updated_at")),
            tags=[d["name"] for d in j.get("departments") or [] if d.get("name")],
            description=html_to_text(j.get("content"), escaped=True),
        ))
    return jobs


def fetch(ctx) -> list[Job]:
    out = []
    for w in ctx["watchlist"]:
        out += fetch_board(w["company"], w["token"])
    return out
