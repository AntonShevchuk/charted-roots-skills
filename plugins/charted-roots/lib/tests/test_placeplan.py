"""The reviewed places plan file: its model, load and save."""

from __future__ import annotations

import os
import unittest

from collections import Counter

from crsync import gedcom, placeplan, places, vault
from crsync.placeplan import PlacEntry, Plan, PlannedPlace

from .helpers import FOLDERS, VaultCase, frontmatter, ged


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


class Extract(VaultCase):
    GED = """0 HEAD
0 @I1@ INDI
1 NAME Ana /Test/
1 BIRT
2 PLAC Breslau, Schlesien
1 DEAT
2 PLAC 3rd Regiment, Berlin
1 FAMS @F1@
1 MARR
2 DATE 1 JAN 1900
2 PLAC Posen
0 @I2@ INDI
1 NAME Bo /Test/
1 BIRT
2 PLAC Breslau, Schlesien
1 FAMS @F1@
0 @F1@ FAM
1 HUSB @I2@
1 WIFE @I1@
1 MARR
2 DATE 1 JAN 1900
2 PLAC Posen
0 TRLR
"""

    def _index(self, *notes):
        for name, keys in notes:
            keys.setdefault("cr_type", "place")
            self.write(f"{FOLDERS['places']}/{name}.md", frontmatter(**keys))
        return places.load(os.path.join(self.root, FOLDERS["places"]))

    def _counts(self):
        return placeplan.count_placs(gedcom.parse(ged(self.GED)))

    def test_counts_individual_and_family_places(self):
        c = self._counts()
        self.assertEqual(c["Breslau, Schlesien"], 2)
        self.assertEqual(c["3rd Regiment, Berlin"], 1)

    def test_a_shared_family_event_is_counted_once(self):
        # The FAM MARR and the spouse's repeated MARR are one marriage.
        self.assertEqual(self._counts()["Posen"], 1)

    def test_a_new_string_is_added_as_proposed(self):
        plan = Plan()
        res = placeplan.extract(plan, Counter({"Posen": 3}), self._index())
        self.assertEqual(res.added, ["Posen"])
        e = plan.plac["Posen"]
        self.assertEqual((e.count, e.status, e.place), (3, "proposed", ""))

    def test_a_non_place_is_marked(self):
        plan = Plan()
        placeplan.extract(plan, Counter({"3rd Regiment, Berlin": 1}),
                          self._index())
        self.assertEqual(plan.plac["3rd Regiment, Berlin"].not_place, "regiment")

    def test_a_rerun_keeps_reviewed_entries(self):
        plan = Plan(plac={"Posen": PlacEntry(
            plac="Posen", count=1, place="poznan", unidentified="u",
            status="approved")})
        res = placeplan.extract(plan, Counter({"Posen": 5}), self._index())
        e = plan.plac["Posen"]
        self.assertEqual((e.count, e.place, e.unidentified, e.status),
                         (5, "poznan", "u", "approved"))
        self.assertEqual((res.added, res.updated), ([], ["Posen"]))

    def test_a_string_gone_from_the_export_is_kept(self):
        plan = Plan(plac={"Old": PlacEntry(plac="Old", count=4)})
        res = placeplan.extract(plan, Counter(), self._index())
        self.assertEqual(plan.plac["Old"].count, 0)
        self.assertEqual(res.updated, ["Old"])

    def test_an_already_resolving_string_is_recorded_as_existing(self):
        index = self._index(
            ("Poland", dict(cr_id="pl-1", title="Poland", full_name="Poland",
                            place_type="country")),
            ("Posen", dict(cr_id="po-1", title="Posen", full_name="Posen, Poland",
                           place_type="city", parent_place='"[[Poland]]"',
                           aliases=["Poznań"])))
        plan = Plan()
        res = placeplan.extract(plan, Counter({"Posen, Poland": 2}), index,
                                root=self.root)
        self.assertEqual(res.resolved, ["Posen, Poland"])
        e = plan.plac["Posen, Poland"]
        self.assertEqual((e.place, e.status), ("po-1", "approved"))
        p = plan.places["po-1"]
        self.assertEqual((p.status, p.cr_id, p.parent, p.aliases, p.title),
                         ("created", "po-1", "pl-1", ["Poznań"], "Posen"))
        self.assertEqual(p.file, f"{FOLDERS['places']}/Posen.md")
        self.assertEqual(plan.places["pl-1"].status, "created")


def _chain(status="approved") -> Plan:
    """Wrocław -> Lower Silesian Voivodeship -> Poland, all new."""
    return Plan(
        places={
            "poland": PlannedPlace(key="poland", title="Poland",
                                   place_type="country", status=status),
            "lower-silesia": PlannedPlace(
                key="lower-silesia", title="Lower Silesian Voivodeship",
                place_type="state", parent="poland", status=status),
            "wroclaw": PlannedPlace(
                key="wroclaw", title="Wrocław", place_type="city",
                parent="lower-silesia", aliases=["Breslau"], status=status),
        },
        plac={
            "Breslau, Schlesien, Preußen": PlacEntry(
                plac="Breslau, Schlesien, Preußen", count=3, place="wroclaw",
                status=status),
        })


class Basename(unittest.TestCase):
    def test_the_title_when_free(self):
        plan = _chain()
        self.assertEqual(
            placeplan.basename_for(plan.places["wroclaw"], plan, set()),
            "Wrocław")

    def test_a_taken_title_gets_the_parent_then_the_next_ancestor(self):
        plan = _chain()
        wro = plan.places["wroclaw"]
        self.assertEqual(
            placeplan.basename_for(wro, plan, {"wrocław"}),
            "Wrocław, Lower Silesian Voivodeship")
        self.assertEqual(
            placeplan.basename_for(
                wro, plan, {"Wrocław", "wrocław, lower silesian voivodeship"}),
            "Wrocław, Lower Silesian Voivodeship, Poland")


class AssignBasenames(unittest.TestCase):
    def _note(self, name, cr_id=""):
        fm = f"---\ncr_type: place\ncr_id: {cr_id}\n---\n"
        return vault.parse_text(fm, f"/v/Places/{name}.md")

    def test_a_clash_gets_the_parent_and_created_keep_their_names(self):
        plan = _chain()
        plan.places["poland"].status = "created"
        plan.places["poland"].cr_id = "pol-111-aaa-111"
        plan.places["poland"].file = "Places/Poland.md"
        plan.places["dup"] = PlannedPlace(
            key="dup", title="Wrocław", place_type="city",
            parent="poland", status="proposed")
        existing = [self._note("Poland", "pol-111-aaa-111"),
                    self._note("wrocław")]
        names = placeplan.assign_basenames(plan, existing)
        self.assertEqual(names, {
            "poland": "Poland",
            "lower-silesia": "Lower Silesian Voivodeship",
            "wroclaw": "Wrocław, Lower Silesian Voivodeship",
            "dup": "Wrocław, Poland"})


class Render(unittest.TestCase):
    def _render(self, key):
        plan = _chain()
        names = {k: p.title for k, p in plan.places.items()}
        ids = {"poland": "pol-111-aaa-111", "lower-silesia": "low-222-bbb-222",
               "wroclaw": "wro-333-ccc-333"}
        return placeplan.render_note(plan.places[key], plan, names, ids)

    def test_a_child_is_written_with_its_chain(self):
        self.assertEqual(self._render("wroclaw"), (
            "---\n"
            "cr_type: place\n"
            "cr_id: wro-333-ccc-333\n"
            "title: Wrocław\n"
            "place_type: city\n"
            'parent_place: "[[Lower Silesian Voivodeship]]"\n'
            "parent_place_id: low-222-bbb-222\n"
            "full_name: Wrocław, Lower Silesian Voivodeship, Poland\n"
            "aliases:\n"
            "  - Breslau\n"
            "---\n"
            "**Part of:** [[Lower Silesian Voivodeship]]\n"))

    def test_a_root_has_no_parent_and_no_part_of_line(self):
        text = self._render("poland")
        self.assertNotIn("parent_place", text)
        self.assertNotIn("aliases", text)
        self.assertNotIn("Part of", text)
        self.assertIn("full_name: Poland\n", text)

    def test_the_output_parses_back(self):
        note = vault.parse_text(self._render("wroclaw"))
        self.assertEqual(note.scalar("full_name"),
                         "Wrocław, Lower Silesian Voivodeship, Poland")
        self.assertEqual(note.as_list("aliases"), ["Breslau"])


class Check(VaultCase):
    def _existing(self, *notes):
        for name, keys in notes:
            keys.setdefault("cr_type", "place")
            self.write(f"{FOLDERS['places']}/{name}.md", frontmatter(**keys))
        return list(vault.iter_notes(self.cfg.places))

    def _check(self, plan, existing=()):
        return placeplan.check(plan, self.cfg, list(existing))

    def test_a_clean_plan_has_no_problems(self):
        self.assertEqual(self._check(_chain()), [])

    def test_missing_parent(self):
        plan = _chain()
        plan.places["wroclaw"].parent = "nowhere"
        out = self._check(plan)
        self.assertTrue(any(p.startswith("wroclaw: ") and "parent 'nowhere'" in p
                            for p in out), out)

    def test_cycle(self):
        plan = _chain()
        plan.places["poland"].parent = "wroclaw"
        out = self._check(plan)
        self.assertTrue(any("cycle" in p for p in out), out)

    def test_bad_place_type(self):
        plan = _chain()
        plan.places["wroclaw"].place_type = "metropolis"
        out = self._check(plan)
        self.assertTrue(any(p.startswith("wroclaw: ") and "place_type" in p
                            for p in out), out)

    def test_a_custom_place_type_is_valid(self):
        plan = _chain()
        plan.places["wroclaw"].place_type = "metropolis"
        self.cfg.settings["customPlaceTypes"] = [{"id": "metropolis"}]
        self.assertEqual(self._check(plan), [])

    def test_duplicate_title_under_one_parent(self):
        plan = _chain()
        plan.places["wroclaw2"] = PlannedPlace(
            key="wroclaw2", title="wrocław", place_type="city",
            parent="lower-silesia", status="approved")
        out = self._check(plan)
        self.assertTrue(any("same title" in p and "wroclaw2" in p for p in out),
                        out)

    def test_unknown_place_key(self):
        plan = _chain()
        plan.plac["Posen"] = PlacEntry(plac="Posen", place="poznan")
        out = self._check(plan)
        self.assertTrue(any(p.startswith("Posen: ") and "'poznan'" in p
                            for p in out), out)

    def test_duplicates_an_existing_note(self):
        existing = self._existing(
            ("Poland", dict(cr_id="exi-111-sti-111", title="Poland",
                            place_type="country", full_name="Poland")))
        out = self._check(_chain(), existing)
        self.assertTrue(any(p.startswith("poland: ") and "already exists" in p
                            for p in out), out)

    def test_a_created_place_is_not_a_duplicate_of_itself(self):
        existing = self._existing(
            ("Poland", dict(cr_id="exi-111-sti-111", title="Poland",
                            place_type="country", full_name="Poland")))
        plan = _chain()
        plan.places["poland"].status = "created"
        plan.places["poland"].cr_id = "exi-111-sti-111"
        plan.places["poland"].file = f"{FOLDERS['places']}/Poland.md"
        self.assertEqual(self._check(plan, existing), [])

    def test_an_approved_string_that_resolves_elsewhere(self):
        # Two Neustadts that the alias fallback cannot tell apart.
        plan = Plan(
            places={
                "hesse": PlannedPlace(key="hesse", title="Hesse",
                                      place_type="state", status="approved"),
                "bavaria": PlannedPlace(key="bavaria", title="Bavaria",
                                        place_type="state", status="approved"),
                "n1": PlannedPlace(key="n1", title="Neustadt (Hesse)",
                                   place_type="city", parent="hesse",
                                   aliases=["Neustadt"], status="approved"),
                "n2": PlannedPlace(key="n2", title="Neustadt (Bavaria)",
                                   place_type="city", parent="bavaria",
                                   aliases=["Neustadt"], status="approved"),
            },
            plac={"Neustadt, Preußen": PlacEntry(
                plac="Neustadt, Preußen", place="n1", status="approved")})
        out = self._check(plan)
        self.assertTrue(any(p.startswith("Neustadt, Preußen: ") and "resolves" in p
                            for p in out), out)

    def test_an_unapproved_string_is_not_resolved(self):
        plan = _chain()
        plan.plac["Breslau, Schlesien, Preußen"].status = "proposed"
        self.assertEqual(self._check(plan), [])

    def test_an_unknown_status(self):
        plan = _chain()
        plan.places["wroclaw"].status = "aproved"
        plan.plac["Breslau, Schlesien, Preußen"].status = "created"
        out = self._check(plan)
        self.assertTrue(any(p.startswith("wroclaw: ") and "status" in p
                            for p in out), out)
        self.assertTrue(any(p.startswith("Breslau, Schlesien, Preußen: ")
                            and "status" in p for p in out), out)

    def test_aliases_must_be_a_list_of_strings(self):
        plan = _chain()
        plan.places["wroclaw"].aliases = "Breslau"
        plan.places["poland"].aliases = ["Polen", 7]
        out = self._check(plan)
        self.assertTrue(any(p.startswith("wroclaw: ") and "aliases" in p
                            for p in out), out)
        self.assertTrue(any(p.startswith("poland: ") and "aliases" in p
                            for p in out), out)

    def test_an_approved_place_needs_an_approved_parent(self):
        plan = _chain()
        plan.places["lower-silesia"].status = "proposed"
        out = self._check(plan)
        self.assertTrue(any(p.startswith("wroclaw: ") and "parent" in p
                            for p in out), out)

    def test_an_approved_string_on_an_unapproved_place(self):
        plan = _chain()
        plan.places["wroclaw"].status = "proposed"
        out = self._check(plan)
        self.assertTrue(any(p.startswith("Breslau, Schlesien, Preußen: ")
                            and "place 'wroclaw' is not approved" in p
                            for p in out), out)

    def test_an_approved_string_that_maps_nowhere(self):
        plan = _chain()
        plan.plac["Posen"] = PlacEntry(plac="Posen", status="approved")
        out = self._check(plan)
        self.assertTrue(any(p.startswith("Posen: ") and "no place" in p
                            for p in out), out)

    def test_duplicates_an_existing_note_by_title_and_parent(self):
        existing = self._existing(
            ("Poland", dict(cr_id="exi-111-sti-111", title="Poland",
                            place_type="country", full_name="Poland")),
            ("Wroclaw", dict(cr_id="exi-222-sti-222", title="Wrocław",
                             place_type="city",
                             parent_place='"[[Lower Silesian Voivodeship]]"',
                             full_name="Wroclaw, Poland")),
            ("Lower Silesian Voivodeship", dict(
                cr_id="exi-333-sti-333", title="Lower Silesian Voivodeship",
                place_type="state", parent_place='"[[Poland]]"',
                full_name="Lower Silesian Voivodeship, Poland")))
        plan = _chain()
        for k in ("poland", "lower-silesia"):
            plan.places[k].status = "created"
        plan.places["poland"].cr_id = "exi-111-sti-111"
        plan.places["poland"].file = f"{FOLDERS['places']}/Poland.md"
        plan.places["lower-silesia"].cr_id = "exi-333-sti-333"
        plan.places["lower-silesia"].file = (
            f"{FOLDERS['places']}/Lower Silesian Voivodeship.md")
        out = self._check(plan, existing)
        self.assertTrue(any(p.startswith("wroclaw: ")
                            and "title and parent" in p for p in out), out)

    def test_a_created_place_whose_note_is_missing(self):
        plan = _chain()
        plan.places["poland"].status = "created"
        plan.places["poland"].cr_id = "gon-111-eee-111"
        plan.places["poland"].file = f"{FOLDERS['places']}/Poland.md"
        out = self._check(plan, [])
        self.assertTrue(any(p.startswith("poland: ") and "note was not found" in p
                            for p in out), out)

    def test_check_writes_nothing(self):
        before = sorted(os.listdir(self.cfg.places))
        self._check(_chain())
        self.assertEqual(sorted(os.listdir(self.cfg.places)), before)
        self.assertFalse(os.path.exists(
            os.path.join(self.root, placeplan.PLAN_PATH)))


class Apply(VaultCase):
    def _apply(self, plan, dry=False):
        return placeplan.apply_plan(plan, self.cfg, dry=dry)

    def _files(self):
        return sorted(os.listdir(os.path.join(self.root, FOLDERS["places"])))

    def test_the_wroclaw_chain_is_written(self):
        plan = _chain()
        res = self._apply(plan)
        self.assertEqual(self._files(), [
            "Lower Silesian Voivodeship.md", "Poland.md", "Wrocław.md"])
        self.assertEqual(res.created, [
            f"{FOLDERS['places']}/{n}.md" for n in
            ("Poland", "Lower Silesian Voivodeship", "Wrocław")])
        self.assertEqual(res.aliased, [])
        text = self.read(f"{FOLDERS['places']}/Wrocław.md")
        ids = {k: p.cr_id for k, p in plan.places.items()}
        self.assertEqual(text, (
            "---\n"
            "cr_type: place\n"
            f"cr_id: {ids['wroclaw']}\n"
            "title: Wrocław\n"
            "place_type: city\n"
            'parent_place: "[[Lower Silesian Voivodeship]]"\n'
            f"parent_place_id: {ids['lower-silesia']}\n"
            "full_name: Wrocław, Lower Silesian Voivodeship, Poland\n"
            "aliases:\n"
            "  - Breslau\n"
            "---\n"
            "**Part of:** [[Lower Silesian Voivodeship]]\n"))
        self.assertEqual(len(set(ids.values())), 3)
        self.assertTrue(all(ids.values()))
        for p in plan.places.values():
            self.assertEqual(p.status, "created")
        self.assertEqual(plan.places["wroclaw"].file,
                         f"{FOLDERS['places']}/Wrocław.md")
        self.assertEqual(placeplan.load(self.root).places["wroclaw"].cr_id,
                         ids["wroclaw"])

    def test_a_taken_basename_gets_the_parent(self):
        old = frontmatter(cr_type="place", cr_id="old-111-old-111",
                          title="Neustadt")
        self.write(f"{FOLDERS['places']}/Neustadt.md", old)
        plan = Plan(places={
            "hesse": PlannedPlace(key="hesse", title="Hesse",
                                  place_type="state", status="approved"),
            "neustadt": PlannedPlace(
                key="neustadt", title="Neustadt", place_type="city",
                parent="hesse", status="approved"),
            "kirche": PlannedPlace(
                key="kirche", title="Kirchdorf", place_type="locality",
                parent="neustadt", status="approved")})
        self._apply(plan)
        self.assertIn("Neustadt, Hesse.md", self._files())
        folder = os.path.join(self.root, FOLDERS["places"])
        note = vault.parse(os.path.join(folder, "Neustadt, Hesse.md"))
        self.assertEqual(note.scalar("title"), "Neustadt")
        child = vault.parse(os.path.join(folder, "Kirchdorf.md"))
        self.assertEqual(child.scalar("parent_place"), "[[Neustadt, Hesse]]")
        self.assertEqual(self.read(f"{FOLDERS['places']}/Neustadt.md"), old)

    def test_an_approved_place_beats_an_earlier_proposed_one_to_the_name(self):
        plan = Plan(places={
            "first": PlannedPlace(key="first", title="Neustadt",
                                  place_type="city", parent="other"),
            "other": PlannedPlace(key="other", title="Other",
                                  place_type="state"),
            "hesse": PlannedPlace(key="hesse", title="Hesse",
                                  place_type="state", status="approved"),
            "second": PlannedPlace(key="second", title="Neustadt",
                                   place_type="city", parent="hesse",
                                   status="approved")})
        self._apply(plan)
        self.assertEqual(plan.places["second"].file,
                         f"{FOLDERS['places']}/Neustadt.md")
        self.assertEqual(plan.places["first"].status, "proposed")

    def test_proposed_places_are_not_written(self):
        plan = _chain(status="proposed")
        res = self._apply(plan)
        self.assertEqual(self._files(), [])
        self.assertEqual((res.created, res.aliased), ([], []))
        self.assertFalse(os.path.exists(
            os.path.join(self.root, placeplan.PLAN_PATH)))

    def test_an_existing_place_only_gains_aliases(self):
        text = ("---\ncr_type: place\ncr_id: wro-111-wro-111\n"
                "title: Wrocław\nplace_type: city\naliases:\n"
                "  - Vratislav\n  - breslau\nnote_key:   spaced\n---\nBody\n")
        path = self.write(f"{FOLDERS['places']}/Wrocław.md", text)
        plan = Plan(places={"wroclaw": PlannedPlace(
            key="wroclaw", title="Wrocław Renamed", place_type="region",
            aliases=["Breslau", "Wratislavia"], status="approved",
            cr_id="wro-111-wro-111")})
        res = self._apply(plan)
        self.assertEqual(res.created, [])
        self.assertEqual(res.aliased, [f"{FOLDERS['places']}/Wrocław.md"])
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), text.replace(
                "  - breslau\n", "  - breslau\n  - Wratislavia\n"))
        self.assertEqual(plan.places["wroclaw"].status, "created")

    def test_a_second_apply_writes_nothing(self):
        self._apply(_chain())
        before = {n: self.read(f"{FOLDERS['places']}/{n}")
                  for n in self._files()}
        plan_text = self.read(placeplan.PLAN_PATH)
        res = self._apply(placeplan.load(self.root))
        self.assertEqual((res.created, res.aliased), ([], []))
        self.assertEqual(before, {n: self.read(f"{FOLDERS['places']}/{n}")
                                  for n in self._files()})
        self.assertEqual(plan_text, self.read(placeplan.PLAN_PATH))

    def test_dry_run_writes_nothing(self):
        plan = _chain()
        res = self._apply(plan, dry=True)
        self.assertEqual(len(res.created), 3)
        self.assertEqual(self._files(), [])
        self.assertFalse(os.path.exists(
            os.path.join(self.root, placeplan.PLAN_PATH)))
        self.assertTrue(all(p.status == "approved" and not p.cr_id
                            for p in plan.places.values()))


if __name__ == "__main__":
    unittest.main()
