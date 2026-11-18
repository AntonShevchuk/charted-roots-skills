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

    def test_even_blocks_are_duplicates_only_with_the_same_type(self):
        def blocks(t2):
            return indi("1 EVEN", "2 TYPE Arrival", "2 DATE 1 JUN 1830",
                        "2 PLAC Musterdorf", "1 EVEN", f"2 TYPE {t2}",
                        "2 DATE 1 JUN 1830", "2 PLAC Musterdorf")
        self.assertEqual(
            [f.check for f in check(blocks("Arrival"))], ["dup-event-exact"])
        self.assertEqual(check(blocks("Departure")), [])


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


DATES = indi("1 BIRT", "2 DATE 25 Foo 1914",
             "1 DEAT", "2 DATE 31 FEB 1850",
             "1 BAPM", "2 DATE 25 Dez 1914",
             "1 RESI", "2 DATE FROM 1850")


def life(birth, death, burial=None):
    lines = ["1 BIRT", f"2 DATE {birth}", "1 DEAT", f"2 DATE {death}"]
    if burial:
        lines += ["1 BURI", f"2 DATE {burial}"]
    return indi(*lines)


def parent_child(child_birth, parent_birth, frel=None):
    chil = "1 CHIL @I3@\n" + (f"2 _FREL {frel}\n" if frel else "")
    return ("0 @I1@ INDI\n1 NAME Karl /Beispiel/\n1 FAMS @F1@\n"
            f"1 BIRT\n2 DATE {parent_birth}\n"
            "0 @I2@ INDI\n1 NAME Anna /Muster/\n1 FAMS @F1@\n"
            "0 @I3@ INDI\n1 NAME Kind /Beispiel/\n1 FAMC @F1@\n"
            f"1 BIRT\n2 DATE {child_birth}\n"
            "0 @F1@ FAM\n1 HUSB @I1@\n1 WIFE @I2@\n" + chil + "0 TRLR\n")


class Dates(unittest.TestCase):
    def test_each_label_maps_to_its_check(self):
        fs = check(DATES)
        self.assertEqual(sorted(f.check for f in fs),
                         ["date-invalid", "date-nonstandard", "date-unreadable"])
        self.assertIn('"25 DEC 1914"', only(fs, "date-nonstandard").fix)
        self.assertTrue(only(fs, "date-unreadable").fix.startswith("in Ancestry: "))

    def test_suppressed_even_dates_are_checked(self):
        f = only(check(indi("1 EVEN", "2 TYPE Obituary", "2 DATE 25 Dez 1914")),
                 "date-nonstandard")
        self.assertIn('"25 DEC 1914"', f.fix)

    def test_death_before_birth(self):
        f = only(check(life("1 JUN 1850", "1 JUN 1840")), "date-order")
        self.assertEqual(f.kind, "review")
        self.assertIn("death", f.what)

    def test_burial_before_death(self):
        f = only(check(life("1 JUN 1800", "1 JUN 1850", "1 JUN 1840")),
                 "date-order")
        self.assertIn("burial", f.what)

    def test_child_born_before_parent(self):
        f = only(check(parent_child("1 JUN 1840", "1 JUN 1850")), "date-order")
        self.assertEqual(f.who, "Kind Beispiel (@I3@)")

    def test_step_child_older_than_step_parent_is_fine(self):
        self.assertEqual(
            check(parent_child("1 JUN 1840", "1 JUN 1850", frel="Step")), [])

    def test_lifespan_over_120(self):
        f = only(check(life("1 JUN 1700", "1 JUN 1830")), "date-order")
        self.assertIn("lifespan", f.what)

    def test_about_dates_do_not_false_positive(self):
        self.assertEqual(check(life("ABT 1850", "1845")), [])


def PLAC(*places):
    return indi(*[x for p in places for x in ("1 RESI", "2 DATE 1 JUN 1830",
                                              f"2 PLAC {p}")])


PLACS = PLAC


class Places(unittest.TestCase):
    def test_non_place(self):
        f = only(check(PLAC("Infanterie-Regiment 51")), "place-non-place")
        self.assertEqual(f.kind, "fix")
        self.assertIn("Infanterie-Regiment 51", f.what)
        self.assertTrue(f.fix.startswith("in Ancestry: "))

    def test_format(self):
        f = only(check(PLAC("Berlin ,  Preußen,")), "place-format")
        self.assertIn('"Berlin, Preußen"', f.fix)

    def test_no_space_after_comma_alone_is_fine(self):
        self.assertEqual(check(PLAC("Berlin,Preußen")), [])

    def test_variant_case_and_accents(self):
        f = only(check(PLACS("Wrocław, Polska", "Wroclaw, Polska",
                             "wrocław, polska", "Wrocław, Polska")),
                 "place-variant")
        self.assertIn('"Wrocław, Polska" (2)', f.fix)

    def test_variant_tie_is_alphabetical(self):
        f = only(check(PLACS("musterdorf", "Musterdorf")), "place-variant")
        self.assertIn('"Musterdorf"', f.fix)

    def test_hierarchy_fuller_form(self):
        f = only(check(PLACS("Berlin, Germany", "Berlin, Brandenburg, Germany")),
                 "place-hierarchy")
        self.assertEqual(f.kind, "review")
        self.assertIn('"Berlin, Brandenburg, Germany"', f.fix)

    def test_variants_do_not_double_report_hierarchy(self):
        findings = check(PLACS("Berlin, Germany", "berlin, germany",
                               "Berlin, Brandenburg, Germany"))
        only(findings, "place-hierarchy")

    def test_bare_leaf_one_fuller_is_a_fix(self):
        f = only(check(PLACS("Berlin", "Berlin, Germany")), "place-hierarchy")
        self.assertEqual(f.kind, "fix")
        self.assertIn('use "Berlin, Germany"', f.fix)

    def test_bare_leaf_two_fuller_is_a_review(self):
        f = only(check(PLACS("Springfield", "Springfield, Illinois",
                             "Springfield, Ohio")), "place-hierarchy")
        self.assertEqual(f.kind, "review")
        self.assertIn("Illinois", f.fix)
        self.assertIn("Ohio", f.fix)

    def test_unrelated_parents_are_fine(self):
        self.assertEqual(
            check(PLACS("Springfield, Illinois", "Springfield, Ohio")), [])

    def _folded(self, plac):
        return (
            "0 @I1@ INDI\n1 NAME Karl /Beispiel/\n1 FAMS @F1@\n"
            f"1 MARR\n2 DATE 1 JUN 1850\n2 PLAC {plac}\n"
            "0 @I2@ INDI\n1 NAME Anna /Muster/\n1 FAMS @F1@\n"
            "0 @F1@ FAM\n1 HUSB @I1@\n1 WIFE @I2@\n1 MARR\n"
            "2 DATE 1 JUN 1850\n0 TRLR\n")

    def test_folded_marriage_place_counted_once(self):
        f = only(check(self._folded("Musterdorf ,")), "place-format")
        self.assertIn("(1 use)", f.what)

    def test_folded_person_only_non_place_is_reported(self):
        f = only(check(self._folded("Infanterie-Regiment 51")),
                 "place-non-place")
        self.assertIn("(1 use)", f.what)

    def test_who_lists_three_then_and_more(self):
        text = "".join(
            f"0 @I{i}@ INDI\n1 NAME P{i} /Muster/\n1 RESI\n2 DATE 1 JUN 1830\n"
            f"2 PLAC Infanterie-Regiment 51\n" for i in range(1, 6)) + "0 TRLR\n"
        f = only(check(text), "place-non-place")
        self.assertTrue(f.who.endswith(" and 2 more"), f.who)
        self.assertIn("(5 uses)", f.what)


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
