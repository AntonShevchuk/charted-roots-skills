"""A second run after `--apply --create` must plan nothing.

Each case here is one the 2026-09-24 run left unsettled: Events it had just
created that the next dry run could not pair, and one it wrongly held back.
"""

from __future__ import annotations

import os
import unittest

from crsync import citations, create, events, gedcom, match, places, vault

from .helpers import FOLDERS, ged
from .test_events import MatchCase, block, indi


class AboutDates(MatchCase):

    def test_an_abt_block_pairs_with_the_event_created_from_it(self):
        # The creator writes `ABT 1876` as `date: 1876` + `estimated`.
        self.event("Residence of Jeanne Test", "residence", "1876")
        self.event("Residence of Jeanne Test-1", "residence", "1886")
        self.event("Residence of Jeanne Test-2", "residence", "1890")
        m = self.match(indi(block("RESI", "ABT 1876"), block("RESI", "1880"),
                            block("RESI", "ABT 1886"), block("RESI", "ABT 1890")))
        self.assertEqual({k: v[0] for k, v in self.pairs(m).items()}, {
            "Residence of Jeanne Test": "content",
            "Residence of Jeanne Test-1": "content",
            "Residence of Jeanne Test-2": "content"})
        self.assertEqual([e.date for e in m.uncreated], ["1880"])


class IdenticalTies(MatchCase):

    def test_identical_undated_notes_pair_with_as_many_blocks(self):
        # A fourth, dated Event elsewhere keeps the counts unequal, so the
        # positional stage cannot pair them either.
        for i in ("", "-1", "-2"):
            self.event(f"Residence of Jeanne Test{i}", "residence", place="Springfield Florida")
        self.event("Residence of Jeanne Test-3", "residence", "1917", "Fairview Virginia")
        m = self.match(indi(block("RESI", place="Springfield, Florida, USA"),
                            block("RESI", place="Springfield, Florida"),
                            block("RESI", place="Springfield, Florida, USA")))
        self.assertEqual(len(m.pairs), 3)
        self.assertEqual(m.uncreated, [])
        self.assertEqual(len(m.arbitrary), 3)
        self.assertEqual(self.unkeyed(m), ["Residence of Jeanne Test-3"])

    def test_distinguishable_notes_still_refuse_a_tie(self):
        self.event("Residence of Jeanne Test", "residence", place="Springfield Florida")
        self.event("Residence of Jeanne Test-1", "residence", "1988", "Springfield Florida")
        m = self.match(indi(block("RESI", place="Springfield, Florida, USA"),
                            block("RESI", place="Springfield, Florida, USA")))
        self.assertEqual([p.stage for p in m.pairs if p.stage == "corroborated"], [])


def couple(indi_marr: str, fam_marr: str) -> str:
    return ("0 HEAD\n1 CHAR UTF-8\n"
            "0 @I1@ INDI\n1 NAME Hans /Test/\n1 SEX M\n1 FAMS @F1@\n"
            "0 @I2@ INDI\n1 NAME Elsa /Test/\n1 SEX F\n1 FAMS @F1@\n" + indi_marr +
            "0 @F1@ FAM\n1 HUSB @I1@\n1 WIFE @I2@\n" + fam_marr + "0 TRLR\n")


class FoldedMarriages(unittest.TestCase):

    def test_an_individual_marriage_repeating_the_family_one_folds(self):
        tree = gedcom.parse(ged(couple(block("MARR", "5 Apr 1898", "Spandau"),
                                       block("MARR", "5 Apr 1898"))))
        (ind_ev, fam_ev), = tree.folded
        self.assertTrue(ind_ev.folded)
        self.assertEqual(fam_ev.place, "Spandau")
        # still on the person, so its citations resolve
        self.assertIn(ind_ev, tree.individuals["I2"].events)

    def test_a_year_folds_into_the_full_date(self):
        tree = gedcom.parse(ged(couple(block("MARR", "1818"),
                                       block("MARR", "8 Feb 1818", "Beeskow"))))
        self.assertEqual(len(tree.folded), 1)
        self.assertEqual(tree.folded[0][1].place, "Beeskow")

    def test_an_undated_individual_marriage_is_left_alone(self):
        tree = gedcom.parse(ged(couple(block("MARR", place="New York"),
                                       block("MARR", "21 Sep 1899"))))
        self.assertEqual(tree.folded, [])

    def test_a_folded_marriage_is_never_created(self):
        tree = gedcom.parse(ged(couple(block("MARR", "5 Apr 1898", "Spandau"),
                                       block("MARR", "5 Apr 1898"))))
        m = events.match_events(tree, [], [], places.Index([]), "")
        self.assertEqual([e.tag + e.owner for e in m.uncreated], ["MARRF1"])


class CreationCap(MatchCase):

    def plan(self, text: str) -> create.CreationPlan:
        tree = gedcom.parse(ged(text))
        people = list(vault.iter_notes(self.cfg.people))
        evn = list(vault.iter_notes(self.cfg.events))
        pidx = places.load(self.cfg.places)
        return create.plan_creation(
            tree, self.cfg, pidx,
            match.match_people(tree, people, self.root, place_index=pidx),
            match.match_sources(tree, [], self.root),
            events.match_events(tree, evn, people, pidx, self.root),
            citations.match_citations(tree, [], people, [], self.root),
            people + evn + pidx.notes)

    def test_a_paired_event_does_not_stand_in_for_another_block(self):
        # Two 1993 residences upstream; the vault's one is Riverton's.
        self.event("Residence of Jeanne Test", "residence", "1993", "Fairview Virginia")
        cplan = self.plan(indi(block("RESI", "1993", "Fairview, Virginia, USA"),
                               block("RESI", "1993", "Springfield, Florida, USA")))
        self.assertEqual(len(cplan.events), 1)
        self.assertEqual(cplan.already_present, [])

    def test_an_unpaired_event_still_caps_creation(self):
        for i in ("", "-1"):
            self.event(f"Residence of Jeanne Test{i}", "residence", place="Springfield Florida")
        cplan = self.plan(indi(block("RESI", place="Springfield, Florida, USA"),
                               block("RESI", place="Fairview, Virginia, USA"),
                               block("RESI", place="Fairview, Virginia, USA")))
        self.assertEqual(len(cplan.events), 1)

    def test_a_new_event_takes_the_importers_dash_suffix(self):
        self.event("Residence of Jeanne Test", "residence", "1988")
        cplan = self.plan(indi(block("RESI", "1988"), block("RESI", "1991")))
        self.assertEqual([os.path.basename(n.path) for n in cplan.events],
                         ["Residence of Jeanne Test-1.md"])


class UniquePath(unittest.TestCase):

    def test_the_default_suffix_is_the_plugins(self):
        used = {os.path.join("P", "X.md")}
        self.assertEqual(create.unique_path("P", "X", used), os.path.join("P", "X 1.md"))

    def test_events_take_a_dash(self):
        used = {os.path.join("E", "X.md"), os.path.join("E", "X-1.md")}
        self.assertEqual(create.unique_path("E", "X", used, sep="-"),
                         os.path.join("E", "X-2.md"))


class CitationNames(unittest.TestCase):

    def test_a_long_source_title_keeps_person_and_fact(self):
        src = "ARCHION Berlin Brandenburg → Landeskirchliches Archiv der Evangelischen Kirche Berlin-Brandenburg-schlesische Oberlausitz"
        stem = create.citation_stem(src, "Anna Test", "birth_date")
        self.assertTrue(stem.endswith(" - Anna Test birth_date"))
        self.assertIn(src, stem)
        self.assertGreater(len(stem), 100)

    def test_a_name_over_the_limit_abbreviates_before_cutting(self):
        src = ("ARCHION Berlin Brandenburg → Landeskirchliches Archiv der Evangelischen "
               "Kirche Berlin-Brandenburg-schlesische Oberlausitz → Kirchenkreis "
               "Musterhagen → Musterhagen, Peter-Paul Deutsche Kirche → Taufen, "
               "Bestattungen 1868-1879")
        stem = create.citation_stem(src, "Anna Elisabeth Test", "birth_date")
        self.assertIn("→ LKA der Ev. Kirche", stem)
        self.assertIn("→ Kirchenkreis Musterhagen →", stem)   # first step was enough
        self.assertTrue(stem.endswith("Bestattungen 1868-1879 - Anna Elisabeth Test birth_date"))
        stem = create.citation_stem(src, "Arthur Emil Von Exampleberg", "baptism_date")
        self.assertIn("→ KK Musterhagen →", stem)
        self.assertLessEqual(len(stem.encode()) + 3, 255)

    def test_a_name_that_fits_keeps_its_source_whole(self):
        src = "ARCHION Berlin Brandenburg → Landeskirchliches Archiv der Evangelischen Kirche"
        self.assertIn(src, create.citation_stem(src, "Anna Test", "birth_date"))

    def test_only_an_unabbreviable_name_is_cut(self):
        stem = create.citation_stem("Ü" * 200, "Anna Test", "death_date")
        self.assertLessEqual(len(stem.encode()) + 3, 255)
        self.assertTrue(stem.endswith("… - Anna Test death_date"))

    def test_a_collision_numbers_after_the_fact(self):
        used = {os.path.join("C", "Citation - S - A birth_date.md")}
        self.assertEqual(create.citation_path("C", "S", "A", "birth_date", used),
                         os.path.join("C", "Citation - S - A birth_date 1.md"))

    def test_a_collision_suffix_still_fits(self):
        used = set()
        first = create.citation_path("C", "Ü" * 200, "A", "birth_date", used)
        second = create.citation_path("C", "Ü" * 200, "A", "birth_date", used)
        self.assertTrue(second.endswith(" birth_date 1.md"))
        self.assertLessEqual(len(os.path.basename(second).encode()), 255)
        self.assertNotEqual(first, second)

class SourceNames(unittest.TestCase):

    def test_a_source_keeps_its_whole_title(self):
        title = "ARCHION Berlin Brandenburg → Landeskirchliches Archiv der Evangelischen Kirche Berlin-Brandenburg-schlesische Oberlausitz → Taufen 1868-1879"
        path = create.unique_path("S", title, set(), cap=None)
        self.assertEqual(path, os.path.join("S", title + ".md"))

    def test_a_repeated_title_numbers_after_the_whole_title(self):
        title = "X" * 150
        used = {os.path.join("S", title + ".md")}
        self.assertEqual(create.unique_path("S", title, used, cap=None),
                         os.path.join("S", title + " 1.md"))


class EscapedTitles(unittest.TestCase):

    def test_an_escaped_separator_becomes_an_arrow(self):
        self.assertEqual(create.sanitise("ARCHION Berlin &gt; Taufen 1818", None),
                         "ARCHION Berlin → Taufen 1818")

    def test_an_escaped_ampersand_is_plain(self):
        self.assertEqual(create.sanitise("Unterhaltungs- &amp; Anzeigeblatt", None),
                         "Unterhaltungs- & Anzeigeblatt")

    def test_a_citation_name_follows_its_source(self):
        self.assertEqual(create.citation_stem("ARCHION Berlin &gt; Taufen", "Anna Test", "birth_date"),
                         "Citation - ARCHION Berlin → Taufen - Anna Test birth_date")


if __name__ == "__main__":
    unittest.main()
