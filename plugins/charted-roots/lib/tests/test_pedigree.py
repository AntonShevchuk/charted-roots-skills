"""Ancestry's `_FREL` / `_MREL` pedigree on a family's children.

A stepmother arrives as the WIFE of the child's family with `2 _MREL step`
under the `1 CHIL`. Reading her as `mother` overwrites the birth mother and
lists the child among her `children`, and does so again on every sync.
"""

from __future__ import annotations

import unittest

from crsync import create, gedcom, vault

from .helpers import FOLDERS, VaultCase, frontmatter, ged

TREE = """0 HEAD
1 GEDC
2 VERS 5.5.1
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Arthur /Kramer/
0 @I2@ INDI
1 NAME Nidia /Vandermolen/
0 @I3@ INDI
1 NAME Richard /Kramer/
0 @I4@ INDI
1 NAME Emily /Kramer/
0 @I5@ INDI
1 NAME Hans /Kramer/
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
2 _MREL step
1 CHIL @I4@
1 CHIL @I5@
2 _FREL Adopted
2 _MREL Foster
0 @I6@ INDI
1 NAME Sadie /Alex/
0 @I7@ INDI
1 NAME John /Ratt/
0 @I8@ INDI
1 NAME Sarah /Andr/
0 @F2@ FAM
1 HUSB @I7@
1 CHIL @I6@
2 _FREL guardian
0 @F3@ FAM
1 WIFE @I8@
1 CHIL @I6@
2 _MREL guardian
0 TRLR
"""

NAMES = ("Arthur Kramer", "Nidia Vandermolen", "Richard Kramer", "Emily Kramer",
         "Hans Kramer", "Sadie Alex", "John Ratt", "Sarah Andr")


class Parse(unittest.TestCase):

    def setUp(self):
        self.fam = gedcom.parse(ged(TREE)).families["F1"]

    def test_pedigree_is_read_per_parent_and_lowercased(self):
        self.assertEqual(self.fam.relation("I3", "WIFE"), "step")
        self.assertEqual(self.fam.relation("I5", "HUSB"), "adopted")
        self.assertEqual(self.fam.relation("I5", "WIFE"), "foster")

    def test_no_marker_means_a_birth_child(self):
        self.assertEqual(self.fam.relation("I3", "HUSB"), "birth")
        self.assertEqual(self.fam.relation("I4", "WIFE"), "birth")


class Relationships(VaultCase):

    def setUp(self):
        super().setUp()
        for i, name in enumerate(NAMES, 1):
            self.person(name, cr_id=f"aaa-000-aaa-00{i}", external_id=f"I{i}")
        notes = list(vault.iter_notes(self.cfg.people))
        self.rels, _ = create.relationship_updates(
            gedcom.parse(ged(TREE)), self.cfg, notes, [])

    def test_a_step_mother_is_written_as_stepmother(self):
        richard = self.rels["I3"]
        self.assertNotIn("mother", richard)
        self.assertEqual(richard["stepmother"], "[[Nidia Vandermolen]]")
        self.assertEqual(richard["stepmother_id"], "aaa-000-aaa-002")
        self.assertEqual(richard["father"], "[[Arthur Kramer]]")

    def test_children_lists_hold_birth_children_only(self):
        self.assertEqual(self.rels["I2"]["children"], ["[[Emily Kramer]]"])
        self.assertEqual(self.rels["I2"]["children_id"], ["aaa-000-aaa-004"])
        self.assertEqual(self.rels["I1"]["children"],
                         ["[[Richard Kramer]]", "[[Emily Kramer]]"])

    def test_adopted_is_adoptive_and_an_unmodelled_pedigree_writes_nothing(self):
        hans = self.rels["I5"]
        self.assertEqual(hans["adoptive_father"], "[[Arthur Kramer]]")
        self.assertNotIn("father", hans)
        self.assertFalse({"mother", "stepmother", "adoptive_mother"} & set(hans))

    def test_a_guardian_couple_is_written_on_both_sides(self):
        sadie = self.rels["I6"]
        self.assertEqual(sadie["guardian"], ["[[John Ratt]]", "[[Sarah Andr]]"])
        self.assertEqual(sadie["guardian_id"], ["aaa-000-aaa-007", "aaa-000-aaa-008"])
        self.assertFalse({"father", "mother", "children"} & set(sadie))
        for g in ("I7", "I8"):
            self.assertEqual(self.rels[g]["ward"], ["[[Sadie Alex]]"])
            self.assertEqual(self.rels[g]["ward_id"], ["aaa-000-aaa-006"])
            self.assertNotIn("children", self.rels[g])


class GuardiansAlreadyInTheVault(VaultCase):

    def rels(self):
        notes = list(vault.iter_notes(self.cfg.people))
        rels, _ = create.relationship_updates(gedcom.parse(ged(TREE)), self.cfg, notes, [])
        return create.relationship_changes(rels, notes, set())

    def setUp(self):
        super().setUp()
        for i, name in enumerate(NAMES, 1):
            if name != "Sadie Alex":
                self.person(name, cr_id=f"aaa-000-aaa-00{i}", external_id=f"I{i}")

    def test_a_vault_guardian_is_kept_and_the_missing_one_added(self):
        self.person("Sadie Alex", cr_id="aaa-000-aaa-006", external_id="I6",
                    guardian=['"[[Other Guardian]]"'], guardian_id=["ooo-000-ooo-000"])
        sadie = self.rels()["I6"]
        self.assertEqual(sadie["guardian"], ["[[Other Guardian]]", "[[John Ratt]]",
                                             "[[Sarah Andr]]"])
        self.assertEqual(sadie["guardian_id"], ["ooo-000-ooo-000", "aaa-000-aaa-007",
                                                "aaa-000-aaa-008"])

    def test_links_already_present_are_not_rewritten(self):
        self.person("Sadie Alex", cr_id="aaa-000-aaa-006", external_id="I6",
                    guardian=['"[[Sarah Andr]]"', '"[[John Ratt]]"'],
                    guardian_id=["aaa-000-aaa-008", "aaa-000-aaa-007"])
        self.assertNotIn("guardian", self.rels().get("I6", {}))


MARRIED = """0 HEAD
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Karl /Ehe/
0 @I2@ INDI
1 NAME Anna /Ehe/
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 MARR
2 DATE 12 MAY 1880
2 PLAC Berlin, Brandenburg
0 @I3@ INDI
1 NAME Otto /Fern/
0 @I4@ INDI
1 NAME Ida /Fern/
0 @F2@ FAM
1 HUSB @I3@
1 WIFE @I4@
1 MARR
2 DATE 1890
2 PLAC Nowhere, Atlantis
0 TRLR
"""


class MarriageLocation(VaultCase):

    def setUp(self):
        super().setUp()
        self.write(f"{FOLDERS['places']}/Berlin Brandenburg.md", frontmatter(
            cr_type="place", cr_id="ppp-000-ppp-001", title="Berlin",
            full_name='"Berlin, Brandenburg"'))

    def rels(self, **anna):
        self.person("Karl Ehe", cr_id="aaa-000-aaa-001", external_id="I1")
        self.person("Anna Ehe", cr_id="aaa-000-aaa-002", external_id="I2", **anna)
        self.person("Otto Fern", cr_id="aaa-000-aaa-003", external_id="I3")
        self.person("Ida Fern", cr_id="aaa-000-aaa-004", external_id="I4")
        notes = list(vault.iter_notes(self.cfg.people))
        rels, _ = create.relationship_updates(gedcom.parse(ged(MARRIED)), self.cfg, notes, [])
        return rels

    def test_a_resolved_place_is_written_as_a_link(self):
        rels = self.rels()
        self.assertEqual(rels["I1"]["spouse1_marriage_location"], "[[Berlin Brandenburg]]")

    def test_an_unresolved_place_is_not_written_as_text(self):
        rels = self.rels()
        self.assertNotIn("spouse1_marriage_location", rels["I3"])
        self.assertEqual(rels["I3"]["spouse1_marriage_date"], "1890")

    def test_a_link_already_in_the_vault_is_kept(self):
        rels = self.rels(spouse1='"[[Karl Ehe]]"', spouse1_id="aaa-000-aaa-001",
                         spouse1_marriage_location='"[[Spandau]]"')
        self.assertNotIn("spouse1_marriage_location", rels["I2"])

    def test_plain_text_in_the_vault_is_replaced_by_the_link(self):
        rels = self.rels(spouse1='"[[Karl Ehe]]"', spouse1_id="aaa-000-aaa-001",
                         spouse1_marriage_location='"Berlin, Brandenburg"')
        self.assertEqual(rels["I2"]["spouse1_marriage_location"], "[[Berlin Brandenburg]]")


if __name__ == "__main__":
    unittest.main()
