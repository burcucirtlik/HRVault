#!/usr/bin/env python3
"""ATS anahtar kelime eşleşmesi — tekrarlanabilir, denetlenebilir ölçüm.

Kullanım (vault kökünden):
  python3 engine/pipeline/ats.py <başvuru> --required "Python; prompt engineering|prompting; LLM" \
                                           [--preferred "Zapier; Airflow"] [--record] [--cikar-gerekce "…"]
  python3 engine/pipeline/ats.py <başvuru> --record       # kayıtlı listeyle yeniden ölç
  (cv.md yokken `--required … --record` yalnızca listeyi kaydeder: tailor listeyi CV'yi yazmadan önce kilitler.)
  python3 engine/pipeline/ats.py <başvuru> --gate         # gönderim kapısı

Anahtar kelimeleri tailor skill'i ilandan **CV'yi yazmadan önce** çıkarır (zorunlu / tercih edilen). `a|b` aynı şartın
yazım farklarıdır: CV'de biri geçerse eşleşir. Tekil/çoğul farkı (4+ harfli son kelimede) kendiliğinden eşleşir.
Ölçüm başvuru klasöründeki cv.md üzerinde yapılır (büyük/küçük harf ve aksan duyarsız, kelime sınırıyla).
Puan: zorunlu ×2, tercih ×1 ağırlıklı yüzde. **İlk `--required` terimi ilanın birincil şartıdır.**

`--record`:
  - Her terimin **en az bir yazımı ilan.md'de geçmeli**; geçmeyen terim listeye girmez (ilan.md yoksa kayıt yok).
    İlanda geçmeyen eş anlamlılar reddedilmez ama her ölçümde ayrıca listelenir.
  - Liste `<başvuru>/ats-terimler.json`'a yazılır. Sonraki kayıtta bir terimi çıkarmak, zorunludan tercihe indirmek ya
    da birincil şartı değiştirmek `--cikar-gerekce` ister ve gerekçe dosyada kalır: liste CV'ye uysun diye budanamaz.
  - Sonuç application.md → `ats_eşleşme`, `ats_eksik_zorunlu`, `ats_eksik_tercih`, `ats_ilk_zorunlu` alanlarına yazılır.

Gönderim kapısı (`--gate`; apply her gönderimden önce, track.py `başvuruldu` yapmadan önce çalıştırır):
**Sabit kural:** ATS puanı %90 altındaysa başvuru yapılmaz. Ayarla değişmez, kişi onayıyla da aşılmaz.
Kapı kayıtlı sayıya güvenmez: kayıtlı terim listesini cv.md üzerinde **yeniden ölçer**. Geçmez (çıkış kodu 1) eğer:
terim listesi kayıtlı değilse, puan %90'ın altındaysa, birincil şart CV'de yoksa ya da yüklenecek PDF cv.md'den eskiyse.
Geçmezse eksik kelimeler ağırlık sırasıyla öneri olarak listelenir; kanıtı olanlar CV'ye eklenir.
form-cevaplar.md varsa eleyici sorular (izin, konum, taşınma, ücret, dil, başlangıç) ayrıca listelenir; engel değildir,
gönderimden önce kişiyle gözden geçirilir.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from pipeline import records  # noqa: E402
from scanner.common import ascii_fold  # noqa: E402

MIN_ATS = 90  # sabit kural — preferences'tan okunmaz, kişi onayıyla da aşılmaz
TERMS = "ats-terimler.json"


def fold(s: str) -> str:
    return re.sub(r"[^a-z0-9+#.]+", " ", ascii_fold(s))


def _forms(w: str) -> list[str]:
    """Bir yazımın tekil/çoğul biçimleri. Yalnızca son kelime 4+ harfse: "IT" → "its" olmasın."""
    words = w.split()
    if not words or len(words[-1]) < 4:
        return [w]
    out = [w, w + "es"]                     # process → processes, approach → approaches
    if w.endswith("es"):
        out.append(w[:-2])                  # processes → process
    if w.endswith("s"):
        out.append(w[:-1])                  # stakeholders → stakeholder
    else:
        out.append(w + "s")
    return out


def found(text: str, term: str) -> bool:
    """`term` (eş anlamlılar `|` ile) katlanmış metinde kelime sınırıyla geçiyor mu."""
    for alt in term.split("|"):
        w = fold(alt).strip()
        if w and any(re.search(rf"(?<![a-z0-9]){re.escape(f)}(?![a-z0-9])", text) for f in _forms(w)):
            return True
    return False


def split(s: str | None) -> list[str]:
    return [x.strip() for x in re.split(r"[;\n]", s or "") if x.strip()]


def _clean(text: str) -> str:
    return " " + fold(re.sub(r"<!--.*?-->", "", text, flags=re.S)) + " "


def measure(cv_text: str, required: list[str], preferred: list[str]) -> dict:
    t = _clean(cv_text)
    req = {k: found(t, k) for k in required}
    pref = {k: found(t, k) for k in preferred}
    total = 2 * len(req) + len(pref)
    got = 2 * sum(req.values()) + sum(pref.values())
    return {
        "yüzde": round(100 * got / total) if total else None,
        "zorunlu": f"{sum(req.values())}/{len(req)}",
        "tercih": f"{sum(pref.values())}/{len(pref)}",
        "ağırlık": [got, total],
        "eşleşen": [k for k, v in {**req, **pref}.items() if v],
        "eksik_zorunlu": [k for k, v in req.items() if not v],
        "eksik_tercih": [k for k, v in pref.items() if not v],
        "birincil_eksik": bool(required) and not req[required[0]],
    }


# ------------------------------------------------------------------ terim listesi
def check_against_ilan(ilan_text: str, terms: list[str]) -> tuple[list[str], list[str]]:
    """→ (hiçbir yazımı ilanda olmayan terimler, ilanda geçmeyen eş anlamlılar "terim → yazım")."""
    t = _clean(ilan_text)
    absent = [k for k in terms if not found(t, k)]
    loose = [f"{k} → {a.strip()}" for k in terms if k not in absent for a in k.split("|") if not found(t, a)]
    return absent, loose


def _alts(term: str) -> frozenset:
    return frozenset(fold(a).strip() for a in term.split("|") if fold(a).strip())


def narrowing(old: dict, req: list[str], pref: list[str]) -> list[str]:
    """Eski listeye göre puanı kolaylaştıran değişiklikler: terim çıkarma, zorunludan indirme, birincil şart değişimi.
    Bir terime ilandaki yeni bir yazım eklemek (a → a|b) daraltma sayılmaz."""
    def kept(term, pool):
        return any(_alts(term) <= _alts(x) for x in pool)
    out = []
    for k in old.get("zorunlu", []):
        if not kept(k, req):
            out.append(f"zorunludan {'tercihe indirildi' if kept(k, pref) else 'çıkarıldı'}: {k}")
    for k in old.get("tercih", []):
        if not kept(k, req + pref):
            out.append(f"tercihten çıkarıldı: {k}")
    if old.get("zorunlu") and req and not _alts(old["zorunlu"][0]) <= _alts(req[0]):
        out.append(f"birincil şart değişti: {old['zorunlu'][0]} → {req[0]}")
    return out


def load_terms(d: Path) -> dict | None:
    p = d / TERMS
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def save_terms(d: Path, req: list[str], pref: list[str], old: dict | None, changes: list[str], why: str | None):
    data = {"zorunlu": req, "tercih": pref, "güncelleme": date.today().isoformat(),
            "ilk_kayıt": (old or {}).get("ilk_kayıt") or date.today().isoformat(),
            "değişiklikler": list((old or {}).get("değişiklikler") or [])}
    for c in changes:
        data["değişiklikler"].append({"tarih": date.today().isoformat(), "değişiklik": c, "gerekçe": why})
    (d / TERMS).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def record(d: Path, r: dict) -> None:
    records.update(d, {
        "ats_eşleşme": f"{r['yüzde']}% (zorunlu {r['zorunlu']}, tercih {r['tercih']})",
        "ats_eksik_zorunlu": "; ".join(r["eksik_zorunlu"]),
        "ats_eksik_tercih": "; ".join(r["eksik_tercih"]),
        "ats_ilk_zorunlu": "eksik" if r["birincil_eksik"] else "var",
    })


# ------------------------------------------------------------------ kapı
def gate_reasons(r: dict | None, *, terms_saved: bool = True) -> list[str]:
    """Ölçüm sonucundan gönderimi durduran sebepler; boş liste = geçer."""
    if not terms_saved:
        return [f"terim listesi kayıtlı değil ({TERMS} yok) — `ats.py <klasör> --required … --record` ile ölç"]
    if not r or r["yüzde"] is None:
        return ["ATS ölçülemedi (cv.md ya da terim yok)"]
    out = []
    if r["yüzde"] < MIN_ATS:
        got, total = r["ağırlık"]
        need = -(-MIN_ATS * total // 100) - got  # tavan
        out.append(f"ATS puanı %{r['yüzde']} < %{MIN_ATS} — en az {need} ağırlık puanı daha gerekli "
                   "(zorunlu kelime = 2, tercih = 1)")
    if r["birincil_eksik"]:
        out.append("ilanın birincil şartı CV'de geçmiyor")
    return out


def pdf_reasons(d: Path, fm: dict) -> list[str]:
    """Forma yüklenecek PDF cv.md'nin son hâlinden mi üretildi."""
    cv = d / "cv.md"
    pdf_name = str(fm.get("cv_pdf") or "").strip()
    if not pdf_name:
        return ["CV PDF'i yok — `render_pdf.py <klasör>` çalıştır"]
    pdf = d / pdf_name
    if not pdf.exists():
        return [f"{pdf_name} klasörde yok — `render_pdf.py <klasör>`"]
    if cv.exists() and cv.stat().st_mtime > pdf.stat().st_mtime:
        return [f"{pdf_name} cv.md'den eski: ölçülen CV ile yüklenecek CV farklı — `render_pdf.py <klasör>`"]
    return []


def check(d: Path) -> tuple[list[str], dict | None]:
    """Kayıtlı terim listesini cv.md üzerinde yeniden ölçer, kaydı günceller → (durdurma sebepleri, ölçüm)."""
    saved = load_terms(d)
    if saved is None:
        return gate_reasons(None, terms_saved=False), None
    cv = d / "cv.md"
    if not cv.exists():
        return ["cv.md yok"], None
    r = measure(cv.read_text(encoding="utf-8"), saved.get("zorunlu", []), saved.get("tercih", []))
    if r["yüzde"] is not None:
        record(d, r)
    return gate_reasons(r) + pdf_reasons(d, records.read(d)), r


def suggestions(r: dict) -> list[str]:
    """Eksik kelimeler, ağırlık sırasıyla (önce zorunlu)."""
    return [f"[zorunlu, +2] {k}" for k in r["eksik_zorunlu"]] + [f"[tercih, +1] {k}" for k in r["eksik_tercih"]]


KNOCKOUT = re.compile(
    r"relocat|umzug|tasin|taşın|work (?:permit|authori[sz]ation)|authori[sz]ed|right to work|visa|sponsor|"
    r"arbeitserlaubnis|aufenthalt|located|based in|reside|wohnort|country|land\b|ülke|salary|gehalt|compensation|"
    r"pay expectation|rate|ücret|maaş|notice|kündigungsfrist|start|eintritt|available|verfügbar|language|sprach|"
    r"german|deutsch|english|englisch|years of experience|berufserfahrung|degree|abschluss|willing|bereit",
    re.I)
NEGATIVE = re.compile(r"^\s*(?:no|nein|hayır|hayir|non)\b", re.I)
POSITIVE = re.compile(r"^\s*(?:yes|ja|evet|oui)\b", re.I)
# Bu sorularda "evet" eleyicidir ("Requires sponsorship? → Yes"), "hayır" değil.
INVERTED = re.compile(r"sponsor|(?:require|need)\w*\s+(?:a\s+)?(?:visa|work permit)|visum\s+benötig|vize\s+gerek", re.I)
UNANSWERED = re.compile(r"sorulacak|boş|bos bırak|^\s*$|\?\?|TODO", re.I)


def knockout_rows(d: Path) -> list[str]:
    """form-cevaplar.md tablosundaki eleyici olabilecek sorular ve cevapları, işaretli."""
    p = d / "form-cevaplar.md"
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or set(cells[0]) <= set("-: ") or cells[0].lower() in ("alan", "soru"):
            continue
        q, a = cells[0], cells[1]
        if not KNOCKOUT.search(q):
            continue
        flag = ""
        if UNANSWERED.search(a):
            flag = "  ⚠ cevapsız"
        elif (POSITIVE if INVERTED.search(q) else NEGATIVE).search(a):
            flag = "  ⚠ bu cevap eleyebilir — kişinin durumuna gerçekten uyuyor mu? (knowledge/forms.md)"
        out.append(f"{q} → {a[:90]}{flag}")
    return out


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser(description="CV ↔ ilan anahtar kelime eşleşmesi")
    ap.add_argument("app", help="başvuru klasörü ya da adının benzersiz parçası")
    ap.add_argument("--required", help="noktalı virgülle; eş anlamlı için a|b; ilk terim birincil şart")
    ap.add_argument("--preferred", default="")
    ap.add_argument("--record", action="store_true", help="listeyi ats-terimler.json'a, sonucu application.md'ye yaz")
    ap.add_argument("--cikar-gerekce", dest="why", help="kayıtlı listeden terim çıkarma / indirme gerekçesi")
    ap.add_argument("--gate", action="store_true", help="gönderim kapısı: kayıtlı listeyle yeniden ölç")
    a = ap.parse_args()
    d = records.app_dir(a.app)

    if a.gate:
        reasons, r = check(d)
        ko = knockout_rows(d)
        if reasons:
            print(f"DUR — {d.name}:")
            for x in reasons:
                print(f"  - {x}")
            if r and suggestions(r):
                print("Öneriler (kanıtı olanı CV'ye ekle, yeniden ölç; kanıtı olmayan eklenmez):")
                for s in suggestions(r):
                    print(f"  - {s}")
        else:
            print(f"geçti — {d.name}: %{r['yüzde']} (zorunlu {r['zorunlu']}, tercih {r['tercih']})")
        if ko:
            print("Eleyici sorular — gönderimden önce kişiyle gözden geçir:")
            for x in ko:
                print(f"  - {x}")
        return 1 if reasons else 0

    saved = load_terms(d)
    if a.required:
        req, pref = split(a.required), split(a.preferred)
    elif a.record and saved:
        req, pref = saved.get("zorunlu", []), saved.get("tercih", [])
    else:
        ap.error("--required gerekli (ya da kayıtlı listeyle --record, ya da --gate)")
    cv = d / "cv.md"
    if not cv.exists() and not a.record:
        sys.exit(f"{d.name}/cv.md yok.")

    ilan = d / "ilan.md"
    loose: list[str] = []
    if a.record:
        if not ilan.exists():
            sys.exit(f"{d.name}/ilan.md yok — terimler ilana karşı doğrulanamaz, kayıt yapılmadı.")
        absent, loose = check_against_ilan(ilan.read_text(encoding="utf-8"), req + pref)
        if absent:
            sys.exit("İlanda hiçbir yazımı geçmeyen terim listeye giremez (ilandaki yazımı kullan):\n  - "
                     + "\n  - ".join(absent))
        changes = narrowing(saved or {}, req, pref)
        if changes and not a.why:
            sys.exit("Kayıtlı terim listesi daraltılıyor; liste CV'ye uysun diye budanamaz.\n  - "
                     + "\n  - ".join(changes)
                     + "\nGerçekten ilandan yanlış çıkarıldıysa: --cikar-gerekce \"…\" (gerekçe ats-terimler.json'da kalır).")
        if not cv.exists():
            # tailor'ın doğru sırası: liste CV'den önce kilitlenir
            save_terms(d, req, pref, saved, changes, a.why)
            print(f"terim listesi kaydedildi → {d.name}/{TERMS} (zorunlu {len(req)}, tercih {len(pref)}); "
                  "cv.md henüz yok, ölçüm CV yazılınca: ats.py <klasör> --record")
            if loose:
                print("İlanda geçmeyen eş anlamlılar:\n  - " + "\n  - ".join(loose))
            return 0

    r = measure(cv.read_text(encoding="utf-8"), req, pref)
    print(json.dumps({k: v for k, v in r.items() if k != "ağırlık"}, ensure_ascii=False, indent=2))
    if loose:
        print("İlanda geçmeyen eş anlamlılar (eşleşme bunlardan geliyorsa gerçekten aynı şart mı?):\n  - "
              + "\n  - ".join(loose), file=sys.stderr)
    if a.record and r["yüzde"] is not None:
        save_terms(d, req, pref, saved, narrowing(saved or {}, req, pref), a.why)
        record(d, r)
        print(f"kaydedildi → {d.name}/{TERMS}, application.md", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
