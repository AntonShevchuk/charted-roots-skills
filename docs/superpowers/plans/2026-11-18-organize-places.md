# organize-places Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create Place notes under modern borders from a reviewed plan, with historical names as aliases, and let the sync link a historical PLAC through those aliases only when the plan approves that exact string.

**Architecture:** A plan file (`History/places-plan.json`) is the reviewed mapping. `crsync/placeplan.py` reads, extends, checks and applies it; `lib/places_plan.py` is its CLI. `crsync/places.Index` gains an alias fallback gated by the plan's approved strings, so every existing caller (match, events, create) gets it through `places.load`. A new skill drives the review.

**Tech Stack:** Python 3.10+ standard library, `unittest`; skill prose in Markdown.

**Spec:** `docs/superpowers/specs/2026-11-18-organize-places-design.md`

## Global Constraints

- Standard library only; code in `plugins/charted-roots/lib/`; tests run from `lib/` with `python3 -m unittest discover -s tests -t .`.
- Fixtures build a synthetic vault (`tests/helpers.py`); fictional person names only.
- Folders from `data.json` via `config.Config`, never hard-coded.
- Place frontmatter keys in `config.KEY_ORDER["place"]` order; `place_type` in `config.PLACE_TYPES | cfg.custom_place_types`; frontmatter wikilinks quoted (`"[[X]]"`).
- Never write raw PLAC text into a place field; ambiguous match → no link.
- No new text in `skills/verify-vault/references/charted-roots-model.md` (hook cap 9,800 bytes).
- Skill name `organize-places`. No web search unless the user asks.
- Existing vault-side names stay: `History/gedcom-sync-decisions.json`, `pre-gedcom-sync-*` tags.

## Review Focus

1. A PLAC that matches an alias but is not approved in the plan stays unresolved, in every consumer (Event fill, Person creation, Person back-fill, spouse marriage location) — test in Task 1 and Task 6.
2. A missing or unreadable plan file: sync behaves exactly as today (no alias matching); `places_plan.py` reports an unreadable file as an error, never overwrites it — test in Task 2.
3. Re-running `extract` on a new export never drops or resets a reviewed entry and never flips a status — test in Task 3.
4. A planned Place whose basename collides with an existing note gets the `, <parent title>` suffix, and links use the final basename — test in Task 5.
5. `apply` on an already-applied plan writes nothing (idempotent) — test in Task 5.

---

### Task 1: Alias fallback in `places.Index`, gated by approved strings

**Files:**
- Modify: `plugins/charted-roots/lib/crsync/places.py` (`Index.__init__`, `Index.find`, `Index.names`, `load`)
- Test: `plugins/charted-roots/lib/tests/test_places.py` (new class `AliasFallback`)

**Interfaces:**
- Produces: `Index(notes: list, approved: set[str] | None = None)`; `load(folder: str, approved: set[str] | None = None) -> Index`; `Index.find(place) -> Note | None` unchanged signature; `Index.names(note)` now also includes `historical_names` entries. `approved` holds `places.key(plac)` values.

- [ ] **Step 1: Write the failing tests** in `AliasFallback(PlaceCase)`, with fixture Places `Poland` (country), `Lower Silesian Voivodeship` (state, parent Poland, aliases `[Schlesien]`), `Wrocław` (city, parent Lower Silesian Voivodeship, aliases `[Breslau]`, `full_name: Wrocław, Lower Silesian Voivodeship, Poland`), and two `Neustadt` Places (`Neustadt, Hesse` under `Hesse`, `Neustadt, Saxony` under `Saxony`):
  - `test_an_approved_historical_place_resolves`: `P = "Breslau, Schlesien, Preußen, Deutschland"`; `places.load(folder, approved={places.key(P)}).find(P).basename == "Wrocław"`.
  - `test_an_unapproved_one_does_not`: same `P`, `approved=set()` → `None`; `approved=None` → `None`.
  - `test_a_tie_is_no_link`: `P = "Neustadt, Preußen"` approved → `None`.
  - `test_the_better_supported_candidate_wins`: `P = "Neustadt, Hessen"` approved, with `Hesse` carrying aliases `[Hessen]` → `Neustadt, Hesse`.
  - `test_plugin_lookups_still_come_first`: `find("Wrocław, Lower Silesian Voivodeship, Poland")` with `approved=None` → `Wrocław`.
  - `test_historical_names_count_as_names`: a Place with `historical_names: [Lemberg]` and title `Lviv`; approved `Lemberg, Galizien` → `Lviv`.

- [ ] **Step 2: Run** `python3 -m unittest tests.test_places.AliasFallback` — expect FAIL (`unexpected keyword argument 'approved'`).

- [ ] **Step 3: Implement.** After both plugin lookups miss, and only if `approved is not None and key(place) in approved`: split `normalise(place)` into segments; candidates = notes whose `names()` contain the leaf (use `_same_name`-free exact key equality for the leaf, so `Neustadt` ≠ `Neustadt an der Weinstraße`); score each candidate by how many remaining segments match (exact key) a name of the candidate's ancestors (`self.ancestors(note)`); return the unique top scorer, else `None`. Segments matching nothing are ignored — `places_plan.py check` guarantees each approved string lands on its planned Place.

- [ ] **Step 4: Run** `python3 -m unittest tests.test_places` and the full suite — expect PASS.

- [ ] **Step 5: Commit** `Add an alias fallback to place lookup for approved PLACs`.

---

### Task 2: The plan file model

**Files:**
- Create: `plugins/charted-roots/lib/crsync/placeplan.py`
- Test: `plugins/charted-roots/lib/tests/test_placeplan.py`

**Interfaces:**
- Produces:
  - `PLAN_PATH = "History/places-plan.json"`
  - `@dataclass PlannedPlace: key: str; title: str; place_type: str; parent: str = ""; aliases: list[str]; reason: str = ""; status: str = "proposed"; cr_id: str = ""; file: str = ""` — `cr_id`/`file` set for an existing or created note.
  - `@dataclass PlacEntry: plac: str; count: int = 0; place: str = ""; not_place: str = ""; unidentified: str = ""; status: str = "proposed"`
  - `@dataclass Plan: places: dict[str, PlannedPlace]; plac: dict[str, PlacEntry]`
  - `STATUSES = {"proposed", "approved", "created"}` (places); `{"proposed", "approved"}` (plac)
  - `load(root: str) -> Plan` (missing file → empty Plan; unreadable/invalid JSON → raise `PlanError`)
  - `save(root: str, plan: Plan) -> None` (via `vault.write_atomic`, sorted keys, `indent=2`, `ensure_ascii=False`)
  - `approved_placs(plan: Plan) -> set[str]` — `places.key(e.plac)` for entries with `status == "approved"`, a `place`, and that place's status in `{"approved", "created"}`.
  - `class PlanError(Exception)`

JSON layout (matches the example shown to the user):

```json
{"version": 1,
 "places": {"wroclaw": {"title": "Wrocław", "place_type": "city", "parent": "lower-silesia",
                        "aliases": ["Breslau"], "reason": "Polish since 1945", "status": "approved"}},
 "plac":   {"Breslau, Schlesien, Preußen, Deutschland": {"count": 38, "place": "wroclaw", "status": "approved"}}}
```

- [ ] **Step 1: Write failing tests:** `test_missing_file_is_an_empty_plan`; `test_round_trip_keeps_every_field` (save then load equals); `test_invalid_json_raises_plan_error_and_leaves_the_file` (file bytes unchanged); `test_approved_needs_both_sides` (plac approved + place proposed → not in set; plac proposed + place created → not in set; both approved → in set; `unidentified` entry → not in set).
- [ ] **Step 2: Run** `python3 -m unittest tests.test_placeplan` — FAIL (module missing).
- [ ] **Step 3: Implement** the dataclasses, `load`, `save`, `approved_placs`.
- [ ] **Step 4: Run** the module, then the full suite — PASS.
- [ ] **Step 5: Commit** `Add the places plan file model`.

---

### Task 3: `extract` — the PLAC worklist

**Files:**
- Modify: `plugins/charted-roots/lib/crsync/placeplan.py`
- Test: `plugins/charted-roots/lib/tests/test_placeplan.py` (class `Extract`)

**Interfaces:**
- Consumes: `gedcom.Tree`, `gedcom.non_place_reason`, `places.Index`.
- Produces: `count_placs(tree: gedcom.Tree) -> collections.Counter[str]` (every non-empty `Event.place` on individuals and families; a shared FAM event counted once); `extract(plan: Plan, counts: Counter, index: places.Index) -> ExtractResult` where `@dataclass ExtractResult: added: list[str]; updated: list[str]; resolved: list[str]` (resolved = strings the plugin's own lookups already find, recorded with `place` = that note's plan key and `status: "approved"`, the note itself recorded as a `PlannedPlace` with `status: "created"` and its `cr_id`/`file`).

- [ ] **Step 1: Write failing tests:** `test_counts_individual_and_family_places`; `test_a_new_string_is_added_as_proposed`; `test_a_non_place_is_marked` (`not_place` = the marker); `test_a_rerun_keeps_reviewed_entries` (an approved entry's `place`, `status`, `unidentified` survive; only `count` changes); `test_a_string_gone_from_the_export_is_kept` (count set to 0, not deleted); `test_an_already_resolving_string_is_recorded_as_existing`.
- [ ] **Step 2: Run** — FAIL.
- [ ] **Step 3: Implement.** `extract` never changes `status`, `place`, `not_place` or `unidentified` on an existing entry.
- [ ] **Step 4: Run** — PASS.
- [ ] **Step 5: Commit** `Extract the PLAC worklist into the places plan`.

---

### Task 4: `check` — the plan is consistent and every approved string lands on its Place

**Files:**
- Modify: `plugins/charted-roots/lib/crsync/placeplan.py`
- Test: `plugins/charted-roots/lib/tests/test_placeplan.py` (class `Check`)

**Interfaces:**
- Consumes: Task 1 `places.Index(notes, approved=...)`.
- Produces: `basename_for` and `render_note` (signatures under Task 5, implemented here because `check` renders planned notes in memory); `check(plan: Plan, cfg: config.Config, existing: list[vault.Note]) -> list[str]` — empty list means OK; each string is one problem, prefixed with the plan key or PLAC.

Checks: parent key exists; no parent cycle; `place_type` valid; no two planned Places with the same title under one parent; a mapped `place` key exists; a non-created Place does not duplicate an existing note by the plugin's keys (`full_name` or `title|parent`); every approved PLAC, resolved against an `Index` of `existing` + in-memory notes rendered from approved/created plan places (`vault.parse_text`), returns the note for its planned key and nothing else.

- [ ] **Step 1: Write failing tests**, one per check: `test_missing_parent`, `test_cycle`, `test_bad_place_type`, `test_duplicate_title_under_one_parent`, `test_unknown_place_key`, `test_duplicates_an_existing_note`, `test_an_approved_string_that_resolves_elsewhere` (e.g. `Neustadt, Preußen` mapped to one Neustadt but tied → reported), `test_a_clean_plan_has_no_problems` (the Wrocław chain from the spec example).
- [ ] **Step 2: Run** — FAIL.
- [ ] **Step 3: Implement** `basename_for`, `render_note` and `check`.
- [ ] **Step 4: Run** — PASS.
- [ ] **Step 5: Commit** `Check the places plan before applying it`.

---

### Task 5: `apply` and the `places_plan.py` CLI

**Files:**
- Modify: `plugins/charted-roots/lib/crsync/placeplan.py`, `plugins/charted-roots/lib/crsync/apply.py` (`check_preconditions`: new `tag_prefix: str = "pre-gedcom-sync"` parameter used in the match and the remedy text)
- Create: `plugins/charted-roots/lib/places_plan.py`
- Test: `plugins/charted-roots/lib/tests/test_placeplan.py` (class `Apply`), `plugins/charted-roots/lib/tests/test_places_plan_cli.py`

**Interfaces:**
- Consumes: Tasks 2–4; `create.mint_cr_id(taken: set) -> str`; `vault.write_atomic`, `Note.set`, `Note.save`; `apply.check_preconditions`; `verify.run`, `verify.regressions`.
- Produces (`basename_for` and `render_note` already exist from Task 4):
  - `basename_for(place: PlannedPlace, plan: Plan, taken: set[str]) -> str` — the title; if taken (case-insensitive, whole places folder), `"<title>, <parent title>"`, then the next ancestor, until free.
  - `render_note(place: PlannedPlace, plan: Plan, basenames: dict[str, str], cr_ids: dict[str, str]) -> str` — frontmatter `cr_type: place`, `cr_id`, `title`, `place_type`, `parent_place: "[[<parent basename>]]"`, `parent_place_id`, `full_name` (title + ancestor titles, `, `-joined), `aliases` (block list, omitted when empty); body `**Part of:** [[<parent basename>]]\n` (omitted for a root).
  - `apply_plan(plan: Plan, cfg: config.Config, dry: bool = True) -> ApplyResult` with `@dataclass ApplyResult: created: list[str]; aliased: list[str]` (vault-relative paths). Approved places only, parents before children; an existing note (has `cr_id`) only gains missing `aliases` via `Note.set`; after a real write, created places get `status: "created"`, `cr_id`, `file`, and the plan is saved.
  - CLI `places_plan.py {extract,check,apply} [--ged PATH] [--vault DIR] [--apply] [--allow-obsidian-open] [--allow-dirty] [--no-restore-point]`; exit 0 ok, 1 problems/refused, 2 usage or input error (same codes as `gedcom_sync.py`). `apply` runs `check` first and refuses on any problem; `--apply` requires `check_preconditions(..., tag_prefix="pre-organize-places")` and compares `verify.run` before/after like `gedcom_sync.cmd_apply`. `extract` writes the plan; `check` never writes.

- [ ] **Step 1: Write failing tests:** `test_the_wroclaw_chain_is_written` (three files, exact frontmatter of `Wrocław.md` as in the spec example, `full_name: Wrocław, Lower Silesian Voivodeship, Poland`, body `**Part of:** [[Lower Silesian Voivodeship]]`); `test_a_taken_basename_gets_the_parent` (existing `Neustadt.md` → new file `Neustadt, Hesse.md`, title stays `Neustadt`, a child's `parent_place` uses the new basename); `test_proposed_places_are_not_written`; `test_an_existing_place_only_gains_aliases` (other keys byte-identical); `test_a_second_apply_writes_nothing`; `test_dry_run_writes_nothing`; CLI: `test_apply_refuses_a_plan_that_fails_check` (exit 1, no files), `test_apply_without_a_restore_point_refuses` (tag `pre-organize-places-*` required), `test_an_unreadable_plan_is_exit_2`.
- [ ] **Step 2: Run** — FAIL.
- [ ] **Step 3: Implement** `apply_plan`, the `tag_prefix` parameter, and the CLI.
- [ ] **Step 4: Run** the new modules and the full suite (the existing `pre-gedcom-sync` tests must still pass) — PASS.
- [ ] **Step 5: Commit** `Create Place notes from an approved places plan`.

---

### Task 6: Sync wiring — approved strings and Person place back-fill

**Files:**
- Modify: `plugins/charted-roots/lib/gedcom_sync.py` (`_reconcile`), `plugins/charted-roots/lib/vault_verify.py` only if it loads places (leave alone otherwise), `plugins/charted-roots/lib/crsync/match.py` (new `_place_fills`, called beside `_place_changes` for `update` and `adopt`), `plugins/charted-roots/lib/crsync/report.py` (unresolved-places row hint)
- Test: `plugins/charted-roots/lib/tests/test_match.py` (class `PlaceFill`), `plugins/charted-roots/lib/tests/test_cli.py`

**Interfaces:**
- Consumes: `placeplan.load`, `placeplan.approved_placs`, `places.load(folder, approved=...)`.
- Produces: `match.PERSON_FILL_PLACES = {"birth_place": "birth", "death_place": "death", "burial_place": "burial"}`; `match._place_fills(note, ind, place_index) -> list[Change]` — for each field empty on the note whose GEDCOM event's PLAC resolves: `Change(field, None, f"[[{basename}]]", kind=FILL)`. `PERSON_PLACES` is unchanged.

- [ ] **Step 1: Write failing tests:** `test_an_empty_birth_place_is_filled_with_a_link`; `test_burial_place_is_filled_too`; `test_a_held_place_is_not_filled` (non-empty field → no fill, existing conflict behaviour unchanged); `test_an_unresolved_plac_fills_nothing`; CLI: `test_sync_links_an_approved_historical_place` (vault has the Wrocław chain + plan approving `Breslau, Schlesien, Preußen, Deutschland`; `--create` dry-run preview shows `birth_place: "[[Wrocław]]"`), `test_sync_ignores_an_unapproved_alias_match` (same vault, plac status `proposed` → no link, counted in "place values left off a new note"), `test_a_broken_plan_file_does_not_stop_the_sync` (invalid JSON → warning line in the report, sync runs without alias matching).
- [ ] **Step 2: Run** — FAIL.
- [ ] **Step 3: Implement.** `_reconcile` loads the plan (on `PlanError`: no approved set, plus a warning in the report) and passes `approved` to `places.load`. The report's unresolved-places row adds `review with /charted-roots:organize-places`.
- [ ] **Step 4: Run** the full suite — PASS.
- [ ] **Step 5: Commit** `Link approved historical places and back-fill Person places in the sync`.

---

### Task 7: The `organize-places` skill and docs

**Files:**
- Create: `plugins/charted-roots/skills/organize-places/SKILL.md`, `plugins/charted-roots/skills/organize-places/references/modern-borders.md`
- Modify: `plugins/charted-roots/lib/README.md`, `plugins/charted-roots/skills/sync-gedcom/SKILL.md` (§ What the script will not do, step 2), `plugins/charted-roots/skills/init-vault/SKILL.md` (step 2 skill list), `plugins/charted-roots/.claude-plugin/plugin.json` (description lists `organize-places`; version `0.5.0`), `README.md` (skill list), `CLAUDE.md` (skill names list, `places_plan.py` among the CLIs)

- [ ] **Step 1: Write `SKILL.md`** — frontmatter `name: organize-places`, description triggering on "places", "gazetteer", "unresolved PLAC", "historical place names". Steps as in spec §5: check vault; baseline `vault_verify.py`; `places_plan.py extract`; propose one batch at a time (largest country first) in the format shown to the user (chain, aliases, reason, uses; unidentified listed with why); record approval only on the user's word by setting `status: "approved"` on the places and PLAC entries of that batch; `places_plan.py check`; `apply` dry run; on explicit approval with Obsidian closed, entity folders committed and a `pre-organize-places-$(date +%Y%m%d-%H%M)` tag, `apply --apply`; re-run the `sync-gedcom` dry run and report the drop in unresolved values; review mode for later exports (only strings not yet in the plan; missing aliases; proposed merges per the core model's merge rule, user-approved each). Never: web search unasked, invent a place, link to a coarser Place, restructure an existing Place in `apply`.
- [ ] **Step 2: Write `references/modern-borders.md`** — the modern-border rule; `place_type` per level (`country` / `state` / `county` / `city` / `township` / `locality`); English titles per the vault Language section, native and historical forms in `aliases`; common historical jurisdictions and where they went (Prussian provinces, Austria-Hungary crown lands, Russian-Empire governorates, Danish/Swedish duchies), stated as guidance with "check the town, not the province"; when to say `unidentified`.
- [ ] **Step 3: Update the docs** listed above. `lib/README.md`: a `places_plan.py` section (subcommands, exit codes, plan path, `pre-organize-places-*` tag) and, under places, that alias matching applies only to plan-approved strings and so resolves beyond the plugin's wizard; Person place back-fill.
- [ ] **Step 4: Verify** `python3 -m unittest discover -s tests -t .` from `lib/` passes; `wc -c skills/verify-vault/references/charted-roots-model.md` unchanged (9784); `grep -rn "organize-places" plugins README.md CLAUDE.md` shows every file above.
- [ ] **Step 5: Commit** `Add the organize-places skill` (version bump included).
