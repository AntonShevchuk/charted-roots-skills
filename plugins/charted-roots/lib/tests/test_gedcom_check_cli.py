"""End-to-end runs of gedcom_check.py against throwaway GEDCOM files."""

from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest

import gedcom_check

from .test_gedcheck import HEAD, TWO_SAME_BIRTHS, indi

CLEAN = indi("1 BIRT", "2 DATE 1 JUN 1824", "2 PLAC Musterdorf")
MANY = "".join(
    f"0 @I{n}@ INDI\n1 NAME Anna /Muster{n}/\n1 BIRT\n2 DATE 1 JUN 1824\n"
    f"1 BIRT\n2 DATE 1 JUN 1824\n" for n in range(1, 4)) + "0 TRLR\n"


class CliCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = tmp.name

    def put(self, text, name="t.ged", raw=None):
        path = os.path.join(self.dir, name)
        with open(path, "wb") as fh:
            fh.write(raw if raw is not None else (HEAD + text).encode("utf-8"))
        return path

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = gedcom_check.main(list(argv))
        return code, out.getvalue(), err.getvalue()


class Cli(CliCase):
    def test_clean_file_exits_0(self):
        code, out, _ = self.run_cli("--ged", self.put(CLEAN))
        self.assertEqual(code, 0)
        self.assertIn("No findings.", out)

    def test_findings_exit_1_and_are_listed(self):
        code, out, _ = self.run_cli("--ged", self.put(TWO_SAME_BIRTHS))
        self.assertEqual(code, 1)
        self.assertIn("dup-vital", out)
        self.assertIn("in Ancestry:", out)
        self.assertIn("1 findings (1 fix, 0 review)", out)

    def test_json_is_complete_and_parseable(self):
        code, out, _ = self.run_cli("--ged", self.put(TWO_SAME_BIRTHS), "--json")
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual(data["host"], "Ancestry")
        self.assertEqual({"check", "group", "kind", "who", "line", "what",
                          "fix"}, set(data["findings"][0]))
        self.assertEqual(
            {"ged", "host", "exported", "sha256", "warnings", "findings"},
            set(data))

    def test_limit_zero_shows_all(self):
        path = self.put(MANY)
        _, out, _ = self.run_cli("--ged", path, "--limit", "1")
        self.assertIn("... and 2 more (--limit 0 shows all)", out)
        _, out, _ = self.run_cli("--ged", path, "--limit", "0")
        self.assertNotIn("more (--limit", out)
        for n in (1, 2, 3):
            self.assertIn(f"Muster{n}", out)

    def test_only_unknown_group_exits_2(self):
        code, _, err = self.run_cli("--ged", self.put(CLEAN), "--only", "bogus")
        self.assertEqual(code, 2)
        self.assertIn("unknown group", err)

    def test_only_limits_groups(self):
        code, out, _ = self.run_cli("--ged", self.put(TWO_SAME_BIRTHS),
                                    "--only", "places")
        self.assertEqual(code, 0)
        self.assertIn("No findings.", out)

    def test_missing_file_exits_2(self):
        path = os.path.join(self.dir, "nope.ged")
        code, _, err = self.run_cli("--ged", path)
        self.assertEqual(code, 2)
        self.assertIn(f"No GEDCOM at {path}", err)

    def test_undecodable_file_exits_2_without_traceback(self):
        path = self.put("", raw=b"0 HEAD\n1 NAME \xff\xfe\n")
        code, _, err = self.run_cli("--ged", path)
        self.assertEqual(code, 2)
        self.assertIn("GEDCOM unreadable", err)
        self.assertNotIn("Traceback", err)

    def test_skipped_lines_warn_in_header(self):
        path = self.put("garbage line\n" + CLEAN)
        code, out, err = self.run_cli("--ged", path)
        self.assertNotEqual(code, 2)
        self.assertIn("WARNING", out)
        self.assertIn("skipped 1 line", out)
        self.assertEqual(err, "")

    def test_out_writes_the_report(self):
        path = self.put(TWO_SAME_BIRTHS)
        report = os.path.join(self.dir, "report.txt")
        code, out, _ = self.run_cli("--ged", path, "--out", report)
        self.assertEqual(code, 1)
        with open(report, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), out)

    def test_writes_nothing_else(self):
        path = self.put(TWO_SAME_BIRTHS)
        with open(path, "rb") as fh:
            before = fh.read()
        self.run_cli("--ged", path)
        self.run_cli("--ged", path, "--json")
        self.assertEqual(os.listdir(self.dir), ["t.ged"])
        report = os.path.join(self.dir, "r.txt")
        self.run_cli("--ged", path, "--out", report)
        self.assertEqual(sorted(os.listdir(self.dir)), ["r.txt", "t.ged"])
        with open(path, "rb") as fh:
            self.assertEqual(fh.read(), before)


if __name__ == "__main__":
    unittest.main()
