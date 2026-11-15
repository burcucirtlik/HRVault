"""Motorun eleme ve ayrıştırma kuralları için testler. Kişisel veri kullanmaz.

Çalıştır (vault kökünden):  python3 -m unittest discover engine/tests
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import ats, inbox  # noqa: E402
from scanner import config  # noqa: E402
from scanner.common import Job  # noqa: E402
from scanner.scan import (ats_location_ok, dedupe_key, excluded, language_ok, location_ok,  # noqa: E402
                          region_ok, role_matches)

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


class Location(unittest.TestCase):
    def test_title_region(self):
        self.assertFalse(region_ok("Community Moderator - India", ALLOWED))
        self.assertFalse(region_ok("Lead Designer - U.S. (30 hours/week)", ALLOWED))
        self.assertTrue(region_ok("Engineer (US Canada, Europe, MENA, India & APAC Timezones)", ALLOWED))
        self.assertTrue(region_ok("Data Annotator - Worldwide (US hours)", ALLOWED))
        self.assertTrue(region_ok("Business Analyst", ALLOWED))  # "us" kelimesi değil, "business" içinde
        self.assertTrue(region_ok("Anything - India", []))      # izinli liste boşsa eleme yok

    def test_ats_location(self):
        self.assertFalse(ats_location_ok(job(location="Mumbai, India"), ALLOWED))
        self.assertFalse(ats_location_ok(job(location="London, Remote (UK)", workplace="remote"), ALLOWED))
        self.assertTrue(ats_location_ok(job(location="United Kingdom", workplace="remote"), ALLOWED))
        self.assertTrue(ats_location_ok(job(location="Remote - Europe"), ALLOWED))
        self.assertTrue(ats_location_ok(job(location="Lisbon, Portugal"), ALLOWED))

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

    def test_word_boundary(self):
        self.assertFalse(ats.found(" " + ats.fold("Javascript") + " ", "Java"))
        self.assertTrue(ats.found(" " + ats.fold("C++ and C#") + " ", "C++"))


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


if __name__ == "__main__":
    unittest.main()
