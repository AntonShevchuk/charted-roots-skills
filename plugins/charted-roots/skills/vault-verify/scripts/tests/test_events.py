"""Pairing vault Events with GEDCOM blocks.

Order is not evidence. Residences are curated in the vault -- dates widened
to ranges, occurrences added from other documents -- so zipping the two
sides in file order paired each Event with another occurrence, and the date
fill then wrote that occurrence's date onto it.
"""

from __future__ import annotations

import unittest

from crsync import events, gedcom, places, vault

from .helpers import FOLDERS, VaultCase, frontmatter, ged


def indi(*blocks: str) -> str:
    return ("0 HEAD\n1 CHAR UTF-8\n0 @I1@ INDI\n1 NAME Jeanne /Test/\n1 SEX F\n"
            + "".join(blocks) + "0 TRLR\n")


def block(tag: str, date: str = "", place: str = "") -> str:
    out = f"1 {tag}\n"
    if date:
        out += f"2 DATE {date}\n"
    if place:
        out += f"2 PLAC {place}\n"
    return out


class MatchCase(VaultCase):

    def setUp(self):
        super().setUp()
        for i, (name, title) in enumerate((("Springfield Florida", "Springfield"),
                                           ("Fairview Virginia", "Fairview"),
                                           ("Brookfield Virginia", "Brookfield"),
                                           ("Izium Kharkiv", "Izium"))):
            self.write(f"{FOLDERS['places']}/{name}.md", frontmatter(
                cr_type="place", cr_id=f"ppp-{i:03}-ppp-000", title=title,
                full_name=title, place_type="city"))
        self.person("Jeanne Test", external_id="I1")
        self.n = 0

    def event(self, name: str, event_type: str, date: str = "", place: str = "") -> None:
        self.n += 1
        keys = dict(cr_type="event", cr_id=f"eee-{self.n:03}-eee-000",
                    event_type=event_type, persons=['"[[Jeanne Test]]"'])
        if date:
            keys["date"] = date
        if place:
            keys["place"] = f'"[[{place}]]"'
        self.write(f"{FOLDERS['events']}/{name}.md", frontmatter(**keys))

    def match(self, text: str) -> events.EventMatch:
        return events.match_events(
            gedcom.parse(ged(text)), list(vault.iter_notes(self.cfg.events)),
            list(vault.iter_notes(self.cfg.people)),
            places.load(self.cfg.places), self.root)

    def pairs(self, m) -> dict:
        """vault basename -> (stage, GEDCOM date, GEDCOM place)"""
        return {p.vault_note.basename: (p.stage, p.ged_event.date, p.ged_event.place)
                for p in m.pairs}

    def unkeyed(self, m) -> list:
        return sorted(n.basename for n, _ in m.unkeyed)


class Corroborated(MatchCase):

    def test_date_and_place_beat_file_order(self):
        # the vault's order is the reverse of the export's
        self.event("Residence of Jeanne Test", "residence", "1999-2001", "Fairview Virginia")
        self.event("Residence of Jeanne Test-1", "residence", "1995-2020", "Brookfield Virginia")
        m = self.match(indi(block("RESI", "1995", "Brookfield, Virginia, USA"),
                            block("RESI", "1999", "Fairview, Virginia, USA")))
        self.assertEqual(self.pairs(m), {
            "Residence of Jeanne Test": ("corroborated", "1999", "Fairview, Virginia, USA"),
            "Residence of Jeanne Test-1": ("corroborated", "1995", "Brookfield, Virginia, USA"),
        })

    def test_a_same_date_at_another_place_yields_to_the_better_pair(self):
        # Content alone pairs the 1999 Springfield Event with the export's 1999
        # Fairview block; the vault's 1999-2001 Fairview Event is the one.
        self.event("Residence of Jeanne Test", "residence", "1999", "Springfield Florida")
        self.event("Residence of Jeanne Test-1", "residence", "1999-2001", "Fairview Virginia")
        m = self.match(indi(block("RESI", "1999", "Fairview, Virginia, USA")))
        self.assertEqual(self.pairs(m), {
            "Residence of Jeanne Test-1": ("corroborated", "1999", "Fairview, Virginia, USA")})
        self.assertEqual(self.unkeyed(m), ["Residence of Jeanne Test"])

    def test_a_same_date_with_no_better_pair_is_still_content(self):
        # a place written in another script is not another occurrence
        self.event("Military service of Jeanne Test", "military", "1941", "Izium Kharkiv")
        m = self.match(indi(block("_MILT", "1941",
                                  "Купянск, Купянский р-н, Харьковская обл.")))
        self.assertEqual(self.pairs(m), {"Military service of Jeanne Test": (
            "content", "1941", "Купянск, Купянский р-н, Харьковская обл.")})


    def test_an_undated_event_pairs_on_a_unique_place(self):
        # counts differ, so order cannot pair it; the place is the evidence
        self.event("Residence of Jeanne Test", "residence", place="Brookfield Virginia")
        m = self.match(indi(block("RESI", "1899", "Brookfield, Virginia, USA"),
                            block("RESI", "1908", "Springfield, Florida, USA")))
        self.assertEqual(self.pairs(m), {"Residence of Jeanne Test": (
            "corroborated", "1899", "Brookfield, Virginia, USA")})

    def test_an_undated_event_with_two_candidates_stays_unpaired(self):
        self.event("Residence of Jeanne Test", "residence", place="Springfield Florida")
        m = self.match(indi(block("RESI", "1988", "Springfield, Florida, USA"),
                            block("RESI", "1991", "Springfield, Florida, USA")))
        self.assertEqual(m.pairs, [])


class Positional(MatchCase):

    def test_contradicting_dates_are_left_unpaired(self):
        self.event("Residence of Jeanne Test", "residence", "1881")
        self.event("Residence of Jeanne Test-1", "residence", "1953")
        m = self.match(indi(block("RESI", "1902"), block("RESI", "1958")))
        self.assertEqual(m.pairs, [])
        self.assertEqual(len(self.unkeyed(m)), 2)
        self.assertEqual(len(m.uncreated), 2)

    def test_undated_entries_still_pair_by_order(self):
        self.event("Residence of Jeanne Test", "residence")
        self.event("Residence of Jeanne Test-1", "residence")
        m = self.match(indi(block("RESI", place="Springfield, Florida, USA"),
                            block("RESI", place="Fairview, Virginia, USA")))
        self.assertEqual({s for s, _, _ in self.pairs(m).values()}, {"positional"})

    def test_an_event_had_once_pairs_despite_the_date(self):
        # One birth each side is the same birth; the year difference is a
        # conflict to report, not a second birth to create.
        self.event("Birth of Jeanne Test", "birth", "1822")
        m = self.match(indi(block("BIRT", "1821-10-30")))
        self.assertEqual(self.pairs(m),
                         {"Birth of Jeanne Test": ("positional", "1821-10-30", "")})
        self.assertEqual(m.uncreated, [])


class Scores(unittest.TestCase):

    def test_date_scores(self):
        self.assertEqual(events._date_score("1999", "1999"), 3)
        self.assertEqual(events._date_score("1995-2001", "1999"), 2)
        self.assertEqual(events._date_score("2002-02-18", "2002"), 2)
        self.assertEqual(events._date_score("BEF 1818", "1810"), 2)
        self.assertEqual(events._date_score("", "1999"), 0)
        self.assertIsNone(events._date_score("1881", "1902"))


if __name__ == "__main__":
    unittest.main()
