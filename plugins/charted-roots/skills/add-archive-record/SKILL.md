---
name: add-archive-record
description: Use when adding an archival document to the vault — a scan, register entry, certificate, index card, or FamilySearch/LitvakSIG/archive index hit. Creates the transcription, Source, Events and Citations and updates the People it names.
---

# Add an archive record

One archival item becomes: scan + transcription in the archive folder, one Source, Events, one Citation per person × fact, and Person updates. The rules are in the core model and the convention modules the vault loads (`archive.md`; `source-collections.md` if present) — read them; this skill sets the order and the checks. Folder names below are the `data.json` keys, never assumed paths.

**Rules.** The core model is `<vault-verify>/references/charted-roots-model.md` (already in context when the plugin's session-start hook ran); the vault's `CLAUDE.md` and `.claude/conventions/*.md` override it. `<vault-verify>` is `${CLAUDE_SKILL_DIR}/../vault-verify`. Run scripts from the vault root.

## Inputs

Scan path and/or the reading (register text, index line), plus whatever locator the user has (archive, fond/opis/sprava, entry number, folio, URL). Ask for what is missing only if it changes the notes; otherwise omit the bullet.

## Procedure

1. **Preflight.**
   - Read `.obsidian/plugins/charted-roots/data.json`: folders (`peopleFolder`, `eventsFolder`, `citationsFolder`, `sourcesFolder`, `placesFolder`, `mediaFolders`), `customSourceTypes`, `enableBidirectionalSync`, `syncOnFileModify`. The **archive folder** is the `mediaFolders` entry holding scans + transcriptions (look for existing ones; else the first entry).
   - Is Obsidian running (`pgrep -x Obsidian` on macOS/Linux)? Open + sync on → write one side of each relationship, small batches, re-read a note before editing it again. Closed → write both sides.
   - Read the existing `research_project` notes and Sources for the family; the identification often already has a hypothesis.

2. **Identify the people** before creating anyone. Search People by every spelling, transliteration, patronymic, maiden/married name, and `aliases:`; confirm by `cr_id`. Check age, place and estate against what the vault has.
   - Uncertain → stop and ask. Never link on a guess.
   - Unlinked people stay in the Source prose; `- **People:** none` takes a stated reason (archive.md).

3. **Scan** → `<archive folder>/<Type>_<Year>_<Surname>_<Given>[_<Surname2>_<Given2>]_<locator>.<jpg|pdf>`. Look at neighbours for the slug pattern; archival codes stay verbatim. PNG → JPEG quality 95 (`sips -s format jpeg -s formatOptions 95` on macOS, or ImageMagick). Multi-page → one PDF.

4. **Transcription** → same basename, `.md`. Archive.md template exactly:
   - H1 genre from the closed list; marriage names joined by `×`.
   - `Document Type` always; every other bullet omitted if unknown, never a placeholder.
   - `## Original Text (<Language>…)` — label per archive.md; verbatim — illegible parts `[…]`, guesses `[word?]`. Never fill a gap from the index.
   - Complete `## English Translation` for non-English originals.
   - Optional `## Uncertain readings`, then `## Notes`, in that order.
   - No frontmatter, no links.

5. **Source** — one per archival item. If one already covers this entry (another scan, the index), add to it instead.
   - Frontmatter: `cr_type: source`, `cr_id`, `title` (quoted), `source_type` (built-in or `customSourceTypes` id; never `document`), `source_date`, real `confidence`, with `source-collections.md`: `source_parent` + `source_parent_id` → the matching `Collection - …` note (child side only); `media:` (full-path wikilink to the scan). No `gedcom_id`; no `repository` unless the document names one.
   - Body: H1 = title; summary with the key original-script names; primary vs derivative; identification reasoning, including why anyone is left unlinked; `charted-roots-media` block.
   - `## Linked records`: `- **Events:**`, `- **People:**` with `(fact)` after cited people and prose roles (witness, godparent) outside the parentheses, `- **Places:**`, `- **Note:**` (which copy, who supplied it, what is not captured). Separator ` · `.
   - Foot: `> [!quote]- <H1 text>` / `> ![[<transcription basename>]]`.

6. **Events.** For each person, look for an existing Event of that type (by `persons:` and by filename) first.
   - Exists → add the Source to `sources:`, and correct `date`/`place` if the new evidence is better. Say so in the summary.
   - New → `<eventsFolder>/<Birth|Death|Marriage|Baptism|Burial> of <name>[ and <name>].md`: `cr_type: event`, `cr_id`, `title`, `event_type`, `date` (ISO) + `date_precision`, `persons:`, `place:` (wikilink), `confidence`, `sources:`; H1 + one-line summary.
   - A notice, obituary or index card is a Source, never an Event; its date is not the event date.

7. **Citations** — one per person × fact (`birth_date`, `death_date`, `marriage_date`, …). Filename `Citation - <source title> - <person name> <fact>.md`. Frontmatter: `cr_type: citation`, `cr_id`, `source`, `subject`, `subject_id` (= the Person's `cr_id`), `fact`, `page` (locator plus the decisive details; escape `"`). Add each Citation to that Person's `citations:`. A second Source documenting the same fact (an index of the same entry) gets its own Citation.

8. **People.**
   - Existing → update `born:` / `died:` / `birth_place:` / `death_place:` to match the Event (`c. YYYY` for an age-derived year; Person date forms per the core model), add relationships, `citations:`, and a sentence of Research Notes prose linking the Source.
   - New → `cr_id`, `cr_type: person`, `name`, `given_name`, `surnames:`, `sex`, `aliases:` (married or alternate forms), dates; body = `# Research Notes` + `charted-roots-media`, `charted-roots-timeline`, `charted-roots-relationships` blocks (copy from an existing Person). Filename collisions take ` 1`, ` 2`.
   - Relationships: wikilink + `_id`; `children` / `children_id` edited together; spouses in the note's existing slot form (`spouse1`, `spouse1_id`, `spouse1_marriage_date`, …).
   - Place not in the gazetteer → stop and ask, unless its hierarchy is known; never invent a parent chain.

9. **cr_ids** — mint against every id in the vault:

   ```sh
   python3 -I -c "
   import sys,re,pathlib;sys.path.insert(0,'<vault-verify>/scripts')
   from crsync.create import mint_cr_id
   t={m.group(1) for p in pathlib.Path('.').rglob('*.md') for m in re.finditer(r'^cr_id:\s*(\S+)',p.read_text(errors='ignore'),re.M)}
   print(*[mint_cr_id(t) for _ in range(N)])"
   ```

10. **Verify** — `python3 <vault-verify>/scripts/vault_verify.py`. All checks must pass; fix anything the new notes broke. Then re-read each new note once against archive.md: H1 ↔ quote-callout title, `## Linked records` ↔ actual Events/Citations, Person dates ↔ Event dates.

11. **Report and commit.** List created and changed notes, identifications made and left open, and any existing fact changed. Commit only when asked: scan + transcription + all entity notes in one commit, message `Add <year> <event> [No. N] of <names>[; short note]`.

## Stop and ask

- An identification is not certain, or two vault people fit.
- The new record contradicts an existing date, place or parent.
- The text is not legible enough to read the decisive field.
- A place, Collection or `source_type` the vault lacks would be needed.
