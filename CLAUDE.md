# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Claude Code plugin marketplace (`.claude-plugin/marketplace.json`) shipping one plugin, `plugins/charted-roots/`, for Obsidian genealogy vaults managed by the **Charted Roots** Obsidian plugin. Most of the content is skill prose (`skills/*/SKILL.md` + `references/`); the code is standard-library Python under `lib/` and `skills/research-ancestry/scripts/`.

This repo is not itself a vault. The `.obsidian/` folder here is untracked editor state, so the session-start hook stays silent in this repo.

## Commands

Python 3.10+, standard library only: no venv, no manifest, no dependencies. Pillow is optional and only used by `scan_montage.py`.

```sh
cd plugins/charted-roots/lib
python3 -m unittest discover -s tests -t .              # all tests
python3 -m unittest tests.test_dates                    # one module
python3 -m unittest tests.test_dates.FromGedcom         # one class / method
```

The tests import `crsync` as a top-level package, so run them from `lib/`. Fixtures (`tests/helpers.py`) build a synthetic vault in a temp dir. Never point tests at a real vault, and keep every fixture name fictional.

There is no linter or build step.

## Architecture

**The shared toolkit is `plugins/charted-roots/lib/`.** It holds the `crsync` package plus the CLIs `vault_verify.py`, `gedcom_sync.py`, `places_plan.py`, `fix_person_dates.py` and `gedcom_check.py`, and is used by `verify-vault`, `sync-gedcom`, `validate-gedcom`, `organize-places` and `add-archive-record`. Skills reach it as `<lib>` = `${CLAUDE_SKILL_DIR}/../../lib`, and the scripts are run from the vault root. The core model is still inside a skill, reached as `${CLAUDE_SKILL_DIR}/../verify-vault/references/`, so renaming `verify-vault` means updating the other skills and the hook.

**The rules exist in one place.** `skills/verify-vault/references/charted-roots-model.md` is the core model (entity model, invariants, evidence chain, vocabularies, places, GEDCOM, date forms). Every skill reads it instead of restating it. Precedence, lowest to highest: core model → a vault's `CLAUDE.md` → that vault's `.claude/conventions/*.md`.

**The session-start hook** (`hooks/session-start.sh`) prints the core model only when `$CLAUDE_PROJECT_DIR/.obsidian/plugins/charted-roots/data.json` exists. It prints nothing if the vault already has its own copy in `.claude/conventions/`. Hook output is capped at 10,000 chars, so the script inlines the model only up to 9,800 bytes and otherwise prints a pointer to the file. The model is currently ~9,780 bytes, so almost any addition to it switches the hook to pointer mode. Keep it tight, or move material into convention modules or skill references.

**Templates are copied into vaults.** `templates/CLAUDE.md` and `templates/conventions/*.md` are what `init-vault` writes into a user's vault. Each skill has to keep working, in a degraded form, when an optional convention module is missing. Folder paths come from the vault's Charted Roots `data.json` keys and are never hard-coded.

**Why `gedcom_sync` exists.** The Charted Roots import wizard does no dedup: it mints a random `cr_id` per record and never reads `external_id`/`gedcom_id` back. `gedcom_sync.py` does that join instead, with a dry run by default and `--apply` to write. `lib/README.md` is the authoritative reference for flags, mode exclusivity, exit codes, date-form rules (`crsync/dates.py`: Person `born`/`died` must pass the plugin's date validator, while Events keep GEDCOM qualifiers) and place-conflict handling. Update it whenever CLI behaviour changes. GEDCOM parsing targets Ancestry 5.5.1 exports. The vault-side names `History/gedcom-sync-decisions.json` and the `pre-gedcom-sync-*` restore tags predate the skill rename and stay as they are, since existing vaults hold them.

## Conventions

- Skills never do web search, upload or e-mail without the user's explicit instruction, and never send letters. Vault data covers living people.
- `research-ancestry` is adapted from an upstream MIT project and keeps its own `LICENSE`. Leave that file in place.
- Skill names are imperative verb–object (`verify-vault`, `sync-gedcom`, `research-ancestry`, `add-archive-record`, `organize-places`, `init-vault`); name new skills the same way.
- The plugin version is in `plugins/charted-roots/.claude-plugin/plugin.json`.
