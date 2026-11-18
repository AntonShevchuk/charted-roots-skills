"""The frontmatter reader/writer.

The writer is a line patcher, not a serialiser: the claim it has to keep is
that a parse/render cycle is byte-identical and that `set` touches only the
lines of the key it changes. Everything else in the tool trusts that, and the
failure mode is silent -- a note that renders fine while Obsidian parses no
properties at all.
"""

from __future__ import annotations

import os
import unittest

from crsync import vault

from . import helpers

PERSON = """---
cr_id: tst-001-fix-001
cr_type: person
name: Jürgen Muster
aliases:
  - Muster, Landwirt Musterdorf
  - "Preußen"
born: ABT 1804
birth_place: "[[Pinewood County North Carolina]]"
children:
  - "[[First Child]]"
  - "[[Second Child]]"
children_id:
  - tst-002-fix-002
  - tst-003-fix-003
---

# Research Notes

Prose that must survive untouched.
"""

CITATION = """---
cr_type: citation
cr_id: abc-123-def-456
source: "[[Collection - Yearbooks]]"
subject: "[[Emil Ashcombe Hollister Jr]]"
subject_id: aaa-111-bbb-222
fact: graduation
page: "\\"U.S., School Yearbooks, 1880-2012\\"; School Name: Central High"
---
"""

NO_FRONTMATTER = "# Death Certificate: Person Name (1915)\n\n## Document Details\n"

UNCLOSED = "---\ncr_type: person\nname: Broken\n\n# Research Notes\n"

EMPTY_LIST = "---\ncr_type: person\nname: Nobody\naliases:\ncitations:\n---\nbody\n"


class RoundTrip(unittest.TestCase):

    def test_render_is_byte_identical(self):
        for label, text in (("person", PERSON), ("citation", CITATION),
                            ("archive", NO_FRONTMATTER), ("empty list", EMPTY_LIST)):
            with self.subTest(label):
                self.assertEqual(vault.parse_text(text).text(), text)

    def test_body_and_frontmatter_split(self):
        note = vault.parse_text(PERSON)
        self.assertTrue(note.has_frontmatter)
        self.assertFalse(note.malformed)
        self.assertTrue(note.body.startswith("\n# Research Notes"))

    def test_archive_note_has_no_frontmatter(self):
        note = vault.parse_text(NO_FRONTMATTER)
        self.assertFalse(note.has_frontmatter)
        self.assertEqual(note.fm, {})

    def test_unclosed_block_is_malformed(self):
        note = vault.parse_text(UNCLOSED)
        self.assertTrue(note.malformed)
        self.assertEqual(note.text(), UNCLOSED)

    def test_a_malformed_note_refuses_every_write(self):
        # Splicing a key into an unparsed block writes a second `---` block
        # above the first. A malformed Source can reach a write, because
        # match_sources recovers its gedcom_id from the body.
        note = vault.parse_text(UNCLOSED, "/x/Broken.md")
        for label, call in (("set", lambda: note.set("name", "Fixed")),
                            ("remove", lambda: note.remove("name")),
                            ("save", note.save)):
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    call()


class Reading(unittest.TestCase):

    def setUp(self):
        self.note = vault.parse_text(PERSON, "/x/Jürgen Muster.md")

    def test_scalar_and_list(self):
        self.assertEqual(self.note.scalar("born"), "ABT 1804")
        self.assertEqual(self.note.as_list("children_id"),
                         ["tst-002-fix-002", "tst-003-fix-003"])
        self.assertEqual(self.note.as_list("cr_id"), ["tst-001-fix-001"])
        self.assertEqual(self.note.as_list("nothing_here"), [])

    def test_quotes_are_stripped_on_read(self):
        self.assertEqual(self.note.as_list("aliases"),
                         ["Muster, Landwirt Musterdorf", "Preußen"])

    def test_links_from_scalar_and_list(self):
        self.assertEqual(self.note.links("birth_place"),
                         ["Pinewood County North Carolina"])
        self.assertEqual(self.note.links("children"), ["First Child", "Second Child"])

    def test_link_alias_and_anchor_are_dropped(self):
        note = vault.parse_text('---\nx: "[[Target Note|shown]]"\n'
                                'y: "[[Other Note#Heading]]"\n---\n')
        self.assertEqual(note.links("x"), ["Target Note"])
        self.assertEqual(note.links("y"), ["Other Note"])

    def test_embedded_quote_survives_the_round_trip(self):
        note = vault.parse_text(CITATION)
        page = note.scalar("page")
        self.assertEqual(page,
                         '"U.S., School Yearbooks, 1880-2012"; '
                         'School Name: Central High')
        # Re-quoting it must produce YAML that reads back as the same text --
        # an unescaped `"` makes Obsidian parse no properties at all.
        self.assertEqual(vault.unquote(vault.quote(page)), page)

    def test_basename_drops_the_extension(self):
        self.assertEqual(self.note.basename, "Jürgen Muster")


class Quoting(unittest.TestCase):

    def test_wikilinks_are_always_quoted(self):
        self.assertTrue(vault.needs_quoting("[[Somewhere]]"))
        self.assertEqual(vault.quote("[[Somewhere]]"), '"[[Somewhere]]"')

    def test_plain_scalars_stay_bare(self):
        for value in ("Jürgen Muster", "ABT 1804", "1884-05-27", "Sumy, Ukraine",
                      "Прикладенко", "locality"):
            with self.subTest(value):
                self.assertEqual(vault.quote(value), value)

    def test_structural_characters_force_quoting(self):
        for value in ("a: b", "#tag", "- leading", "trailing ", "a|b", "*star"):
            with self.subTest(value):
                self.assertTrue(vault.needs_quoting(value))

    def test_yaml_words_that_are_not_strings(self):
        for value in ("true", "False", "null", "yes", "no", "on", "off", "~"):
            with self.subTest(value):
                self.assertTrue(vault.needs_quoting(value))

    def test_inner_quotes_and_backslashes_are_escaped(self):
        for value in ('say "this"', r'back\slash', '"leading', 'trailing"'):
            with self.subTest(value):
                self.assertEqual(vault.unquote(vault.quote(value)), value)

    def test_newlines_are_collapsed_not_truncated(self):
        # A newline cannot live in a single-line scalar; dropping the tail
        # silently is how a citation stops matching itself.
        self.assertEqual(vault.unquote(vault.quote("one\ntwo")), "one two")


class UnparsedLines(unittest.TestCase):
    """Lines the key pattern does not match are reported, never ignored.

    Such a line is invisible to the span index -- it sits inside the
    preceding key's span -- so a write to *that* key splices it away. Which
    key, and therefore whether anything is lost, depends on where the line
    falls: the worst shape a data loss can have.
    """

    NESTED = ("---\ncr_type: person\nname: Nested\n"
              "relations:\n  father: someone\n---\nbody\n")
    PROSE = "---\ncr_type: person\nthis line is not a key at all\n---\n"

    def test_a_flat_note_has_nothing_unparsed(self):
        self.assertEqual(vault.parse_text(PERSON).unparsed, [])
        self.assertTrue(vault.parse_text(PERSON).writable)

    def test_a_nested_map_is_reported(self):
        note = vault.parse_text(self.NESTED)
        self.assertEqual(note.unparsed, ["  father: someone"])
        self.assertFalse(note.writable)
        self.assertIn("key index cannot see", note.unwritable_reason())

    def test_a_stray_prose_line_is_reported(self):
        note = vault.parse_text(self.PROSE)
        self.assertEqual(note.unparsed, ["this line is not a key at all"])

    def test_it_still_round_trips(self):
        # Refusing to write is the guard; reading must stay lossless, because
        # the report and the invariant suite both read these notes.
        for text in (self.NESTED, self.PROSE):
            with self.subTest(text[:30]):
                self.assertEqual(vault.parse_text(text).text(), text)

    def test_every_write_refuses(self):
        note = vault.parse_text(self.NESTED, "/x/Nested.md")
        for label, call in (("set", lambda: note.set("name", "Other")),
                            ("remove", lambda: note.remove("name")),
                            ("save", note.save)):
            with self.subTest(label):
                with self.assertRaises(ValueError) as caught:
                    call()
                self.assertIn("refusing to write", str(caught.exception))

    def test_an_unclosed_block_gives_its_own_reason(self):
        note = vault.parse_text(UNCLOSED, "/x/Broken.md")
        self.assertEqual(note.unwritable_reason(),
                         "frontmatter block never closes")


class OtherPluginKeys(unittest.TestCase):
    """A dash or a dot in a key is legal YAML, and other plugins emit them."""

    TEXT = ("---\ncr_type: person\nname: Someone\n"
            "cover-image: pic.jpg\ndate.created: 2026-09-23\n---\nbody\n")

    def test_they_parse_as_keys(self):
        note = vault.parse_text(self.TEXT)
        self.assertEqual(note.scalar("cover-image"), "pic.jpg")
        self.assertEqual(note.scalar("date.created"), "2026-09-23")
        self.assertEqual(note.unparsed, [])

    def test_a_note_carrying_them_stays_writable(self):
        note = vault.parse_text(self.TEXT, "/x/Someone.md")
        self.assertTrue(note.set("died", "1971"))
        self.assertIn("cover-image: pic.jpg", note.text())
        self.assertIn("died: 1971", note.text())

    def test_and_they_keep_their_own_span(self):
        note = vault.parse_text(self.TEXT)
        note.set("cover-image", "other.jpg")
        self.assertIn("cover-image: other.jpg", note.text())
        self.assertIn("date.created: 2026-09-23", note.text())


class Mutation(unittest.TestCase):

    def test_set_touches_only_its_own_lines(self):
        note = vault.parse_text(PERSON)
        before = list(note._lines)
        self.assertTrue(note.set("born", "1804-06-01"))
        after = note._lines
        self.assertEqual(len(before), len(after))
        differing = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
        self.assertEqual([before[i] for i in differing], ["born: ABT 1804"])
        self.assertEqual([after[i] for i in differing], ["born: 1804-06-01"])

    def test_set_rewrites_a_list_in_place(self):
        note = vault.parse_text(PERSON)
        note.set("aliases", ["Muster"])
        self.assertIn("aliases:\n  - Muster\nborn: ABT 1804", note.text())

    def test_setting_the_same_value_is_not_a_change(self):
        note = vault.parse_text(PERSON)
        self.assertFalse(note.set("born", "ABT 1804"))
        self.assertFalse(note.dirty)

    def test_new_key_lands_in_the_conventional_order(self):
        note = vault.parse_text(PERSON)
        note.set("died", "1871")
        keys = [line.split(":")[0] for line in note._lines if not line.startswith(" ")]
        self.assertEqual(keys.index("died"), keys.index("born") + 1)

    def test_unknown_key_goes_to_the_end(self):
        note = vault.parse_text(PERSON)
        note.set("no_such_property", "x")
        self.assertEqual(note._lines[-1], "no_such_property: x")

    def test_remove_deletes_the_whole_span(self):
        note = vault.parse_text(PERSON)
        self.assertTrue(note.remove("children"))
        self.assertNotIn("children:", note.text())
        self.assertNotIn("[[First Child]]", note.text())
        # its `_id` companion is a separate key and must be untouched
        self.assertIn("children_id:", note.text())
        self.assertFalse(note.remove("children"))

    def test_remove_of_an_absent_key_is_a_no_op(self):
        note = vault.parse_text(PERSON)
        self.assertFalse(note.remove("not_there"))
        self.assertFalse(note.dirty)


class Saving(helpers.VaultCase):

    def test_save_writes_exactly_text(self):
        path = self.person("Test Person", born="1900")
        note = vault.parse(path)
        note.set("died", "1970")
        note.save()
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), note.text())
        self.assertFalse(note.dirty)

    def test_save_leaves_no_temp_files_behind(self):
        path = self.person("Test Person", born="1900")
        note = vault.parse(path)
        note.set("died", "1970")
        note.save()
        folder = os.path.dirname(path)
        self.assertEqual([n for n in os.listdir(folder) if n.startswith(".crsync")], [])

    def test_iter_notes_reads_the_folder_in_name_order(self):
        self.person("Bertha Muster")
        self.person("Alma Muster")
        names = [n.basename for n in vault.iter_notes(self.cfg.people)]
        self.assertEqual(names, ["Alma Muster", "Bertha Muster"])

    def test_iter_notes_on_a_missing_folder_is_empty(self):
        self.assertEqual(list(vault.iter_notes(os.path.join(self.root, "nope"))), [])


#: The vault this checkout lives in, wherever the scripts folder sits.
VAULT = helpers.find_vault(__file__)


@unittest.skipUnless(os.path.isdir(os.path.join(VAULT, "Charted Roots")),
                     "run from inside the vault")
class RealVault(unittest.TestCase):
    """Read-only. The writer's whole licence to patch lines in place.

    The claim is that parsing and re-rendering any note in the vault returns
    the original bytes. If it does not, a run that changes one field rewrites
    unrelated lines, and the diff stops being reviewable.
    """

    def test_every_note_round_trips(self):
        bad, scanned = [], 0
        for dirpath, dirnames, filenames in os.walk(VAULT):
            # Dot-folders (.git, .obsidian, .claude) are not vault notes --
            # Obsidian ignores them, and so does the invariant suite.
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for name in filenames:
                if not name.endswith(".md"):
                    continue
                path = os.path.join(dirpath, name)
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
                scanned += 1
                if vault.parse_text(text, path).text() != text:
                    bad.append(os.path.relpath(path, VAULT))
        self.assertEqual(bad[:10], [], f"{len(bad)} of {scanned} notes differ")
        self.assertGreater(scanned, 0)

    def test_every_note_is_writable(self):
        # A note with an unclosed block, or a line the key index cannot see,
        # is one the writer refuses -- so a sync would stop on it. Nothing in
        # Obsidian reports either.
        bad = []
        for dirpath, dirnames, filenames in os.walk(VAULT):
            # Dot-folders (.git, .obsidian, .claude) are not vault notes --
            # Obsidian ignores them, and so does the invariant suite.
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for name in filenames:
                if not name.endswith(".md"):
                    continue
                path = os.path.join(dirpath, name)
                note = vault.parse(path)
                if not note.writable:
                    bad.append(f"{os.path.relpath(path, VAULT)}: "
                               f"{note.unwritable_reason()}")
        self.assertEqual(bad[:10], [])


if __name__ == "__main__":
    unittest.main()
