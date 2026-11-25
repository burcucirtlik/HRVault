"""Himalayas — herkese açık arama API'si. Rol anahtar kelimeleriyle arar (sayfa başı 20 ilan).

- **Ülke filtresi:** `country=<ülke>` adayın o ülkeden başvurabileceği ilanları (kısıtsız "worldwide" ilanlar dahil)
  döndürür; tek ülke alır, geçersizse 400 verir. Filtre olmadan ilk sayfalar başka ülkelere kısıtlı ilanlarla dolar
  ve uygun ilanlar okunmadan kalır. Ülke `feeds.himalayas.country` ile verilir; yoksa worker `ülkeler` listesindeki
  ülke adlarından (bölge ve "Worldwide" gibi ifadeler hariç) türetilir.
- **Sayfa:** alaka sırası başlık eşleşmelerini ilk sayfalara toplar. Bir sayfada başlığı sorguya uyan ilan yoksa
  sonraki sayfalar okunmaz; `feeds.himalayas.pages` üst sınırdır.
- **Hız sınırı:** 429 gelirse 15, 60 ve 120 saniye bekleyerek tekrar dener; yine gelirse durur ve okunmayan sorguları
  `ctx["uyarılar"]`'a yazar (tarama özetinde görünür). Başlangıç sorgusu güne göre döner: kesilirse hep aynı
  roller dışarıda kalmaz.
"""
import time
import urllib.error
from datetime import date
from urllib.parse import urlencode

from ..common import Job, html_to_text, http_json, is_region, role_matches, to_iso

SEARCH = "https://himalayas.app/jobs/api/search"
DELAY_S = 1.0      # istekler arası bekleme; arka arkaya istekler 429 (Too Many Requests) döndürüyor
BACKOFF_S = (15, 60, 120)   # 429 gelirse sırayla bu kadar bekleyip tekrar dene; hepsi dolarsa kalan sorgular raporlanır
PAGE = 20


class _RateLimited(Exception):
    pass


class _BadCountry(Exception):
    pass


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


def countries(ctx) -> list[str]:
    """Aramada kullanılacak ülkeler; boş liste = filtresiz."""
    c = (ctx.get("feed") or {}).get("country")
    if c:
        return [c] if isinstance(c, str) else [str(x) for x in c]
    return [x for x in ctx.get("countries") or [] if x and not is_region(x)]


def _get(params: dict) -> dict:
    url = SEARCH + "?" + urlencode(params)
    for wait in (*BACKOFF_S, None):
        try:
            return http_json(url)
        except urllib.error.HTTPError as e:
            if e.code == 400 and "country" in params:
                raise _BadCountry(params["country"]) from e
            if e.code != 429:
                raise
            if wait is None:
                raise _RateLimited() from e
            time.sleep(wait)
    raise AssertionError("ulaşılmaz")


def fetch(ctx) -> list[Job]:
    pages = max(1, int((ctx.get("feed") or {}).get("pages", 1)))
    warn = ctx.setdefault("uyarılar", [])
    queries = list(ctx.get("queries") or [])
    if queries:
        k = date.today().toordinal() % len(queries)
        queries = queries[k:] + queries[:k]
    plan = [(c, q) for c in (countries(ctx) or [None]) for q in queries]
    out: dict[str, Job] = {}
    bad: set[str] = set()
    first = True
    for n, (country, q) in enumerate(plan):
        if country in bad:
            continue
        for page in range(1, pages + 1):
            if not first:
                time.sleep(DELAY_S)
            first = False
            params = {"q": q, "page": page} | ({"country": country} if country else {})
            try:
                data = _get(params)
            except _BadCountry:
                bad.add(country)
                warn.append(f"'{country}' Himalayas'ta geçersiz ülke; bu ülke için arama yapılmadı "
                            "(feeds.himalayas.country ile düzelt)")
                break
            except _RateLimited:
                left = [q2 for _, q2 in plan[n:]]
                warn.append(f"hız sınırı (429): {len(left)}/{len(plan)} sorgu okunmadı — "
                            f"{', '.join(left[:8])}{'…' if len(left) > 8 else ''}")
                return list(out.values())
            batch = data.get("jobs") or []
            for j in batch:
                job = _job(j)
                out[job.native_id] = job
            if len(batch) < PAGE or not any(role_matches(j.get("title", ""), q) for j in batch):
                break
    if bad and len(bad) == len(set(countries(ctx))):
        # Hiçbir ülke geçerli değilse eski davranış: filtresiz ara (sonuç az ama boş değil).
        retry = dict(ctx, feed=dict(ctx.get("feed") or {}, country=None), countries=[])
        return list({**{j.native_id: j for j in fetch(retry)}, **out}.values())
    return list(out.values())
