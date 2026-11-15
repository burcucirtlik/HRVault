"""Ortak yardımcılar: HTTP, HTML→metin, tarih, ilan şeması."""
from __future__ import annotations

import html
import json
import os
import re
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

USER_AGENT = "HRVault/0.1 (personal job search; low volume)"
DESC_LIMIT = 15000


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
