"""Motorun eleme ve ayrıştırma kuralları için testler. Kişisel veri kullanmaz.

Çalıştır (vault kökünden):  python3 -m unittest discover engine/tests
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qsl, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import date  # noqa: E402

from pipeline import ats, inbox, learn  # noqa: E402
from scanner import config  # noqa: E402
from scanner.common import (Job, company_blocked, expand_places, fold, fresh_age, is_region,  # noqa: E402
                            posting_language)
from scanner.scan import (ats_location_ok, dedupe_key, excluded, language_ok, location_ok,  # noqa: E402
                          partial_remote_ok, region_ok, role_matches, workplace_ok)
from scanner.sources import himalayas  # noqa: E402

ALLOWED = ["Portugal", "EU", "Europe", "EMEA", "Worldwide", "Anywhere"]


def job(**kw) -> Job:
    base = dict(source="greenhouse", native_id="1", company="Acme", title="Data Annotator", url="u")
    return Job(**(base | kw))


class TitleMatching(unittest.TestCase):
    def test_role_prefix_match(self):
        self.assertTrue(role_matches("Data Analysts (Remote)", "data analyst"))
        self.assertTrue(role_matches("Senior QA Automation Lead", "QA automation"))

    def test_short_words_need_whole_word(self):
        self.assertFalse(role_matches("Aircraft Mechanic", "AI"))
        self.assertTrue(role_matches("AIs and You", "AI"))

    def test_exclusion_is_whole_word(self):
        # "intern" önek olarak eşleşseydi "Internal" ilanı elenirdi (yaşanmış hata)
        self.assertFalse(excluded("Internal Tools Lead", "intern"))
        self.assertFalse(excluded("International Sales Manager", "intern"))
        self.assertTrue(excluded("Marketing Intern", "intern"))
        self.assertTrue(excluded("Summer Interns 2027", "intern"))

    def test_dedupe_key_ignores_suffixes(self):
        self.assertEqual(dedupe_key("Acme Inc", "Data Annotator (Remote)"), dedupe_key("Acme", "Data Annotator"))

    def test_local_letters_fold(self):
        # NFKD "ı"yı ASCII'ye indiremez; eskiden silinip "yazlm" oluyordu
        self.assertEqual(fold("Yazılım Eğitmeni"), "yazilim egitmeni")
        self.assertTrue(role_matches("Kıdemli Yazılım Eğitmeni", "yazilim egitmeni"))
        self.assertEqual(fold("İçerik Straße"), "icerik strasse")
        self.assertTrue(ats.found(" " + ats.fold("Veri analizi, Kılavuz yazımı") + " ", "kilavuz"))


class Location(unittest.TestCase):
    def test_title_region(self):
        self.assertFalse(region_ok("Community Moderator - India", ALLOWED))
        self.assertFalse(region_ok("Lead Designer - U.S. (30 hours/week)", ALLOWED))
        self.assertTrue(region_ok("Engineer (US Canada, Europe, MENA, India & APAC Timezones)", ALLOWED))
        self.assertTrue(region_ok("Data Annotator - Worldwide (US hours)", ALLOWED))
        self.assertTrue(region_ok("Business Analyst", ALLOWED))  # "us" kelimesi değil, "business" içinde
        self.assertTrue(region_ok("Anything - India", []))      # izinli liste boşsa eleme yok

    def test_us_pronoun_is_not_a_region(self):
        self.assertTrue(region_ok("Join us: Data Platform Lead", ALLOWED))
        self.assertTrue(region_ok("Build with Us - Backend Engineer", ALLOWED))
        self.assertFalse(region_ok("Backend Engineer - US", ALLOWED))
        self.assertFalse(region_ok("Product Designer (U.S. only)", ALLOWED))

    def test_region_covers_allowed_country(self):
        feed = dict(source="himalayas")
        only_country = ["Austria"]
        self.assertTrue(location_ok(job(location="DACH", **feed), only_country))
        self.assertTrue(location_ok(job(location="European Union", **feed), only_country))
        self.assertTrue(location_ok(job(location="EMEA", **feed), only_country))
        self.assertTrue(region_ok("Solutions Lead - UK & EU", only_country))
        self.assertFalse(location_ok(job(location="Belgium, France", **feed), only_country))
        # yalnızca yukarı doğru: izinli "EU" bölge adı, EU üyesi bir ülkeye kısıtlı ilanı geçirmez
        self.assertFalse(location_ok(job(location="Belgium", **feed), ["EU"]))

    def test_partial_remote_exception(self):
        rule = {"tipler": ["freelance"], "min_remote_yüzde": 80, "şehirler": ["Lyon"]}
        hybrid_city = job(location="Lyon, France", workplace="hybrid")
        self.assertFalse(workplace_ok("hybrid", ["remote"]))
        self.assertTrue(partial_remote_ok(hybrid_city, rule))
        self.assertFalse(partial_remote_ok(job(location="Paris, France", workplace="hybrid"), rule))   # başka şehir
        self.assertFalse(partial_remote_ok(job(location="Lyon, France", workplace="onsite"), rule))   # tamamen ofis
        self.assertFalse(partial_remote_ok(hybrid_city, None))                                         # istisna yok

    def test_region_names(self):
        self.assertTrue(is_region("EU") and is_region("Worldwide") and is_region("Europe"))
        self.assertFalse(is_region("Austria"))
        self.assertIn("dach", expand_places(["Austria"]))
        self.assertNotIn("austria", expand_places(["EU"]))

    def test_ats_location(self):
        self.assertFalse(ats_location_ok(job(location="Mumbai, India"), ALLOWED))
        self.assertFalse(ats_location_ok(job(location="London, Remote (UK)", workplace="remote"), ALLOWED))
        self.assertTrue(ats_location_ok(job(location="United Kingdom", workplace="remote"), ALLOWED))
        self.assertTrue(ats_location_ok(job(location="Remote - Europe"), ALLOWED))
        self.assertTrue(ats_location_ok(job(location="Lisbon, Portugal"), ALLOWED))
        # ABD şehirleri "United States" yazmasa da elenir; izinli yer ya da yalnızca açık ifade geçer
        self.assertFalse(ats_location_ok(job(location="San Francisco, California"), ALLOWED))
        self.assertFalse(ats_location_ok(job(location="Remote - Washington D.C."), ALLOWED))
        self.assertFalse(ats_location_ok(job(location="San Francisco; Seattle; Remote"), ALLOWED))
        self.assertFalse(ats_location_ok(job(location="Remote, AMER"), ALLOWED))
        self.assertTrue(ats_location_ok(job(location="Remote"), ALLOWED))
        self.assertTrue(ats_location_ok(job(location="Home based - Worldwide"), ALLOWED))
        self.assertTrue(ats_location_ok(job(location="Home based - EMEA"), ALLOWED))
        self.assertTrue(ats_location_ok(job(location="N/A"), ALLOWED))

    def test_feed_location(self):
        feed = dict(source="himalayas")
        self.assertTrue(location_ok(job(location="Worldwide", **feed), ALLOWED))
        self.assertFalse(location_ok(job(location="United States", **feed), ALLOWED))
        self.assertFalse(location_ok(job(location="Sint Eustatius", **feed), ["EU"]))
        self.assertTrue(location_ok(job(location="Anything"), ALLOWED))  # ATS: karar skill'de


class Languages(unittest.TestCase):
    def test_language_specialist_titles(self):
        self.assertFalse(language_ok("Kazakh Language Specialist - Annotation Project", ["en"]))
        self.assertFalse(language_ok("Dutch Audio Specialist - Freelance Annotation Project", ["en"]))
        self.assertTrue(language_ok("Spanish Language Specialist - Annotation Project", ["es", "en"]))
        self.assertTrue(language_ok("English Writing Expert", ["en"]))
        self.assertTrue(language_ok("Data Annotator", ["en"]))
        self.assertTrue(language_ok("German Market Lead", ["en"]))  # dil adı var ama dil/uzman kelimesi yok
        # uzun tire silinseydi "koreanjapanese" tek kelime olur, filtre kaçırırdı
        self.assertFalse(language_ok("Korean–Japanese Bilingual Specialist – Annotation", ["en"]))
        self.assertFalse(language_ok("Maltese Language Specialist - Annotation Project", ["en"]))


class PostingLanguage(unittest.TestCase):
    EN = ("We are looking for a data analyst who will work with our product team. You will build dashboards and "
          "reports for the business, and you have experience with SQL. This is a remote role and we offer flexible "
          "hours. Your work will be used by teams across the company, and you are comfortable presenting it to them. "
          "We are a small team that values clear writing and we will support you from the first day on.")
    DE = ("Wir suchen eine Person für unsere Datenanalyse, die mit dem Produktteam arbeitet. Du erstellst Berichte und "
          "Dashboards für das Unternehmen und bringst Erfahrung mit SQL mit. Die Stelle ist remote und wir bieten "
          "flexible Arbeitszeiten. Deine Arbeit wird von Teams im ganzen Unternehmen genutzt und du bist es gewohnt, "
          "sie zu präsentieren. Wir sind ein kleines Team und unterstützen dich ab dem ersten Tag.")

    def test_detects_language_of_long_text(self):
        self.assertEqual(posting_language(self.EN), "en")
        self.assertEqual(posting_language(self.DE), "de")

    def test_does_not_guess(self):
        self.assertEqual(posting_language("Data Analyst (m/w/d) remote"), "")          # kısa özet
        self.assertEqual(posting_language(self.EN[:260] + " " + self.DE[:260]), "")   # iki dilli ilan

    def test_company_blocklist(self):
        self.assertTrue(company_blocked("Acme Inc.", ["acme"]))
        self.assertTrue(company_blocked("ACME", ["Acme"]))
        self.assertFalse(company_blocked("Acmeworks", ["Acme"]))   # başka şirketin adının parçası
        self.assertFalse(company_blocked("Beta", []))


class Freshness(unittest.TestCase):
    def test_repost_counts_as_fresh(self):
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        old, recent = (now - timedelta(days=40)).isoformat(), (now - timedelta(days=2)).isoformat()
        self.assertLess(fresh_age(job(published=old, updated=recent)), 3)   # eski ilan, yeniden yayımlanmış
        self.assertGreater(fresh_age(job(published=old)), 39)
        self.assertIsNone(fresh_age(job()))                                 # tarih yoksa filtre uygulanmaz


class MiniYaml(unittest.TestCase):
    def test_nested_lists_and_maps(self):
        text = (
            "a: 1\n"
            "b: [x, y]   # yorum\n"
            "kara_liste:\n"
            "  şirketler: [A, B]\n"
            "  anahtar_kelimeler:\n"
            "    # açıklama\n"
            "    - fluent French\n"
            "    - français courant\n"
            "liste:\n"
            "  - p\n"
            "  - q\n"
            "boş:\n"
            "c: metin\n"
        )
        self.assertEqual(config._mini_yaml(text), {
            "a": 1, "b": ["x", "y"],
            "kara_liste": {"şirketler": ["A", "B"], "anahtar_kelimeler": ["fluent French", "français courant"]},
            "liste": ["p", "q"], "boş": None, "c": "metin",
        })

    def test_matches_pyyaml_when_available(self):
        try:
            import yaml  # type: ignore
        except ImportError:
            self.skipTest("PyYAML yok")
        tpl = Path(__file__).resolve().parents[1] / "templates" / "me" / "profile" / "preferences.md"
        body = tpl.read_text(encoding="utf-8").split("---\n")[1]
        self.assertEqual(config._mini_yaml(body), yaml.safe_load(body))


class Ats(unittest.TestCase):
    def test_measure(self):
        r = ats.measure("Built workflows with Claude and Python; ran workshops.",
                        ["Claude", "prompt engineering|workflows", "TypeScript"], ["Python"])
        self.assertEqual(r["zorunlu"], "2/3")
        self.assertEqual(r["eksik_zorunlu"], ["TypeScript"])
        self.assertEqual(r["yüzde"], 71)  # (2*2+1)/(2*3+1)

    def test_gate_reasons(self):
        self.assertEqual(len(ats.gate_reasons(None, terms_saved=False)), 1)
        ok = ats.measure("a b c d e", ["a", "b", "c", "d", "e"], [])
        self.assertEqual(ats.gate_reasons(ok), [])
        # 9 zorunlu var, 1 eksik → 18/20 = %90 geçer; 2 eksik → %80
        low = ats.measure("a b c d e f g h", list("abcdefghij"), [])
        self.assertTrue(any("%80 < %90" in r and "2 ağırlık" in r for r in ats.gate_reasons(low)))
        first = ats.measure("b c d e f g h i j k l m n o p q r s t", list("abcdefghijklmnopqrst"), [])
        self.assertTrue(first["yüzde"] >= 90)
        self.assertTrue(any("birincil" in r for r in ats.gate_reasons(first)))

    def test_suggestions_order(self):
        r = ats.measure("x", ["a", "b"], ["c"])
        self.assertEqual(ats.suggestions(r), ["[zorunlu, +2] a", "[zorunlu, +2] b", "[tercih, +1] c"])

    def test_word_boundary(self):
        self.assertFalse(ats.found(" " + ats.fold("Javascript") + " ", "Java"))
        self.assertTrue(ats.found(" " + ats.fold("C++ and C#") + " ", "C++"))

    def test_plural_forms(self):
        t = " " + ats.fold("Managed stakeholder relations; built REST APIs; IT support") + " "
        self.assertTrue(ats.found(t, "stakeholders"))
        self.assertTrue(ats.found(t, "APIs"))
        self.assertFalse(ats.found(t, "API"))      # 3 harfli terim çoğullanmaz: "API|APIs" yazılmalı
        self.assertTrue(ats.found(" " + ats.fold("reviewed processes") + " ", "process"))
        self.assertFalse(ats.found(" " + ats.fold("its value") + " ", "IT"))   # kısa kelime çoğullanmaz

    def test_terms_must_come_from_ilan(self):
        absent, loose = ats.check_against_ilan("We need SQL and stakeholder management.",
                                               ["SQL", "stakeholder management|stakeholders", "Kubernetes"])
        self.assertEqual(absent, ["Kubernetes"])
        self.assertEqual(loose, [])   # "stakeholders" çoğul biçimiyle ilanda sayılır
        _, loose = ats.check_against_ilan("Natural Language Processing", ["Natural Language Processing|NLP"])
        self.assertEqual(loose, ["Natural Language Processing|NLP → NLP"])

    def test_narrowing(self):
        old = {"zorunlu": ["SQL", "dbt"], "tercih": ["Airflow"]}
        self.assertEqual(ats.narrowing(old, ["SQL", "dbt|data build tool"], ["Airflow", "Spark"]), [])
        ch = ats.narrowing(old, ["SQL"], ["dbt"])
        self.assertTrue(any("tercihe indirildi: dbt" in c for c in ch))
        self.assertTrue(any("tercihten çıkarıldı: Airflow" in c for c in ch))
        self.assertTrue(any("birincil" in c for c in ats.narrowing(old, ["dbt", "SQL"], ["Airflow"])))


class AtsFolder(unittest.TestCase):
    """Başvuru klasörü üzerinde uçtan uca: kayıt, yeniden ölçen kapı, eski PDF, track kapısı."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name) / "2026-01-01-acme-analyst"
        self.d.mkdir()
        (self.d / "application.md").write_text("---\nşirket: Acme\nrol: Analyst\ncv_pdf: CV.pdf\ndurum: hazırlandı\n"
                                               "ats_eşleşme:\n---\n# x\n", encoding="utf-8")
        (self.d / "ilan.md").write_text("Must have SQL, Python and Tableau. Nice: dbt.", encoding="utf-8")
        self.cv("Analyst. SQL, Python, Tableau, dbt.")
        self.pdf()

    def tearDown(self):
        self.tmp.cleanup()

    def cv(self, text):
        (self.d / "cv.md").write_text(text, encoding="utf-8")
        import os
        os.utime(self.d / "cv.md", (1_000_000, 1_000_000))

    def pdf(self, t=2_000_000):
        p = self.d / "CV.pdf"
        p.write_bytes(b"%PDF")
        import os
        os.utime(p, (t, t))

    def test_gate_remeasures_instead_of_trusting_record(self):
        ats.save_terms(self.d, ["SQL", "Python", "Tableau"], ["dbt"], None, [], None)
        reasons, r = ats.check(self.d)
        self.assertEqual(reasons, [])
        self.assertEqual(r["yüzde"], 100)
        # kayıt elle şişirilse de kapı yeniden ölçer
        from pipeline import records
        records.update(self.d, {"ats_eşleşme": "100% (zorunlu 3/3, tercih 1/1)"})
        self.cv("Analyst. SQL.")
        self.pdf(3_000_000)
        reasons, r = ats.check(self.d)
        self.assertTrue(any("< %90" in x for x in reasons))
        self.assertTrue(records.read(self.d)["ats_eşleşme"].startswith("29%"))

    def test_cli_locks_list_before_cv_and_refuses_pruning(self):
        (self.d / "cv.md").unlink()
        run = lambda *x: mock.patch("sys.argv", ["ats.py", str(self.d), *x])  # noqa: E731
        with run("--required", "SQL; Python; Tableau", "--preferred", "dbt", "--record"), mock.patch("sys.stdout"):
            self.assertEqual(ats.main(), 0)
        self.assertEqual(ats.load_terms(self.d)["zorunlu"], ["SQL", "Python", "Tableau"])
        with run("--required", "SQL; Kubernetes", "--record"), self.assertRaises(SystemExit) as e:
            ats.main()
        self.assertIn("Kubernetes", str(e.exception.code))
        self.cv("Analyst. SQL.")
        with run("--required", "SQL", "--record"), self.assertRaises(SystemExit) as e:
            ats.main()
        self.assertIn("budanamaz", str(e.exception.code))
        with run("--record"), mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            self.assertEqual(ats.main(), 0)   # kayıtlı listeyle ölç
        from pipeline import records
        self.assertTrue(records.read(self.d)["ats_eşleşme"].startswith("29%"))

    def test_gate_without_saved_terms(self):
        reasons, _ = ats.check(self.d)
        self.assertTrue(reasons and "terim listesi kayıtlı değil" in reasons[0])

    def test_stale_pdf_blocks(self):
        ats.save_terms(self.d, ["SQL"], [], None, [], None)
        self.pdf(500_000)   # PDF cv.md'den eski
        reasons, _ = ats.check(self.d)
        self.assertTrue(any("cv.md'den eski" in x for x in reasons))

    def test_track_refuses_without_gate(self):
        from pipeline import track
        args = mock.Mock(app=str(self.d), durum="başvuruldu", sebep=None, not_=None, takip_gün=10, harici=None)
        with self.assertRaises(SystemExit):
            track.cmd_set(args)
        from pipeline import records
        self.assertEqual(records.read(self.d)["durum"], "hazırlandı")
        args.harici = "kişi 2026-01-01'de şirket sitesinden kendisi gönderdi"
        with mock.patch("sys.stdout"):
            track.cmd_set(args)
        self.assertEqual(records.read(self.d)["durum"], "başvuruldu")
        self.assertIn("ATS kapısı atlandı", (self.d / "application.md").read_text(encoding="utf-8"))

    def test_knockout_rows(self):
        (self.d / "form-cevaplar.md").write_text(
            "| Alan | Cevap | Kaynak |\n|---|---|---|\n| Willing to relocate to <Ülke>? | No | answers |\n"
            "| Earliest start date | kişiye sorulacak | — |\n| First name | X | answers |\n"
            "| Requires visa sponsorship? | No | answers |\n| Will you require sponsorship? | Yes | answers |\n",
            encoding="utf-8")
        rows = ats.knockout_rows(self.d)
        self.assertEqual(len(rows), 4)
        self.assertIn("eleyebilir", rows[0])
        self.assertIn("cevapsız", rows[1])
        self.assertNotIn("⚠", rows[2])        # sponsorluk gerekmiyor: iyi cevap
        self.assertIn("eleyebilir", rows[3])


class Decisions(unittest.TestCase):
    def test_latest_decision_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "decisions.jsonl"
            log.write_text(
                '{"tarih":"2026-01-01","karar":"onay","no":1,"id":"a"}\n'
                '{"tarih":"2026-01-01","karar":"onay","no":2,"id":"b"}\n'
                'bozuk satır\n'
                '{"tarih":"2026-01-01","karar":"ret","no":1,"id":"a","sebep":"vazgeçti"}\n',
                encoding="utf-8")
            old = inbox.DECISIONS
            inbox.DECISIONS = log
            try:
                last = inbox.latest_decisions()
            finally:
                inbox.DECISIONS = old
        self.assertEqual(last["a"]["karar"], "ret")
        self.assertEqual(last["b"]["karar"], "onay")
        self.assertEqual(len(last), 2)


class LearnReport(unittest.TestCase):
    """learn.py'nin saf fonksiyonları; sentetik ilanlar."""

    def jobs(self):
        noise = [{"id": f"f:{i}", "source": "feed", "title": f"Widget Rater {i}", "workers": ["w1"],
                  "matched": ["widget rater"], "elendi": "alan uzmanlığı şartı (tekstil); x"} for i in range(9)]
        good = [{"id": "f:a", "source": "feed", "title": "Data Analyst", "workers": ["w1"], "matched": ["data analyst"],
                 "sınıf": {}, "skor": {"puan": 75}, "key": "acme|data analyst"},
                {"id": "f:b", "source": "ats", "title": "Data Analyst II", "workers": ["w1"], "matched": ["data analyst"],
                 "elendi": "zaten başvuruldu", "key": "beta|data analyst ii"}]
        return noise + good

    def test_funnel_counts_and_app_overrides_late_drop_tag(self):
        apps = [{"ilan_id": "f:a", "durum": "mülakat", "şirket": "Acme", "rol": "Data Analyst"},
                {"ilan_id": "x:zzz", "durum": "başvuruldu", "şirket": "Beta", "rol": "Data Analyst II",
                 "uygunluk_puanı": "70"}]
        f = learn.funnel(self.jobs(), {"f:a": {"karar": "onay"}}, apps, 60)
        c = f["kelime"]["data analyst"]
        self.assertEqual([c[s] for s in learn.STAGES], [2, 2, 2, 2, 2, 1])  # ikinci başvuru anahtarla eşleşti
        self.assertEqual(f["kelime"]["widget rater"]["kaldı"], 0)

    def test_noisy_and_dead(self):
        js = self.jobs()
        f = learn.funnel(js, {}, [], 60)
        nz = learn.noisy(f["kelime"], js)
        self.assertEqual(nz[0][0], "widget rater")
        self.assertEqual(nz[0][2][0], ("alan uzmanlığı şartı", 9))
        dead = learn.dead_roles([{"ad": "w1", "roller": ["data analyst", "widget rater", "gadget tester"]}], f["kelime"])
        self.assertEqual(dead, {"w1": ["gadget tester"]})

    def test_clusters_point_at_keyword_and_skip_rule_reasons(self):
        cl = learn.drop_clusters(self.jobs())
        self.assertEqual(len(cl), 1)   # "zaten başvuruldu" kural sebebi: küme değil
        self.assertEqual(cl[0]["sayı"], 9)
        self.assertIn("'widget rater' rolünü", cl[0]["öneri"])

    def test_late_drop_copy_does_not_erase_scored_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            sc = Path(tmp) / "scans"
            sc.mkdir()
            (sc / "2026-01-01.json").write_text('{"jobs":[{"id":"f:a","skor":{"puan":80}}]}', encoding="utf-8")
            (sc / "2026-01-02.json").write_text('{"jobs":[{"id":"f:a","elendi":"zaten başvuruldu"}]}', encoding="utf-8")
            js = learn.load_jobs(Path(tmp), 0)
        self.assertEqual(js[0].get("skor"), {"puan": 80})

    def test_pending(self):
        dec = {"a": {"karar": "ret", "sebep": "", "şirket": "Acme", "rol": "R", "tarih": "2026-01-01"},
               "b": {"karar": "ret", "sebep": "çok kıdemli", "şirket": "Beta", "rol": "R"}}
        apps = [("x1", {"durum": "iptal", "iptal_sebebi": "belirtilmedi", "şirket": "Gamma", "rol": "R"}),
                ("x2", {"durum": "ret", "şirket": "Delta", "rol": "R"}),
                ("x3", {"durum": "ret", "şirket": "Epsilon", "rol": "R"}),
                ("x4", {"durum": "başvuruldu", "başvuru_tarihi": "2026-01-01", "şirket": "Zeta", "rol": "R"})]
        out = learn.pending(dec, apps, "Epsilon reddi işlendi", date(2026, 2, 15), 30)
        self.assertEqual(len(out), 4)
        self.assertTrue(any("sebepsiz ret" in x and "Acme" in x for x in out))
        self.assertTrue(any("sebepsiz iptal" in x and "Gamma" in x for x in out))
        self.assertTrue(any("işlenmemiş" in x and "Delta" in x for x in out))
        self.assertTrue(any("sessiz adayı (45 gün" in x and "x4" in x for x in out))


class Dashboard(unittest.TestCase):
    """Sentetik bir vault'tan panel: kaçışlama, en fazla 20 elenen, ATS eksikleri, ret bölümü."""

    def test_render_from_synthetic_vault(self):
        from pipeline import dashboard
        with tempfile.TemporaryDirectory() as tmp:
            v = Path(tmp)
            me = v / "me"
            (me / "pipeline" / "scans").mkdir(parents=True)
            (me / "profile").mkdir()
            (me / "workers").mkdir()
            (me / "profile" / "preferences.md").write_text("---\nmin_uygunluk_puanı: 60\n---\n", encoding="utf-8")
            jobs = [{"id": "f:ok", "source": "feed", "title": "Data <b>Analyst</b>", "company": "Acme", "url": "javascript:alert(1)",
                     "sınıf": {"tip": "full-time", "yer": "remote"}, "skor": {"puan": 80, "gerekçe": "uygun", "eksikler": ["dbt"]}}]
            jobs += [{"id": f"f:{i}", "source": "feed", "title": f"Role {i}", "company": "Beta", "url": "https://x.test/j",
                      "elendi": "ilan dili: de" if i % 2 else "ücret 20 < 45"} for i in range(30)]
            (me / "pipeline" / "scans" / "2026-01-02.json").write_text(json.dumps({"meta": {"kaynaklar": {"feed": {"çekilen": 99}}},
                                                                                  "jobs": jobs}), encoding="utf-8")
            app = me / "pipeline" / "applications" / "2026-01-01-gamma-writer"
            app.mkdir(parents=True)
            (app / "application.md").write_text(
                "---\nşirket: Gamma\nrol: Writer\ndurum: ret\nbaşvuru_tarihi: 2026-01-01\nuygunluk_puanı: 70\n"
                "ats_eşleşme: 80% (zorunlu 4/5, tercih 0/0)\nats_eksik_zorunlu: SEO|search\n---\n"
                "## Durum geçmişi\n- 2026-01-05 · ret — e-posta geldi\n- 2026-01-01 · başvuruldu\n", encoding="utf-8")
            page = dashboard.render(dashboard.collect(v))
        self.assertIn("Data &lt;b&gt;Analyst&lt;/b&gt;", page)        # başlık kaçışlandı
        self.assertNotIn('href="javascript:', page)                   # yalnızca http(s) bağlantı
        dropped = page.split("Elenenler ve eşik altı")[1].split("</details>")[0]
        self.assertEqual(dropped.count("<tr>") - 1, 20)                # en fazla 20 satır (başlık satırı hariç)
        self.assertIn("e-posta geldi", page)                           # ret notu
        self.assertIn(">SEO<", page)                                   # a|b teriminin ilk yazımı
        self.assertIn("için +1 ağırlık", page)                         # %90'a kalan


class DashboardFreshInstall(unittest.TestCase):
    def test_template_vault_shows_setup_stage(self):
        """Klonlayıp `profile.py init` yapan biri: tarama, başvuru, worker yok; panel çökmez, kurulum aşamasını gösterir."""
        import shutil
        from pipeline import dashboard
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            v = Path(tmp)
            shutil.copytree(root / "engine" / "templates" / "me", v / "me")
            (v / "engine").mkdir()
            (v / "engine" / "VERSION").write_text("0.0.0", encoding="utf-8")
            page = dashboard.render(dashboard.collect(v))
        self.assertIn("Kurulum — 1 · Tanışma", page)
        self.assertIn("/coach", page)
        self.assertIn("Henüz tarama yok", page)
        self.assertNotIn("Elenenler ve eşik altı", page)

    def test_missing_me_is_reported_not_created(self):
        from pipeline import dashboard
        with tempfile.TemporaryDirectory() as tmp:
            page = dashboard.setup_card({"me": False, "hazır": False, "eksikler": []})
            self.assertIn("henüz bir kişi için kurulmadı", page)
            self.assertFalse((Path(tmp) / "me").exists())


class SourceStatus(unittest.TestCase):
    def test_last_scan_per_source(self):
        from datetime import date
        from pipeline import dashboard
        with tempfile.TemporaryDirectory() as tmp:
            me = Path(tmp) / "me"
            (me / "pipeline" / "scans").mkdir(parents=True)
            (me / "pipeline" / "scans" / "2026-01-01.json").write_text(json.dumps({"meta": {
                "kaynaklar": {"himalayas": {"eşleşen": 5}},
                "elle_okumalar": [{"kaynak": "linkedin", "yöntem": "girişsiz arama", "ilan": 3},
                                  {"kaynak": "linkedin", "yöntem": "oturumlu arama", "ilan": 4},
                                  {"kaynak": "indeed", "yöntem": "tarayıcı", "ilan": 0, "not": "gürültülü"}]}, "jobs": []}),
                encoding="utf-8")
            (me / "pipeline" / "scans" / "2026-01-09.json").write_text(json.dumps({"meta": {
                "kaynaklar": {"himalayas": {"eşleşen": 2}}}, "jobs": []}), encoding="utf-8")
            cfg = {"feeds": {"himalayas": {"enabled": True}},
                   "elle_kaynaklar": {"indeed": "tarayıcıyla okunur", "stepstone": "tarayıcıyla okunur",
                                      "glassdoor": "taranmaz; yalnızca iş alarmı e-postaları"}}
            rows = {r["ad"]: r for r in dashboard.source_status(me, cfg, date(2026, 1, 10))}
        self.assertEqual((rows["himalayas"]["tarih"], rows["himalayas"]["ilan"], rows["himalayas"]["eski"]), ("2026-01-09", 2, False))
        self.assertEqual(rows["linkedin · arama"]["ilan"], 7)            # aynı gün iki arama toplanır
        self.assertTrue(rows["linkedin · arama"]["eski"])                 # 9 gün > 7
        self.assertEqual(rows["indeed"]["not"], "gürültülü")
        self.assertTrue(rows["stepstone"]["eski"])                        # hiç taranmadı
        self.assertFalse(rows["glassdoor"]["eski"])                       # yalnızca linkle çalışır


class HimalayasFetch(unittest.TestCase):
    """Ağ yok: http_json sahte bir sunucuyla değiştirilir."""

    def run_fetch(self, server, ctx):
        calls = []

        def fake(url, **_kw):
            q = dict(parse_qsl(urlparse(url).query))
            calls.append(q)
            return server(q)
        with mock.patch.object(himalayas, "http_json", fake), mock.patch.object(himalayas.time, "sleep"):
            return himalayas.fetch(ctx), calls

    @staticmethod
    def page(titles):
        return {"jobs": [{"guid": f"g-{t}", "title": t} for t in titles]}

    def test_country_from_workers_and_early_stop(self):
        def server(q):
            if q["page"] == "1":
                return self.page([f"Data Analyst {i}" for i in range(20)])
            if q["page"] == "2":
                return self.page([f"Sales Lead {i}" for i in range(20)])  # başlık eşleşmesi yok → dur
            raise AssertionError("3. sayfa okunmamalı")
        ctx = {"queries": ["data analyst"], "feed": {"pages": 5},
               "countries": ["Austria", "EU", "Europe", "Worldwide"]}
        jobs, calls = self.run_fetch(server, ctx)
        self.assertEqual(len(jobs), 40)
        self.assertEqual([c.get("country") for c in calls], ["Austria", "Austria"])
        self.assertEqual(ctx["uyarılar"], [])

    def test_explicit_country_wins(self):
        _, calls = self.run_fetch(lambda q: self.page([]), {"queries": ["x"], "feed": {"country": "Portugal"},
                                                            "countries": ["Austria"]})
        self.assertEqual(calls[0]["country"], "Portugal")

    def test_rate_limit_is_reported(self):
        def server(q):
            if q["q"] == "b":
                raise urllib.error.HTTPError("u", 429, "Too Many Requests", {}, None)
            return self.page(["A role"])
        ctx = {"queries": ["a", "b", "c"], "feed": {}, "countries": []}
        with mock.patch.object(himalayas, "date") as d, mock.patch.object(himalayas, "BACKOFF_S", (1, 2)):
            d.today.return_value.toordinal.return_value = 0   # sıra döndürülmesin
            jobs, _ = self.run_fetch(server, ctx)
        self.assertEqual(len(jobs), 1)
        self.assertTrue(ctx["uyarılar"] and "2/3 sorgu okunmadı" in ctx["uyarılar"][0])

    def test_rate_limit_retries_before_giving_up(self):
        hits = {"n": 0}

        def server(q):
            hits["n"] += 1
            if hits["n"] <= 2:   # ilk iki istek 429, üçüncüsü geçer
                raise urllib.error.HTTPError("u", 429, "Too Many Requests", {}, None)
            return self.page(["A role"])
        ctx = {"queries": ["a"], "feed": {}, "countries": []}
        with mock.patch.object(himalayas, "BACKOFF_S", (1, 2)):
            jobs, _ = self.run_fetch(server, ctx)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(ctx["uyarılar"], [])

    def test_bad_country_falls_back_to_unfiltered(self):
        def server(q):
            if "country" in q:
                raise urllib.error.HTTPError("u", 400, "Bad Request", {}, None)
            return self.page(["A role"])
        ctx = {"queries": ["a"], "feed": {}, "countries": ["Atlantis"]}
        jobs, calls = self.run_fetch(server, ctx)
        self.assertEqual(len(jobs), 1)
        self.assertNotIn("country", calls[-1])
        self.assertTrue(any("geçersiz ülke" in w for w in ctx["uyarılar"]))


if __name__ == "__main__":
    unittest.main()
