---
name: init-vault
description: Set up an Obsidian + Charted Roots vault for this plugin — writes the vault's CLAUDE.md, copies the chosen convention modules into .claude/conventions/, and enables the plugin at project scope. Run once per vault, or again to add modules.
disable-model-invocation: true
---

# Set up a vault

Installs the vault-side files. The core model (`${CLAUDE_SKILL_DIR}/../verify-vault/references/charted-roots-model.md`) is not copied: the plugin's session-start hook loads it into every session in a vault. Templates: `${CLAUDE_SKILL_DIR}/../../templates/` — `CLAUDE.md` and `conventions/*.md`. If that folder is missing (skills copied without the plugin), say so and stop.

Nothing is written until the user approves the plan in step 4. Never overwrite a file without showing the diff first.

## 1. Check the vault

Work in the project root (`${CLAUDE_PROJECT_DIR}`). It must contain `.obsidian/plugins/charted-roots/data.json`; if not, stop — this is not a Charted Roots vault. Read `data.json` for the folder keys used below.

## 2. Inventory what exists

- `CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/conventions/*.md`, `.claude/settings.json`.
- Local copies of this plugin's skills in `.claude/skills/` (`add-archive-record`, `research-ancestry`, `verify-vault`, `sync-gedcom`, `organize-places`): each would appear twice next to the plugin's. Report them; remove only if the user agrees.
- An existing `CLAUDE.md` that already holds the core model (sections such as *Entity model*, *Invariants*, *Evidence chain*): with the hook loading the model, those sections are duplicates. Propose trimming them, never silently.

## 3. Propose modules

`archive.md` and `source-collections.md` are always installed — every vault gets them, so they are not offered. Suggest each of the other modules from evidence in the vault, and say what the evidence is:

| Module | Suggest when |
|---|---|
| `research.md` | `cr_type: research_project` notes with `Hypothesis - ` / `Survey - ` / `Reference - ` / `Search Plan - ` prefixes |
| `letters.md` | a `Letters/` folder |
| `history.md` | a `History/` folder |
| `upstream-ancestry.md` | a `.ged` at the vault root exported from Ancestry (`1 SOUR Ancestry.com` in the header) |

A module with no evidence is still offered — a new vault may want it. Ask once, as a single multi-select question, which of these four to install, and which working language to use (default English).

## 4. Show the plan

List each file to create or change, with the full content of new files and a diff for changed ones:

- **`CLAUDE.md`** — from `templates/CLAUDE.md`: keep the `@.claude/conventions/<module>.md` lines for `archive.md`, `source-collections.md` and the chosen modules only; set the Language section to the chosen language. With an existing `CLAUDE.md`, merge: keep every vault-specific line, add the missing sections, and mark the core-model duplicates from step 2.
- **`.claude/conventions/<module>.md`** — a copy of `archive.md`, `source-collections.md` and each chosen template. An existing file that differs from the template is the vault's own version: keep it unless the user asks to replace it, and show the diff.
- **`.claude/settings.json`** — merge in, keeping every existing key:

  ```json
  {
    "extraKnownMarketplaces": {
      "charted-roots-skills": {
        "source": { "source": "github", "repo": "AntonShevchuk/charted-roots-skills" }
      }
    },
    "enabledPlugins": { "charted-roots@charted-roots-skills": true }
  }
  ```

  This file is committed, so anyone who clones the vault gets the plugin offered. Skip it if the user keeps the plugin enabled some other way.

Wait for approval.

## 5. Write and report

Write the approved files. Then report:

- what was created, changed and left alone;
- next steps: commit the new files; collaborators run `claude plugin install charted-roots@charted-roots-skills --scope project` once per clone; start a new session (or `/reload-plugins`) so the hook loads the model;
- run `/charted-roots:verify-vault` for a first baseline.
