---
name: add-archive-record
description: Use when adding an archival document to the vault — a scan, screenshot, register entry, certificate, index card, or FamilySearch/LitvakSIG/archive index hit. Creates the transcription, Source, Events and Citations, updates the People it names, and suggests the upstream GEDCOM changes as a table per person.
---

# Add an archive record

One archival item becomes: scan + transcription in the archive folder, one Source, Events, one Citation per person × fact, and Person updates. The rules are in the core model and the convention modules the vault loads (`archive.md`; `source-collections.md` if present) — read them; this skill sets the order and the checks. Folder names below are the `data.json` keys, never assumed paths.

**Rules.** The core model is `<verify-vault>/references/charted-roots-model.md` (already in context when the plugin's session-start hook ran); the vault's `CLAUDE.md` and `.claude/conventions/*.md` override it. `<verify-vault>` is `${CLAUDE_SKILL_DIR}/../verify-vault`; `<lib>`, the shared scripts, is `${CLAUDE_SKILL_DIR}/../../lib`. Run scripts from the vault root.

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
   import sys,re,pathlib;sys.path.insert(0,'<lib>')
   from crsync.create import mint_cr_id
   t={m.group(1) for p in pathlib.Path('.').rglob('*.md') for m in re.finditer(r'^cr_id:\s*(\S+)',p.read_text(errors='ignore'),re.M)}
   print(*[mint_cr_id(t) for _ in range(N)])"
   ```

10. **Verify** — `python3 <lib>/vault_verify.py`. All checks must pass; fix anything the new notes broke. Then re-read each new note once against archive.md: H1 ↔ quote-callout title, `## Linked records` ↔ actual Events/Citations, Person dates ↔ Event dates.

11. **Suggest upstream GEDCOM changes** — when the vault has an upstream tree (its `.ged` export at the vault root, `FamilyTree.ged` unless the vault names another; use that filename in the command below). The `.ged` is never edited (core model: upstream master): this is a table for the user to enter upstream by hand. For **every person** the document names with a fact to add or correct:
   - **Heading** — the full name exactly as the `.ged` holds it (the INDI's `1 NAME`, read via the Person's `external_id`), then the xref and the vault note: `### Anna Meyer (@I123@ · [[Anna Meyer]])`. A person not in the `.ged` yet: the vault's full name plus `— not in the .ged; add as a new person`.
   - **Table** — columns `Event type | Date | Place | Description`, one row per fact:
     - *Event type* — the GEDCOM fact (Birth, Baptism, Marriage, Death, Burial, Residence, …).
     - *Date* — GEDCOM form, as Ancestry takes it (`12 MAR 1871`, `ABT 1871`, `BEF 1909`).
     - *Place* — the modern full location name: the linked Place's `full_name` (`Wrocław, Lower Silesian Voivodeship, Poland`). No Place note → the modern chain as identified, marked `(no Place note)`; unidentified → the document's form, marked `(unidentified)`.
     - *Description* — English. If the document gives a historical location that differs from the modern one, it is the **first line**: `Historical: Breslau, Schlesien, Preußen`, then `<br>` and the description proper (parish, role, age, the document and its locator).
   - **A fact the `.ged` already has** (same event type for that person, compared per the core model § GEDCOM, Reconciliation) gets **two rows**: first `<Type> — current` with the `.ged`'s values verbatim (date and PLAC as exported, its description), then `<Type> — new` with the new values. An unchanged fact gets no row; a new fact gets one row.
   - **Relationships** — when the document adds, removes or contradicts a parent, spouse or child link, a second table under the same heading, columns `Relationship | Person | Change | Evidence`:
     - *Relationship* — from this person's side: Father, Mother, Spouse, Child (Stepfather, Adoptive mother, … where the document says so).
     - *Person* — the other person's full name as the `.ged` holds it, with the xref (`Karl Meyer (@I45@)`); not in the `.ged` → the vault's full name plus `(not in the .ged; add first)`.
     - *Change* — `Add`, or `Remove` (a link the document disproves), or for a replaced link two rows, `Father — current` with the `.ged`'s person, then `Father — new` with the new one.
     - *Evidence* — English: what the document says and its locator (`Named as father in the baptism entry, 1871 No. 214`).
     - A marriage itself is an event and goes in the events table; this table records only who is linked to whom. Give each link once, on the person the document is about (the child for parents, the first-named spouse for a marriage), not again from the other side.
   - A person with nothing to add or correct is left out. Read the current values — events, then parents, spouses and children — with:

     ```sh
     python3 -I -c "
     import sys;sys.path.insert(0,'<lib>');from crsync import gedcom
     t=gedcom.parse('FamilyTree.ged');i=t.individuals['I123'];print(i.name)
     [print(e.event_type,'|',e.date_raw,'|',e.place,'|',e.description) for e in i.events]
     n=lambda x:f'{t.individuals[x].name} (@{x}@)' if x in t.individuals else ''
     [print('parents |',n(t.families[f].husband),'|',n(t.families[f].wife)) for f in i.famc if f in t.families]
     [print('spouse |',n(t.families[f].wife if t.families[f].husband=='I123' else t.families[f].husband),'| children |',', '.join(map(n,t.families[f].children))) for f in i.fams if f in t.families]"
     ```

   Example:

   ```markdown
   ### Anna Meyer (@I123@ · [[Anna Meyer]])

   | Event type | Date | Place | Description |
   |---|---|---|---|
   | Birth — current | ABT 1871 | Breslau, Preußen | |
   | Birth — new | 12 MAR 1871 | Wrocław, Lower Silesian Voivodeship, Poland | Historical: Breslau, Schlesien, Preußen<br>Born in St. Elisabeth parish; baptism register 1871, No. 214 |
   | Baptism | 19 MAR 1871 | Wrocław, Lower Silesian Voivodeship, Poland | Historical: Breslau, Schlesien, Preußen<br>Baptised at St. Elisabeth; godmother Maria Weber |

   | Relationship | Person | Change | Evidence |
   |---|---|---|---|
   | Father — current | Johann Meyer (@I44@) | Replace | |
   | Father — new | Karl Meyer (@I45@) | Replace | Named as father in the baptism entry, 1871 No. 214 |
   | Mother | Eva Roth (not in the .ged; add first) | Add | Named as mother, née Roth, in the same entry |
   ```

12. **Report and commit.** List created and changed notes, identifications made and left open, and any existing fact changed; then the upstream tables from step 11. Commit only when asked: scan + transcription + all entity notes in one commit, message `Add <year> <event> [No. N] of <names>[; short note]`.

## Stop and ask

- An identification is not certain, or two vault people fit.
- The new record contradicts an existing date, place or parent.
- The text is not legible enough to read the decisive field.
- A place, Collection or `source_type` the vault lacks would be needed.
