"""We Work Remotely — herkese açık RSS. feed.categories ile kategori RSS'leri eklenebilir."""
import xml.etree.ElementTree as ET

from ..common import Job, html_to_text, http_get, to_iso

MAIN = "https://weworkremotely.com/remote-jobs.rss"
CAT = "https://weworkremotely.com/categories/{slug}.rss"


def _parse(xml: bytes) -> list[Job]:
    out = []
    for it in ET.fromstring(xml).iter("item"):
        g = lambda tag: (it.findtext(tag) or "").strip()  # noqa: E731
        raw = g("title")
        company, _, title = raw.partition(": ")
        if not title:
            company, title = "", raw
        link = g("link")
        out.append(Job(
            source="weworkremotely",
            native_id=g("guid") or link,
            company=company,
            title=title,
            url=link,
            apply_url=link,
            location=", ".join(x for x in [g("region"), g("country"), g("state")] if x),
            workplace="remote",
            employment_type=g("type"),
            published=to_iso(g("pubDate")),
            tags=[s.strip() for s in g("skills").split(",") if s.strip()] + ([g("category")] if g("category") else []),
            description=html_to_text(g("description")),
        ))
    return out


def fetch(ctx) -> list[Job]:
    slugs = (ctx.get("feed") or {}).get("categories") or []
    urls = [CAT.format(slug=s) for s in slugs] or [MAIN]
    jobs: dict[str, Job] = {}
    for u in urls:
        for j in _parse(http_get(u)):
            jobs[j.native_id] = j
    return list(jobs.values())
