import re

from ..common import Job, http_json, norm_workplace, to_iso

API = "https://api.lever.co/v0/postings/{token}?mode=json"


def _salary(j) -> str:
    r = j.get("salaryRange") or {}
    if not r:
        return ""
    return f"{r.get('min', '')}–{r.get('max', '')} {r.get('currency', '')} {r.get('interval', '')}".strip()


def _list_text(l) -> str:
    items = [x.strip() for x in re.sub(r"<[^>]+>", "\n", l.get("content", "")).split("\n") if x.strip()]
    return l.get("text", "") + "\n" + "\n".join("- " + x for x in items)


def fetch_board(company: str, token: str) -> list[Job]:
    jobs = []
    for j in http_json(API.format(token=token)):
        cat = j.get("categories") or {}
        lists = "\n\n".join(_list_text(l) for l in j.get("lists") or [])
        desc = "\n\n".join(x for x in [j.get("descriptionPlain", ""), lists, j.get("additionalPlain", "")] if x)
        jobs.append(Job(
            source="lever",
            native_id=j["id"],
            company=company,
            title=j.get("text", ""),
            url=j.get("hostedUrl", ""),
            apply_url=j.get("applyUrl", ""),
            location=", ".join(cat.get("allLocations") or [cat.get("location", "")]),
            workplace=norm_workplace(j.get("workplaceType")),
            employment_type=cat.get("commitment", ""),
            salary=_salary(j),
            published=to_iso(j.get("createdAt")),
            tags=[t for t in [cat.get("team"), cat.get("department")] if t],
            description=desc.strip(),
        ))
    return jobs


def fetch(ctx) -> list[Job]:
    out = []
    for w in ctx["watchlist"]:
        out += fetch_board(w["company"], w["token"])
    return out
