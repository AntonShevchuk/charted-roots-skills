"""Date forms: what the sync reads from GEDCOM and writes for the plugin."""

from __future__ import annotations

import unittest

from crsync import dates

SETTINGS = {"dateFormatStandard": "flexible", "allowPartialDates": True,
            "allowCircaDates": True, "allowDateRanges": True,
            "requireLeadingZeros": False}


class FromGedcom(unittest.TestCase):

    def test_forms_upstream_exports_carry(self):
        cases = [
            ("Abt. 1804", ("ABT 1804", "estimated")),
            ("abt 1804", ("ABT 1804", "estimated")),
            ("Bef. 12 Oct 1890", ("BEF 1890-10-12", "estimated")),
            ("12 April 1890", ("1890-04-12", "exact")),
            ("25 Dez 1914", ("1914-12-25", "exact")),
            ("15 Okt 1795", ("1795-10-15", "exact")),
            ("27Mar1989", ("1989-03-27", "exact")),
            ("17.2.1852", ("1852-02-17", "exact")),
            ("1939-1948", ("1939-1948", "range")),
            ("FROM 1850 TO 1858", ("1850-1858", "range")),
            ("10 Sep 18888", ("10 Sep 18888", "unknown")),
            ("7 Aug 1905; 19 Jan 1929", ("7 Aug 1905; 19 Jan 1929", "unknown")),
        ]
        for raw, want in cases:
            with self.subTest(raw):
                self.assertEqual(dates.from_gedcom(raw), want)

    def test_a_word_starting_with_a_qualifier_is_not_one(self):
        self.assertEqual(dates.from_gedcom("Calif 1850")[1], "unknown")


class PersonForm(unittest.TestCase):

    def test_every_form_passes_the_plugin_validator(self):
        cases = [
            ("1804", "1804"),
            ("1804-03-12", "1804-03-12"),
            ("ABT 1804", "c. 1804"),
            ("ABT 1824-06-01", "c. 1824-06-01"),
            ("BEF 1909", "1909"),
            ("AFT 1869-03-26", "1869-03-26"),
            ("1850-1858", "1850 to 1858"),
            ("sometime in the 1840s", ""),
            ("", ""),
        ]
        for value, want in cases:
            with self.subTest(value):
                got = dates.person_form(value)
                self.assertEqual(got, want)
                if got:
                    self.assertEqual(dates.plugin_error(got, SETTINGS), "")


class Meaning(unittest.TestCase):

    def test_respellings_read_the_same(self):
        groups = [
            ["ABT 1804", "c. 1804", "ca. 1804", "circa 1804", "~1804", "CAL 1804"],
            ["1850-1858", "1850 to 1858", "BET 1850 AND 1858"],
            ["25 Dez 1914", "1914-12-25", "25 DEC 1914"],
        ]
        for group in groups:
            with self.subTest(group[0]):
                self.assertEqual(len({dates.meaning(v) for v in group}), 1)

    def test_before_is_not_about(self):
        self.assertNotEqual(dates.meaning("BEF 1909"), dates.meaning("c. 1909"))


class PluginValidator(unittest.TestCase):
    """Verdicts checked against the plugin's own code (`Sse` in main.js)."""

    def test_verdicts(self):
        ok = ["1804", "1804-03", "1804-03-12", "1804-3-2", "c. 1804", "ca. 1804",
              "circa 1804", "~1804", "c.1804", "1850 to 1858", "15 JAN 1920", "Jan 1920"]
        bad = ["ABT 1804", "BEF 1909", "AFT 1909", "1850-1858", "1850 - 1858",
               "- 1909", "to 1909", "BET 1850 AND 1858", "25 Dez 1914", "17.2.1852"]
        for v in ok:
            with self.subTest(ok=v):
                self.assertEqual(dates.plugin_error(v, SETTINGS), "")
        for v in bad:
            with self.subTest(bad=v):
                self.assertNotEqual(dates.plugin_error(v, SETTINGS), "")

    def test_settings_are_honoured(self):
        self.assertIn("Circa", dates.plugin_error(
            "c. 1804", {**SETTINGS, "allowCircaDates": False}))
        self.assertIn("ranges", dates.plugin_error(
            "1850 to 1858", {**SETTINGS, "allowDateRanges": False}))
        self.assertNotEqual(dates.plugin_error(
            "1804", {**SETTINGS, "allowPartialDates": False}), "")


if __name__ == "__main__":
    unittest.main()
