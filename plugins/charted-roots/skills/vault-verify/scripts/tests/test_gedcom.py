"""The GEDCOM reader.

The two things worth pinning are the ones the plugin's own parser drops: the
`1 EVEN` blocks distinguished only by `2 TYPE`, and the fact that a shared
event arrives once per individual, so a naive scan double-counts a marriage.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from crsync import gedcom

from .helpers import ged

SMALL = """0 HEAD
1 SOUR Ancestry.com Family Trees
2 NAME Ancestry.com Member Trees
1 GEDC
2 VERS 5.5.1
1 DATE 21 SEP 2026
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Jürgen /Muster/
2 GIVN Jürgen
2 SURN Muster
1 NAME Jürgen Muster, Landwirt Musterdorf
1 FACT
2 TYPE AKA
2 NOTE Jürgen Mustere
1 SEX M
1 BIRT
2 DATE 1 JUN 1824
2 PLAC Musterdorf, Preußen
2 SOUR @S1@
3 PAGE Kirchenbuch 1824, Nr. 14
1 RESI
2 DATE 1850
2 PLAC Musterdorf
1 RESI
2 DATE 1861
2 PLAC Musterdorf
1 DEAT
2 DATE ABT 1871
1 EVEN
2 TYPE Arrival
2 DATE 12 MAY 1852
2 PLAC New York
1 EVEN
2 TYPE Obituary
2 DATE 14 JAN 1872
1 EVEN
2 TYPE Marriage of Jürgen Muster and Anna Meyer
2 DATE 27 MAY 1849
1 FAMS @F1@
0 @I2@ INDI
1 NAME Anna /Meyer/
1 SEX F
1 BIRT
2 DATE BET 1826 AND 1828
1 EVEN
2 TYPE Marriage of Jürgen Muster and Anna Meyer
2 DATE 27 MAY 1849
1 FAMS @F1@
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
1 MARR
2 DATE 27 MAY 1849
2 PLAC Musterdorf
0 @S1@ SOUR
1 TITL Kirchenbuch Musterdorf
1 AUTH Evangelische Kirche
1 PUBL Landesarchiv
0 @O1@ OBJE
1 FILE
2 TITL A caption, not a path
2 FORM jpg
3 _MTYPE PHOTO
1 _OID abc123
0 TRLR
"""

CONTINUED = """0 @I9@ INDI
1 NAME Test /Person/
1 NOTE first line
2 CONT second line
2 CONC  continued
0 TRLR
"""


class Dates(unittest.TestCase):

    def test_the_forms_the_vault_permits(self):
        cases = [
            ("1 JUN 1824", ("1824-06-01", "exact")),
            ("JUN 1824", ("1824-06", "month")),
            ("1824", ("1824", "year")),
            ("824", ("0824", "year")),
            ("ABT 1804", ("ABT 1804", "estimated")),
            ("BEF 1908", ("BEF 1908", "estimated")),
            ("AFT 1908", ("AFT 1908", "estimated")),
            ("EST 1804", ("ABT 1804", "estimated")),
            ("BET 1904 AND 1908", ("1904-1908", "range")),
            ("BET 1904 AND 1904", ("1904", "range")),
            ("", ("", "unknown")),
            ("sometime in the 1840s", ("sometime in the 1840s", "unknown")),
            ("1904-1908", ("1904-1908", "range")),
        ]
        for raw, want in cases:
            with self.subTest(raw):
                self.assertEqual(gedcom.normalise_date(raw), want)

    def test_a_qualified_full_date_keeps_the_qualifier(self):
        self.assertEqual(gedcom.normalise_date("ABT 1 JUN 1824"),
                         ("ABT 1824-06-01", "estimated"))


class Even(unittest.TestCase):

    def test_classification(self):
        cases = [
            ("Arrival", ("immigration", "travel")),
            ("departure", ("emigration", "travel")),
            ("Death", ("death", "travel")),
            ("Obituary of Jürgen Muster", (None, "derivative")),
            ("Testament", (None, "derivative")),
            ("Marriage License", (None, "derivative")),
            ("Marriage of A and B", (None, "shared")),
            ("Something else entirely", (None, "unknown")),
            ("", (None, "unknown")),
        ]
        for raw, want in cases:
            with self.subTest(raw):
                self.assertEqual(gedcom.classify_even(raw), want)


class Parse(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path = ged(SMALL)
        cls.tree = gedcom.parse(cls.path)

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.path)

    def test_header(self):
        self.assertEqual(self.tree.header["version"], "5.5.1")
        self.assertEqual(self.tree.header["date"], "21 SEP 2026")
        self.assertTrue(self.tree.header["source"].startswith("Ancestry"))

    def test_individual_names(self):
        ind = self.tree.individuals["I1"]
        self.assertEqual(ind.name, "Jürgen Muster")
        self.assertEqual(ind.given, "Jürgen")
        self.assertEqual(ind.surname, "Muster")
        self.assertEqual(ind.sex, "M")

    def test_alternate_names_include_the_aka_fact(self):
        # Reading only the first `1 NAME` reports a maiden/married pair as a
        # disagreement. the upstream-ancestry convention.
        self.assertEqual(self.tree.individuals["I1"].alt_names,
                         ["Jürgen Muster, Landwirt Musterdorf", "Jürgen Mustere"])

    def test_event_tags_map_to_vault_event_types(self):
        types = [e.event_type for e in self.tree.individuals["I1"].events]
        self.assertEqual(types, ["birth", "residence", "residence", "death",
                                 "immigration"])

    def test_ordinals_count_within_a_type(self):
        resi = [e for e in self.tree.individuals["I1"].events
                if e.event_type == "residence"]
        self.assertEqual([e.ordinal for e in resi], [0, 1])
        self.assertEqual([e.date for e in resi], ["1850", "1861"])

    def test_citations_are_read_with_their_page(self):
        birth = self.tree.individuals["I1"].events[0]
        self.assertEqual(birth.citations, [("S1", "Kirchenbuch 1824, Nr. 14")])
        self.assertEqual(birth.place, "Musterdorf, Preußen")

    def test_derivative_and_shared_even_blocks_are_suppressed(self):
        kinds = sorted(d for d, _ in self.tree.suppressed)
        self.assertEqual(kinds, ["derivative", "shared", "shared"])
        for _, ev in self.tree.suppressed:
            self.assertNotIn(ev, self.tree.events)

    def test_a_shared_event_is_counted_once_at_the_family(self):
        # Two INDI each carry a `Marriage of ...` EVEN; only the FAM MARR
        # survives, so the couple's timeline gets one marriage, not three.
        marriages = [e for e in self.tree.events if e.event_type == "marriage"]
        self.assertEqual(len(marriages), 1)
        ev = marriages[0]
        self.assertTrue(ev.shared)
        self.assertEqual(ev.couple, ("I1", "I2"))
        self.assertEqual(ev.owner, "F1")

    def test_family_structure(self):
        fam = self.tree.families["F1"]
        self.assertEqual((fam.husband, fam.wife, fam.children),
                         ("I1", "I2", ["I3"]))

    def test_source_repository_comes_from_publ(self):
        src = self.tree.sources["S1"]
        self.assertEqual((src.title, src.author, src.publisher),
                         ("Kirchenbuch Musterdorf", "Evangelische Kirche",
                          "Landesarchiv"))

    def test_media_with_an_empty_file_still_parses(self):
        obj = self.tree.media["O1"]
        self.assertEqual((obj.title, obj.form, obj.oid),
                         ("A caption, not a path", "jpg", "abc123"))


class Folding(unittest.TestCase):

    def test_cont_and_conc(self):
        path = ged(CONTINUED)
        self.addCleanup(os.unlink, path)
        tree = gedcom.parse(path)
        self.assertIn("I9", tree.individuals)


def _raw_ged(data: bytes) -> str:
    """Write raw bytes (possibly invalid UTF-8) to a temp .ged; return its path."""
    fd, path = tempfile.mkstemp(suffix=".ged")
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)
    return path


#: `с` (d1 81) of "Записано" cut after its first byte, as byte-count wrapping
#: exporters do. The CONC line holds the second byte.
SPLIT_HEAD = (b"0 HEAD\r\n1 SOUR Test\r\n2 VERS 2.0\r\n1 GEDC\r\n"
              b"2 VERS 5.5.1\r\n1 CHAR UTF-8\r\n")
SPLIT_BODY = (b"0 @I9@ INDI\r\n1 NAME Test /Person/\r\n"
              b"1 NOTE \xd0\x97\xd0\xb0\xd0\xbf\xd0\xb8\xd1\r\n"
              b"2 CONC \x81\xd0\xb0\xd0\xbd\xd0\xbe\r\n0 TRLR\r\n")


class Encoding(unittest.TestCase):

    def parse_bytes(self, data: bytes):
        path = _raw_ged(data)
        self.addCleanup(os.unlink, path)
        messages = []
        return gedcom.parse(path, warn=messages.append), messages, path

    def test_character_split_across_conc_is_rejoined_with_a_warning(self):
        data = SPLIT_HEAD + SPLIT_BODY
        tree, messages, path = self.parse_bytes(data)
        self.assertEqual(tree.header["version"], "5.5.1")
        self.assertIn("I9", tree.individuals)
        self.assertEqual(len(messages), 1, messages)
        self.assertIn("CONC", messages[0])
        self.assertIn("line(s): 10", messages[0])
        with open(path, "rb") as fh:
            self.assertEqual(fh.read(), data, "the file is never rewritten")

    def test_the_rejoined_value_is_the_whole_word(self):
        path = _raw_ged(SPLIT_HEAD + SPLIT_BODY)
        self.addCleanup(os.unlink, path)
        root = next(r for r in gedcom._tree(path) if r.tag == "INDI")
        self.assertEqual(root.val("NOTE"), "Записано")

    def test_a_split_before_an_unrelated_or_unsupported_line_still_fails(self):
        cases = {
            "CONT": SPLIT_BODY.replace(b"2 CONC ", b"2 CONT "),
            "unrelated level": SPLIT_BODY.replace(b"2 CONC ", b"1 CONC "),
        }
        for case, body in cases.items():
            with self.subTest(case), self.assertRaises(UnicodeDecodeError):
                self.parse_bytes(SPLIT_HEAD + body)
        heads = {
            "GEDCOM 7": SPLIT_HEAD.replace(b"2 VERS 5.5.1", b"2 VERS 7.0"),
            "ANSEL": SPLIT_HEAD.replace(b"CHAR UTF-8", b"CHAR ANSEL"),
        }
        for case, head in heads.items():
            with self.subTest(case), self.assertRaises(UnicodeDecodeError):
                self.parse_bytes(head + SPLIT_BODY)

    def test_unparseable_lines_are_counted_not_dropped_silently(self):
        tree, messages, _ = self.parse_bytes(
            CONTINUED.replace("1 NAME", "garbage here\n1 NAME").encode())
        self.assertIn("I9", tree.individuals)
        self.assertEqual(messages, [m for m in tree.warnings])
        self.assertEqual(len(messages), 1)
        self.assertIn("skipped 1 line(s)", messages[0])
        self.assertIn(": 2", messages[0])

    def test_a_well_formed_file_warns_nothing(self):
        tree, messages, _ = self.parse_bytes(SMALL.encode("utf-8"))
        self.assertEqual((messages, tree.warnings), ([], []))


class NonPlaces(unittest.TestCase):

    def test_a_rank_or_unit_in_plac_is_reported(self):
        for value in ("Infanterie-Regiment 32", "Landwehr Bataillon",
                      "Сумський РВК"):
            with self.subTest(value):
                self.assertTrue(gedcom.non_place_reason(value))

    def test_a_real_place_is_not(self):
        for value in ("Musterdorf, Preußen", "Lebedyn, Sumy Oblast", ""):
            with self.subTest(value):
                self.assertEqual(gedcom.non_place_reason(value), "")


if __name__ == "__main__":
    unittest.main()
