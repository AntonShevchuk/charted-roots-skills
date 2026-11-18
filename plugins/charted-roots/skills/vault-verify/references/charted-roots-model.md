# Charted Roots vault model

The shared rule set for an Obsidian vault managed by the **Charted Roots** plugin. Every skill in this plugin reads it. A vault's own `CLAUDE.md` and `.claude/conventions/*.md` override it where they differ.

## What this is

An **Obsidian vault** of genealogy notes managed by the **Charted Roots** plugin (`.obsidian/plugins/charted-roots`). No build, test or lint — work is editing Markdown frontmatter and bodies.

- **Read `.obsidian/plugins/charted-roots/data.json` first.** Every folder, custom type and sync setting is configured there, not by convention. Settings live nowhere else; change them through the plugin UI. Never hand-edit `data.json` while Obsidian is running — it rewrites the file from memory.
- Never edit the plugin's `main.js` (vendored, minified).
- If the tree has an **upstream master** (Ancestry or another hosted tree), never edit the vault's `.ged` and never push structural changes by round-trip — change it upstream and re-export.
- If a `History/` folder exists (the `history` module), read it before bulk data-quality work.

## Entity model

Every note is typed by `cr_type` and keyed by `cr_id` (`abc-123-def-456`) — the stable cross-note key, independent of filename.

| `data.json` key | `cr_type` | Holds |
|---|---|---|
| `peopleFolder` | `person` | individuals |
| `eventsFolder` | `event` | one dated life event each |
| `citationsFolder` | `citation` | one source → one fact about one person |
| `sourcesFolder` | `source` | records and record collections |
| `placesFolder` | `place` | hierarchical gazetteer |
| `mediaFolders` | — | scans + transcriptions, no frontmatter |
| `basesFolder` | — | Obsidian Bases definitions |
| *(none)* | `research_project` | research notes; path is free-form |

A configured folder that does not exist is normal.

**Never invent a `cr_type`.** Valid: `person`, `place`, `event`, `source`, `citation`, `map`, `organization`, `schema`, `universe`, `proof_summary`, `timeline-export`, `research_project`, `research_report`, `individual_research_note`, `research_journal`, `research_log_entry`. Not valid: `hypothesis`, `survey`, `reference`, `letter`, `report`, `timeline`. (`valueAliases.noteType` only remaps spellings.)

## Invariants

- **Every relationship is stored twice — wikilink + `_id`** holding the target's `cr_id` (`father` / `father_id`). `children` / `children_id` are **parallel arrays**: add, remove or reorder both together.
- **Bidirectional sync** — if `enableBidirectionalSync` and `syncOnFileModify` are on *and Obsidian is open*, write one side only; the plugin writes the reciprocal. Keep scripted edits to small batches and re-read a note before a follow-up edit. Otherwise write both sides by hand.
- **Spouses use numbered slots**: `spouse1`, `spouse1_id`, `spouse1_marriage_date`, `spouse1_marriage_location`, `spouse1_divorce_date`, … `spouse5`. Legacy unnumbered `spouse` exists; follow the note's existing form, never both.
- **Facts live in two places.** `born:` / `birth_place:` on the Person (what charts read) and `Events/Birth of <name>.md` (the evidence). Correct both.
- Person notes have **no `date_precision`**: `born: c. 1804` on the Person, `date: 1804` + `date_precision: estimated` on the Event. Not a conflict.
- **Person `born`/`died` must pass the plugin's *Validate date formats*** (settings in `data.json`): ISO or `D MMM YYYY`, `c. YYYY` for about, `YYYY to YYYY` for a range. It has no before/after form — `BEF`/`AFT` stays on the Event `date:` and the Person carries the bare date. Never `ABT`, `BEF`, `AFT` or `YYYY-YYYY` on a Person.
- Preserve the Person body: `# Research Notes` plus the `charted-roots-media`, `charted-roots-timeline` and `charted-roots-relationships` code blocks. Narrative prose goes under the heading.

## Evidence chain — Person → Citation → Source

- A Citation carries `source`, `subject` + `subject_id`, one `fact` (`birth_date`, `death_date`, `marriage_date`, `baptism_date`, `burial_date`, `residence`, `occupation`, `probate`, `graduation`, `naturalization`, `emigration`) and the locator in `page`.
- **`subject_id` must equal the Person's `cr_id`**, and the Citation must appear in that Person's `citations:` list. Recompute both directions after bulk work: entries pointing at no Citation, and Citations on the wrong Person.
- Name citations `Citation - <source title> - <person name> <fact>.md`.
- **Never rewrite `page:` values or Source titles** — they quote archival material.
- Before creating an Event, check the person has none of that type already. Do not create per-document Sources for imported Events, but do link an existing Source that documents one.
- **A notice, obituary or index card is a Source, never an Event**; its publication date is not an event date. Fold import-created notice Events into the real Event and delete them; re-check after re-import.
- Distinguish primary from derivative in the Source body; `confidence` rates the reading, not the document's authority. Non-import Sources get a real `confidence` (never `unknown`) and no `gedcom_id`.

## Vocabularies

**`source_type`** — built-ins `vital_record`, `obituary`, `census`, `church_record`, `court_record`, `land_deed`, `probate`, `military`, `immigration`, `photo`, `correspondence`, `newspaper`, `oral_history`, `custom`, plus ids in `customSourceTypes`. `custom` is a smell (a real id is missing). **`document` is never valid** — it is the importer's fallback, renders silently without icon or category, and returns on every re-import.

**`place_type`** — closed list (plus `customPlaceTypes`):

| Value | Meaning |
|---|---|
| `country` | sovereign state, incl. historical |
| `state` | first-level division (state, province, oblast, Land) |
| `county` | second-level (county, Kreis, raion, urban district) |
| `city` | incorporated primary settlement |
| `township` | US civil township |
| `locality` | village, district, ward, parish, cemetery, address |
| `region` | informal / supra-national — rare |

Map `town` / `village` to `locality`. No child ranked above its parent; `region` is exempt from ranking.

## Places

- `parent_place` + `parent_place_id` build the tree. `full_name` is **derived** (own `title` + each ancestor's) — recompute after structural change, except on root notes, whose stored value is richer.
- Events and People link places by **wikilink only** (no `place_id`).
- **Merging**: choose the survivor by hierarchy position, not usage; repoint `parent_place`, `parent_place_id`, the body `**Part of:**` line and every referring note in the same edit; re-parent to the nearest surviving ancestor; add the retired name to `aliases:`. Do not merge numbered census wards.
- A non-place in a `place:` field means the Event needs fixing first.

## GEDCOM

- **Provenance markers** — `external_id` / `external_id_source: gedcom`, `gedcom_id`, `_Imported from GEDCOM_` lines, merge notes. Never renumber or strip them. Import version: `preferredGedcomVersion`.
- **Export loses**: coordinates, `aliases`, the `parent_place` hierarchy, `place_type`, all `research_project` notes, the archive folder's scans and transcriptions. Push structural changes upstream by hand.
- **Reconciliation** — compare vault Events to `.ged` tags per `event_type`. Archive-derived Event = every `sources:` entry lacks `gedcom_id` (a proxy; linking real evidence onto an imported Event reclassifies it — fine). Map `1 EVEN` blocks by `2 TYPE`; a shared event yields one block per individual, so dedupe per family. Record baselines in a run record (the `history` module) or the report, never in an instruction file.
- Alternate names arrive as extra `1 NAME` blocks and `1 FACT` / `2 TYPE AKA`; populate `aliases:` from them deliberately.

## Working conventions

- **Wikilinks target bare filenames**; filenames stay unique vault-wide, with no leading/trailing space. Rename via Obsidian, never `mv`.
- **Quote wikilinks in frontmatter**: `birth_place: "[[Place Name]]"`.
- **Escape `"` inside double-quoted values** — one unescaped quote silently drops every property on the note. Hosted-tree exports produce this in `page:`. Verify by parsing every frontmatter block, not by eye.
- **Event dates are ISO**: `YYYY-MM-DD`, `YYYY-MM`, `YYYY`, `YYYY-YYYY`, `BEF`/`AFT YYYY`; never a native month name (`Dez`) or `D.M.YYYY`. Event `date_precision`: `exact`, `month`, `year`, `decade`, `estimated`, `range`, `unknown`. A specific precision with no `date:` is a dropped value.
- **Search every script** the vault uses (and by `cr_id`) before concluding a note does not exist.
- **Mask fenced blocks and inline code** before auditing links.
- **Bases**: check every filter literal and property name against the data (wrong names fail silently); quote labels containing `#`; Obsidian canonicalises `.base` files while open — a large diff is not corruption. Empty views for unused types are scaffolding.
- **Privacy**: the vault holds data on living people; with `enablePrivacyProtection: false` the plugin redacts nothing. Never send contents to external services or public output without explicit instruction.

## Known hygiene issues — flag, don't fix opportunistically

- Trailing `-N` in an Event filename is a sequence number, not a duplicate. Never bulk-delete.
- `confidence: unknown` = unassessed, not doubtful.
- Plugin classification fields (`research_level`, `collection`, `group_name`, numbering columns) are usually empty.
- Imported coordinates are often city-level; historic places without coordinates are often unresolvable.
- Unidentified places stay unidentified until someone checks the image.
- Historic place chains can be anachronistic — a schema decision, not a fix.

