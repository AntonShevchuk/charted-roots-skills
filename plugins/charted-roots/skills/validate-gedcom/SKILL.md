---
name: validate-gedcom
description: Use when a GEDCOM export arrives, before sync-gedcom, or when asked to check, validate or lint a .ged file. Lists duplicate events, bad dates and inconsistent place names as fixes to make in the host tree (Ancestry, MyHeritage, …); never edits the file.
---

# Validate a GEDCOM export

An export carries the host's mistakes: duplicate events, marriages written on a person instead of the family, dates the plugin cannot read, one place spelled several ways. This skill lists them as fixes to make in the host, before the export reaches `sync-gedcom`. No vault is needed.

- **Check list, flags, JSON shape, exit codes:** `<lib>/README.md` (§ gedcom_check). `<lib>` is `${CLAUDE_SKILL_DIR}/../../lib`.

```sh
python3 <lib>/gedcom_check.py --ged <file> --json
```

Exit 0: no findings. Exit 1: findings. Exit 2: the run did not start (bad flags, missing or unreadable file); say why, it is not a pass.

## Steps

1. **Run** the command above on the file the user names (default `FamilyTree.ged` in the current directory). The JSON holds `ged`, `host`, `exported`, `sha256`, `warnings` and `findings`, each finding `{check, group, kind, who, line, what, fix}`; `kind` is `fix` or `review`.
2. **Present**, in this order:
   - A header line: file, host, export date, any warnings.
   - **Fixes** (`kind: fix`): a table per person with the person (name and xref as the `.ged` holds it), line, what is wrong, and the fix to make in the host.
   - **Your decisions** (`kind: review`): one line per finding on why it needs the user's judgment.
   - **Places**: their own table of PLAC value, count and fix.
   - With more than about 40 findings, give the counts per check first and offer the full list.
3. **Offer** to save the fix list to a file the user names. Write it only there.
4. **Next step**: the user makes the changes in the host, exports again, and re-runs this check; then `sync-gedcom`.

## Never

- Edit the `.ged`. Changes are made in the host, then re-exported.
- Send findings anywhere external (web search, upload, e-mail); the tree holds living people.
