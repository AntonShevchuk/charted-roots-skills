"""End-to-end runs of vault_verify.py against a throwaway vault."""

from __future__ import annotations

import contextlib
import io
import os
import re
import unittest

import vault_verify

from .helpers import FOLDERS, VaultCase, frontmatter


class VerifyCase(VaultCase):

    def setUp(self):
        super().setUp()
        self.write(f"{FOLDERS['places']}/Musterdorf.md", frontmatter(
            cr_type="place", cr_id="ppp-000-ppp-000", title="Musterdorf",
            full_name="Musterdorf", place_type="locality"))
        self.person("Jürgen Muster", cr_id="aaa-111-aaa-111", born="1824")

    def run_cli(self, *argv, vault=None) -> tuple:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = vault_verify.main(["--vault", vault or self.root, *argv])
        return code, out.getvalue(), err.getvalue()


class Verify(VerifyCase):

    def test_it_passes_on_a_consistent_vault(self):
        code, out, _ = self.run_cli()
        self.assertEqual(code, 0, out)
        self.assertIn("checks passed", out)

    def test_it_fails_and_names_the_check(self):
        self.write(f"{FOLDERS['people']}/Broken.md", "---\ncr_type: person\n")
        code, out, _ = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("checks FAILED", out)
        self.assertIn("frontmatter blocks close", out)

    def test_it_finds_a_line_the_key_index_cannot_see(self):
        self.write(f"{FOLDERS['people']}/Nested.md",
                   "---\ncr_type: person\ncr_id: nnn-000-nnn-000\n"
                   "relations:\n  father: someone\n---\n")
        code, out, _ = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("every frontmatter line parses", out)
        self.assertIn("father: someone", out)

    def test_limit_caps_the_detail_it_prints(self):
        for i in range(5):
            self.write(f"{FOLDERS['people']}/Invented Type {i}.md",
                       frontmatter(cr_type="hypothesis", cr_id=f"hhh-00{i}-hhh-000"))
        for limit in (1, 5):
            with self.subTest(limit=limit):
                code, out, _ = self.run_cli("--limit", str(limit))
                self.assertEqual(code, 1)
                self.assertEqual(sum(1 for line in out.splitlines()
                                     if "cr_type=" in line), limit)

    def test_it_takes_no_gedcom_flags(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                vault_verify.main(["--vault", self.root, "--apply"])
        self.assertEqual(caught.exception.code, 2)


class Inputs(VerifyCase):

    def test_a_missing_vault_is_an_error_not_a_clean_pass(self):
        code, _, err = self.run_cli(vault=os.path.join(self.root, "nope"))
        self.assertEqual(code, 2)
        self.assertIn("No vault at", err)

    def test_unreadable_plugin_settings_are_an_error(self):
        self.write(".obsidian/plugins/charted-roots/data.json", "{not json")
        code, _, err = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("Plugin settings unreadable", err)


class AttachmentCount(VerifyCase):

    def test_a_scan_in_two_formats_counts_twice(self):
        # X.jpg beside X.pdf is common in the Archive; halving the name set
        # counted it as one and a half.
        def count() -> int:
            _, out, _ = self.run_cli()
            return int(re.search(r"(\d+) attachments", out).group(1))

        before = count()
        for name in ("X.jpg", "X.pdf", "Y.jpg"):
            self.write(f"Charted Roots/Archive/{name}", "")
        self.assertEqual(count() - before, 3)


if __name__ == "__main__":
    unittest.main()
