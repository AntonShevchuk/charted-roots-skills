"""The invariant suite.

Every check gets a vault that passes it and a vault that breaks it exactly
once. A check that cannot fail is worse than no check: `--apply` compares the
suite before and after a run and calls a regression on the difference.
"""

from __future__ import annotations

import unittest

from crsync import verify

from .helpers import FOLDERS, VaultCase, frontmatter


class CleanVault(VaultCase):
    """A small vault that satisfies all twelve invariants."""

    def setUp(self):
        super().setUp()
        self.person("Father Name", cr_id="fff-000-fff-000",
                    children=['"[[Child Name]]"'], children_id=["ccc-000-ccc-000"])
        self.person("Child Name", cr_id="ccc-000-ccc-000",
                    born="1850", birth_place='"[[Musterdorf]]"',
                    father='"[[Father Name]]"', father_id="fff-000-fff-000",
                    citations=['"[[Citation - Kirchenbuch - Child Name birth_date]]"'])
        self.citation("Citation - Kirchenbuch - Child Name birth_date",
                      cr_id="cit-000-cit-000",
                      source='"[[Kirchenbuch Musterdorf]]"',
                      subject='"[[Child Name]]"',
                      subject_id="ccc-000-ccc-000",
                      fact="birth_date", page='"Nr. 14"')
        self.write(f"{FOLDERS['sources']}/Kirchenbuch Musterdorf.md", frontmatter(
            cr_type="source", cr_id="sss-000-sss-000", title="Kirchenbuch Musterdorf",
            source_type="church_record", confidence="high"))
        self.write(f"{FOLDERS['places']}/Preußen.md", frontmatter(
            cr_type="place", cr_id="ppp-000-ppp-000", title="Preußen",
            place_type="country"))
        self.write(f"{FOLDERS['places']}/Musterdorf.md", frontmatter(
            cr_type="place", cr_id="ppp-111-ppp-111", title="Musterdorf",
            place_type="locality", parent_place='"[[Preußen]]"',
            parent_place_id="ppp-000-ppp-000"))
        self.write(f"{FOLDERS['events']}/Birth of Child Name.md", frontmatter(
            cr_type="event", cr_id="eee-000-eee-000", title="Birth of Child Name",
            event_type="birth", date="1850", date_precision="year",
            place='"[[Musterdorf]]"', sources=['"[[Kirchenbuch Musterdorf]]"']))

    def index(self) -> verify.Index:
        return verify.Index(self.cfg)

    def assertPasses(self, check):
        result = check(self.index())
        self.assertTrue(result.ok, f"{result.name}: {result.detail}\n"
                                   + "\n".join(str(i) for i in result.items))

    def assertFails(self, check, needle=""):
        result = check(self.index())
        self.assertFalse(result.ok, f"{result.name} passed but should not")
        if needle:
            self.assertTrue(any(needle in str(i) for i in result.items),
                            f"{needle!r} not in {result.items}")
        return result


class Baseline(CleanVault):

    def test_the_whole_suite_passes(self):
        results = verify.run(self.cfg)
        failed = [f"{r.name}: {r.detail}" for r in results if not r.ok]
        self.assertEqual(failed, [])
        self.assertEqual(len(results), len(verify.CHECKS))

    def test_run_reuses_a_prepared_index(self):
        idx = self.index()
        self.assertEqual(len(verify.run(self.cfg, idx)), len(verify.CHECKS))


class Violations(CleanVault):

    def test_unterminated_frontmatter(self):
        self.write(f"{FOLDERS['people']}/Broken.md", "---\ncr_type: person\n")
        self.assertFails(verify.check_frontmatter_parses, "Broken.md")

    def test_a_frontmatter_line_the_key_index_cannot_see(self):
        self.write(f"{FOLDERS['people']}/Nested.md",
                   "---\ncr_type: person\ncr_id: nnn-000-nnn-000\n"
                   "relations:\n  father: someone\n---\n")
        result = self.assertFails(verify.check_frontmatter_lines, "father: someone")
        self.assertIn("Nested.md", result.items[0])

    def test_a_list_item_and_a_blank_line_are_fine(self):
        self.write(f"{FOLDERS['people']}/Listy.md",
                   "---\ncr_type: person\ncr_id: lll-000-lll-000\n"
                   "aliases:\n  - One\n  -\n\nsex: F\n---\n")
        self.assertPasses(verify.check_frontmatter_lines)

    def test_duplicate_cr_id(self):
        self.person("Twin Note", cr_id="ccc-000-ccc-000")
        self.assertFails(verify.check_cr_id_unique, "ccc-000-ccc-000")

    def test_invented_cr_type(self):
        self.write(f"{FOLDERS['people']}/Hypothesis Note.md",
                   frontmatter(cr_type="hypothesis", cr_id="hhh-000-hhh-000"))
        self.assertFails(verify.check_cr_type_valid, "hypothesis")

    def test_padded_filename(self):
        self.write(f"{FOLDERS['people']}/Trailing Space .md",
                   frontmatter(cr_type="person", cr_id="ttt-000-ttt-000"))
        self.assertFails(verify.check_filenames, "Trailing Space")

    def test_colliding_basenames(self):
        self.write(f"{FOLDERS['sources']}/Child Name.md",
                   frontmatter(cr_type="source", cr_id="xxx-000-xxx-000",
                               source_type="census"))
        self.assertFails(verify.check_filenames, "basename not unique")

    def test_citation_subject_id_drift(self):
        self.citation("Citation - Kirchenbuch - Child Name death_date",
                      cr_id="ccc-999-ccc-999",
                      source='"[[Kirchenbuch Musterdorf]]"',
                      subject='"[[Child Name]]"', subject_id="wrong-id",
                      fact="death_date")
        self.assertFails(verify.check_citation_subject_ids, "wrong-id")

    def test_citation_not_listed_on_its_subject(self):
        self.citation("Citation - Kirchenbuch - Child Name death_date",
                      cr_id="ccc-888-ccc-888",
                      source='"[[Kirchenbuch Musterdorf]]"',
                      subject='"[[Child Name]]"', subject_id="ccc-000-ccc-000",
                      fact="death_date")
        self.assertFails(verify.check_citation_backlinks, "not in [[Child Name]]")

    def test_phantom_citations_entry(self):
        self.person("Child Name", cr_id="ccc-000-ccc-000", born="1850",
                    father='"[[Father Name]]"', father_id="fff-000-fff-000",
                    citations=['"[[Citation - Kirchenbuch - Child Name birth_date]]"',
                               '"[[Citation - Kirchenbuch - Child Name death_date]]"'])
        result = self.assertFails(verify.check_citation_backlinks,
                                  "is not a Citation")
        self.assertIn("1 phantom", result.detail)

    def test_desynchronised_id_companion(self):
        self.person("Father Name", cr_id="fff-000-fff-000",
                    children=['"[[Child Name]]"', '"[[Second Child]]"'],
                    children_id=["ccc-000-ccc-000"])
        self.assertFails(verify.check_id_companions, "children has 2")

    def test_id_pointing_at_the_wrong_note(self):
        self.person("Child Name", cr_id="ccc-000-ccc-000", born="1850",
                    father='"[[Father Name]]"', father_id="ppp-000-ppp-000",
                    citations=['"[[Citation - Kirchenbuch - Child Name birth_date]]"'])
        self.assertFails(verify.check_id_targets, "father_id")

    def test_dangling_wikilink_in_the_body(self):
        self.person("Child Name", "See [[No Such Note]].\n",
                    cr_id="ccc-000-ccc-000", born="1850",
                    father='"[[Father Name]]"', father_id="fff-000-fff-000",
                    citations=['"[[Citation - Kirchenbuch - Child Name birth_date]]"'])
        self.assertFails(verify.check_links, "No Such Note")

    def test_event_with_a_precision_but_no_date(self):
        self.write(f"{FOLDERS['events']}/Death of Child Name.md", frontmatter(
            cr_type="event", cr_id="eee-111-eee-111", event_type="death",
            date_precision="exact"))
        self.assertFails(verify.check_event_shape, "Death of Child Name")

    def test_an_undated_event_is_fine_when_it_says_so(self):
        self.write(f"{FOLDERS['events']}/Death of Child Name.md", frontmatter(
            cr_type="event", cr_id="eee-111-eee-111", event_type="death",
            date_precision="unknown"))
        self.assertPasses(verify.check_event_shape)

    def test_unregistered_source_type(self):
        self.write(f"{FOLDERS['sources']}/Some Document.md", frontmatter(
            cr_type="source", cr_id="sss-111-sss-111", source_type="document"))
        self.assertFails(verify.check_source_types, "document")

    def test_a_registered_custom_source_type_is_accepted(self):
        self.cfg.settings["customSourceTypes"] = [{"id": "finding_aid"}]
        self.write(f"{FOLDERS['sources']}/A Finding Aid.md", frontmatter(
            cr_type="source", cr_id="sss-222-sss-222", source_type="finding_aid"))
        self.assertPasses(verify.check_source_types)

    def test_place_type_outside_the_closed_list(self):
        self.write(f"{FOLDERS['places']}/Some Village.md", frontmatter(
            cr_type="place", cr_id="ppp-222-ppp-222", place_type="village"))
        self.assertFails(verify.check_place_types, "village")


class Regressions(unittest.TestCase):
    """What --apply calls a regression: passed before the run, fails after."""

    def results(self, *pairs) -> list:
        return [verify.Result(name, ok) for name, ok in pairs]

    def test_a_check_that_starts_failing(self):
        before = self.results(("a", True), ("b", True))
        after = self.results(("a", True), ("b", False))
        self.assertEqual(verify.regressions(before, after), ["b"])

    def test_a_pre_existing_failure_is_not_a_regression(self):
        before = self.results(("a", False), ("b", True))
        after = self.results(("a", False), ("b", True))
        self.assertEqual(verify.regressions(before, after), [])

    def test_a_check_the_run_fixed(self):
        before = self.results(("a", False))
        after = self.results(("a", True))
        self.assertEqual(verify.regressions(before, after), [])

    def test_an_inserted_check_does_not_shift_the_comparison(self):
        # Pairing by position reports "a" -- which was already failing -- as
        # this run's fault, and misses nothing else. Pairing by name gives
        # the right answer, which is that nothing regressed.
        before = self.results(("a", False), ("b", True))
        after = self.results(("new", True), ("a", False), ("b", True))
        positional = [x.name for x, y in zip(after, before)
                      if not x.ok and y.ok]
        self.assertEqual(positional, ["a"])
        self.assertEqual(verify.regressions(before, after), [])

    def test_a_check_that_only_exists_after_counts_as_one(self):
        before = self.results(("a", True))
        after = self.results(("a", True), ("brand new", False))
        self.assertEqual(verify.regressions(before, after), ["brand new"])

    def test_nothing_at_all(self):
        self.assertEqual(verify.regressions([], []), [])


class Masking(CleanVault):

    def test_history_quotes_dead_links_by_design(self):
        # A run record names notes it deleted. Reporting those as broken makes
        # the check useless, so they are counted separately.
        self.write("History/A Past Pass.md",
                   "Deleted `[[Some Deleted Note]]`, and:\n\n"
                   "```\n[[Another Deleted Note]]\n```\n"
                   "and [[A Third Deleted Note]].\n")
        result = verify.check_links(self.index())
        self.assertTrue(result.ok, result.items)
        self.assertIn("in History/", result.detail)
        self.assertIn("(1 more", result.detail)

    def test_mask_code_keeps_the_line_count(self):
        text = "a\n```\nb\nc\n```\nd\n"
        self.assertEqual(verify.mask_code(text).count("\n"), text.count("\n"))

    def test_link_target_strips_alias_and_anchor(self):
        self.assertEqual(verify.link_target("Note|shown"), "Note")
        self.assertEqual(verify.link_target("Note#Heading"), "Note")
        self.assertEqual(verify.link_target(r"Note\\"), "Note")


class DotFolders(CleanVault):

    def test_notes_in_a_dot_folder_are_not_indexed(self):
        # Obsidian ignores .claude/, .obsidian/ and the like; two SKILL.md
        # files there collided as vault notes.
        for skill in ("one", "two"):
            self.write(f".claude/skills/{skill}/SKILL.md", "# Skill\n")
        self.write(".claude/Child Name.md", "# Not a vault note\n")
        self.assertPasses(verify.check_filenames)
        self.assertFalse(any("/.claude/" in p for p in self.index().notes))


class PersonDates(CleanVault):

    def test_a_validator_clean_form_passes(self):
        self.person("Circa Name", cr_id="cir-000-cir-000", born='"c. 1804"',
                    died='"1850 to 1858"')
        self.assertPasses(verify.check_person_dates)

    def test_a_gedcom_qualifier_fails(self):
        self.person("Before Name", cr_id="bef-000-bef-000", born="BEF 1909")
        self.assertFails(verify.check_person_dates, "Before Name: born='BEF 1909'")


class PersonPlaces(CleanVault):

    def test_a_link_alias_or_plain_title_resolves(self):
        self.person("Wed Name", cr_id="wed-000-wed-000", spouse1='"[[Child Name]]"',
                    spouse1_marriage_location='"[[Musterdorf]]"',
                    death_place="Musterdorf")
        self.assertPasses(verify.check_person_places)

    def test_a_gedcom_place_string_is_a_missing_place_note(self):
        self.person("Wed Name", cr_id="wed-000-wed-000", spouse1='"[[Child Name]]"',
                    spouse1_marriage_location='"Musterdorf, Kreis X, Preußen"')
        self.assertFails(verify.check_person_places, "Musterdorf, Kreis X, Preußen")

    def test_a_location_without_a_spouse_slot_is_not_read(self):
        # The plugin walks spouseN while spouseN or spouseN_id exists.
        self.person("Lone Name", cr_id="lon-000-lon-000",
                    spouse2_marriage_location='"Nowhere"')
        self.assertPasses(verify.check_person_places)


class Resolution(CleanVault):

    def test_an_attachment_resolves_by_stem_or_full_name(self):
        self.write(f"{FOLDERS['people']}/../Archive/Scan_1854.jpg", "")
        idx = self.index()
        self.assertTrue(idx.resolves("Scan_1854"))
        self.assertTrue(idx.resolves("Scan_1854.jpg"))
        self.assertFalse(idx.resolves("Scan_1855"))

    def test_a_note_resolves_by_path_or_explicit_extension(self):
        idx = self.index()
        self.assertTrue(idx.resolves("Child Name"))
        self.assertTrue(idx.resolves("Charted Roots/People/Child Name"))
        self.assertTrue(idx.resolves("Child Name.md"))


if __name__ == "__main__":
    unittest.main()
