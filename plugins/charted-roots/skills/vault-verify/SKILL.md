---
name: vault-verify
description: Use when checking the vault for consistency — after adding records, merging, a GEDCOM sync or re-import, bulk edits, or when asked to verify, audit or health-check the vault or a part of it. Read-only; reports findings, fixes nothing without approval.
---

# Verify the vault

Read-only. `scripts/` here is the vault's shared toolkit — `gedcom-sync` and `add-archive-record` use it too; tests: `cd scripts && python3 -m unittest discover -s tests -t .`. Runs the scripted invariants, then the checks not yet scripted, and reports what is new. Rules being checked live in `references/charted-roots-model.md` (the core model, which the other skills in this plugin read too), overridden by the vault's `CLAUDE.md` and the convention modules it loads; skip the rows of a module the vault does not use.

## Scope

- **Whole vault** — default, and after any sync or re-import.
- **Changed notes** — after a local edit: `git status --porcelain -z` and/or `git diff --name-only <rev>`, plus every note those notes link to or are linked from (a relationship has two sides). Say which scope was run.

## 1. Scripted invariants

```sh
python3 <this skill's base directory>/scripts/vault_verify.py --limit 50   # from the vault root
```

Vault-wide always (cheap). Exit 0 pass, 1 a check failed, 2 could not start — fix the input on 2, never report it as a pass. Covers: frontmatter closes and parses, `cr_id` unique, `cr_type` / `source_type` / `place_type` vocabularies, filenames, Citation `subject_id` and both-direction `citations:` links, `_id` parity and targets, wikilinks (code masked, `History/` exempt), Event precision without date, Person `born`/`died` against the plugin's date validator.

## 2. Checks not yet scripted

Run over the scope with a throwaway script in the scratchpad (read notes with `crsync.vault.iter_notes` / `parse`, folders from `crsync.config.load`, via `sys.path.insert(0, '<this skill>/scripts')` — no YAML library is installed). Mask fenced blocks and inline code before reading body links.

| Area | Check |
|---|---|
| Graph | father/mother ↔ parent's `children`; `spouseN` ↔ the spouse's slot pointing back; `children`/`children_id` same order |
| Facts | Person `born`/`died`/`birth_place`/`death_place` agree with the Birth/Death Event (`c. YYYY` ↔ `date_precision: estimated`; a bare Person date may pair with an Event `BEF`/`AFT`) |
| Events | one Event per type per person (a trailing `-N` is a sequence number, not a duplicate); no notice/obituary/index card typed as an Event |
| Places | no child ranked above its parent (`region` exempt); `full_name` = title + ancestors, except root notes |
| Sources | with `source-collections.md`: non-parent Sources have exactly one `source_parent`, parents carry no `repository`, `confidence: unknown`; always: non-import Sources have real `confidence`, no `gedcom_id` |
| Source bodies | with `archive.md`: `## Linked records` names the Events and Citations that actually point at the Source; each transcription embedded once, callout title = its H1 |
| Transcriptions | with `archive.md`: template — H1 genre, `Document Type` present, no frontmatter, no links out, `## English Translation` for non-English originals, only allowed trailing sections in order |
| Research notes | with `research.md`: only allowed properties; `status`/`result` agree with the `**Status:**` badge (prose wins) |
| Letters | with `letters.md`: every letter has a letters-index row; row status = the letter's status line |
| Media | with `archive.md`: scans are `.jpg`/`.pdf`; a transcription's scan exists or its Source says where the image lives |

When one of these proves stable, propose adding it to `scripts/crsync/verify.py` with a test in `scripts/tests/test_verify.py` (upstream, in this plugin's repository) instead of re-scripting it.

## 3. Classify

- **Known hygiene issue** (core model § Known hygiene issues: `-N` filenames, `confidence: unknown`, empty classification fields, missing coordinates, unidentified places, anachronistic chains) → note the count, not a failure.
- **Pre-existing** → with `history.md`, compare against the latest relevant `History/* - Report.md`; a finding already recorded there is a baseline, not news.
- **New** → the actual result.

## 4. Report

Per check: pass/fail, count, each failing note as a clickable path with the one-line reason. New findings first. End with the suggested fix for each class and whether it is one note or a bulk change.

- **Fix nothing unasked.** A fix the user approves: small batches; with Obsidian open and sync on, write one side only; re-run step 1 after.
- With `history.md`: bulk fixes get a `History/<task>.md` method + `History/<task> - Report.md` run record.
- Baselines from a whole-vault run go in `History/Vault Verification - Report.md` (or, without `history.md`, only in the report to the user) — never in an instruction file.
- The vault holds data on living people: findings stay local.
