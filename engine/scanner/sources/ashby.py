from ..common import Job, http_json, norm_workplace, to_iso

API = "https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true"


def fetch_board(company: str, token: str) -> list[Job]:
    jobs = []
    for j in http_json(API.format(token=token)).get("jobs", []):
        if j.get("isListed") is False:
            continue
        comp = (j.get("compensation") or {}).get("compensationTierSummary") or ""
        wp = norm_workplace(j.get("workplaceType")) or ("remote" if j.get("isRemote") else "")
        locs = [j.get("location", "")] + [s.get("location", "") for s in j.get("secondaryLocations") or []]
        jobs.append(Job(
            source="ashby",
            native_id=j["id"],
            company=company,
            title=j.get("title", ""),
            url=j.get("jobUrl", ""),
            apply_url=j.get("applyUrl", ""),
            location=", ".join(l for l in locs if l),
            workplace=wp,
            employment_type=j.get("employmentType", ""),
            salary=comp,
            published=to_iso(j.get("publishedAt")),
            tags=[t for t in [j.get("department"), j.get("team")] if t],
            description=j.get("descriptionPlain", ""),
        ))
    return jobs


def fetch(ctx) -> list[Job]:
    out = []
    for w in ctx["watchlist"]:
        out += fetch_board(w["company"], w["token"])
    return out
