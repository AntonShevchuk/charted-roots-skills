"""The reviewed places plan file: its model, load and save."""

from __future__ import annotations

import os
import unittest

from crsync import placeplan, places
from crsync.placeplan import PlacEntry, Plan, PlannedPlace

from .helpers import VaultCase


def _plan() -> Plan:
    return Plan(
        places={
            "wroclaw": PlannedPlace(
                key="wroclaw", title="Wrocław", place_type="city",
                parent="lower-silesia", aliases=["Breslau"],
                reason="Polish since 1945", status="approved",
                cr_id="abc-123", file="Charted Roots/Places/Wrocław.md"),
            "lower-silesia": PlannedPlace(
                key="lower-silesia", title="Lower Silesia", place_type="region"),
        },
        plac={
            "Breslau, Schlesien": PlacEntry(
                plac="Breslau, Schlesien", count=38, place="wroclaw",
                status="approved"),
            "Nowhere": PlacEntry(plac="Nowhere", count=2, not_place="a note"),
            "Lost": PlacEntry(plac="Lost", unidentified="no trace"),
        })


class PlanFile(VaultCase):
    def test_missing_file_is_an_empty_plan(self):
        plan = placeplan.load(self.root)
        self.assertEqual(plan.places, {})
        self.assertEqual(plan.plac, {})

    def test_round_trip_keeps_every_field(self):
        plan = _plan()
        placeplan.save(self.root, plan)
        self.assertEqual(placeplan.load(self.root), plan)

    def test_invalid_json_raises_plan_error_and_leaves_the_file(self):
        path = self.write(placeplan.PLAN_PATH, "{not json")
        with open(path, "rb") as fh:
            before = fh.read()
        with self.assertRaises(placeplan.PlanError):
            placeplan.load(self.root)
        with open(path, "rb") as fh:
            self.assertEqual(fh.read(), before)

    def test_wrong_shape_raises_plan_error(self):
        self.write(placeplan.PLAN_PATH, "[1, 2]")
        with self.assertRaises(placeplan.PlanError):
            placeplan.load(self.root)

    def test_save_creates_history_folder(self):
        placeplan.save(self.root, Plan())
        self.assertTrue(
            os.path.isfile(os.path.join(self.root, placeplan.PLAN_PATH)))


class Approved(VaultCase):
    def _set(self, plac_status, place_status, **extra):
        plan = Plan(
            places={"p": PlannedPlace(key="p", title="P", place_type="city",
                                      status=place_status)},
            plac={"Old, Name": PlacEntry(plac="Old, Name", place="p",
                                         status=plac_status, **extra)})
        return placeplan.approved_placs(plan)

    def test_approved_needs_both_sides(self):
        k = places.key("Old, Name")
        self.assertEqual(self._set("approved", "proposed"), set())
        self.assertEqual(self._set("proposed", "created"), set())
        self.assertEqual(self._set("approved", "approved"), {k})
        self.assertEqual(self._set("approved", "created"), {k})

    def test_unidentified_and_not_place_are_excluded(self):
        self.assertEqual(
            self._set("approved", "approved", unidentified="x"), set())
        self.assertEqual(
            self._set("approved", "approved", not_place="x"), set())

    def test_unknown_place_is_excluded(self):
        plan = Plan(plac={"A": PlacEntry(plac="A", place="gone",
                                         status="approved")})
        self.assertEqual(placeplan.approved_placs(plan), set())


if __name__ == "__main__":
    unittest.main()
