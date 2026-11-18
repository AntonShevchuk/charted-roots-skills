"""gedcheck: the standalone GEDCOM findings."""

from __future__ import annotations

import os
import unittest

from crsync import gedcheck, gedcom

from .helpers import ged

HEAD = """0 HEAD
1 SOUR Ancestry.com Family Trees
1 GEDC
2 VERS 5.5.1
1 CHAR UTF-8
"""


def check(text, only=None):
    path = ged(HEAD + text)
    try:
        tree = gedcom.parse(path, warn=lambda m: None)
    finally:
        os.unlink(path)
    return gedcheck.run(tree, only)


def only(findings, name):
    hits = [f for f in findings if f.check == name]
    assert len(hits) == 1, findings
    return hits[0]


def indi(*lines):
    return "0 @I1@ INDI\n1 NAME Anna /Muster/\n" + "\n".join(lines) + "\n0 TRLR\n"


TWO_SAME_BIRTHS = indi("1 BIRT", "2 DATE 1 JUN 1824", "2 PLAC Musterdorf",
                       "1 BIRT", "2 DATE 1 JUN 1824", "2 PLAC Musterdorf")
TWO_DIFFERENT_BIRTHS = indi("1 BIRT", "2 DATE 1 JUN 1824", "2 PLAC Musterdorf",
                            "1 BIRT", "2 DATE 1825", "2 PLAC Musterdorf")
THREE_RESI_TWO_CENS = indi(
    "1 RESI", "2 DATE 1 JUN 1830", "2 PLAC Musterdorf",
    "1 RESI", "2 DATE 1 JUN 1840", "2 PLAC Musterdorf",
    "1 RESI", "2 DATE 1 JUN 1850", "2 PLAC Beispielstadt",
    "1 CENS", "2 DATE 1 JUN 1860", "2 PLAC Musterdorf",
    "1 CENS", "2 DATE 1 JUN 1870", "2 PLAC Musterdorf")
TWO_SAME_RESI = indi("1 RESI", "2 DATE 1 JUN 1830", "2 PLAC Musterdorf",
                     "1 RESI", "2 DATE 1 JUN 1830", "2 PLAC Musterdorf")


def fam(*marrs, xref="F1", h="I1", w="I2"):
    return (f"0 @{xref}@ FAM\n1 HUSB @{h}@\n1 WIFE @{w}@\n"
            + "".join(f"1 MARR\n2 DATE {d}\n2 PLAC Musterdorf\n" for d in marrs))


COUPLE = ("0 @I1@ INDI\n1 NAME Karl /Beispiel/\n1 FAMS @F1@\n1 FAMS @F2@\n"
          "0 @I2@ INDI\n1 NAME Anna /Muster/\n1 FAMS @F1@\n1 FAMS @F2@\n")
SAME_MARRIAGES = COUPLE + fam("1 JUN 1850", "1 JUN 1850") + "0 TRLR\n"
OTHER_MARRIAGES = COUPLE + fam("1 JUN 1850", "1 JUN 1851") + "0 TRLR\n"
TWO_FAMS = COUPLE + fam("1 JUN 1850") + fam("1 JUN 1851", xref="F2") + "0 TRLR\n"
EVEN_MARR = (
    "0 @I1@ INDI\n1 NAME Karl /Beispiel/\n1 FAMS @F1@\n"
    "1 EVEN\n2 TYPE MARR\n2 DATE 1 JUN 1850\n2 PLAC Musterdorf\n"
    "0 @I2@ INDI\n1 NAME Anna /Muster/\n1 FAMS @F1@\n"
    + fam("1 JUN 1850") + "0 TRLR\n")


class Duplicates(unittest.TestCase):
    def test_identical_births_are_a_fix(self):
        f = only(check(TWO_SAME_BIRTHS), "dup-vital")
        self.assertEqual((f.kind, f.who), ("fix", "Anna Muster (@I1@)"))
        self.assertTrue(f.fix.startswith("in Ancestry: "))

    def test_conflicting_births_are_a_review(self):
        f = only(check(TWO_DIFFERENT_BIRTHS), "dup-vital")
        self.assertEqual(f.kind, "review")
        self.assertIn("1 JUN 1824", f.what)
        self.assertIn("1825", f.what)

    def test_repeatable_facts_are_not_duplicates(self):
        self.assertEqual(check(THREE_RESI_TWO_CENS), [])

    def test_exact_repeat_of_a_fact(self):
        self.assertEqual(only(check(TWO_SAME_RESI), "dup-event-exact").kind,
                         "fix")

    def test_two_marriages_in_one_family(self):
        self.assertEqual(only(check(SAME_MARRIAGES), "dup-marriage").kind,
                         "fix")
        f = only(check(OTHER_MARRIAGES), "dup-marriage")
        self.assertEqual(f.kind, "review")
        self.assertEqual(f.who, "Karl Beispiel & Anna Muster (@F1@)")

    def test_two_families_for_one_couple(self):
        self.assertEqual(only(check(TWO_FAMS), "dup-family").kind, "review")

    def test_even_type_marr_counts_as_marr(self):
        found = check(EVEN_MARR)
        self.assertEqual([f.check for f in found], ["marriage-on-person"])


PERSON_MARRIAGES = """0 @I1@ INDI
1 NAME Jürgen /Muster/
1 FAMS @F1@
1 MARR
2 DATE 27 MAY 1849
2 PLAC Musterdorf
0 @I2@ INDI
1 NAME Anna /Meyer/
1 FAMS @F1@
0 @I3@ INDI
1 NAME Karl /Beispiel/
1 EVEN
2 TYPE MARR
2 DATE 1 JUN 1880
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 MARR
2 DATE 27 MAY 1849
0 TRLR
"""


class Marriages(unittest.TestCase):
    def setUp(self):
        self.found = check(PERSON_MARRIAGES)

    def test_same_findings_as_the_old_section_8(self):
        dup, loose = self.found
        self.assertEqual((dup.kind, loose.kind), ("fix", "review"))
        self.assertTrue(dup.fix.startswith("in Ancestry: "))
        self.assertIn("delete the person-level marriage", dup.fix)
        self.assertIn("Anna Meyer (@I2@)", dup.what)
        self.assertEqual(loose.who, "Karl Beispiel (@I3@)")
        self.assertIn("no family", loose.what)
        self.assertIn("add the spouse", loose.fix)


class Run(unittest.TestCase):
    def test_only_filters_by_group(self):
        text = TWO_SAME_BIRTHS
        self.assertEqual(len(check(text, {"duplicates"})), 1)
        self.assertEqual(check(text, {"marriages"}), [])

    def test_unknown_group_raises(self):
        with self.assertRaises(ValueError) as cm:
            gedcheck.parse_only("dupes")
        self.assertIn("duplicates", str(cm.exception))

    def test_parse_only(self):
        self.assertIsNone(gedcheck.parse_only(""))
        self.assertEqual(gedcheck.parse_only("Dates, places"),
                         {"dates", "places"})


if __name__ == "__main__":
    unittest.main()
