# Design: organise Places to modern borders (`organize-places`)

Date: 2026-11-18 · Status: draft for approval

## Why

A vault synced from an Ancestry export has no Place notes. `gedcom_sync.py` only writes a place as a `[[Place]]` link to an existing Place note, so a dry run reports thousands of place values as "left off a new note" (one real vault: 3,242 values, 765 distinct PLAC strings). The script deliberately never creates Places, because the export records historical and native forms (`Preußen`, `Deutschland`, `Danmark`) and the place hierarchy is a schema decision (core model § Places, `sync-gedcom` § What the script will not do).

The user wants that decision made once, carefully, and then kept: Place notes under **modern borders**, with **historical and native names as `aliases:`**, so every PLAC in the export links to the right modern Place.

## Goals

1. A new skill, **`organize-places`**, that reads the vault's PLAC strings (from the `.ged`) and the existing Places, and proposes a modern-border gazetteer: for each PLAC, the modern chain (country → first-level division → … → locality) it belongs under, and the aliases each Place needs. The user reviews it in batches (one country at a time); nothing is written until a batch is approved.
2. A script that creates and updates Place notes from the approved plan: dry run by default, `--apply` to write, with the same safety rails as `gedcom_sync.py --apply`.
3. The sync resolves historical PLACs through aliases: `…, Preußen, Deutschland` links to the modern Place it was mapped to.
4. People get their places after the fact: a later sync fills an empty `birth_place` / `death_place` / `burial_place` once the PLAC resolves (today only Events are back-filled; Person place fields are filled only on creation).
5. The skill stays useful after the first pass: on a later export it proposes only the PLAC strings not yet in the plan (a new string is never linked through an alias until reviewed), and it can review existing Places for missing aliases and duplicates.

## Non-goals

- Coordinates or geocoding. No web lookups unless the user explicitly asks (repo convention).
- Automatic merging of existing Places. The skill may *propose* a merge; carrying it out follows the core model's merge rule and needs the user's approval per merge.
- Editing the `.ged` or pushing structure upstream (the export loses `aliases` and `parent_place` anyway).
- Matching parity with the plugin's import wizard. After this change the script resolves PLACs the wizard would not; the wizard is not used for re-imports in these vaults (`sync-gedcom`).

## Anti-goals (a failure even if it runs)

- An anachronistic chain in the vault (`Preußen` as a country, `Schlesien` under `Germany` for a town now in Poland).
- A Place invented for a string that cannot be identified. Unidentified stays unidentified (core model § Places/heuristics) and the PLAC stays unresolved and reported.
- Raw PLAC text written into a place field, or a wrong link from an ambiguous alias match. Ambiguous → no link, reported.
- Duplicate Places: a planned Place that already exists in the vault (by the plugin's own `full_name` / `title|parent` keys, or by name + parent) is reused, not re-created.

## Constraints

- Python 3.10+, standard library only; scripts live in `plugins/charted-roots/lib/`, reuse `crsync` (`config`, `vault`, `places`, `gedcom`, the line-patching writer, `mint_cr_id`, the restore-point / Obsidian-open / clean-tree preflight).
- Folder from `data.json` `placesFolder`, never hard-coded.
- Place frontmatter per `config.KEY_ORDER["place"]`: `cr_type: place`, `cr_id`, `title`, `place_type` (closed list + `customPlaceTypes`), `parent_place` (quoted wikilink) + `parent_place_id`, `full_name` (derived: own title + ancestors'), `aliases`. Body carries the `**Part of:**` line the core model's merge rule repoints.
- The core model is at ~9,780 of 9,800 bytes for the session hook. New rules go in the skill and its `references/`, not the model.
- Tests use the synthetic vault in `lib/tests/helpers.py`, fictional names only.
- Skill name verb–object: `organize-places`.

## Approaches considered

- **A. Mirror the export, reorganise later.** Create Places exactly as PLAC names them, then merge/rename/re-parent to modern borders. Everything links at once, but the vault holds a wrong hierarchy in between and each merge repoints every referring note. Rejected: it builds the anti-goal first.
- **B. Plan first, create once — chosen.** The skill proposes a reviewed plan; a script creates Places from the approved plan; the matcher reads aliases. Correct the first time, no churn; nothing lands until a batch is reviewed.
- **C. Like B, with a PLAC → Place lookup table instead of alias matching.** Keeps the matcher identical to the plugin, but the same knowledge lives in two places (table and aliases) that can drift. Rejected. (B still reads the plan, but only as an allow-list of reviewed strings — see §3.)

## Design

### 1. The plan file

`History/places-plan.json` in the vault, next to `History/gedcom-sync-decisions.json` (the sync already keeps its state there, with or without the `history` module). Committed with the vault. Two parts:

- **places** — one entry per Place, existing or proposed: a stable plan key, `title` (modern English form, per the vault's Language section), `place_type`, `parent` (plan key), `aliases` (historical and native names), `status` (`proposed` / `approved` / `created`), and a one-line `reason` for any non-obvious mapping (e.g. `Breslau → Wrocław: in Poland since 1945`). An existing Place note is referenced by `cr_id` rather than duplicated.
- **plac** — one entry per distinct PLAC string with its usage count: maps to a plan key, or is marked `not-a-place` (reusing `gedcom.non_place_reason`) or `unidentified` (with what is uncertain).

Approval is per batch (a country, or a top-level PLAC segment); the skill flips `status` only on the user's word.

### 2. `lib/places_plan.py` (CLI)

- `extract` — reads the `.ged` (`--ged`, default as in `gedcom_sync`) and the vault; writes or merges the `plac` worklist: distinct strings, counts, whether each already resolves, non-place flags. Re-running on a new export adds only new strings and never drops a reviewed entry.
- `check` — validates the plan: every parent exists, no cycles, `place_type` valid, no two Places with the same title under one parent, every mapped PLAC would resolve to its planned Place under the new matcher (§3) and to no other. Exit non-zero on any failure.
- `apply` — dry run by default, listing the notes to create and the aliases to add to existing Places; `--apply` writes approved entries only, top-down so parents exist first, computes `full_name`, mints `cr_id`, then marks them `created`. Same preflight as `gedcom_sync.py --apply` (Obsidian closed, clean entity folders, restore-point tag, before/after `vault_verify` comparison). Adding aliases to an existing Place goes through the line patcher; nothing else on an existing Place is changed.

### 3. Alias-aware matching in `crsync/places.py` — reviewed names only

`Index.find` keeps the plugin's two lookups (`full_name`, `title|parent`) first; a hit there links as today. When both miss, it tries a name-based match: the PLAC's leaf against each Place's title / name / aliases (and `historical_names`), with the remaining segments checked against the candidate's ancestors' names and aliases. **This fallback is used only for a PLAC string the plan lists as approved** (user decision): the sync loads `History/places-plan.json` and treats an alias match on any other string as unresolved, reported with `organize-places` as the next step. A missing plan file means no alias matching at all.

The plan is an allow-list, not a second copy of the mapping: the link target still comes from the aliases, and `check` fails when an approved string resolves to anything but its planned Place. A unique candidate is returned; none or several → `None`. Historical chains differ in depth from modern ones (`Halle, Sachsen, Preußen, Deutschland` vs `Halle (Saale) → Saxony-Anhalt → Germany`), so the exact rule for segments that match no ancestor is the builder's call, within the `check` constraint; the skill fixes a failing mapping by adding the alias that disambiguates it.

### 4. Back-filling Person places in `gedcom_sync`

A matched Person with an empty `birth_place` / `death_place` / `burial_place` and a PLAC that resolves gets a `fill` change (a link, never text), exactly as Events already do via `EVENT_FILL_ONLY`. A non-empty field keeps today's conflict/coarsen handling.

### 5. The `organize-places` skill

`skills/organize-places/SKILL.md` + `references/` (the mapping guidance: modern-border rule, how to read historical German/Scandinavian/Slavic jurisdiction names, `place_type` per level, when to say `unidentified`). Steps:

1. Check the vault (Charted Roots `data.json`), baseline `vault_verify.py`.
2. `places_plan.py extract`.
3. Propose, one batch at a time, largest batches first: the modern chain for each PLAC, the aliases, the reasons, and the unidentified list. From knowledge and the PLAC strings themselves; no web search unless the user asks.
4. User corrects and approves; the skill records approval in the plan file.
5. `places_plan.py check`, then `apply` dry run, then — on explicit approval, with Obsidian closed and a commit — `apply --apply`.
6. Re-run the `sync-gedcom` dry run and report how many place values now resolve.
7. Review mode (later runs): new PLACs only; existing Places missing an alias the export uses; likely duplicates proposed as merges for the user.

### 6. Docs and wiring

- `lib/README.md`: `places_plan.py`, the alias-aware matcher (and that it now resolves beyond the plugin's wizard), Person place back-fill.
- `sync-gedcom/SKILL.md`: point "will not create Places" at `organize-places`; report unresolved PLACs with that next step.
- `init-vault/SKILL.md` step 2: add `organize-places` to the list of local skill copies to detect.
- `plugin.json` description lists the new skill; version bump.
- Root `README.md` skill list; repo `CLAUDE.md` skill names.

## Calls made during review (author's, not the user's)

- **Existing Places on a historical chain** (e.g. an existing `Preußen` country): the plan never parents new Places under them and never creates a modern twin. That branch is blocked and the skill proposes a re-parent/retitle/merge to the user under the core model's merge rule; `apply` does not restructure existing notes. (The motivating vault has no Places yet.)
- **Filenames:** a new Place's basename is its `title`. When that basename is already taken anywhere in the places folder, it becomes `<title>, <parent title>` (then the next ancestor, until unique); `title` stays the bare name. Links are plain `[[basename]]`, never piped.
- **Partly identifiable PLACs** (unknown village in an identifiable region): stay `unidentified`, never linked to the coarser Place (core model: unidentified stays unidentified). The plan records the candidate region in the entry's note.
- **Burial back-fill:** a separate fill-only path for `burial_place` (and birth/death when empty). `match.PERSON_PLACES` is not extended, so no new conflict/coarsen reporting and no change to what existing rulings cover.
- **`historical_names`:** the matcher reads it as well as `aliases`; the plan writes only `aliases`.

## Left to the builder

- The exact segment-matching rule in §3, within the `check` constraint.
- Plan file field names and plan-key format.
- Whether `extract`/`check`/`apply` are subcommands of one CLI or flags.
- Body text of a created Place note beyond the `**Part of:**` line.
- Test layout (new `test_places_plan.py`, extended `test_places.py` / `test_match.py`).
