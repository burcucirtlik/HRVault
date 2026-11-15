"""Export ve sızıntı taraması testleri. Uydurma bir kişiyle, geçici bir vault üzerinde çalışır.

Çalıştır (vault kökünden):  python3 -m unittest discover engine/tests
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))

from pipeline import export  # noqa: E402

# Uydurma kişinin verisi parçalardan kurulur: bu dosyanın kendisi sızıntı taramasının genel kurallarına takılmasın.
MAIL = "cagri.yildizoglu" + "@" + "posta.test"
PHONE = "+" + "90 532 111 22 33"
PROFILE = "linkedin.com/" + "in/cagri-yildizoglu-9a1"
CUR = "EU" + "R"

ANSWERS = f"""# Form Cevap Bankası
## Kimlik ve iletişim
- full_name: Çağrı Yıldızoğlu
- email: {MAIL}
- phone: {PHONE}
- location: Lizbon, Portugal
- linkedin_url: https://www.{PROFILE}
- portfolio_url:
## Ücret
- salary_expectation_annual: 84500 {CUR}
- hourly_rate: 47
"""
CV = f"""# Ana CV
## Kişisel bilgiler
- Ad Soyad: Çağrı Yıldızoğlu
- E-posta: {MAIL}
## Özet
Zorlu tedarik zinciri verilerini sadeleştirip karar vericilere anlaşılır panolar olarak sunan analist.
## Deneyim
### Depo Planlamacısı — Zeplin Lojistik (2020-01 – 2023-05) · Lizbon, Portugal
- Raporlamayı otomatikleştirdim.
"""
EVIDENCE = """## Hard skills
### SQL
- kanıtlar:
  - **[Depo Planlamacısı — Zeplin Lojistik, 2022]** Depo raporunu altı saatten bir saate indirdim.
"""
PREFS = """---
kara_liste:
  şirketler: [Kuzgun Holding]
worker_varsayılanları:
  ilan_dilleri: [en]
---
"""
WORKER = """---
ad: supply-analyst
durum: aktif
roller: [supply chain analyst, analyst]
---
"""
ENTRY = """# test — öğrenimler

## Öğrenimler
- **[2026-03-14] Telefon alanı zorunlu** `k:forms-telefon-zorunlu`
  Formda telefon yıldızlı geliyor; boşsa başlamadan sor.
  _dayanak: 1 form · güven: yüksek_
"""


def make_vault(root: Path, *, me: bool = True) -> Path:
    v = root / "vault"
    for d in ("templates", "export", "adapters"):
        shutil.copytree(ENGINE / d, v / "engine" / d, ignore=shutil.ignore_patterns(".DS_Store", "allow.json"))
    (v / "engine" / "VERSION").write_text("9.9.9\n", encoding="utf-8")
    (v / "knowledge").mkdir()
    (v / "knowledge" / "forms.md").write_text(ENTRY, encoding="utf-8")
    (v / "README.md").write_text("# Test vault\n", encoding="utf-8")
    if me:
        prof = v / "me" / "profile"
        prof.mkdir(parents=True)
        (prof / "answers.md").write_text(ANSWERS, encoding="utf-8")
        (prof / "cv-master.md").write_text(CV, encoding="utf-8")
        (prof / "evidence-bank.md").write_text(EVIDENCE, encoding="utf-8")
        (prof / "preferences.md").write_text(PREFS, encoding="utf-8")
        (v / "me" / "workers").mkdir()
        (v / "me" / "workers" / "supply-analyst.md").write_text(WORKER, encoding="utf-8")
        (v / "me" / "sources.json").write_text(json.dumps({"watchlist": [{"ats": "lever", "company": "Tramola Labs",
                                                                         "token": "tramolalabs"}]}), encoding="utf-8")
        app = v / "me" / "pipeline" / "applications" / "2026-03-01-x"
        app.mkdir(parents=True)
        (app / "application.md").write_text("---\nşirket: Pusula Robotik\n---\n", encoding="utf-8")
    return v


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hrvault-test-"))
        self.v = make_vault(self.tmp)
        self._vault = export.VAULT
        export.VAULT = self.v

    def tearDown(self):
        export.VAULT = self._vault
        shutil.rmtree(self.tmp, ignore_errors=True)

    def plant(self, text: str, rel: str = "knowledge/forms.md"):
        p = self.v / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text((p.read_text(encoding="utf-8") if p.exists() else "") + "\n" + text + "\n", encoding="utf-8")

    def kinds(self, level=None):
        return {(f.level, f.kind) for f in export.lint(self.v)["bulgular"] if level in (None, f.level)}

    def run_build(self, **kw):
        a = argparse.Namespace(dest=None, reviewed=False, zip=False, knowledge_only=False, update=None)
        vars(a).update(kw)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = export.cmd_build(a)
        return code, out.getvalue()


class Lint(Base):
    def test_clean_vault(self):
        self.assertEqual(export.blocking(export.lint(self.v)["bulgular"]), [])

    def test_direct_identifiers_block(self):
        for text, kind in [
            ("Bu formu Çağrı doldurdu.", "isim"),
            ("iletişim: " + MAIL, "e-posta"),
            ("ara: 0532 111 22 33", "telefon"),
            ("Pusula Robotik formu maaşı rakam istiyor.", "başvurulan şirket"),
            ("Tramola Labs panosu yavaş.", "takip edilen şirket"),
            ("Kuzgun Holding ilanları elenir.", "kara liste"),
            ("Zeplin Lojistik'te öğrenildi.", "CV başlığı"),
            ("profil: " + PROFILE, "profil adresi"),
            ("beklenti 84.500 yıllık", "kişinin ücret rakamı"),
            ("saatlik 47 " + CUR, "kişinin ücret rakamı"),
        ]:
            with self.subTest(kind=kind):
                v = make_vault(Path(tempfile.mkdtemp(dir=self.tmp)))
                (v / "knowledge" / "forms.md").write_text(ENTRY + "\n" + text + "\n", encoding="utf-8")
                found = {(f.level, f.kind) for f in export.lint(v)["bulgular"]}
                self.assertIn((export.ENGEL, kind), found)

    def test_turkish_folding_and_slug(self):
        self.plant("yazar: cagri yildizoglu / CAGRI_YILDIZOGLU / cagri-yildizoglu")
        self.assertIn((export.ENGEL, "isim"), self.kinds())

    def test_indirect_identifiers_need_review(self):
        self.plant("Kartlarda Portekiz (Remote) yazıyor; supply chain analyst ilanları az.")
        got = self.kinds(export.GOZDEN)
        self.assertIn((export.GOZDEN, "konum"), got)
        self.assertIn((export.GOZDEN, "aranan rol"), got)

    def test_single_word_role_is_not_a_pattern(self):
        self.plant("Her analyst ilanı aynı değildir.")
        self.assertNotIn((export.GOZDEN, "aranan rol"), self.kinds())

    def test_profile_sentence(self):
        self.plant("Zorlu tedarik zinciri verilerini sadeleştirip karar vericilere anlaşılır panolar sunmak işe yarar.")
        self.assertIn((export.GOZDEN, "profilden cümle"), self.kinds())

    def test_generic_rules(self):
        self.plant("yol: /" + "Users/birisi/Desktop ve baska" + "@" + "alan.org")
        got = self.kinds(export.ENGEL)
        self.assertIn((export.ENGEL, "kullanıcı yolu"), got)
        self.assertIn((export.ENGEL, "e-posta"), got)

    def test_unknown_file_is_a_finding(self):
        (self.v / "notlar.txt").write_text("zararsız", encoding="utf-8")
        (self.v / "engine" / "veri.csv").write_text("a,b", encoding="utf-8")
        files = {f.file for f in export.lint(self.v)["bulgular"] if "tanınmayan" in f.kind}
        self.assertEqual(files, {"notlar.txt", "engine/veri.csv"})

    def test_file_names_are_scanned(self):
        self.plant("zararsız içerik", "knowledge/sites/pusula-robotik.md")
        self.assertIn((export.ENGEL, "başvurulan şirket (dosya adında)"), self.kinds())

    def test_filled_template_blocks(self):
        p = self.v / "engine" / "templates" / "me" / "profile" / "answers.md"
        p.write_text(p.read_text(encoding="utf-8").replace("- full_name:", "- full_name: Biri"), encoding="utf-8")
        self.assertIn((export.ENGEL, "şablonda dolu alan"), self.kinds())

    def test_fail_closed_without_me(self):
        v = make_vault(Path(tempfile.mkdtemp(dir=self.tmp)), me=False)
        with self.assertRaises(export.ScanError):
            export.lint(v)

    def test_fail_closed_with_empty_profile(self):
        (self.v / "me" / "profile" / "answers.md").write_text("- full_name:\n- email:\n", encoding="utf-8")
        (self.v / "me" / "profile" / "cv-master.md").write_text("", encoding="utf-8")
        with self.assertRaises(export.ScanError):
            export.lint(self.v)

    def test_generic_only_mode_works_without_profile(self):
        v = make_vault(Path(tempfile.mkdtemp(dir=self.tmp)), me=False)
        self.assertEqual(export.blocking(export.lint(v, generic_only=True)["bulgular"]), [])

    def test_allow_is_bound_to_line_content_and_never_covers_engel(self):
        self.plant("Kartlarda Portekiz (Remote) yazıyor.")
        f = next(x for x in export.lint(self.v)["bulgular"] if x.kind == "konum")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(export.cmd_allow(argparse.Namespace(dosya=f.file, satır=f.line, gerekce="test")), 0)
        self.assertEqual(export.blocking(export.lint(self.v)["bulgular"]), [])
        p = self.v / "knowledge" / "forms.md"
        p.write_text(p.read_text(encoding="utf-8").replace("Kartlarda Portekiz", "Kartlarda hep Portekiz"), encoding="utf-8")
        self.assertTrue(export.blocking(export.lint(self.v)["bulgular"]))   # satır değişti, izin düştü
        self.plant("Pusula Robotik")
        f = next(x for x in export.lint(self.v)["bulgular"] if x.level == export.ENGEL)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(export.cmd_allow(argparse.Namespace(dosya=f.file, satır=f.line, gerekce="test")), 1)


class Build(Base):
    def test_dry_run_creates_nothing(self):
        code, out = self.run_build()
        self.assertEqual(code, 0)
        self.assertIn("OLUŞMADI", out)
        self.assertEqual([p.name for p in self.tmp.iterdir()], ["vault"])

    def test_findings_stop_the_build(self):
        self.plant("Pusula Robotik")
        code, _ = self.run_build(reviewed=True)
        self.assertEqual(code, 1)
        self.assertEqual([p.name for p in self.tmp.iterdir()], ["vault"])

    def test_package_contents(self):
        (self.v / ".DS_Store").write_bytes(b"x")
        (self.v / "engine" / "__pycache__").mkdir()
        (self.v / "engine" / "__pycache__" / "a.pyc").write_bytes(b"x")
        (self.v / ".claude").mkdir()
        (self.v / ".claude" / "settings.local.json").write_text("{}", encoding="utf-8")
        (self.v / ".git").mkdir()
        (self.v / ".git" / "HEAD").write_text("ref", encoding="utf-8")
        dest = self.tmp / "paket"
        code, out = self.run_build(reviewed=True, dest=str(dest), zip=True)
        self.assertEqual(code, 0, out)
        names = {p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file()}
        for bad in (".DS_Store", "engine/__pycache__/a.pyc", ".claude/settings.local.json", ".git/HEAD",
                    "engine/export/allow.json", "me/profile/cv-master.md.bak"):
            self.assertNotIn(bad, names)
        self.assertFalse(any(n.startswith("me/pipeline/applications/2026") for n in names))
        # me/ = boş şablon
        tpl = self.v / "engine" / "templates" / "me"
        for p in tpl.rglob("*"):
            if p.is_file():
                self.assertEqual((dest / "me" / p.relative_to(tpl)).read_bytes(), p.read_bytes())
        self.assertNotIn("Çağrı", (dest / "me" / "profile" / "answers.md").read_text(encoding="utf-8"))
        # tek sabit tarih
        self.assertEqual(len({int(p.stat().st_mtime) for p in dest.rglob("*") if p.is_file()}), 1)
        # bilgi: tarih silinir, sayım yuvarlanır, tek kişilik gözlemin güveni düşer, baseline yazılır
        k = (dest / "knowledge" / "forms.md").read_text(encoding="utf-8")
        self.assertNotIn("2026", k)
        self.assertIn("- **Telefon alanı zorunlu** `k:forms-telefon-zorunlu`", k)
        self.assertIn("_dayanak: tek form · güven: orta_", k)
        for a in (dest / "engine" / "adapters").glob("*.md"):
            self.assertIsNone(export.DATE.search(a.read_text(encoding="utf-8")), a.name)
        self.assertEqual(len({int(p.stat().st_mtime) for p in dest.rglob("*") if p.is_file()} - {int(export._fixed_time())}), 0)
        base = json.loads((dest / "knowledge" / ".baseline.json").read_text(encoding="utf-8"))
        self.assertIn("forms-telefon-zorunlu", base)
        # EXPORT.json kişi ya da yol taşımaz
        info = (dest / "EXPORT.json").read_text(encoding="utf-8")
        self.assertNotIn(str(self.tmp), info)
        self.assertNotIn("/Users/", info)
        self.assertEqual(json.loads(info)["hrvault_sürümü"], "9.9.9")
        self.assertEqual(export.verify(dest), [])
        self.assertTrue((self.tmp / "paket.zip").exists())

    def test_existing_destination_is_not_overwritten(self):
        dest = self.tmp / "paket"
        dest.mkdir()
        code, _ = self.run_build(reviewed=True, dest=str(dest))
        self.assertEqual(code, 2)
        self.assertEqual(list(dest.iterdir()), [])

    def test_destination_inside_vault_refused(self):
        code, _ = self.run_build(reviewed=True, dest=str(self.v / "paket"))
        self.assertEqual(code, 2)

    def test_update_keeps_git_and_replaces_rest(self):
        dest = self.tmp / "paket"
        self.run_build(reviewed=True, dest=str(dest))
        (dest / ".git").mkdir()
        (dest / ".git" / "HEAD").write_text("ref", encoding="utf-8")
        (dest / "eski.md").write_text("artık yok", encoding="utf-8")
        (self.v / "README.md").write_text("# Yeni sürüm\n", encoding="utf-8")
        code, out = self.run_build(reviewed=True, update=str(dest))
        self.assertEqual(code, 0, out)
        self.assertTrue((dest / ".git" / "HEAD").exists())
        self.assertFalse((dest / "eski.md").exists())
        self.assertEqual((dest / "README.md").read_text(encoding="utf-8"), "# Yeni sürüm\n")
        self.assertEqual(export.verify(dest), [])
        shutil.rmtree(dest / "me")          # depodan alınan paket: me/ .gitignore'da
        self.assertEqual(export.verify(dest), [])
        # paket olmayan klasöre --update yazmaz
        other = self.tmp / "baska"
        other.mkdir()
        self.assertEqual(self.run_build(reviewed=True, update=str(other))[0], 2)

    def test_verify_detects_tampering(self):
        dest = self.tmp / "paket"
        self.run_build(reviewed=True, dest=str(dest))
        (dest / "README.md").write_text("değişti", encoding="utf-8")
        (dest / "ek.md").write_text("yeni", encoding="utf-8")
        (dest / "me" / "profile" / "answers.md").write_text("- full_name: Biri\n", encoding="utf-8")
        issues = "\n".join(export.verify(dest))
        self.assertIn("değişmiş: README.md", issues)
        self.assertIn("listede olmayan dosya: ek.md", issues)
        self.assertIn("me/ boş şablonla aynı değil", issues)
        self.assertEqual(export.verify(self.tmp), ["EXPORT.json yok — bu klasör onaylanmış bir paket değil"])


class Neutralize(unittest.TestCase):
    def test_round_counts(self):
        self.assertEqual(export.round_counts("1 oturum, 8 arama"), "tek oturum, birkaç arama")
        self.assertEqual(export.round_counts("1 tarama, ~35 ilan"), "tek tarama, çok sayıda ilan")
        self.assertEqual(export.round_counts("ilk tarama (5 ilan)"), "ilk tarama (birkaç ilan)")
        self.assertEqual(export.round_counts("genel bilgi · +1 kullanıcı (2 form)"), "genel bilgi · +1 kullanıcı (birkaç form)")

    def test_strip_dates(self):
        t = ("<!-- durum: deneme (2026-11-14) -->\n- **[2026-11-12] Başlık** `k:x`\n"
             "- `GET https://api.example.com/x` (doğrulandı 2026-11-12)\n- yollar (2026-11-14 kontrolü):\n")
        out = export.strip_dates(t)
        self.assertIsNone(export.DATE.search(out))
        self.assertIn("- **Başlık** `k:x`", out)
        self.assertIn("<!-- durum: deneme -->", out)
        self.assertEqual(export.parse_entries(out)[0]["id"], "x")


class Regional(Base):
    def add_regional(self):
        (self.v / "engine" / "adapters" / "yerelpano.md").write_text(
            "# Yerel Pano\n\n- **tür:** akış\n- **kapsam:** XX\n", encoding="utf-8")
        src = self.v / "engine" / "scanner" / "sources"
        src.mkdir(parents=True, exist_ok=True)
        (src / "yerelpano.py").write_text('KAPSAM = "XX"\n', encoding="utf-8")
        (self.v / "knowledge" / "sites").mkdir(exist_ok=True)
        (self.v / "knowledge" / "sites" / "yerelpano.md").write_text("# yerelpano\n", encoding="utf-8")
        (self.v / "knowledge" / "sites" / "yerelsite.md").write_text(
            "# yerelsite\n> **kapsam:** XX — bölgesel\n", encoding="utf-8")

    def test_regional_adapters_stay_out(self):
        self.add_regional()
        r = export.lint(self.v)
        self.assertTrue({"yerelpano", "yerelsite"} <= set(r["bölgesel"]))
        for f in ("engine/adapters/yerelpano.md", "engine/scanner/sources/yerelpano.py",
                  "knowledge/sites/yerelpano.md", "knowledge/sites/yerelsite.md"):
            self.assertNotIn(f, r["dosyalar"])
        dest = self.tmp / "paket"
        code, out = self.run_build(reviewed=True, dest=str(dest))
        self.assertEqual(code, 0, out)
        self.assertFalse((dest / "engine" / "adapters" / "yerelpano.md").exists())
        self.assertEqual(export.verify(dest), [])

    def test_reference_to_excluded_adapter_blocks(self):
        self.add_regional()
        self.plant("Bu ilanlar yerelpano üzerinden de gelir.", "README.md")
        self.assertIn((export.ENGEL, "dışlanan bölgesel adaptöre atıf"), self.kinds())

    def test_flag_true_keeps_them(self):
        self.add_regional()
        mp = self.v / "engine" / "export" / "manifest.json"
        m = json.loads(mp.read_text(encoding="utf-8"))
        m["bölgesel_adaptörler"] = True
        m["kopyala"].append("engine/scanner/sources/*.py")
        mp.write_text(json.dumps(m), encoding="utf-8")
        self.assertIn("engine/adapters/yerelpano.md", export.lint(self.v)["dosyalar"])


class Knowledge(Base):
    def test_ids_are_assigned_once_and_stable(self):
        self.plant("- **[2026-04-02] Yeni kural**\n  Açıklama.\n  _dayanak: 1 ilan · güven: düşük_")
        self.assertEqual(export.assign_ids(self.v), 1)
        self.assertEqual(export.assign_ids(self.v), 0)
        ids = [e["id"] for e in export.parse_entries((self.v / "knowledge" / "forms.md").read_text(encoding="utf-8"))]
        self.assertEqual(ids, ["forms-telefon-zorunlu", "forms-yeni-kural"])

    def test_knowledge_only_package_and_merge(self):
        # alıcı: baseline'ı olan vault; bir maddeyi doğruladı, bir madde ekledi
        (self.v / "knowledge" / ".baseline.json").write_text(
            json.dumps(export.baseline_of(self.v), ensure_ascii=False), encoding="utf-8")
        p = self.v / "knowledge" / "forms.md"
        p.write_text(p.read_text(encoding="utf-8").replace("_dayanak: 1 form", "_dayanak: devralındı (1 form) + 2 form"),
                     encoding="utf-8")
        self.plant("- **[2026-04-02] Yeni kural** `k:forms-yeni-kural`\n  Açıklama.\n  _dayanak: 1 ilan · güven: düşük_")
        dest = self.tmp / "bilgi"
        code, out = self.run_build(reviewed=True, knowledge_only=True, dest=str(dest))
        self.assertEqual(code, 0, out)
        self.assertEqual({q.relative_to(dest).as_posix() for q in dest.rglob("*") if q.is_file()},
                         {"EXPORT.json", "knowledge/forms.md"})
        self.assertIn("tek form + birkaç form", (dest / "knowledge" / "forms.md").read_text(encoding="utf-8"))

        # kaynak vault: aynı maddenin özgün hali var
        src = make_vault(Path(tempfile.mkdtemp(dir=self.tmp)))
        res = export.merge(src, dest)
        self.assertEqual(res["eklendi"], ["forms-yeni-kural"])
        self.assertEqual(res["güçlendi"], ["forms-telefon-zorunlu"])
        text = (src / "knowledge" / "forms.md").read_text(encoding="utf-8")
        self.assertIn("+1 kullanıcı (tek form + birkaç form)", text)
        self.assertIn("k:forms-yeni-kural", text)
        self.assertEqual(export.merge(src, dest)["eklendi"], [])     # ikinci kez: değişiklik yok

    def test_merge_keeps_both_on_conflict(self):
        dest = self.tmp / "bilgi"
        (dest / "knowledge").mkdir(parents=True)
        (dest / "knowledge" / "forms.md").write_text(ENTRY.replace("yıldızlı geliyor", "hiç zorunlu değil"), encoding="utf-8")
        res = export.merge(self.v, dest)
        self.assertEqual(res["çelişki"], ["forms-telefon-zorunlu"])
        text = (self.v / "knowledge" / "forms.md").read_text(encoding="utf-8")
        self.assertIn("yıldızlı geliyor", text)
        self.assertIn("k:forms-telefon-zorunlu-gelen", text)

    def test_nothing_new_is_not_a_package(self):
        (self.v / "knowledge" / ".baseline.json").write_text(
            json.dumps(export.baseline_of(self.v), ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(export.ScanError):
            self.run_build(reviewed=True, knowledge_only=True, dest=str(self.tmp / "bilgi"))


if __name__ == "__main__":
    unittest.main()
