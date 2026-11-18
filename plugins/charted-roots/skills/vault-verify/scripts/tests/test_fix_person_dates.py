"""The one-off Person date repair: what it rewrites, and what it holds."""

from __future__ import annotations

import fix_person_dates as fix
from crsync import vault

from .helpers import FOLDERS, VaultCase, frontmatter


class Plan(VaultCase):

    def event(self, name, person, event_type, date):
        return self.write(f"{FOLDERS['events']}/{name}.md", frontmatter(
            cr_type="event", cr_id=f"e-{name[:3]}", event_type=event_type,
            date=date, persons=[f'"[[{person}]]"']))

    def plan(self):
        p = fix.plan(self.cfg)
        return ({(f.note.basename, f.key): f for f in p.fixes},
                {(n.basename, k): why for n, k, _, why in p.held})

    def test_respellings(self):
        self.person("A", cr_id="a-1", born="ABT 1804", died="1850-1858")
        self.person("B", cr_id="b-1", born='"25 Dez 1914"')
        fixes, held = self.plan()
        self.assertEqual(fixes[("A", "born")].new, "c. 1804")
        self.assertEqual(fixes[("A", "died")].new, "1850 to 1858")
        self.assertEqual(fixes[("B", "born")].new, "1914-12-25")
        self.assertEqual(held, {})

    def test_a_valid_date_is_left_alone(self):
        self.person("A", cr_id="a-1", born='"c. 1804"', died="1850")
        self.assertEqual(self.plan(), ({}, {}))

    def test_before_drops_only_when_the_event_keeps_it(self):
        self.person("Kept", cr_id="k-1", died="BEF 1909")
        self.event("Death of Kept", "Kept", "death", "BEF 1909")
        self.person("Bare", cr_id="b-1", died="BEF 1909")
        self.event("Death of Bare", "Bare", "death", "1909")
        self.person("Finer", cr_id="f-1", died="BEF 1889")
        self.event("Death of Finer", "Finer", "death", '"BEF 1889-02-01"')
        self.person("None", cr_id="n-1", died="BEF 1909")
        self.person("Other", cr_id="o-1", died="BEF 1909")
        self.event("Death of Other", "Other", "death", "1911")
        fixes, held = self.plan()
        self.assertEqual(fixes[("Kept", "died")].new, "1909")
        self.assertIsNone(fixes[("Kept", "died")].event)
        self.assertEqual(fixes[("Bare", "died")].event_date, "BEF 1909")
        self.assertEqual(fixes[("Finer", "died")].new, "1889-02-01")
        self.assertIn("0 death Events", held[("None", "died")])
        self.assertIn("1911", held[("Other", "died")])

    def test_an_unreadable_date_is_held(self):
        self.person("A", cr_id="a-1", born='"7 Aug 1905; 19 Jan 1929"')
        _, held = self.plan()
        self.assertIn(("A", "born"), held)

    def test_apply_writes_person_and_event(self):
        self.person("Bare", cr_id="b-1", died="BEF 1909")
        self.event("Death of Bare", "Bare", "death", "1909")
        p = fix.plan(self.cfg)
        f = p.fixes[0]
        f.note.set(f.key, f.new)
        f.event.set("date", f.event_date)
        f.note.save(), f.event.save()
        self.assertEqual(vault.parse(f.note.path).scalar("died"), "1909")
        self.assertEqual(vault.parse(f.event.path).scalar("date"), "BEF 1909")
