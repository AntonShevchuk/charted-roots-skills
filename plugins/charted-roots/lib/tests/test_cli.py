"""End-to-end runs of the CLI against a throwaway vault.

The unit tests pin each writer; this pins the driver -- in particular that the
count it prints is the count `git diff` will show. A Person can be rewritten
by the field pass, the relationship pass and the citation rebuild in one run,
and summing the passes counts it three times.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import subprocess
import unittest

import gedcom_sync
from crsync import decisions

from .helpers import FOLDERS, VaultCase, frontmatter

GED = """0 HEAD
1 SOUR Ancestry.com Family Trees
1 GEDC
2 VERS 5.5.1
1 DATE 21 SEP 2026
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Jürgen /Muster/
2 GIVN Jürgen
2 SURN Muster
1 SEX M
1 BIRT
2 DATE 1 JUN 1824
2 PLAC Musterdorf
1 FAMS @F1@
0 @I2@ INDI
1 NAME Anna /Meyer/
1 SEX F
1 BIRT
2 DATE 1826
2 PLAC Musterdorf
1 FAMS @F1@
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 MARR
2 DATE 27 MAY 1849
0 @S1@ SOUR
1 TITL Kirchenbuch Musterdorf
0 TRLR
"""


class CliCase(VaultCase):

    def setUp(self):
        super().setUp()
        self.write("FamilyTree.ged", GED)
        self.write(f"{FOLDERS['places']}/Musterdorf.md", frontmatter(
            cr_type="place", cr_id="ppp-000-ppp-000", title="Musterdorf",
            full_name="Musterdorf", place_type="locality"))
        self.person("Jürgen Muster", cr_id="aaa-111-aaa-111", external_id="I1",
                    external_id_source="gedcom", born="1824")
        self.git("init", "-q")
        self.git("add", "-A")
        self.git("-c", "user.email=t@t", "-c", "user.name=t",
                 "commit", "-q", "-m", "base")

    def git(self, *args) -> str:
        return subprocess.run(["git", "-C", self.root, *args],
                              capture_output=True, text=True).stdout

    def run_cli(self, *argv) -> tuple:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = gedcom_sync.main(["--vault", self.root, *argv])
        return code, out.getvalue(), err.getvalue()

    def changed_notes(self) -> list:
        """Vault notes git sees as modified or new after the run."""
        # -z, because git quotes and octal-escapes any path with a space or
        # a non-ASCII byte, and genealogy vaults are full of both.
        entries = self.git("status", "--porcelain", "-z",
                           "--untracked-files=all", "--", "Charted Roots")
        return sorted(e[3:] for e in entries.split("\0") if e.endswith(".md"))

    def new_notes(self) -> list:
        """Vault notes that did not exist before the run."""
        entries = self.git("status", "--porcelain", "-z",
                           "--untracked-files=all", "--", "Charted Roots")
        return sorted(e[3:] for e in entries.split("\0")
                      if e.endswith(".md") and e.startswith("??"))

    def commit(self, message="fixture") -> None:
        self.git("add", "-A")
        self.git("-c", "user.email=t@t", "-c", "user.name=t",
                 "commit", "-q", "-m", message)

    def rule(self, **entry) -> None:
        """Write a decisions file with one ruling."""
        self.write(os.path.join("History", decisions.FILENAME),
                   json.dumps({"decisions": [entry]}, ensure_ascii=False))


class Verify(CliCase):

    def test_verify_is_an_alias_for_vault_verify(self):
        self.write(f"{FOLDERS['people']}/Broken.md", "---\ncr_type: person\n")
        code, out, _ = self.run_cli("--verify")
        self.assertEqual(code, 1)
        self.assertIn("checks FAILED", out)
        self.assertIn("frontmatter blocks close", out)

    def test_apply_refuses_before_writing_to_such_a_note(self):
        # The note is in the plan and has a field the export would fill, so
        # the run would write it -- and a write would delete the line the
        # index cannot see. It refuses, having written nothing.
        self.write(f"{FOLDERS['people']}/Jürgen Muster.md",
                   "---\ncr_id: aaa-111-aaa-111\ncr_type: person\n"
                   "name: Jürgen Muster\nexternal_id: I1\n"
                   "relations:\n  father: someone\n---\n")
        self.commit("a note the writer refuses")
        code, out, err = self.run_cli("--apply", "--allow-obsidian-open",
                                      "--no-restore-point")
        self.assertEqual(code, 1)
        self.assertIn("could not be written", err)
        self.assertIn("key index cannot see", err)
        self.assertEqual(self.changed_notes(), [])


class DryRun(CliCase):

    def test_the_default_run_writes_nothing(self):
        code, out, _ = self.run_cli()
        self.assertEqual(code, 0, out)
        self.assertIn("dry run", out)
        self.assertEqual(self.changed_notes(), [])

    def test_a_missing_gedcom_is_an_error_not_a_traceback(self):
        os.unlink(os.path.join(self.root, "FamilyTree.ged"))
        code, _, err = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("No GEDCOM at", err)

    def test_apply_fails_the_same_way_as_the_dry_run(self):
        # One failure, one exit code, one message: --apply used to raise
        # SystemExit(1) from the reconciler while the dry run returned 2.
        os.unlink(os.path.join(self.root, "FamilyTree.ged"))
        dry_code, _, dry_err = self.run_cli()
        code, out, err = self.run_cli("--apply", "--allow-obsidian-open",
                                      "--no-restore-point")
        self.assertEqual((code, err), (dry_code, dry_err))
        # and it is checked before anything else runs, so no preconditions
        # are printed on the way to the error
        self.assertEqual(out, "")

    def test_an_absolute_ged_path_is_used_as_given(self):
        import shutil
        moved = os.path.join(self.root, "elsewhere.ged")
        shutil.move(os.path.join(self.root, "FamilyTree.ged"), moved)
        code, out, err = self.run_cli("--ged", moved)
        self.assertEqual(code, 0, err)
        self.assertIn("elsewhere.ged", out)

    def test_the_report_can_be_written_to_a_file(self):
        out_path = os.path.join(self.root, "report.txt")
        code, _, _ = self.run_cli("--out", out_path)
        self.assertEqual(code, 0)
        with open(out_path, encoding="utf-8") as fh:
            self.assertIn("GEDCOM RECONCILIATION", fh.read())


class CreationPreview(CliCase):
    """--create on a dry run. The riskiest half of a sync, previewed."""

    def test_the_default_report_has_no_creation_section(self):
        _, out, _ = self.run_cli()
        self.assertNotIn("7. CREATION", out)
        self.assertIn("Re-run with --apply to execute", out)

    def test_it_previews_the_plan_and_writes_nothing(self):
        code, out, err = self.run_cli("--create")
        self.assertEqual(code, 0, err)
        self.assertIn("7. CREATION", out)
        self.assertIn("Charted Roots/People/Anna Meyer.md", out)
        self.assertIn("Re-run with --apply --create to execute", out)
        self.assertEqual(self.changed_notes(), [])

    def test_it_shows_the_first_planned_note_in_full(self):
        _, out, _ = self.run_cli("--create")
        self.assertIn("external_id: I2", out)
        self.assertIn("cr_type: person", out)

    def test_the_preview_is_quoted_the_way_it_would_be_written(self):
        # An unquoted [[...]] in frontmatter is invalid YAML; a preview that
        # showed one would send the reader after a bug that is not there.
        _, out, _ = self.run_cli("--create")
        self.assertIn('birth_place: "[[Musterdorf]]"', out)

    def test_it_reports_the_follow_up_passes(self):
        _, out, _ = self.run_cli("--create")
        self.assertRegex(out, r"People rewritten for relationships\s+\d")
        self.assertRegex(out, r"People whose citations: is recomputed\s+\d")

    def test_the_preview_count_is_what_apply_then_creates(self):
        _, preview, _ = self.run_cli("--create")
        planned = int(re.search(r"would create\s+(\d+) notes", preview).group(1))
        code, out, err = self.run_cli("--apply", "--allow-obsidian-open",
                                      "--no-restore-point", "--create")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(planned, len(self.new_notes()))


class Rulings(CliCase):
    """The decisions file: History/gedcom-sync-decisions.json."""

    def seed_conflict(self) -> None:
        # The export says 1824-06-01, the vault says 1822: a conflict, held
        # back by default.
        self.person("Jürgen Muster", cr_id="aaa-111-aaa-111", external_id="I1",
                    external_id_source="gedcom", born="1822")
        self.commit("seed conflict")

    def test_the_dry_run_says_nothing_is_accepted_without_a_file(self):
        _, out, _ = self.run_cli()
        self.assertIn("every coarsen and conflict stays held", out)

    def test_the_dry_run_reports_what_the_rulings_cover(self):
        self.seed_conflict()
        self.rule(external_id="I1", label="Jürgen Muster",
                  accept_conflict=["born"], reason="Corrected upstream.",
                  decided_by="user", date="2026-09-22")
        _, out, _ = self.run_cli()
        self.assertIn("rulings in History/gedcom-sync-decisions.json", out)
        self.assertIn("conflicts covered           1", out)

    def test_a_held_conflict_stays_held_without_a_ruling(self):
        self.seed_conflict()
        code, out, err = self.run_cli("--apply", "--allow-obsidian-open",
                                      "--no-restore-point")
        self.assertEqual(code, 0, out + err)
        self.assertIn("born: 1822", self.read(
            f"{FOLDERS['people']}/Jürgen Muster.md"))

    def test_a_ruling_lets_exactly_that_field_through(self):
        self.seed_conflict()
        self.rule(external_id="I1", label="Jürgen Muster",
                  accept_conflict=["born"], reason="Corrected upstream.",
                  decided_by="user", date="2026-09-22")
        # The decisions file lives in History/, so the entity folders stay
        # clean and no --allow-dirty is needed.
        code, out, err = self.run_cli("--apply", "--allow-obsidian-open",
                                      "--no-restore-point")
        self.assertEqual(code, 0, out + err)
        note = self.read(f"{FOLDERS['people']}/Jürgen Muster.md")
        self.assertIn("born: 1824-06-01", note)

    def test_an_unusable_file_is_an_error_not_a_fallback_to_empty(self):
        # Falling back to "accept nothing" would quietly revert every
        # reviewed ruling, so this must stop the run.
        self.write(os.path.join("History", decisions.FILENAME), "{not json")
        for argv in ([], ["--apply", "--allow-obsidian-open",
                          "--no-restore-point"]):
            with self.subTest(argv or "dry run"):
                code, _, err = self.run_cli(*argv)
                self.assertEqual(code, 2)
                self.assertIn("Decisions file unusable", err)
        self.assertEqual(self.changed_notes(), [])


class ParseOnly(unittest.TestCase):
    """--only used to be accepted and ignored. A typo must not narrow a run."""

    def test_nothing_means_every_entity_type(self):
        self.assertIsNone(gedcom_sync.parse_only(""))
        self.assertIsNone(gedcom_sync.parse_only("  ,  "))

    def test_canonical_names(self):
        self.assertEqual(gedcom_sync.parse_only("person,event"),
                         {"person", "event"})

    def test_the_plural_spelling_the_help_used_to_advertise(self):
        self.assertEqual(gedcom_sync.parse_only("people,sources,citations"),
                         {"person", "source", "citation"})

    def test_case_and_whitespace(self):
        self.assertEqual(gedcom_sync.parse_only(" Person , EVENTS "),
                         {"person", "event"})

    def test_an_alias_and_its_canonical_form_collapse(self):
        self.assertEqual(gedcom_sync.parse_only("person,people"), {"person"})

    def test_an_unknown_name_is_an_error(self):
        for value in ("peeple", "person,peeple", "note"):
            with self.subTest(value):
                with self.assertRaises(ValueError) as caught:
                    gedcom_sync.parse_only(value)
                self.assertIn("unknown entity type", str(caught.exception))

    def test_in_scope(self):
        self.assertTrue(gedcom_sync.in_scope(None, "event"))
        self.assertTrue(gedcom_sync.in_scope({"event"}, "event"))
        self.assertFalse(gedcom_sync.in_scope({"person"}, "event"))


class Scope(CliCase):

    def test_an_unknown_entity_type_stops_the_run(self):
        code, _, err = self.run_cli("--only", "peeple")
        self.assertEqual(code, 2)
        self.assertIn("unknown entity type", err)

    def test_the_report_keeps_only_the_sections_asked_for(self):
        _, out, _ = self.run_cli("--only", "person")
        self.assertIn("scope  --only person", out)
        self.assertIn("1. PERSON", out)
        for section in ("2. SOURCE", "3. EVENT", "4. CITATION", "5. SUPPRESSED"):
            self.assertNotIn(section, out)

    def test_a_plural_name_scopes_the_same_section(self):
        _, out, _ = self.run_cli("--only", "sources")
        self.assertIn("2. SOURCE", out)
        self.assertNotIn("1. PERSON", out)

    def test_it_scopes_what_apply_writes(self):
        code, out, err = self.run_cli("--apply", "--allow-obsidian-open",
                                      "--no-restore-point", "--only", "source")
        self.assertEqual(code, 0, out + err)
        self.assertIn("skipped, not in --only", out)
        # The Person note has four fields the export would fill, and none of
        # them may be written when only Sources are in scope.
        self.assertEqual(self.changed_notes(), [])

    def test_the_same_run_in_scope_does_write(self):
        code, out, err = self.run_cli("--apply", "--allow-obsidian-open",
                                      "--no-restore-point", "--only", "person")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.changed_notes(),
                         ["Charted Roots/People/Jürgen Muster.md"])

    def test_create_refuses_a_partial_scope(self):
        # Events name People by filename and Citations name both, so creating
        # one kind without the others leaves dangling links.
        code, _, err = self.run_cli("--only", "person", "--create")
        self.assertEqual(code, 2)
        self.assertIn("dangling links", err)

    def test_create_accepts_the_full_scope_spelled_out(self):
        code, out, _ = self.run_cli(
            "--only", "person,source,event,citation,place", "--create")
        self.assertEqual(code, 0)
        self.assertIn("7. CREATION", out)

    def test_verify_is_vault_wide(self):
        code, _, err = self.run_cli("--verify", "--only", "person")
        self.assertEqual(code, 2)
        self.assertIn("vault-wide", err)


class PlanLeftovers(CliCase):
    """Two plan outputs that were computed and reported nowhere.

    `already_present` is a GEDCOM event the vault already holds but the
    matcher could not pair, and `skipped_citations` is a citation whose
    subject resolves to no Person. Both cap what creation writes, so a run
    that does not mention them looks like it created everything it found.
    They are hard to provoke from a fixture, so the plan is seeded directly.
    """

    def setUp(self):
        super().setUp()
        real = gedcom_sync.create.plan_creation

        def with_leftovers(*a, **kw):
            plan = real(*a, **kw)
            plan.already_present.append("one unpaired GEDCOM event")
            plan.skipped_citations.append(
                ("no-such-crid", "Kirchenbuch Musterdorf", "birth_date", "Nr. 14"))
            return plan

        gedcom_sync.create.plan_creation = with_leftovers
        self.addCleanup(setattr, gedcom_sync.create, "plan_creation", real)

    def test_the_dry_run_counts_them(self):
        _, out, _ = self.run_cli("--create")
        self.assertRegex(out, r"Events the vault already holds\s+1")
        self.assertRegex(out, r"Citations with no resolvable subject\s+1")

    def test_apply_names_them_as_not_created(self):
        code, out, err = self.run_cli("--apply", "--allow-obsidian-open",
                                      "--no-restore-point", "--create")
        self.assertEqual(code, 0, out + err)
        self.assertIn("1 Events NOT created", out)
        self.assertIn("1 Citations NOT created", out)


class HistoricalPlaces(CliCase):
    """A historical PLAC links through aliases only when the plan approves it."""

    PLAC = "Breslau, Schlesien, Preußen, Deutschland"
    GED_ALIAS = GED.replace("2 DATE 1826\n2 PLAC Musterdorf",
                            f"2 DATE 1826\n2 PLAC {PLAC}")

    def setUp(self):
        super().setUp()
        self.write("FamilyTree.ged", self.GED_ALIAS)
        self.write(f"{FOLDERS['places']}/Wrocław.md", frontmatter(
            cr_type="place", cr_id="ppp-111-ppp-111", title="Wrocław",
            full_name="Wrocław, Poland", place_type="city",
            aliases=["Breslau"]))
        self.commit("places")

    def plan(self, status="approved", raw=None):
        if raw is not None:
            self.write("History/places-plan.json", raw)
            return
        self.write("History/places-plan.json", json.dumps({
            "version": 1,
            "places": {"wroclaw": {"title": "Wrocław", "place_type": "city",
                                   "status": "approved"}},
            "plac": {self.PLAC: {"count": 1, "place": "wroclaw",
                                 "status": status}}},
            ensure_ascii=False))

    def test_sync_links_an_approved_historical_place(self):
        self.plan("approved")
        code, out, err = self.run_cli("--create")
        self.assertEqual(code, 0, err)
        self.assertIn('birth_place: "[[Wrocław]]"', out)

    def test_sync_ignores_an_unapproved_alias_match(self):
        self.plan("proposed")
        code, out, err = self.run_cli("--create")
        self.assertEqual(code, 0, err)
        self.assertNotIn("[[Wrocław]]", out)
        self.assertRegex(out, r"place values left off a new note\s+[1-9]")
        self.assertIn("review with /charted-roots:organize-places", out)

    def test_a_broken_plan_file_does_not_stop_the_sync(self):
        self.plan(raw="{not json")
        code, out, err = self.run_cli("--create")
        self.assertEqual(code, 0, err)
        self.assertIn("places-plan.json", out)
        self.assertIn("alias matching is off", out)
        self.assertNotIn("[[Wrocław]]", out)

    def test_apply_logs_the_broken_plan_warning(self):
        self.plan(raw="{not json")
        self.commit("broken plan")
        code, out, err = self.run_cli("--apply", "--allow-obsidian-open",
                                      "--no-restore-point")
        self.assertEqual(code, 0, out + err)
        self.assertIn("alias matching is off", out)


class Apply(CliCase):

    def apply(self, *argv):
        return self.run_cli("--apply", "--allow-obsidian-open",
                            "--no-restore-point", *argv)

    def reported_count(self, out: str) -> int:
        line = [l for l in out.splitlines()
                if "notes modified. Review with: git diff -- " in l]
        self.assertEqual(len(line), 1, out)
        return int(line[0].split()[0])

    def test_it_refuses_without_a_restore_point(self):
        code, out, err = self.run_cli("--apply", "--allow-obsidian-open")
        self.assertEqual(code, 1)
        self.assertIn("a restore point tags HEAD", out)
        self.assertIn("Refusing to write", err)
        self.assertEqual(self.changed_notes(), [])

    def test_it_refuses_a_dirty_entity_folder(self):
        self.person("Someone New")
        code, out, err = self.run_cli("--apply", "--allow-obsidian-open",
                                      "--no-restore-point")
        self.assertEqual(code, 1)
        self.assertIn("Refusing to write", err)

    def test_the_field_pass_writes_and_counts_exactly_the_diff(self):
        code, out, err = self.apply()
        self.assertEqual(code, 0, out + err)
        changed = self.changed_notes()
        self.assertEqual(changed, ["Charted Roots/People/Jürgen Muster.md"])
        self.assertEqual(self.reported_count(out), len(changed))
        self.assertIn("given_name: Jürgen", self.read(changed[0]))

    def test_creation_counts_each_note_once_however_many_passes_touch_it(self):
        code, out, err = self.apply("--create")
        self.assertEqual(code, 0, out + err)
        changed = self.changed_notes()
        # Anna Meyer is created, then rewritten by the relationship pass; the
        # existing Person is rewritten by the field pass and again for her
        # spouse. Summing the passes double-counts both.
        self.assertIn("Charted Roots/People/Anna Meyer.md", changed)
        self.assertEqual(self.reported_count(out), len(changed))

    def test_limit_caps_the_invariant_detail_it_prints(self):
        # --limit was honoured by --verify and the report but fixed at three
        # here, so the same flag meant two things.
        for i in range(5):
            self.write(f"{FOLDERS['people']}/Invented Type {i}.md",
                       frontmatter(cr_type="hypothesis", cr_id=f"hhh-00{i}-hhh-000"))
        self.commit("five invalid cr_types")
        counts = {}
        for limit in (1, 5):
            code, out, err = self.apply("--limit", str(limit))
            self.assertEqual(code, 0, out + err)
            counts[limit] = sum(1 for line in out.splitlines()
                                if "cr_type=" in line)
            # the first run leaves the entity folders dirty, which the
            # second one would refuse
            self.commit(f"after --limit {limit}")
        self.assertEqual(counts, {1: 1, 5: 5})

    def test_the_sidecar_records_the_gedcom_it_was_built_from(self):
        import json
        self.apply()
        with open(os.path.join(self.root, "History",
                               "gedcom-import-map.json"), encoding="utf-8") as fh:
            payload = json.load(fh)
        self.assertEqual(len(payload["ged_sha256"]), 16)

    def test_a_run_that_regresses_an_invariant_exits_nonzero(self):
        # Seeded after the baseline is taken, so the invariant is broken only
        # by this run -- which is exactly what the after-run suite must catch.
        real = gedcom_sync.apply_mod.rebuild_citation_lists

        def sabotage(cfg, dry=True):
            written = real(cfg, dry=dry)
            self.person("Invented Type", cr_id="zzz-000-zzz-000",
                        cr_type="hypothesis")
            return written

        gedcom_sync.apply_mod.rebuild_citation_lists = sabotage
        self.addCleanup(setattr, gedcom_sync.apply_mod,
                        "rebuild_citation_lists", real)
        code, out, err = self.apply("--create")
        self.assertEqual(code, 1, out)
        self.assertIn("REGRESSED", err)
        self.assertIn("cr_type from the plugin vocabulary", err)



class DryRunMatchesApply(CliCase):
    """The dry run runs the same preflight --apply does."""

    def test_the_dry_run_names_what_apply_would_refuse(self):
        self.write(f"{FOLDERS['people']}/Jürgen Muster.md",
                   "---\ncr_id: aaa-111-aaa-111\ncr_type: person\n"
                   "name: Jürgen Muster\nexternal_id: I1\n"
                   "relations:\n  father: someone\n---\n")
        self.commit("a note the writer refuses")
        code, out, _ = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("WOULD REFUSE", out)
        self.assertIn("key index cannot see", out)
        self.assertEqual(self.changed_notes(), [])

    def test_a_clean_dry_run_has_no_refusal_section(self):
        code, out, _ = self.run_cli()
        self.assertEqual(code, 0)
        self.assertNotIn("WOULD REFUSE", out)


class ScopeWrites(CliCase):

    def apply(self, *argv):
        return self.run_cli("--apply", "--allow-obsidian-open",
                            "--no-restore-point", *argv)

    def sidecar(self) -> str:
        return os.path.join(self.root, "History", gedcom_sync.EVENT_MAP)

    def test_the_sidecar_is_skipped_with_the_event_pass(self):
        code, out, err = self.apply("--only", "person")
        self.assertEqual(code, 0, out + err)
        self.assertFalse(os.path.exists(self.sidecar()))

    def test_the_sidecar_is_written_when_events_are_in_scope(self):
        code, out, err = self.apply("--only", "event")
        self.assertEqual(code, 0, out + err)
        self.assertTrue(os.path.exists(self.sidecar()))

    def test_a_scope_with_no_write_pass_is_refused(self):
        for scope in ("place", "citation", "place,citation"):
            with self.subTest(scope):
                code, out, err = self.apply("--only", scope)
                self.assertEqual(code, 2)
                self.assertIn("nothing to write", err)
                self.assertEqual(out, "")

    def test_out_of_scope_matchers_do_not_run(self):
        real = gedcom_sync.match.match_people

        def fail(*a, **kw):
            raise AssertionError("match_people ran out of scope")

        gedcom_sync.match.match_people = fail
        self.addCleanup(setattr, gedcom_sync.match, "match_people", real)
        code, out, err = self.run_cli("--only", "source")
        self.assertEqual(code, 0, out + err)
        self.assertIn("2. SOURCE", out)


class ModeFlags(CliCase):
    """A flag outside the mode it belongs to is refused, not ignored."""

    def test_verify_and_apply_are_exclusive(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                gedcom_sync.main(["--vault", self.root, "--verify", "--apply"])
        self.assertEqual(caught.exception.code, 2)

    def test_misplaced_flags(self):
        for argv, flag in ((["--apply", "--out", "r.txt"], "--out"),
                           (["--verify", "--create"], "--create"),
                           (["--verify", "--adopt-by-name"], "--adopt-by-name"),
                           (["--verify", "--ged", "x.ged"], "--ged"),
                           (["--allow-dirty"], "--allow-dirty"),
                           (["--no-restore-point"], "--no-restore-point")):
            with self.subTest(argv):
                code, out, err = self.run_cli(*argv)
                self.assertEqual(code, 2)
                self.assertIn(f"{flag} does not apply to", err)
                self.assertEqual(out, "")
        self.assertEqual(self.changed_notes(), [])


class Inputs(CliCase):

    def test_a_missing_vault_is_an_error_not_a_clean_pass(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = gedcom_sync.main(
                ["--vault", os.path.join(self.root, "nope")])
        self.assertEqual(code, 2)
        self.assertIn("No vault at", err.getvalue())

    def test_unreadable_plugin_settings_are_an_error(self):
        self.write(".obsidian/plugins/charted-roots/data.json", "{not json")
        code, _, err = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("Plugin settings unreadable", err)

    def test_an_undecodable_gedcom_is_an_error(self):
        with open(os.path.join(self.root, "FamilyTree.ged"), "wb") as fh:
            fh.write(b"0 HEAD\n1 NOTE \xff\xfe\xfa\n0 TRLR\n")
        code, _, err = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("GEDCOM unreadable", err)


if __name__ == "__main__":
    unittest.main()
