"""Ortak yardımcılar: HTTP, HTML→metin, tarih, ilan şeması, metin katlama, başlık ve bölge eşleşmesi."""
from __future__ import annotations

import html
import json
import os
import re
import ssl
import time
import unicodedata
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path

USER_AGENT = "HRVault/0.1 (personal job search; low volume)"
DESC_LIMIT = 15000


# ---------------------------------------------------------------- Metin katlama
# NFKD ayrıştırmasıyla ASCII'ye inmeyen harfler: bunlar olmadan "ı" silinir ("Yazılım" → "yazlm"),
# "İ".lower() birleşik nokta bırakır, "ß" kaybolur.
_ASCII = str.maketrans({"ı": "i", "İ": "I", "ß": "ss", "ẞ": "SS", "ø": "o", "Ø": "O", "æ": "ae", "Æ": "AE",
                        "œ": "oe", "Œ": "OE", "ł": "l", "Ł": "L", "đ": "d", "Đ": "D", "þ": "th", "Þ": "Th"})


def ascii_fold(s: str | None) -> str:
    """Aksanları ve yerel harfleri ASCII karşılığına indirir, küçük harfe çevirir.
    Aksan işaretleri düşer; ASCII karşılığı olmayan diğer karakterler (uzun tire, tırnak, emoji) boşluk olur:
    silinselerdi "Korean–Japanese" tek kelimeye ("koreanjapanese") dönüşürdü."""
    s = unicodedata.normalize("NFKD", (s or "").translate(_ASCII))
    return "".join(c if c.isascii() else ("" if unicodedata.combining(c) else " ") for c in s).lower()


def fold(s: str | None) -> str:
    """Karşılaştırma biçimi: ASCII, küçük harf, harf/rakam dışı her şey tek boşluk."""
    return re.sub(r"[^a-z0-9]+", " ", ascii_fold(s)).strip()


def role_matches(title: str, role: str) -> bool:
    """Rolün tüm kelimeleri başlıkta kelime başı olarak geçiyor mu (çoğul ekine izin verir)."""
    t = fold(title)
    words = fold(role).split()

    # Kısa kelimeler (ai, ml, qa…) önek olarak eşleşirse gürültü yapar: "ai" → "aircraft". Bunlar tam kelime (+ çoğul) eşleşir.
    def hit(w: str) -> bool:
        pat = rf"\b{re.escape(w)}s?\b" if len(w) <= 3 else rf"\b{re.escape(w)}"
        return bool(re.search(pat, t))
    return bool(words) and all(hit(w) for w in words)


# ---------------------------------------------------------------- İlan dili
# Dile özgü sık işlev kelimeleri (katlanmış). Amaç çeviri değil, ilanın *yazıldığı* dili ayırmak:
# worker'ın `ilan_dilleri` listesinde olmayan dilde yazılmış ilan sınıflandırmaya gelmeden elenir.
_LANG_WORDS = {
    "en": "the and with for you your our are will of that this have from as an be on we is to in",
    "de": "und der die das mit fur wir sie ihre bei eine einen unsere deine du bist sind zu auf nicht ist im den dem des oder sowie uns",
    "fr": "et les des pour vous nous avec une est dans votre notre sur qui au aux du ce cette sont ou",
    "es": "los las para con una que por nuestro nuestra tu sus como mas del al es en son experiencia",
    "it": "il gli per con una che di nel della delle sono il nostro tua esperienza siamo anche",
    "nl": "het een van voor met je jij wij onze zijn bij naar ook wordt deze niet als dat",
    "pt": "os as para com uma que por nossa nosso voce sao em na no dos das experiencia tambem",
    "tr": "ve bir icin ile bu olarak olan gibi daha sizin bizim deneyim calisma en az tercihen",
}
_LANG_SETS = {k: set(v.split()) for k, v in _LANG_WORDS.items()}
LANG_MIN_CHARS = 300   # kısa özetten dil çıkarılmaz (bazı kaynaklar yalnızca birkaç cümle verir)


def posting_language(text: str | None) -> str:
    """İlan metninin yazıldığı dil (ISO kodu) ya da emin değilse "". Kısa ya da karışık metinde tahmin etmez."""
    if not text or len(text) < LANG_MIN_CHARS:
        return ""
    words = fold(text).split()
    score = {k: sum(1 for w in words if w in s) for k, s in _LANG_SETS.items()}
    # Kelimeler diller arasında örtüşür ("in", "de", "en"); yalnızca o dile özgü olanlar ayırt eder.
    uniq = {k: sum(1 for w in words if w in s and not any(w in o for kk, o in _LANG_SETS.items() if kk != k))
            for k, s in _LANG_SETS.items()}
    best, second = sorted(uniq.items(), key=lambda x: -x[1])[:2]
    if best[1] < 8 or best[1] < 2 * max(second[1], 1) or score[best[0]] < 0.04 * len(words):
        return ""
    return best[0]


def company_blocked(company: str | None, blocked: list) -> bool:
    """Şirket kara listede mi: katlanmış ad eşitse ya da kara liste adı şirket adının içinde geçiyorsa."""
    c = fold(company)
    return any(b and (b == c or re.search(rf"\b{re.escape(b)}\b", c)) for b in (fold(str(x)) for x in blocked or []))


# ---------------------------------------------------------------- Bölgeler
def _load_regions() -> dict[str, dict]:
    raw = json.loads((Path(__file__).with_name("regions.json")).read_text(encoding="utf-8"))["bölgeler"]

    def members(key: str, seen: frozenset = frozenset()) -> set[str]:
        out = set()
        for m in raw[key]["üyeler"]:
            if m.startswith("@"):
                if m[1:] not in seen:
                    out |= members(m[1:], seen | {key})
            else:
                out.add(fold(m))
        return out
    return {k: {"adlar": [fold(a) for a in v["adlar"]], "üyeler": members(k)} for k, v in raw.items()}


REGIONS = _load_regions()
OPEN_PLACES = {"worldwide", "anywhere", "global", "globally", "remote"}


def is_region(name: str) -> bool:
    """Bir ülke değil de bölge ya da açık ifade mi ("EU", "Europe", "Worldwide")."""
    f = fold(name)
    return f in OPEN_PLACES or any(f in r["adlar"] for r in REGIONS.values())


def expand_places(allowed: list) -> list[str]:
    """İzin listesine (katlanmış), içindeki ülkeleri kapsayan bölgelerin adlarını ekler.
    ["Austria"] → ["austria", "eu", "european union", "europe", "dach", …]. Bölge adı ülkeye genişlemez."""
    base = [fold(str(a)) for a in allowed if fold(str(a))]
    have = set(base)
    out = list(base)
    for r in REGIONS.values():
        if r["üyeler"] & have:
            out += [a for a in r["adlar"] if a not in out]
    return out


def place_hit(text_folded: str, places: list[str]) -> bool:
    """Katlanmış metinde izinli yerlerden biri kelime sınırıyla geçiyor mu."""
    return any(p and re.search(rf"\b{re.escape(p)}\b", text_folded) for p in places)


# ---------------------------------------------------------------- HTTP
def _ssl_context() -> ssl.SSLContext:
    """Varsayılan sertifika deposu boşsa (macOS'ta python.org kurulumu) certifi'ye
    ya da sistem paketine düş."""
    ctx = ssl.create_default_context()
    if ctx.cert_store_stats().get("x509_ca", 0):
        return ctx
    try:
        import certifi  # type: ignore
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    for path in ("/etc/ssl/cert.pem", "/etc/ssl/certs/ca-certificates.crt", "/etc/pki/tls/certs/ca-bundle.crt"):
        if os.path.exists(path):
            return ssl.create_default_context(cafile=path)
    return ctx


_SSL = _ssl_context()


def http_get(url: str, *, timeout: int = 30, retries: int = 2) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=_SSL) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (404, 401, 403):
                raise
            last = e
        except urllib.error.URLError as e:
            if isinstance(e.reason, ssl.SSLError):
                raise  # sertifika hatası tekrar denemeyle düzelmez
            last = e
        except TimeoutError as e:
            last = e
        time.sleep(1.5 * (attempt + 1))
    raise last  # type: ignore[misc]


def http_json(url: str, **kw):
    return json.loads(http_get(url, **kw).decode("utf-8"))


# ---------------------------------------------------------------- HTML
class _Text(HTMLParser):
    BLOCK = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "ul", "ol"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self.out.append("\n- ")
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        self.out.append(data)


def html_to_text(s: str | None, *, escaped: bool = False) -> str:
    if not s:
        return ""
    if escaped:
        s = html.unescape(s)
    p = _Text()
    p.feed(s)
    text = "".join(p.out).replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------- Tarih
def to_iso(value) -> str | None:
    """epoch (s/ms), ISO ya da RFC822 → ISO-8601 UTC."""
    if value in (None, ""):
        return None
    try:
        if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
            v = float(value)
            if v > 1e12:
                v /= 1000
            return datetime.fromtimestamp(v, tz=timezone.utc).isoformat()
        s = str(value)
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            dt = parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return None


def age_days(iso: str | None) -> float | None:
    if not iso:
        return None
    return (datetime.now(timezone.utc) - datetime.fromisoformat(iso)).total_seconds() / 86400


def fresh_age(job) -> float | None:
    """İlanın tazeliği: yayın ve güncelleme tarihlerinden yeni olanının yaşı (gün). Yeniden yayımlanan ya da
    güncellenen ilan taze sayılır. Tarih yoksa None (filtre uygulanmaz)."""
    ages = [a for a in (age_days(job.published), age_days(getattr(job, "updated", None))) if a is not None]
    return min(ages) if ages else None


# ---------------------------------------------------------------- Şema
@dataclass
class Job:
    source: str
    native_id: str
    company: str
    title: str
    url: str
    apply_url: str = ""
    location: str = ""
    workplace: str = ""          # remote | hybrid | onsite | "" (kaynağın beyanı; scan skill'i doğrular)
    employment_type: str = ""    # kaynağın ham değeri
    salary: str = ""
    published: str | None = None
    updated: str | None = None   # kaynak veriyorsa son güncelleme / yeniden yayım (Greenhouse updated_at)
    tags: list[str] = field(default_factory=list)
    description: str = ""
    # scan.py doldurur
    workers: list[str] = field(default_factory=list)
    matched: list[str] = field(default_factory=list)
    also_on: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return f"{self.source}:{self.native_id}"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["id"] = self.id
        d["description"] = (self.description or "")[:DESC_LIMIT]
        return d


def norm_workplace(raw) -> str:
    s = str(raw or "").lower().replace("-", "").replace("_", "")
    if "hybrid" in s:
        return "hybrid"
    if "remote" in s:
        return "remote"
    if "onsite" in s or "on site" in s or "office" in s:
        return "onsite"
    return ""
