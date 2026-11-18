"""End-to-end runs of places_plan.py against a throwaway vault."""

from __future__ import annotations

import contextlib
import io
import os
import subprocess

import places_plan
from crsync import placeplan, vault

from .helpers import FOLDERS, VaultCase
from .test_placeplan import _chain

GED = """0 HEAD
1 GEDC
2 VERS 5.5.1
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Anna /Muster/
1 BIRT
2 DATE 1824
2 PLAC Breslau, Schlesien, Preußen
0 TRLR
"""


class CliCase(VaultCase):
    def setUp(self):
        super().setUp()
        self.write("FamilyTree.ged", GED)
        self.git("init", "-q")
        self.commit("base")

    def git(self, *args) -> str:
        return subprocess.run(["git", "-C", self.root, *args],
                              capture_output=True, text=True).stdout

    def commit(self, message="fixture") -> None:
        self.git("add", "-A")
        self.git("-c", "user.email=t@t", "-c", "user.name=t",
                 "commit", "-q", "-m", message)

    def run_cli(self, *argv) -> tuple:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = places_plan.main([argv[0], "--vault", self.root, *argv[1:]])
        return code, out.getvalue(), err.getvalue()

    def save_plan(self, plan=None):
        placeplan.save(self.root, plan or _chain())
        self.commit("plan")

    def places(self) -> list:
        return sorted(os.listdir(os.path.join(self.root, FOLDERS["places"])))


class Extract(CliCase):
    def test_extract_writes_the_plan(self):
        code, out, _ = self.run_cli("extract")
        self.assertEqual(code, 0, out)
        plan = placeplan.load(self.root)
        self.assertEqual(plan.plac["Breslau, Schlesien, Preußen"].count, 1)

    def test_a_missing_gedcom_is_exit_2(self):
        code, _, err = self.run_cli("extract", "--ged", "nope.ged")
        self.assertEqual(code, 2)
        self.assertIn("No GEDCOM", err)


class Check(CliCase):
    def test_check_reports_problems_and_writes_nothing(self):
        plan = _chain()
        plan.places["wroclaw"].parent = "missing"
        self.save_plan(plan)
        code, out, _ = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("not in plan", out)
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_a_clean_plan_checks_ok(self):
        self.save_plan()
        self.assertEqual(self.run_cli("check")[0], 0)


class Apply(CliCase):
    def test_the_default_run_is_a_dry_run(self):
        self.save_plan()
        code, out, _ = self.run_cli("apply")
        self.assertEqual(code, 0, out)
        self.assertIn("Wrocław.md", out)
        self.assertEqual(self.places(), [])

    def test_apply_refuses_a_plan_that_fails_check(self):
        plan = _chain()
        plan.places["wroclaw"].place_type = "galaxy"
        self.save_plan(plan)
        code, out, _ = self.run_cli(
            "apply", "--apply", "--allow-obsidian-open", "--no-restore-point")
        self.assertEqual(code, 1)
        self.assertEqual(self.places(), [])

    def test_apply_without_a_restore_point_refuses(self):
        self.save_plan()
        self.git("tag", "pre-gedcom-sync-20260101-0000")
        code, out, _ = self.run_cli("apply", "--apply", "--allow-obsidian-open")
        self.assertEqual(code, 1)
        self.assertIn("pre-organize-places-", out)
        self.assertEqual(self.places(), [])

    def test_apply_writes_with_a_restore_point(self):
        self.save_plan()
        self.git("tag", "pre-organize-places-20260101-0000")
        code, out, err = self.run_cli(
            "apply", "--apply", "--allow-obsidian-open")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.places(), [
            "Lower Silesian Voivodeship.md", "Poland.md", "Wrocław.md"])
        self.assertEqual(placeplan.load(self.root).places["poland"].status,
                         "created")

    def test_a_write_failure_names_the_restore_tag_and_exits_1(self):
        self.save_plan()
        real = vault.write_atomic

        def boom(path, text):
            raise OSError(28, "No space left on device")
        vault.write_atomic = boom
        try:
            code, out, err = self.run_cli(
                "apply", "--apply", "--allow-obsidian-open",
                "--no-restore-point")
        finally:
            vault.write_atomic = real
        self.assertEqual(code, 1, out + err)
        self.assertIn("No space left", err)
        self.assertIn("pre-organize-places-", err)
        self.assertEqual(len(err.strip().splitlines()), 1, err)

    def test_override_flags_need_apply(self):
        self.save_plan()
        for flag in ("--allow-obsidian-open", "--allow-dirty",
                     "--no-restore-point"):
            code, _, err = self.run_cli("apply", flag)
            self.assertEqual(code, 2, flag)
            self.assertIn(flag, err)

    def test_an_unreadable_plan_is_exit_2(self):
        self.write(placeplan.PLAN_PATH, "{not json")
        for cmd in ("check", "apply"):
            code, _, err = self.run_cli(cmd)
            self.assertEqual(code, 2, cmd)
            self.assertIn("cannot read", err)
