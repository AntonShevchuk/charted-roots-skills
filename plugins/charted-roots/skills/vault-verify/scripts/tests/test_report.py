"""The apply log.

Every line `--apply` prints lives in `report.ApplyLog`, which is what keeps
the two halves of the tool from describing the same run differently. It takes
its sinks as callables, so this asserts the text without capturing stdout --
and in particular that a refusal goes to stderr, where a caller piping the
report to a file still sees it.
"""

from __future__ import annotations

import unittest

from crsync import decisions, match, report, verify
from crsync.apply import Precondition


def action(key="I1", label="Test Person", path="People/Test Person.md"):
    return match.Action(kind="update", entity="person", key=key, label=label,
                        path=path)


class Log(unittest.TestCase):

    def setUp(self):
        self.out: list = []
        self.err: list = []
        self.log = report.ApplyLog(out=self.out.append, err=self.err.append,
                                   limit=2)

    def test_preconditions_show_the_remedy_only_when_blocking(self):
        self.log.preconditions([
            Precondition("Obsidian is closed", True, "not running", "quit it"),
            Precondition("clean in git", False, "20 modified", "commit first"),
        ])
        self.assertEqual(self.out, [
            "Preconditions",
            "  [OK   ] Obsidian is closed: not running",
            "  [BLOCK] clean in git: 20 modified",
            "            commit first",
        ])

    def test_a_refusal_goes_to_stderr(self):
        self.log.refuse_preconditions()
        self.assertEqual(self.out, [])
        self.assertEqual(self.err, ["\nRefusing to write."])

    def test_the_baseline_names_what_was_already_failing(self):
        self.log.baseline([verify.Result("a check", True, "fine"),
                           verify.Result("another", False, "2 broken")])
        self.assertEqual(self.out, ["\nBaseline invariants",
                                    "  [note] pre-existing: another -- 2 broken"])

    def test_no_scope_line_without_only(self):
        self.log.scope(None)
        self.assertEqual(self.out, [])

    def test_the_scope_line_is_sorted(self):
        self.log.scope({"source", "person"})
        self.assertEqual(self.out, ["\nScope: --only person, source -- "
                                    "every other pass is skipped"])

    def test_rulings_with_no_file(self):
        self.log.rulings(decisions.Decisions())
        self.assertIn("every coarsen and conflict stays held", self.out[0])

    def test_rulings_with_a_file(self):
        self.log.rulings(decisions.Decisions(
            entries=[{"external_id": "I1"}],
            coarsen_exempt={"I1": {"name"}},
            conflict_accepted={"I1": {"born", "died"}}))
        self.assertIn("1 in History/gedcom-sync-decisions.json", self.out[0])
        self.assertIn("1 coarsen exemptions, 2 accepted conflicts", self.out[0])

    def test_the_three_case_verdicts(self):
        for n, direction, needle in ((0, 0, "none"), (4, 1, "uniform (+1)"),
                                     (4, -1, "uniform (-1)"), (4, 0, "MIXED")):
            with self.subTest(f"{n}/{direction}"):
                self.out.clear()
                self.log.case(n, direction)
                self.assertIn(needle, self.out[0])

    def test_blocked_gives_a_reason_per_action_and_caps_the_detail(self):
        self.log.blocked([(action("I1"), "no note at that path in the index"),
                          (action("I2"), "frontmatter block never closes"),
                          (action("I3"), "whatever")])
        self.assertEqual(self.out, [])
        self.assertIn("could not be written", self.err[0])
        self.assertIn("<- I1", self.err[1])
        self.assertIn("no note at that path", self.err[2])
        self.assertIn("<- I2", self.err[3])
        self.assertIn("never closes", self.err[4])
        self.assertEqual(self.err[5], "  ... and 1 more")
        self.assertIn("Refusing to write", self.err[6])

    def test_the_applying_line_mentions_case_only_when_it_is_safe(self):
        self.log.applying(0)
        self.log.applying(1)
        self.assertNotIn("case", self.out[0])
        self.assertIn("+ case", self.out[1])

    def test_a_skipped_pass_lines_up_with_a_written_one(self):
        self.log.field_pass("person", [(None, ["a", "b"])], [(None, ["c"])])
        self.log.pass_skipped("event")
        written, skipped = self.out
        self.assertIn("person      1 notes,    2 fields written,    1 held back",
                      written)
        self.assertEqual(skipped, "  event       - skipped, not in --only")
        # The entity name occupies the same columns either way, so a scoped
        # run's output still reads as a table.
        self.assertEqual(written[:10], "  person  ")
        self.assertEqual(skipped[:10], "  event   ")

    def test_the_event_pass(self):
        self.log.event_pass([(None, ["a"])], [(None, ["b", "c"])])
        self.assertIn("event       1 notes,    1 fields written,    2 held back",
                      self.out[0])

    def test_the_final_count_and_the_two_failure_lines(self):
        self.log.done(41, ["Family/People", "Family/Events"])
        self.assertEqual(self.out[0],
                         "\n41 notes modified. "
                         "Review with: git diff -- 'Family/People' 'Family/Events'")
        self.log.regressed(["a check", "another"])
        self.log.lost([1, 2])
        self.assertEqual(self.err[0], "\nREGRESSED: a check, another")
        self.assertIn("2 planned changes were never written", self.err[1])

    def test_it_defaults_to_stdout_and_stderr(self):
        log = report.ApplyLog()
        self.assertIsNotNone(log.out)
        self.assertIsNotNone(log.err)
        self.assertEqual(log.limit, 10)


class Header(unittest.TestCase):
    """The dry-run header reports the probe's three answers, not two."""

    def render(self, obsidian):
        from crsync import config, gedcom
        cfg = config.Config(root="/x", settings={})
        tree = gedcom.Tree(header={"source": "s", "version": "5.5.1"})

        class FakeEventMatch:
            pairs, unkeyed, arbitrary, uncreated = [], [], [], []

            def counts(self):
                return {}

        class FakeCitationMatch:
            matched, uncreated, duplicates, unresolved = [], [], [], []

        class FakePlaces:
            invisible: list = []

        import os
        import tempfile
        fd, path = tempfile.mkstemp()
        os.close(fd)
        self.addCleanup(os.unlink, path)
        return report.render(cfg, tree, path, match.Plan(), match.Plan(),
                             FakeEventMatch(), FakeCitationMatch(),
                             FakePlaces(), obsidian)

    def test_the_three_states(self):
        self.assertIn("Obsidian: closed", self.render(False))
        self.assertIn("Obsidian: RUNNING -- apply would refuse",
                      self.render(True))
        self.assertIn("Obsidian: cannot tell -- apply would refuse",
                      self.render(None))


class Sha(unittest.TestCase):

    def test_the_digest_is_short_and_stable(self):
        import os
        import tempfile
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, "w") as fh:
            fh.write("0 HEAD\n")
        self.addCleanup(os.unlink, path)
        self.assertEqual(len(report.sha256(path)), 16)
        self.assertEqual(report.sha256(path), report.sha256(path))


if __name__ == "__main__":
    unittest.main()
