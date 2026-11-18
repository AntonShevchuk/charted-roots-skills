"""The decisions file.

It is the one place where a human overrides the tool's refusal to write, so a
malformed entry must be an error and never a silent "accept nothing" -- that
would revert every reviewed ruling on the next run without saying so.
"""

from __future__ import annotations

import json
import os
import unittest

from crsync import decisions

from .helpers import VaultCase, find_vault

ENTRY = {
    "external_id": "I1",
    "label": "Jürgen Muster",
    "accept_conflict": ["name"],
    "reason": "Grunwald without the umlaut is the correct form.",
    "decided_by": "user",
    "date": "2026-09-21",
}


class Loading(VaultCase):

    def put(self, *entries) -> None:
        self.write(os.path.join("History", decisions.FILENAME),
                   json.dumps({"decisions": list(entries)}, ensure_ascii=False))

    def load(self):
        return decisions.load(self.root)

    def test_a_missing_file_accepts_nothing(self):
        ruled = self.load()
        self.assertEqual(ruled.entries, [])
        self.assertEqual((ruled.coarsen_exempt, ruled.conflict_accepted), ({}, {}))
        self.assertEqual(ruled.rel_path,
                         os.path.join("History", decisions.FILENAME))

    def test_an_entry_becomes_a_field_set(self):
        self.put(ENTRY)
        ruled = self.load()
        self.assertEqual(ruled.conflict_accepted, {"I1": {"name"}})
        self.assertEqual(ruled.coarsen_exempt, {})
        self.assertEqual(ruled.counts(), (0, 1))
        self.assertEqual(len(ruled.entries), 1)

    def test_both_classes_in_one_entry(self):
        self.put({**ENTRY, "accept_coarsen": ["surnames"]})
        ruled = self.load()
        self.assertEqual(ruled.coarsen_exempt, {"I1": {"surnames"}})
        self.assertEqual(ruled.conflict_accepted, {"I1": {"name"}})

    def test_two_rulings_on_one_person_are_unioned_not_shadowed(self):
        # A dict keyed by external_id silently discards the earlier entry and
        # its reason. One ruling per occasion is the point.
        self.put(ENTRY, {**ENTRY, "accept_conflict": ["born"],
                         "reason": "Date corrected upstream."})
        ruled = self.load()
        self.assertEqual(ruled.conflict_accepted, {"I1": {"name", "born"}})
        self.assertEqual(ruled.repeated, ["I1"])
        self.assertEqual(len(ruled.entries), 2)


class Rejection(Loading):

    def assertRejected(self, needle, *entries):
        self.put(*entries)
        with self.assertRaises(decisions.DecisionsError) as caught:
            self.load()
        self.assertIn(needle, str(caught.exception))

    def test_a_ruling_with_no_reason(self):
        entry = {k: v for k, v in ENTRY.items() if k != "reason"}
        self.assertRejected("has no reason", entry)

    def test_a_blank_reason(self):
        self.assertRejected("has no reason", {**ENTRY, "reason": "  "})

    def test_an_entry_that_accepts_nothing(self):
        entry = {k: v for k, v in ENTRY.items() if k != "accept_conflict"}
        self.assertRejected("accepts nothing", entry)

    def test_a_misspelled_key(self):
        # `accept_conflicts` would read as an entry that accepts nothing, and
        # the ruling would vanish. Typos must not be silently ignored.
        entry = {k: v for k, v in ENTRY.items() if k != "accept_conflict"}
        entry["accept_conflicts"] = ["name"]
        self.assertRejected("unknown keys", entry)

    def test_a_field_list_that_is_a_string(self):
        self.assertRejected("must be a list",
                            {**ENTRY, "accept_conflict": "name"})

    def test_a_missing_external_id(self):
        entry = {k: v for k, v in ENTRY.items() if k != "external_id"}
        self.assertRejected("non-empty external_id", entry)

    def test_malformed_json(self):
        self.write(os.path.join("History", decisions.FILENAME), "{not json")
        with self.assertRaises(decisions.DecisionsError):
            self.load()

    def test_a_file_without_a_decisions_list(self):
        self.write(os.path.join("History", decisions.FILENAME),
                   json.dumps({"rulings": []}))
        with self.assertRaises(decisions.DecisionsError) as caught:
            self.load()
        self.assertIn('"decisions" list', str(caught.exception))


VAULT = find_vault(__file__)


@unittest.skipUnless(os.path.exists(os.path.join(VAULT, "History",
                                                 decisions.FILENAME)),
                     "no decisions file in this vault")
class RealFile(unittest.TestCase):

    def test_it_loads_and_every_entry_carries_a_reason(self):
        ruled = decisions.load(VAULT)
        self.assertTrue(ruled.entries)
        for entry in ruled.entries:
            self.assertTrue(entry.get("reason", "").strip(), entry)
            self.assertTrue(entry.get("label", "").strip(), entry)


if __name__ == "__main__":
    unittest.main()
