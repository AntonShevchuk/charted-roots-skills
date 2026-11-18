"""A place the export disagrees with.

The sync used to fill `place:` only where the vault had none, so an upstream
place correction vanished without a word -- and a date fill on the same Event
then paired the new date with the old place, a record neither side holds.
"""

from __future__ import annotations

import unittest

from crsync import apply as apply_mod
from crsync import decisions, events, gedcom, match, places, vault

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


if __name__ == "__main__":
    unittest.main()
