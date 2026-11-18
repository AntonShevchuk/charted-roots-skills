"""The Person and Source joins, and the change classifier that gates writes.

`classify` decides what `--apply` is allowed to write, so its truth table is
the most load-bearing pure function in the tool: a `coarsen` misread as a
`refine` reverts curated work silently.
"""

from __future__ import annotations

import os
import unittest

from crsync import apply as apply_mod
from crsync import gedcom, match, places, vault

from .helpers import FOLDERS, VaultCase, frontmatter, ged

TWO_PEOPLE = """0 @I1@ INDI
1 NAME Jürgen /Muster/
2 GIVN Jürgen
2 SURN Muster
1 SEX M
1 BIRT
2 DATE 1 JUN 1824
0 @I2@ INDI
1 NAME Anna /Meyer/
1 SEX F
0 @S1@ SOUR
1 TITL Kirchenbuch Musterdorf
0 TRLR
"""


class Classify(unittest.TestCase):

    def test_truth_table(self):
        cases = [
            ("name", "", "Anna", match.FILL),
            ("name", None, "Anna", match.FILL),
            ("name", "von Example", "Von Example", match.CASE),
            ("name", "Amos", "Amos B Fairbourne", match.REFINE),
            ("name", "Amos B Fairbourne", "Amos", match.COARSEN),
            ("name", "Grünwald", "Grunwald", match.CONFLICT),
            ("born", "1884", "1884-05", match.REFINE),
            ("born", "1884-05", "1884", match.COARSEN),
            ("born", "ABT 1820", "1820", match.COARSEN),
            ("born", "c. 1820", "1820", match.COARSEN),
            ("born", "ABT 1820", "c. 1820", match.FORMAT),
            ("born", "BEF 1909", "1909", match.FORMAT),
            ("born", "1850-1858", "1850 to 1858", match.FORMAT),
            ("born", "25 Dez 1914", "1914-12-25", match.FORMAT),
            ("born", "c. 1820", "c. 1820-05", match.REFINE),
            ("born", "BEF 1909", "1909-05", match.REFINE),
            ("born", "1850 to 1858", "1850 to 1860", match.CONFLICT),
            ("born", "c. 1820", "C. 1820", match.FORMAT),
            ("date", "15 Okt 1795", "1795-10-15", match.FORMAT),
            ("date", "BEF 1909", "1909", match.COARSEN),
            ("born", "1822", "1821-10-30", match.CONFLICT),
            ("died", "1871", "1871", ""),
        ]
        for field, old, new, want in cases:
            with self.subTest(f"{field} {old!r} -> {new!r}"):
                self.assertEqual(match.classify(field, old, new), want)

    def test_a_list_is_compared_as_text(self):
        self.assertEqual(match.classify("surnames", ["Muster"], ["Muster"]), "")
        self.assertEqual(
            match.classify("surnames", ["Muster, Landwirt Musterdorf"], ["Muster"]),
            match.COARSEN)

    def test_change_classifies_itself(self):
        self.assertEqual(match.Change("born", "1884", "1884-05").kind, match.REFINE)
        self.assertEqual(match.Change("born", "1884", "1884-05",
                                      kind=match.FILL).kind, match.FILL)


class Projection(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path = ged(TWO_PEOPLE)
        cls.tree = gedcom.parse(cls.path)

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.path)

    def test_person_projection_takes_the_birth_date(self):
        p = match.person_projection(self.tree.individuals["I1"])
        self.assertEqual(p["name"], "Jürgen Muster")
        self.assertEqual(p["surnames"], ["Muster"])
        self.assertEqual(p["born"], "1824-06-01")
        self.assertEqual(p["sex"], "M")
        self.assertNotIn("died", p)

    def test_source_projection_maps_publ_to_repository(self):
        src = gedcom.SourceRec("S9", title="A Title", publisher="An Archive")
        self.assertEqual(match.source_projection(src),
                         {"title": "A Title", "repository": "An Archive"})


class MatchPeople(VaultCase):

    def setUp(self):
        super().setUp()
        self.ged = ged(TWO_PEOPLE)
        self.addCleanup(os.unlink, self.ged)
        self.tree = gedcom.parse(self.ged)

    def plan(self, adopt=False):
        people = list(vault.iter_notes(self.cfg.people))
        return match.match_people(self.tree, people, self.root, adopt=adopt)

    def test_external_id_joins_and_reports_the_delta(self):
        self.person("Jürgen Muster", external_id="I1", born="1824")
        plan = self.plan()
        updates = plan.of("person", "update")
        self.assertEqual([a.key for a in updates], ["I1"])
        fields = {c.field: c.kind for c in updates[0].changes}
        self.assertEqual(fields["born"], match.REFINE)
        self.assertEqual(fields["given_name"], match.FILL)

    def test_an_identical_note_is_a_plain_match(self):
        self.person("Jürgen Muster", external_id="I1", born="1824-06-01",
                    given_name="Jürgen", surnames=["Muster"], sex="M")
        plan = self.plan()
        self.assertEqual(len(plan.of("person", "match")), 1)
        self.assertEqual(plan.of("person", "update"), [])

    def test_an_unmatched_indi_is_a_creation(self):
        plan = self.plan()
        self.assertEqual(sorted(a.key for a in plan.of("person", "create")),
                         ["I1", "I2"])

    def test_a_vault_only_external_id_is_an_orphan_never_a_deletion(self):
        self.person("Someone Else", external_id="I999")
        plan = self.plan()
        orphans = plan.of("person", "orphan")
        self.assertEqual([a.key for a in orphans], ["I999"])
        self.assertIn("never deleted", orphans[0].note)

    def test_two_notes_sharing_an_external_id_are_ambiguous(self):
        self.person("Jürgen Muster", external_id="I1")
        self.person("Jurgen Muster", external_id="I1")
        self.assertEqual(len(self.plan().of("person", "ambiguous")), 1)

    def test_a_name_match_is_a_candidate_until_adopt_is_asked_for(self):
        self.person("Jürgen Muster", born="1824-06-01")
        plan = self.plan()
        self.assertEqual([a.key for a in plan.of("person", "candidate")], ["I1"])
        # I2 has no vault counterpart at all and is a creation either way;
        # what matters is that I1 is not one.
        self.assertEqual([a.key for a in plan.of("person", "create")], ["I2"])

    def test_adopt_writes_the_join_key(self):
        self.person("Jürgen Muster", born="1824-06-01")
        actions = self.plan(adopt=True).of("person", "adopt")
        self.assertEqual(len(actions), 1)
        changes = {c.field: c.new for c in actions[0].changes}
        self.assertEqual(changes["external_id"], "I1")
        self.assertEqual(changes["external_id_source"], "gedcom")


class MatchSources(VaultCase):

    def setUp(self):
        super().setUp()
        self.ged = ged(TWO_PEOPLE)
        self.addCleanup(os.unlink, self.ged)
        self.tree = gedcom.parse(self.ged)

    def plan(self):
        sources = list(vault.iter_notes(self.cfg.sources))
        return match.match_sources(self.tree, sources, self.root)

    def source(self, name, body="", **keys):
        keys.setdefault("cr_type", "source")
        keys.setdefault("title", name)
        from .helpers import FOLDERS, frontmatter
        return self.write(f"{FOLDERS['sources']}/{name}.md",
                          frontmatter(**keys) + body)

    def test_gedcom_id_joins(self):
        self.source("Kirchenbuch Musterdorf", gedcom_id="S1")
        self.assertEqual(len(self.plan().of("source", "match")), 1)

    def test_a_stripped_key_is_recovered_from_the_body(self):
        self.source("Kirchenbuch Musterdorf",
                    body="_Imported from GEDCOM source S1_\n")
        self.assertEqual([a.key for a in self.plan().of("source", "match")], ["S1"])


class AliasBackfill(VaultCase):

    def test_the_export_primary_becomes_an_alias(self):
        path = self.person("Jürgen Muster, Landwirt Musterdorf")
        note = vault.parse(path)
        ind = gedcom.Individual("I1", name="Jürgen Muster",
                                alt_names=["Jürgen Mustere"])
        self.assertEqual(match.alias_backfill(note, ind),
                         ["Jürgen Muster", "Jürgen Mustere"])

    def test_an_alias_equal_to_the_display_name_is_dropped(self):
        path = self.person("Jürgen Muster", aliases=["Jürgen Muster"])
        note = vault.parse(path)
        ind = gedcom.Individual("I1", name="Jürgen Muster")
        self.assertEqual(match.alias_backfill(note, ind), [])

    def test_nothing_to_add_returns_none(self):
        path = self.person("Jürgen Muster", aliases=["Jürgen Mustere"])
        note = vault.parse(path)
        ind = gedcom.Individual("I1", name="Jürgen Muster",
                                alt_names=["Jürgen Mustere"])
        self.assertIsNone(match.alias_backfill(note, ind))


class Variant(VaultCase):

    def test_the_maiden_married_pair_is_the_convention_not_a_conflict(self):
        # Ancestry's surname field holds the maiden name; the married form is
        # a separate NAME block. A note holding the other form must not be
        # reported as a disagreement.
        path = self.person("Anna Muster")
        note = vault.parse(path)
        projection = {"name": "Anna Meyer", "_alt_names": ["Anna Muster"]}
        self.assertEqual(match._compare(note, projection, ["name"]), [])

    def test_a_substring_alternate_is_flagged_variant(self):
        path = self.person("Anna Muster")
        note = vault.parse(path)
        projection = {"name": "Anna Meyer",
                      "_alt_names": ["Anna Muster, of Musterdorf"]}
        changes = match._compare(note, projection, ["name"])
        self.assertEqual([c.kind for c in changes], [match.VARIANT])


class PlaceFill(VaultCase):
    """An empty Person place field is filled once the PLAC resolves."""

    GED = """0 HEAD
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Vera /Test/
1 BIRT
2 PLAC Musterdorf
1 DEAT
2 PLAC Musterdorf
1 BURI
2 PLAC Musterdorf
0 TRLR
"""

    def setUp(self):
        super().setUp()
        self.write(f"{FOLDERS['places']}/Musterdorf.md", frontmatter(
            cr_type="place", cr_id="ppp-000-ppp-000", title="Musterdorf",
            full_name="Musterdorf", place_type="locality"))

    def note(self, **keys):
        path = self.person("Vera Test", external_id="I1", **keys)
        return vault.parse(path)

    def fills(self, note, text=None):
        ind = gedcom.parse(ged(text or self.GED)).individuals["I1"]
        return match._place_fills(note, ind, places.load(self.cfg.places))

    def test_an_empty_birth_place_is_filled_with_a_link(self):
        changes = self.fills(self.note())
        birth = [c for c in changes if c.field == "birth_place"]
        self.assertEqual([(c.old, c.new, c.kind) for c in birth],
                         [(None, "[[Musterdorf]]", match.FILL)])

    def test_burial_place_is_filled_too(self):
        self.assertIn("burial_place", [c.field for c in self.fills(self.note())])

    def test_a_held_place_is_not_filled(self):
        note = self.note(birth_place='"[[Elsewhere]]"')
        self.assertNotIn("birth_place", [c.field for c in self.fills(note)])

    def test_an_unresolved_plac_fills_nothing(self):
        text = self.GED.replace("Musterdorf", "Nowhereville")
        self.assertEqual(self.fills(self.note(), text), [])

    def test_the_person_places_stay_birth_and_death_only(self):
        self.assertEqual(set(match.PERSON_PLACES), {"birth_place", "death_place"})

    def test_the_field_pass_writes_a_quoted_link(self):
        self.note()
        people = list(vault.iter_notes(self.cfg.people))
        tree = gedcom.parse(ged(self.GED))
        plan = match.match_people(tree, people, self.root,
                                  place_index=places.load(self.cfg.places))
        by_path = {n.path: n for n in people}
        written, _, _ = apply_mod.apply_field_updates(
            plan, "person", by_path, self.root, dry=False)
        self.assertTrue(written)
        text = self.read(f"{FOLDERS['people']}/Vera Test.md")
        self.assertIn('burial_place: "[[Musterdorf]]"', text)
        self.assertIn('birth_place: "[[Musterdorf]]"', text)


if __name__ == "__main__":
    unittest.main()
