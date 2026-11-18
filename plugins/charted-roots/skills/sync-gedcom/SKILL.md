---
name: sync-gedcom
description: Use when a new GEDCOM export of the upstream tree has arrived, or when asked to sync, reconcile, re-import or diff the upstream tree against an Obsidian + Charted Roots vault. Runs the dedup-aware reconciler instead of the plugin's import wizard, which duplicates every record. Dry run first; writes only after the user approves.
---

# Sync a GEDCOM export into the vault

Never use the Charted Roots import wizard for a re-import: it never reads `external_id` / `gedcom_id` back and adds a second note per record. This skill runs the reconciler that does the join. It applies only where the vault's `CLAUDE.md` names an upstream master (core model § GEDCOM); a vault that is its own master has nothing to sync.

- **Flags, exit codes, join keys, design notes:** `<lib>/README.md`.
- **Rules.** The core model is `<verify-vault>/references/charted-roots-model.md` (already in context when the plugin's session-start hook ran); the vault's `CLAUDE.md` and `.claude/conventions/*.md` override it. `<verify-vault>` is `${CLAUDE_SKILL_DIR}/../verify-vault`; `<lib>`, the shared scripts, is `${CLAUDE_SKILL_DIR}/../../lib`. Run scripts from the vault root.
- **The export:** `--ged <file>` (default `FamilyTree.ged` at the vault root). Read names per the vault's upstream-tree convention, if any.
- **Accepted rulings:** `History/gedcom-sync-decisions.json` — the script reads it from that path; a missing file accepts nothing. Created on the first ruling.
- **With `history.md`:** the method note `History/GEDCOM Reconciliation.md` (if present) and its run record `History/GEDCOM Reconciliation - Report.md` — read the latest entry before judging a finding new.

The scripts are in the plugin's `lib/`; run them from the vault root:

```sh
S=<lib>
python3 $S/vault_verify.py --limit 50                    # baseline, no GEDCOM
python3 $S/gedcom_sync.py --out <scratchpad>/sync.txt    # dry run
```

## Steps

1. **Baseline** — `vault_verify.py`. Record which checks already fail: `--apply` compares the suite before and after and calls only the difference a regression. Exit 2 means the run did not start, not a pass.
2. **Dry run** and read section 0 first. Report to the user: adoption candidates, unresolved PLAC values, non-places in PLAC, citation duplicates, held `coarsen` / `conflict` changes, WOULD REFUSE lines.
3. **Stop for rulings.** Held changes, adoptions (`--adopt-by-name`) and creation (`--create`) are the user's decisions. Write a ruling into the decisions file only when the user gives it, with their reason.
4. **Preview** `--create` on a dry run if creation is wanted; list the planned notes.
5. **Apply — only on explicit approval.** The user quits Obsidian; commit the entity folders; tag `pre-gedcom-sync-$(date +%Y%m%d-%H%M)`; then `--apply`, scoped with `--only` for a large sync. The script refuses without all three. Never pass `--allow-obsidian-open`, `--allow-dirty` or `--no-restore-point` unasked.
6. **After** — review the diff, re-run `vault_verify.py`, then the `verify-vault` skill's unscripted checks over the changed notes. Re-check for import-created notice/obituary Events and `source_type: document` (`CLAUDE.md`).
7. **Record** — with `history.md`, a dated entry in the run record: export date + sha256, restore point, baseline and after results, rulings made, hand fixes. Otherwise put the same in the report to the user.

## What the script will not do

- **Create Places**, or write a PLAC value it cannot resolve against the gazetteer — the place hierarchy is a schema decision and its own pass.
- **Create an Event for a suppressed `EVEN` block** — an obituary, testament or licence block is a Source reporting an event.
- **Delete anything** — vault-only People, Sources and Events are reported as orphans and left alone.
- **Touch a note whose frontmatter it cannot fully parse**, or whose `---` block never closes.

Everything is idempotent: a second run with no upstream change writes nothing.

## Never

- Edit the `.ged`, or push structural changes back by round-trip — changes go upstream by hand.
- Delete vault-only notes the report lists as orphans.
- Send report contents anywhere external; the tree holds living people.
