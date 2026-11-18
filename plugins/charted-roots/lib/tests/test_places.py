"""A place the export disagrees with.

The sync used to fill `place:` only where the vault had none, so an upstream
place correction vanished without a word -- and a date fill on the same Event
then paired the new date with the old place, a record neither side holds.
"""

from __future__ import annotations

import unittest

from crsync import apply as apply_mod
from crsync import create, decisions, events, gedcom, match, places, vault

from .helpers import FOLDERS, VaultCase, frontmatter, ged

GED = """0 HEAD
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Vera /Test/
1 SEX F
1 BIRT
2 DATE 29 Nov 1929
2 PLAC Aralsk, Kyzylorda, Kazakhstan
0 TRLR
"""


class PlaceCase(VaultCase):

    def setUp(self):
        super().setUp()
        self.place("Russia", title="Russia", full_name="Russia",
                   place_type="country")
        self.place("Smolensk Russia", title="Smolensk",
                   full_name="Smolensk, Russia", place_type="city",
                   parent_place='"[[Russia]]"')
        self.place("Kings County New York", title="Kings County",
                   full_name="Kings County", place_type="county")
        self.place("Berlin Berlin", title="Berlin", full_name="Berlin",
                   place_type="city", aliases=["Berlijn"])

    def place(self, name: str, **keys) -> None:
        keys.setdefault("cr_type", "place")
        keys.setdefault("cr_id", f"ppp-{len(name):03}-ppp-000")
        self.write(f"{FOLDERS['places']}/{name}.md", frontmatter(**keys))

    def index(self) -> places.Index:
        return places.load(self.cfg.places)


class Compare(PlaceCase):

    def test_the_same_place_agrees(self):
        self.assertEqual(self.index().compare(
            "[[Smolensk Russia]]", "Smolensk, Smolensk, Russia"), "")

    def test_another_place_is_a_conflict(self):
        self.assertEqual(self.index().compare(
            "[[Smolensk Russia]]", "Aralsk, Kyzylorda, Kazakhstan"), "conflict")

    def test_an_ancestor_is_a_coarsen(self):
        self.assertEqual(self.index().compare("[[Smolensk Russia]]", "Russia"),
                         "coarsen")

    def test_a_name_inside_the_other_agrees(self):
        self.assertEqual(self.index().compare(
            "[[Kings County New York]]", "Kings, New York, USA"), "")

    def test_an_alias_agrees(self):
        # adding the export's form to aliases: is how a variant is resolved
        self.assertEqual(self.index().compare("[[Berlin Berlin]]", "Berlijn"), "")

    def test_nothing_to_compare(self):
        idx = self.index()
        self.assertEqual(idx.compare("[[No Such Place]]", "Kazalinsk"), "")
        self.assertEqual(idx.compare("[[Smolensk Russia]]", ""), "")


class EventPlace(PlaceCase):

    def pair(self):
        tree = gedcom.parse(ged(GED))
        path = self.write(f"{FOLDERS['events']}/Birth of Vera Test.md", frontmatter(
            cr_type="event", cr_id="eee-000-eee-000", event_type="birth",
            date_precision="unknown", place='"[[Smolensk Russia]]"'))
        return events.Pair(vault_note=vault.parse(path),
                           ged_event=tree.individuals["I1"].events[0],
                           stage="positional")

    def test_a_differing_place_is_reported_as_a_conflict(self):
        changes = events.event_changes(self.pair(), self.index(), match.Change)
        place = [c for c in changes if c.field == "place"]
        self.assertEqual([(c.kind, c.old) for c in place],
                         [("conflict", "[[Smolensk Russia]]")])

    def test_apply_holds_the_place_and_says_so(self):
        pair = self.pair()
        written, held = apply_mod.apply_event_updates(
            events.EventMatch(pairs=[pair]), self.index(), dry=False)
        self.assertIn("place", [c.field for _, h in held for c in h])
        text = self.read(f"{FOLDERS['events']}/Birth of Vera Test.md")
        self.assertIn('place: "[[Smolensk Russia]]"', text)


class PersonPlace(PlaceCase):

    def plan(self, **keys):
        self.person("Vera Test", external_id="I1", sex="F", **keys)
        people = list(vault.iter_notes(self.cfg.people))
        return match.match_people(gedcom.parse(ged(GED)), people, self.root,
                                  place_index=self.index())

    def place_changes(self, plan) -> list:
        return [c for a in plan.of("person", "update") for c in a.changes
                if c.field in match.PERSON_PLACES]

    def test_a_differing_birth_place_is_a_conflict(self):
        changes = self.place_changes(self.plan(
            birth_place='"[[Smolensk Russia]]"'))
        self.assertEqual([(c.field, c.kind) for c in changes],
                         [("birth_place", "conflict")])

    def test_an_empty_birth_place_is_left_alone(self):
        self.assertEqual(self.place_changes(self.plan()), [])

    def test_no_ruling_writes_a_place_that_resolves_to_nothing(self):
        # Kazalinsk has no Place note here, so `new` is raw PLAC text; an
        # accepted conflict must not put that into birth_place:.
        plan = self.plan(birth_place='"[[Smolensk Russia]]"')
        act = plan.of("person", "update")[0]
        ruling = decisions.Decisions(
            path="x", entries=[{"external_id": "I1"}],
            conflict_accepted={"I1": {"birth_place"}})
        safe = apply_mod.safe_changes(act, external_id="I1", decisions=ruling)
        self.assertNotIn("birth_place", [c.field for c in safe])
        # the born fill beside it is still written
        self.assertIn("born", [c.field for c in safe])


class AliasCase(PlaceCase):

    def setUp(self):
        super().setUp()
        self.place("Poland", title="Poland", full_name="Poland",
                   place_type="country")
        self.place("Lower Silesian Voivodeship",
                   title="Lower Silesian Voivodeship",
                   full_name="Lower Silesian Voivodeship, Poland",
                   place_type="state", parent_place='"[[Poland]]"',
                   aliases=["Schlesien"])
        self.place("Wrocław", title="Wrocław",
                   full_name="Wrocław, Lower Silesian Voivodeship, Poland",
                   place_type="city",
                   parent_place='"[[Lower Silesian Voivodeship]]"',
                   aliases=["Breslau"])
        self.place("Hesse", title="Hesse", full_name="Hesse",
                   place_type="state", aliases=["Hessen"])
        self.place("Saxony", title="Saxony", full_name="Saxony",
                   place_type="state")
        self.place("Neustadt, Hesse", title="Neustadt",
                   full_name="Neustadt, Hesse", place_type="city",
                   parent_place='"[[Hesse]]"')
        self.place("Neustadt, Saxony", title="Neustadt",
                   full_name="Neustadt, Saxony", place_type="city",
                   parent_place='"[[Saxony]]"')

    def load(self, approved):
        return places.load(self.cfg.places, approved=approved)


class AliasFallback(AliasCase):

    def test_an_approved_historical_place_resolves(self):
        p = "Breslau, Schlesien, Preußen, Deutschland"
        self.assertEqual(self.load({places.key(p)}).find(p).basename, "Wrocław")

    def test_an_unapproved_one_does_not(self):
        p = "Breslau, Schlesien, Preußen, Deutschland"
        self.assertIsNone(self.load(set()).find(p))
        self.assertIsNone(self.load(None).find(p))

    def test_a_tie_is_no_link(self):
        p = "Neustadt, Preußen"
        self.assertIsNone(self.load({places.key(p)}).find(p))

    def test_the_better_supported_candidate_wins(self):
        p = "Neustadt, Hessen"
        hit = self.load({places.key(p)}).find(p)
        self.assertEqual(hit.basename, "Neustadt, Hesse")

    def test_plugin_lookups_still_come_first(self):
        p = "Wrocław, Lower Silesian Voivodeship, Poland"
        self.assertEqual(self.load(None).find(p).basename, "Wrocław")

    def test_historical_names_count_as_names(self):
        self.place("Lviv", title="Lviv", full_name="Lviv, Ukraine",
                   place_type="city", historical_names=["Lemberg"])
        p = "Lemberg, Galizien"
        self.assertEqual(self.load({places.key(p)}).find(p).basename, "Lviv")

    # -- the approved input may carry each string's target ----------------

    PLAC = "Breslau, Schlesien, Preußen, Deutschland"

    def later_rival(self):
        """A Place added after review that outscores Wrocław for PLAC."""
        self.place("Prussia", title="Prussia", full_name="Prussia",
                   place_type="state", aliases=["Preußen"])
        self.place("Silesia Province", title="Silesia Province",
                   full_name="Silesia Province, Prussia", place_type="state",
                   parent_place='"[[Prussia]]"', aliases=["Schlesien"])
        self.place("Breslau Bis", title="Breslau Bis",
                   full_name="Breslau Bis, Silesia Province, Prussia",
                   place_type="city",
                   parent_place='"[[Silesia Province]]"', aliases=["Breslau"])

    def test_a_target_dict_accepts_the_planned_place(self):
        idx = self.load({places.key(self.PLAC): "ppp-007-ppp-000"})
        self.assertEqual(idx.find(self.PLAC).basename, "Wrocław")

    def test_a_later_place_that_outscores_the_target_gives_no_link(self):
        self.later_rival()
        # the set form is unchanged: the rival wins
        self.assertEqual(self.load({places.key(self.PLAC)}).find(
            self.PLAC).basename, "Breslau Bis")
        idx = self.load({places.key(self.PLAC): "ppp-007-ppp-000"})
        self.assertIsNone(idx.find(self.PLAC))

    def test_a_target_without_a_cr_id_is_the_vault_relative_file(self):
        self.write(f"{FOLDERS['places']}/Hamburg.md", frontmatter(
            cr_type="place", title="Hamburg", full_name="Hamburg",
            place_type="city", aliases=["Hammaburg"]))
        p = "Hammaburg, Sachsen"
        rel = f"{FOLDERS['places']}/Hamburg.md"
        self.assertEqual(self.load({places.key(p): rel}).find(p).basename,
                         "Hamburg")
        self.assertIsNone(self.load({places.key(p): "Elsewhere/Hamburg.md"})
                          .find(p))
        # no identity yet (a target not applied): any hit is the wrong note
        self.assertIsNone(self.load({places.key(p): ""}).find(p))


class UnapprovedAliasNeverLinks(AliasCase):
    """No write path may link a PLAC through an alias the plan has not approved."""

    PLAC = "Breslau, Schlesien, Preußen, Deutschland"

    def tree(self) -> gedcom.Tree:
        return gedcom.parse(ged(
            "0 HEAD\n1 CHAR UTF-8\n"
            "0 @I1@ INDI\n1 NAME Vera /Test/\n1 SEX F\n"
            f"1 BIRT\n2 DATE 1829\n2 PLAC {self.PLAC}\n"
            "1 FAMS @F1@\n0 @I2@ INDI\n1 NAME Karl /Test/\n1 FAMS @F1@\n"
            "0 @F1@ FAM\n1 HUSB @I2@\n1 WIFE @I1@\n1 MARR\n2 DATE 1850\n"
            f"2 PLAC {self.PLAC}\n0 TRLR\n"))

    def approved(self):
        return {places.key(self.PLAC)}

    def event_place_changes(self, idx):
        path = self.write(f"{FOLDERS['events']}/Birth of Vera Test.md",
                          frontmatter(cr_type="event", cr_id="eee-000-eee-000",
                                      event_type="birth",
                                      date_precision="unknown"))
        pair = events.Pair(vault_note=vault.parse(path),
                           ged_event=self.tree().individuals["I1"].events[0],
                           stage="positional")
        return [c for c in events.event_changes(pair, idx, match.Change)
                if c.field == "place"]

    def test_the_event_place_fill(self):
        self.assertEqual(self.event_place_changes(self.load(set())), [])
        self.assertEqual(self.event_place_changes(self.load(None)), [])
        got = self.event_place_changes(self.load(self.approved()))
        self.assertEqual([c.new for c in got], ["[[Wrocław]]"])

    def marriage_rels(self, idx):
        self.person("Vera Test", cr_id="aaa-000-aaa-001", external_id="I1")
        self.person("Karl Test", cr_id="aaa-000-aaa-002", external_id="I2")
        notes = list(vault.iter_notes(self.cfg.people))
        rels, _ = create.relationship_updates(
            self.tree(), self.cfg, notes, [], idx)
        return rels

    def test_the_spouse_marriage_location(self):
        for idx in (self.load(set()), self.load(None)):
            rels = self.marriage_rels(idx)
            self.assertNotIn("spouse1_marriage_location", rels["I1"])
        rels = self.marriage_rels(self.load(self.approved()))
        self.assertEqual(rels["I1"]["spouse1_marriage_location"], "[[Wrocław]]")

    def fills(self, idx):
        self.person("Vera Test", external_id="I1", sex="F")
        note = next(vault.iter_notes(self.cfg.people))
        return match._place_fills(note, self.tree().individuals["I1"], idx)

    def test_the_person_back_fill(self):
        self.assertEqual(self.fills(self.load(set())), [])
        self.assertEqual(self.fills(self.load(None)), [])
        got = self.fills(self.load(self.approved()))
        self.assertEqual([(c.field, c.new) for c in got],
                         [("birth_place", "[[Wrocław]]")])


class Fold(unittest.TestCase):

    def test_accent_and_letter_variants_fold_together(self):
        self.assertEqual(places.fold("Wrocław"), places.fold("wroclaw"))
        self.assertEqual(places.fold("Preußen"), places.fold("PREUSSEN"))
        self.assertEqual(places.fold("Łódź"), places.fold("Lodz"))
        self.assertEqual(places.fold("Malmö"), "malmo")

    def test_a_different_spelling_does_not_fold(self):
        self.assertNotEqual(places.fold("Muenchen"), places.fold("München"))


class FoldedAliasMatch(PlaceCase):

    def setUp(self):
        super().setUp()
        self.place("Poland", title="Poland", full_name="Poland",
                   place_type="country", aliases=["Polska"])
        self.place("Lower Silesian Voivodeship",
                   title="Lower Silesian Voivodeship",
                   full_name="Lower Silesian Voivodeship, Poland",
                   place_type="state", parent_place='"[[Poland]]"',
                   aliases=["Dolnośląskie"])
        self.place("Wrocław", title="Wrocław",
                   full_name="Wrocław, Lower Silesian Voivodeship, Poland",
                   place_type="city",
                   parent_place='"[[Lower Silesian Voivodeship]]"')

    PLAC = "Wroclaw, Dolnoslaskie, Polska"

    def load(self, approved):
        return places.load(self.cfg.places, approved=approved)

    def test_an_approved_accent_free_form_resolves(self):
        idx = self.load({places.key(self.PLAC)})
        self.assertEqual(idx.find(self.PLAC).basename, "Wrocław")

    def test_unapproved_it_does_not(self):
        self.assertIsNone(self.load(set()).find(self.PLAC))
        self.assertIsNone(self.load(None).find(self.PLAC))

    def test_two_notes_folding_to_one_leaf_tie(self):
        self.place("Wroclaw", title="Wroclaw",
                   full_name="Wroclaw, Lower Silesian Voivodeship, Poland",
                   place_type="city",
                   parent_place='"[[Lower Silesian Voivodeship]]"')
        idx = self.load({places.key(self.PLAC)})
        self.assertIsNone(idx.find(self.PLAC))

    def test_the_plugin_lookup_stays_exact(self):
        self.place("Wrocław Pl", title="Wrocław Pl",
                   full_name="Wrocław, Poland", place_type="city")
        self.assertIsNone(self.load(None).find("Wroclaw, Poland"))


if __name__ == "__main__":
    unittest.main()
