"""The write layer.

These are the functions that decide what reaches disk, so each one is pinned
from both sides: what it writes, and what it must refuse to write or report
instead of dropping.
"""

from __future__ import annotations

import os
import subprocess
import unittest
from unittest import mock

from crsync import apply as apply_mod
from crsync import decisions, match, vault

from .helpers import FOLDERS, VaultCase


def action(key="I1", path="Charted Roots/People/Test Person.md", *changes,
           kind="update"):
    return match.Action(kind=kind, entity="person", key=key,
                        label="Test Person", path=path, changes=list(changes))


def rulings(coarsen=None, conflict=None) -> decisions.Decisions:
    """A Decisions object as if read from History/gedcom-sync-decisions.json."""
    return decisions.Decisions(
        path="History/gedcom-sync-decisions.json",
        entries=[{"external_id": x} for x in
                 set(coarsen or {}) | set(conflict or {})],
        coarsen_exempt={k: set(v) for k, v in (coarsen or {}).items()},
        conflict_accepted={k: set(v) for k, v in (conflict or {}).items()})


def plan_of(*actions) -> match.Plan:
    plan = match.Plan()
    for a in actions:
        plan.add(a)
    return plan


class SafeChanges(unittest.TestCase):

    def test_fill_and_refine_are_always_written(self):
        act = action("I1", "p.md",
                     match.Change("born", "", "1824"),
                     match.Change("died", "1871", "1871-03-02"))
        self.assertEqual([c.kind for c in apply_mod.safe_changes(act)],
                         [match.FILL, match.REFINE])

    def test_case_needs_an_explicit_go_ahead(self):
        act = action("I1", "p.md", match.Change("name", "von X", "Von X"))
        self.assertEqual(apply_mod.safe_changes(act), [])
        self.assertEqual(len(apply_mod.safe_changes(act, allow_case=True)), 1)

    def test_coarsen_and_conflict_are_held_by_default(self):
        act = action("I1", "p.md",
                     match.Change("born", "1884-05", "1884"),
                     match.Change("name", "Grünwald", "Grunwald"))
        self.assertEqual(apply_mod.safe_changes(act), [])

    def test_with_no_rulings_nothing_is_accepted(self):
        act = action("I1", "p.md", match.Change("born", "1884-05", "1884"))
        self.assertEqual(apply_mod.safe_changes(act, external_id="I1"), [])
        self.assertEqual(apply_mod.safe_changes(
            act, external_id="I1", decisions=decisions.Decisions()), [])

    def test_an_exemption_is_keyed_by_external_id_and_field(self):
        act = action("I1", "p.md", match.Change("surnames", ["Muster, Landwirt"],
                                                ["Muster"]))
        ruled = rulings(coarsen={"I1": {"surnames"}})
        self.assertEqual(len(apply_mod.safe_changes(
            act, external_id="I1", decisions=ruled)), 1)
        # A ruling about one person says nothing about another, and a ruling
        # about one field says nothing about another field.
        self.assertEqual(apply_mod.safe_changes(
            act, external_id="I2", decisions=ruled), [])
        self.assertEqual(apply_mod.safe_changes(
            act, external_id="I1",
            decisions=rulings(coarsen={"I1": {"name"}})), [])

    def test_an_accepted_conflict_is_field_specific(self):
        act = action("I1", "p.md",
                     match.Change("name", "Grünwald", "Grunwald"),
                     match.Change("born", "1822", "1821-10-30"))
        safe = apply_mod.safe_changes(act, external_id="I1",
                                      decisions=rulings(conflict={"I1": {"name"}}))
        self.assertEqual([c.field for c in safe], ["name"])

    def test_a_coarsen_ruling_does_not_accept_a_conflict(self):
        act = action("I1", "p.md", match.Change("name", "Grünwald", "Grunwald"))
        self.assertEqual(apply_mod.safe_changes(
            act, external_id="I1",
            decisions=rulings(coarsen={"I1": {"name"}})), [])


class CountAccepted(unittest.TestCase):
    """What the dry run reports: which held changes the rulings cover."""

    def plan(self):
        return plan_of(
            action("I1", "a.md",
                   match.Change("surnames", ["Muster, Landwirt"], ["Muster"]),
                   match.Change("name", "Grünwald", "Grunwald")),
            action("I2", "b.md", match.Change("born", "1822", "1821-10-30")))

    def test_it_counts_per_class(self):
        ruled = rulings(coarsen={"I1": {"surnames"}},
                        conflict={"I1": {"name"}, "I2": {"born"}})
        self.assertEqual(
            apply_mod.count_accepted(self.plan(), "person", ruled), (1, 2))

    def test_a_ruling_on_a_field_that_no_longer_disagrees_counts_nothing(self):
        # Fixed upstream since the ruling was made: the entry is spent, and
        # the report says so rather than implying it still applies.
        ruled = rulings(conflict={"I9": {"name"}})
        self.assertEqual(
            apply_mod.count_accepted(self.plan(), "person", ruled), (0, 0))


class CaseDirection(unittest.TestCase):

    def direction(self, *pairs):
        changes = [match.Change("name", old, new) for old, new in pairs]
        return apply_mod.case_direction(plan_of(action("I1", "p.md", *changes)),
                                        "person")

    def test_uniformly_adding_capitals(self):
        self.assertEqual(self.direction(("von x", "Von X")), 1)

    def test_uniformly_removing_capitals(self):
        self.assertEqual(self.direction(("Von X", "von x")), -1)

    def test_mixed_is_held(self):
        self.assertEqual(self.direction(("von x", "Von X"), ("Von Y", "von y")), 0)

    def test_no_case_changes_at_all(self):
        self.assertEqual(self.direction(), 0)

    def test_only_case_changes_count(self):
        plan = plan_of(action("I1", "p.md", match.Change("born", "", "1824")))
        self.assertEqual(apply_mod.case_direction(plan, "person"), 0)


class FieldUpdates(VaultCase):

    def setUp(self):
        super().setUp()
        self.path = self.person("Test Person", external_id="I1", born="1824",
                                aliases=["Old Alias"])
        self.rel = os.path.relpath(self.path, self.root)
        self.note = vault.parse(self.path)
        self.index = {self.path: self.note}

    def apply(self, *changes, **kw):
        plan = plan_of(action("I1", self.rel, *changes))
        return apply_mod.apply_field_updates(plan, "person", self.index,
                                             self.root, dry=False, **kw)

    def test_a_fill_reaches_disk(self):
        written, held, missing = self.apply(match.Change("died", "", "1871"))
        self.assertEqual(len(written), 1)
        self.assertEqual((held, missing), ([], []))
        self.assertIn("died: 1871", self.read(self.rel))

    def test_an_emptied_list_removes_the_key(self):
        # Writing `aliases:` with nothing under it is worse than no key.
        self.apply(match.Change("aliases", ["Old Alias"], [], kind=match.FILL))
        self.assertNotIn("aliases", self.read(self.rel))

    def test_a_held_change_is_reported_and_not_written(self):
        written, held, missing = self.apply(
            match.Change("born", "1824", "1820"))
        self.assertEqual(written, [])
        self.assertEqual([c.field for _, changes in held for c in changes], ["born"])
        self.assertIn("born: 1824", self.read(self.rel))

    def test_a_change_already_on_disk_is_not_counted_as_written(self):
        written, _, _ = self.apply(match.Change("born", "", "1824"))
        self.assertEqual(written, [])

    def test_a_dry_run_writes_nothing(self):
        plan = plan_of(action("I1", self.rel, match.Change("died", "", "1871")))
        apply_mod.apply_field_updates(plan, "person", self.index, self.root,
                                      dry=True)
        self.assertNotIn("died", self.read(self.rel))

    def test_a_planned_change_with_no_note_is_reported_not_dropped(self):
        # A planned write whose target is not in the index is a matcher or
        # indexing bug. Skipping it silently loses the finding: the run reports
        # neither a write nor a hold, and the next run plans it again.
        plan = plan_of(action("I1", "Charted Roots/People/Not Indexed.md",
                              match.Change("died", "", "1871")))
        written, held, missing = apply_mod.apply_field_updates(
            plan, "person", self.index, self.root, dry=False)
        self.assertEqual((written, held), ([], []))
        self.assertEqual([a.key for a, _ in missing], ["I1"])

    def test_the_preflight_finds_them_before_anything_is_written(self):
        plan = plan_of(action("I1", "Charted Roots/People/Not Indexed.md",
                              match.Change("died", "", "1871")))
        blocked = apply_mod.preflight(plan, "person", self.index, self.root)
        self.assertEqual([(a.key, reason) for a, reason in blocked],
                         [("I1", "no note at that path in the index")])

    def test_the_preflight_ignores_an_action_with_nothing_safe_to_write(self):
        plan = plan_of(action("I1", "Charted Roots/People/Not Indexed.md",
                              match.Change("born", "1824", "1820")))
        self.assertEqual(apply_mod.preflight(
            plan, "person", self.index, self.root), [])

    def test_the_preflight_refuses_a_note_the_writer_cannot_patch(self):
        # Readable, but a line of it is invisible to the span index, so a
        # write to the key above it would delete that line.
        path = self.write("Charted Roots/People/Stray Line.md",
                          "---\ncr_type: person\nname: Stray\n"
                          "nested:\n  sub: value\n---\n")
        note = vault.parse(path)
        plan = plan_of(action("I9", os.path.relpath(path, self.root),
                              match.Change("died", "", "1871")))
        blocked = apply_mod.preflight(plan, "person", {path: note}, self.root)
        self.assertEqual(len(blocked), 1)
        self.assertIn("key index cannot see", blocked[0][1])
        self.assertIn("sub: value", blocked[0][1])


class CitationLists(VaultCase):

    def citations_of(self, name="Child Name"):
        return vault.parse(
            os.path.join(self.root, FOLDERS["people"], f"{name}.md")
        ).as_list("citations")

    def make_citation(self, fact="birth_date", subject_id="ccc-000-ccc-000"):
        name = f"Citation - Kirchenbuch - Child Name {fact}"
        self.citation(name, cr_id=f"cit-{fact[:3]}-cit-000",
                      subject='"[[Child Name]]"', subject_id=subject_id,
                      fact=fact)
        return name

    def test_a_missing_entry_is_added(self):
        self.person("Child Name", cr_id="ccc-000-ccc-000")
        name = self.make_citation()
        touched = apply_mod.rebuild_citation_lists(self.cfg, dry=False)
        self.assertEqual([os.path.basename(p) for p in touched],
                         ["Child Name.md"])
        self.assertEqual(self.citations_of(), [f"[[{name}]]"])

    def test_an_entirely_phantom_list_is_cleared(self):
        # The half that rots. A `citations:` entry pointing at no Citation
        # note fails the invariant suite, and skipping the empty case meant
        # --apply could never fix it.
        self.person("Child Name", cr_id="ccc-000-ccc-000",
                    citations=['"[[Citation - Gone - Child Name birth_date]]"'])
        touched = apply_mod.rebuild_citation_lists(self.cfg, dry=False)
        self.assertEqual(len(touched), 1)
        self.assertEqual(self.citations_of(), [])
        self.assertNotIn("citations", self.read(f"{FOLDERS['people']}/Child Name.md"))

    def test_a_correct_list_in_another_order_is_left_alone(self):
        # Membership is the invariant, not order. Rewriting every list to this
        # function's sort would churn hundreds of notes for no change in fact.
        first = self.make_citation("birth_date")
        second = self.make_citation("death_date")
        self.person("Child Name", cr_id="ccc-000-ccc-000",
                    citations=[f'"[[{second}]]"', f'"[[{first}]]"'])
        before = self.read(f"{FOLDERS['people']}/Child Name.md")
        self.assertEqual(apply_mod.rebuild_citation_lists(self.cfg, dry=False), [])
        self.assertEqual(self.read(f"{FOLDERS['people']}/Child Name.md"), before)

    def test_a_duplicate_entry_is_collapsed(self):
        name = self.make_citation()
        self.person("Child Name", cr_id="ccc-000-ccc-000",
                    citations=[f'"[[{name}]]"', f'"[[{name}]]"'])
        self.assertEqual(len(apply_mod.rebuild_citation_lists(self.cfg, dry=False)), 1)
        self.assertEqual(self.citations_of(), [f"[[{name}]]"])

    def test_a_citation_whose_subject_id_matches_nobody_is_ignored(self):
        self.person("Child Name", cr_id="ccc-000-ccc-000")
        self.make_citation(subject_id="no-such-id")
        self.assertEqual(apply_mod.rebuild_citation_lists(self.cfg, dry=False), [])

    def test_a_dry_run_writes_nothing(self):
        self.person("Child Name", cr_id="ccc-000-ccc-000")
        self.make_citation()
        self.assertEqual(len(apply_mod.rebuild_citation_lists(self.cfg, dry=True)), 1)
        self.assertEqual(self.citations_of(), [])


class Relationships(VaultCase):

    class FakePlan:
        people: list = []

    def test_it_returns_the_paths_it_rewrote(self):
        path = self.person("Father Name", external_id="I1")
        notes = [vault.parse(path)]
        touched = apply_mod.write_relationships(
            {"I1": {"children": ['"[[Child Name]]"'],
                    "children_id": ["ccc-000-ccc-000"]}},
            notes, self.FakePlan(), dry=False)
        self.assertEqual(touched, [path])
        self.assertIn("children_id:", self.read(f"{FOLDERS['people']}/Father Name.md"))

    def test_an_unknown_xref_is_skipped(self):
        path = self.person("Father Name", external_id="I1")
        notes = [vault.parse(path)]
        self.assertEqual(apply_mod.write_relationships(
            {"I999": {"children": []}}, notes, self.FakePlan(), dry=False), [])


class ObsidianProbe(unittest.TestCase):
    """One probe, and an unanswerable question is not a "no".

    The CLI carried a second copy that returned False when `pgrep` could not
    be run, which reads as "Obsidian is closed" -- the same fail-open shape
    as a `git status` that fails and reads as a clean tree.
    """

    def probe_with(self, **kw):
        def fake_run(*args, **kwargs):
            if "exc" in kw:
                raise kw["exc"]
            return subprocess.CompletedProcess(args, kw["returncode"])
        with mock.patch.object(subprocess, "run", fake_run):
            return apply_mod.obsidian_running()

    def test_it_answers_on_this_machine(self):
        self.assertIn(apply_mod.obsidian_running(), (True, False))

    def test_pgrep_exit_codes(self):
        self.assertIs(self.probe_with(returncode=0), True)    # a match
        self.assertIs(self.probe_with(returncode=1), False)   # no match
        self.assertIsNone(self.probe_with(returncode=2))      # pgrep itself
        self.assertIsNone(self.probe_with(returncode=3))

    def test_no_pgrep_at_all(self):
        self.assertIsNone(self.probe_with(exc=FileNotFoundError("pgrep")))


class UnansweredProbe(VaultCase):

    def checks_with(self, running, **kw):
        with mock.patch.object(apply_mod, "obsidian_running", lambda: running):
            return {c.name: c for c in apply_mod.check_preconditions(
                self.cfg, require_restore_point=False, **kw)}

    def test_it_blocks_when_it_cannot_tell(self):
        c = self.checks_with(None)["Obsidian is closed"]
        self.assertFalse(c.ok)
        self.assertIn("cannot tell", c.detail)
        self.assertIn("did not answer", c.remedy)

    def test_the_override_still_works(self):
        self.assertTrue(self.checks_with(None, allow_obsidian=True)[
            "Obsidian is closed"].ok)

    def test_running_blocks_and_closed_passes(self):
        self.assertFalse(self.checks_with(True)["Obsidian is closed"].ok)
        self.assertTrue(self.checks_with(False)["Obsidian is closed"].ok)


class SyncState(VaultCase):
    """The reason to close Obsidian is asserted from data.json, not stated.

    The vault model: name the setting, then the rule that follows if it is on. The
    remedy used to declare bidirectional sync ON as a fact about the vault,
    which is false for any vault that turns it off -- and a precondition that
    argues from a setting nobody checked is one a reader cannot act on.
    """

    def cfg_with(self, **settings):
        from crsync import config
        return config.Config(root=self.root, settings=settings)

    def test_both_on(self):
        cfg = self.cfg_with(enableBidirectionalSync=True, syncOnFileModify=True)
        self.assertEqual(apply_mod.sync_state(cfg), "on")
        self.assertIn("would write the reciprocal", apply_mod.sync_remedy(cfg))

    def test_both_off_names_both_settings(self):
        cfg = self.cfg_with()
        self.assertEqual(apply_mod.sync_state(cfg), "off")
        self.assertEqual(apply_mod.sync_flags(cfg),
                         "enableBidirectionalSync off, syncOnFileModify off")
        remedy = apply_mod.sync_remedy(cfg)
        self.assertIn("nothing would reciprocate these writes", remedy)
        # still a reason to quit, just a different one
        self.assertIn("rewrites data.json from memory", remedy)

    def test_half_on_is_not_live(self):
        cfg = self.cfg_with(enableBidirectionalSync=True)
        self.assertEqual(apply_mod.sync_state(cfg), "off")
        self.assertEqual(apply_mod.sync_flags(cfg),
                         "enableBidirectionalSync on, syncOnFileModify off")
        remedy = apply_mod.sync_remedy(cfg)
        self.assertIn("not live", remedy)
        self.assertIn("enableBidirectionalSync on", remedy)

    def test_the_precondition_carries_the_state_either_way(self):
        for settings, needle in (({"enableBidirectionalSync": True,
                                   "syncOnFileModify": True},
                                  "bidirectional sync on"),
                                 ({}, "bidirectional sync off")):
            with self.subTest(needle):
                checks = apply_mod.check_preconditions(
                    self.cfg_with(**settings), require_restore_point=False,
                    allow_obsidian=True)
                detail = {c.name: c.detail for c in checks}["Obsidian is closed"]
                self.assertIn(needle, detail)


class AtomicWrite(VaultCase):
    """One implementation, used by every writer.

    There were three: the note writer used mkstemp and cleaned up, while the
    sidecar and the new-note writer wrote a sibling `.tmp` and left it behind
    on failure -- inside an entity folder, where Obsidian would index it.
    """

    def path(self, name="Charted Roots/People/Written.md") -> str:
        return os.path.join(self.root, name)

    def temp_files(self, path) -> list:
        return [n for n in os.listdir(os.path.dirname(path))
                if n.startswith(".crsync-")]

    def test_it_writes_and_leaves_no_temp_file(self):
        path = self.path()
        vault.write_atomic(path, "hello\n")
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "hello\n")
        self.assertEqual(self.temp_files(path), [])

    def test_it_creates_missing_parents(self):
        path = self.path("Charted Roots/Nowhere/Deep/Note.md")
        vault.write_atomic(path, "x")
        self.assertTrue(os.path.exists(path))

    def test_a_failed_write_keeps_the_old_file_and_cleans_up(self):
        path = self.path()
        vault.write_atomic(path, "original\n")
        with self.assertRaises(TypeError):
            vault.write_atomic(path, 17)      # not a string
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "original\n")
        self.assertEqual(self.temp_files(path), [])

    def test_the_sidecar_goes_through_it(self):
        sidecar = os.path.join(self.root, "History", "map.json")

        class FakeMatch:
            pairs: list = []

        apply_mod.write_event_keys(FakeMatch(), sidecar, "sha", dry=False)
        self.assertTrue(os.path.exists(sidecar))
        self.assertEqual(self.temp_files(sidecar), [])

    def test_new_notes_go_through_it(self):
        from crsync.create import NewNote

        class FakePlan:
            def __init__(self, note):
                self.sources, self.people = [], [note]
                self.events, self.citations = [], []

        note = NewNote(self.path("Charted Roots/People/Fresh.md"),
                       {"cr_type": "person", "name": "Fresh"}, "# Research Notes\n",
                       "person")
        written = apply_mod.write_new_notes(FakePlan(note), dry=False)
        self.assertEqual([n.path for n in written], [note.path])
        self.assertEqual(self.read("Charted Roots/People/Fresh.md"), note.text())
        self.assertEqual(self.temp_files(note.path), [])


class Preconditions(VaultCase):

    def checks(self, **kw):
        kw.setdefault("allow_obsidian", True)
        return {c.name: c for c in apply_mod.check_preconditions(self.cfg, **kw)}

    def git(self, *args, **kw):
        return subprocess.run(["git", "-C", self.root, *args],
                              capture_output=True, text=True, **kw)

    def test_a_vault_that_is_not_a_repository_blocks(self):
        # `git status` printing nothing because there is no repository is not
        # the same as printing nothing because the tree is clean, and taking
        # the second for the first writes to an unguarded vault.
        c = self.checks(require_restore_point=False)[apply_mod.CLEAN]
        self.assertFalse(c.ok)

    def test_allow_dirty_does_not_cover_a_git_failure(self):
        c = self.checks(require_restore_point=False,
                        allow_dirty=True)[apply_mod.CLEAN]
        self.assertFalse(c.ok)

    def test_a_missing_restore_point_blocks(self):
        c = self.checks()["a restore point tags HEAD"]
        self.assertFalse(c.ok)

    def test_a_clean_repository_with_a_tag_passes(self):
        self.git("init", "-q")
        self.git("-c", "user.email=t@t", "-c", "user.name=t",
                 "commit", "-q", "--allow-empty", "-m", "base")
        self.git("tag", "pre-gedcom-sync-20260922-1200")
        checks = self.checks()
        self.assertTrue(checks[apply_mod.CLEAN].ok,
                        checks[apply_mod.CLEAN].detail)
        self.assertTrue(checks["a restore point tags HEAD"].ok)

    def test_an_uncommitted_entity_folder_blocks_unless_allowed(self):
        self.git("init", "-q")
        self.git("-c", "user.email=t@t", "-c", "user.name=t",
                 "commit", "-q", "--allow-empty", "-m", "base")
        self.person("Test Person")
        self.assertFalse(self.checks(require_restore_point=False)[
            apply_mod.CLEAN].ok)
        self.assertTrue(self.checks(require_restore_point=False, allow_dirty=True)[
            apply_mod.CLEAN].ok)

    def test_the_folders_come_from_data_json(self):
        # A vault laid out elsewhere: dirt outside its entity folders does not
        # block, dirt inside a configured folder does.
        self.cfg.settings["peopleFolder"] = "Family/People"
        os.makedirs(os.path.join(self.root, "Family/People"))
        self.git("init", "-q")
        self.git("-c", "user.email=t@t", "-c", "user.name=t",
                 "commit", "-q", "--allow-empty", "-m", "base")
        self.write("Notes/scratch.md", "loose\n")
        self.assertTrue(self.checks(require_restore_point=False)[apply_mod.CLEAN].ok)
        self.write("Family/People/Anna.md", "---\ncr_type: person\n---\n")
        self.assertFalse(self.checks(require_restore_point=False)[apply_mod.CLEAN].ok)
        self.assertIn("Family/People", self.cfg.entity_paths)


class EventKeys(VaultCase):

    class FakePair:
        def __init__(self, note, key, stage):
            self.vault_note, self.key, self.stage = note, key, stage

    class FakeMatch:
        def __init__(self, pairs):
            self.pairs = pairs

    def test_the_sidecar_is_keyed_by_cr_id(self):
        import json
        path = self.person("Test Person", cr_id="eee-000-eee-000")
        pair = self.FakePair(vault.parse(path), "I1:BIRT:0", "content")
        sidecar = os.path.join(self.root, "History", "map.json")
        mapping = apply_mod.write_event_keys(self.FakeMatch([pair]), sidecar,
                                             "deadbeef", dry=False)
        self.assertEqual(mapping, {"eee-000-eee-000":
                                   {"ged_key": "I1:BIRT:0", "stage": "content"}})
        with open(sidecar, encoding="utf-8") as fh:
            payload = json.load(fh)
        self.assertEqual(payload["ged_sha256"], "deadbeef")
        self.assertEqual(payload["events"], mapping)

    def test_a_dry_run_writes_no_sidecar(self):
        path = self.person("Test Person", cr_id="eee-000-eee-000")
        pair = self.FakePair(vault.parse(path), "I1:BIRT:0", "content")
        sidecar = os.path.join(self.root, "History", "map.json")
        apply_mod.write_event_keys(self.FakeMatch([pair]), sidecar, "x", dry=True)
        self.assertFalse(os.path.exists(sidecar))


if __name__ == "__main__":
    unittest.main()
