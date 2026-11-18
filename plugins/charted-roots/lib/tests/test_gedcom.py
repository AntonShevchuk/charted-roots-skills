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


EVEN_ALIASES = """0 HEAD
1 SOUR MYHERITAGE
1 GEDC
2 VERS 5.5.1
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Jürgen /Muster/
1 FAMS @F1@
1 EVEN
2 TYPE MARR
2 DATE 5 APR 1898
2 PLAC Musterdorf
2 SOUR @S1@
3 PAGE Heiratsregister Nr. 21
1 EVEN
2 TYPE Taufe
2 DATE 9 MAR 1871
1 EVEN
2 TYPE Hochzeit
2 DATE 1 JUN 1920
1 EVEN
2 TYPE Verlobung
2 DATE 1 JAN 1898
1 EVEN
2 TYPE Konfirmation
2 DATE 2 APR 1885
1 EVEN
2 TYPE Military Service
2 DATE 1916
1 EVEN
2 TYPE Reference Number
2 DATE 1 JAN 1900
1 CHR
2 DATE 12 MAR 1871
0 @I2@ INDI
1 NAME Anna /Beispiel/
1 FAMS @F1@
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 MARR
2 DATE 5 APR 1898
0 @S1@ SOUR
1 TITL Heiratsregister Musterdorf
0 TRLR
"""


class EvenAliases(unittest.TestCase):
    """MyHeritage writes standard facts as `1 EVEN` + a `2 TYPE` label."""

    @classmethod
    def setUpClass(cls):
        cls.path = ged(EVEN_ALIASES)
        cls.tree = gedcom.parse(cls.path)

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.path)

    def test_the_labels_classify_as_standard_facts(self):
        for raw, want in [("MARR", "marriage"), ("marr", "marriage"),
                          ("Hochzeit", "marriage"), ("Taufe", "baptism"),
                          ("Taufe ", "baptism"), ("Konfirmation", "confirmation"),
                          ("Verlobung", "engagement"),
                          ("Military Service", "military")]:
            with self.subTest(raw):
                self.assertEqual(gedcom.classify_even(raw), (want, "standard"))

    def test_they_become_events_with_the_standard_tag(self):
        events = {(e.tag, e.date) for e in self.tree.individuals["I1"].events}
        self.assertIn(("BAPM", "1871-03-09"), events)
        self.assertIn(("MARR", "1920-06-01"), events)

    def test_a_marr_even_folds_into_the_family_marriage_it_repeats(self):
        # Same date as the FAM MARR: one marriage, which gains the place.
        on_person = [e for e in self.tree.individuals["I1"].events
                     if e.tag == "MARR" and e.date == "1898-04-05"]
        self.assertTrue(all(e.folded for e in on_person))
        fam = [e for e in self.tree.families["F1"].events if e.tag == "MARR"]
        self.assertEqual([(e.date, e.place) for e in fam],
                         [("1898-04-05", "Musterdorf")])

    def test_the_citation_and_label_are_kept(self):
        ev = next(e for e in self.tree.individuals["I1"].events
                  if e.date == "1898-04-05")
        self.assertEqual(ev.citations, [("S1", "Heiratsregister Nr. 21")])
        self.assertEqual(ev.even_type, "MARR")

    def test_a_marriage_only_on_the_person_is_recorded_for_an_upstream_fix(self):
        # 1 JUN 1920 matches no family marriage, so it stays a person-level
        # Event -- and the report asks for it to be moved upstream.
        loose = [(e.date, why) for e, why in self.tree.person_marriages]
        self.assertEqual(loose, [("1920-06-01", "no family marriage on this date")])

    def test_other_labels_are_still_set_aside(self):
        self.assertEqual([(d, e.even_type) for d, e in self.tree.suppressed],
                         [("unknown", "Reference Number")])

    def test_labelled_facts_take_the_plugins_event_types(self):
        types = {e.even_type: (e.tag, e.event_type)
                 for e in self.tree.individuals["I1"].events if e.even_type}
        self.assertEqual(types["Konfirmation"], ("CONF", "confirmation"))
        self.assertEqual(types["Verlobung"], ("ENGA", "engagement"))
        self.assertEqual(types["Military Service"], ("MILI", "military"))

    def test_chr_is_a_christening_as_the_plugin_imports_it(self):
        chr_ = [e for e in self.tree.individuals["I1"].events if e.tag == "CHR"]
        self.assertEqual([e.event_type for e in chr_], ["christening"])


class TagTable(unittest.TestCase):

    def test_event_titles_read_like_the_plugins(self):
        from crsync import create
        self.assertEqual(create.event_label("christening"), "Christening")
        self.assertEqual(create.event_label("first_communion"), "First Communion")
        self.assertEqual(create.event_label("military"), "Military service")

    def test_the_tag_table_is_the_plugins(self):
        # Charted Roots 0.22.76 `Yoe`, plus Ancestry's `_MILT`.
        plugin = {
            "BIRT": "birth", "DEAT": "death", "MARR": "marriage", "DIV": "divorce",
            "BURI": "burial", "CREM": "cremation", "ADOP": "adoption",
            "GRAD": "graduation", "RETI": "retirement", "CENS": "census",
            "RESI": "residence", "OCCU": "occupation", "EDUC": "education",
            "PROB": "probate", "WILL": "will", "NATU": "naturalization",
            "MILI": "military", "IMMI": "immigration", "EMIG": "emigration",
            "BAPM": "baptism", "CHR": "christening", "CHRA": "adult_christening",
            "CONF": "confirmation", "FCOM": "first_communion",
            "ORDN": "ordination", "BARM": "bar_mitzvah", "BASM": "bas_mitzvah",
            "BLES": "blessing", "ENGA": "engagement", "MARB": "marriage_bann",
            "MARC": "marriage_contract", "MARL": "marriage_license",
            "MARS": "marriage_settlement", "ANUL": "annulment",
            "DIVF": "divorce_filed"}
        self.assertEqual(gedcom.TAG_TO_EVENT, {**plugin, "_MILT": "military"})


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
        self.assertIn("plac_form", self.tree.header)
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


class SourceLines(unittest.TestCase):

    def _parse(self, text):
        path = ged(text)
        self.addCleanup(os.unlink, path)
        return gedcom.parse(path, warn=lambda m: None)

    def test_events_and_records_carry_their_line(self):
        tree = self._parse(SMALL)
        ind = tree.individuals["I1"]
        self.assertEqual(ind.line, 8)                    # "0 @I1@ INDI"
        birt = next(e for e in ind.events if e.tag == "BIRT")
        self.assertEqual(birt.line, 17)                  # "1 BIRT"
        self.assertEqual(tree.families["F1"].line, 50)

    def test_place_raw_survives_marriage_folding(self):
        tree = self._parse("""0 HEAD
1 GEDC
2 VERS 5.5.1
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Anna /Beispiel/
1 MARR
2 DATE 3 MAY 1900
2 PLAC Musterdorf
1 FAMS @F1@
0 @F1@ FAM
1 HUSB @I1@
1 MARR
2 DATE 3 MAY 1900
0 TRLR
""")
        ind_ev = next(e for e in tree.individuals["I1"].events if e.tag == "MARR")
        fam_ev = tree.families["F1"].events[0]
        self.assertEqual(fam_ev.place, "Musterdorf")
        self.assertEqual(fam_ev.place_raw, "")
        self.assertEqual(ind_ev.place_raw, "Musterdorf")

    def test_media_file(self):
        tree = self._parse("""0 HEAD
1 GEDC
2 VERS 5.5.1
1 CHAR UTF-8
0 @O1@ OBJE
1 FILE
0 @O2@ OBJE
1 FILE  a.jpg
0 @O3@ OBJE
1 _OID x
0 TRLR
""")
        self.assertEqual(tree.media["O1"].file, "")
        self.assertEqual(tree.media["O2"].file, "a.jpg")
        self.assertEqual(tree.media["O3"].file, "")


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

    def test_a_split_after_a_bare_text_line_is_rejoined(self):
        # MyHeritage writes multi-line TEXT with raw line breaks instead of
        # CONT, so the cut line can be a bare text line with no level; the
        # CONC still continues the TEXT value above it.
        body = (b"0 @I9@ INDI\r\n1 NAME Test /Person/\r\n1 SOUR @S1@\r\n"
                b"2 DATA\r\n3 TEXT Birth: 1871\r\n"
                b"Parents: \xd0\x97\xd0\xb0\xd0\xbf\xd0\xb8\xd1\r\n"
                b"4 CONC \x81\xd0\xb0\xd0\xbd\xd0\xbe\r\n0 TRLR\r\n")
        tree, messages, _ = self.parse_bytes(SPLIT_HEAD + body)
        self.assertIn("I9", tree.individuals)
        self.assertTrue(any("CONC" in m and "line(s): 13" in m for m in messages),
                        messages)

    def test_a_split_after_a_bare_line_under_an_unrelated_level_still_fails(self):
        body = (b"0 @I9@ INDI\r\n1 NAME Test /Person/\r\n1 SOUR @S1@\r\n"
                b"2 DATA\r\n3 TEXT Birth: 1871\r\n"
                b"Parents: \xd0\x97\xd0\xb0\xd0\xbf\xd0\xb8\xd1\r\n"
                b"2 CONC \x81\xd0\xb0\xd0\xbd\xd0\xbe\r\n0 TRLR\r\n")
        with self.assertRaises(UnicodeDecodeError):
            self.parse_bytes(SPLIT_HEAD + body)

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
