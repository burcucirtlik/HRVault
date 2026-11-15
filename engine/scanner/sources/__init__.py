"""Kaynak kaydı. Her modül `fetch(ctx) -> list[Job]` sağlar.

ctx: {"watchlist": [...], "feed": {...kaynağa özel ayar}, "queries": [rol anahtar kelimeleri]}
"""
import importlib
import pkgutil

from . import ashby, greenhouse, himalayas, lever, remoteok, remotive, weworkremotely

# ATS kaynakları: takip listesindeki şirketlerden çeker (me/sources.json → watchlist)
ATS = {"greenhouse": greenhouse, "lever": lever, "ashby": ashby}
# Akış kaynakları: kendi genel ilan akışları (me/sources.json → feeds)
FEEDS = {
    "remotive": remotive,
    "remoteok": remoteok,
    "weworkremotely": weworkremotely,
    "himalayas": himalayas,
}
# Bölgesel akışlar: bu klasördeki diğer modüller kendiliğinden bulunur. Modül `KAPSAM = "<ülke kodu>"` taşır ve
# yalnızca `me/sources.json → feeds.<ad>.enabled: true` ise taranır. Paylaşım paketinde bulunmayabilirler.
for _m in pkgutil.iter_modules(__path__):
    if _m.name not in ATS and _m.name not in FEEDS:
        FEEDS[_m.name] = importlib.import_module(f".{_m.name}", __name__)
ALL = {**ATS, **FEEDS}
