---
name: organize-places
description: Use when a vault synced from a GEDCOM export has unresolved PLAC values or no Place notes, or when asked to organise places, build a gazetteer, map historical place names (Breslau, Preußen, Danmark) to modern borders, or review Places for missing aliases. Proposes a modern-border gazetteer in batches, then creates the approved Place notes with historical names as aliases. Nothing is written until the user approves a batch.
---

# Organise places to modern borders

An export records places as they were named then and in the native language (`Breslau, Schlesien, Preußen, Deutschland`). `gedcom_sync.py` links a place only to an existing Place note and never creates one, so those values stay unresolved. This skill makes the gazetteer decision once: Place notes under **modern borders**, historical and native names in `aliases:`, so every PLAC links to the right modern Place. The sync then resolves the PLACs the user approved.

- **Flags, exit codes, plan fields:** `<lib>/README.md` (§ places_plan).
- **Rules.** The core model (§ Places, `place_type`, merge rule) is `<verify-vault>/references/charted-roots-model.md`, already in context when the plugin's session-start hook ran; the vault's `CLAUDE.md` and `.claude/conventions/*.md` override it. `<verify-vault>` is `${CLAUDE_SKILL_DIR}/../verify-vault`; `<lib>`, the shared scripts, is `${CLAUDE_SKILL_DIR}/../../lib`. Run scripts from the vault root.
- **Mapping guidance:** `${CLAUDE_SKILL_DIR}/references/modern-borders.md`. Read it before the first batch.
- **Folders** come from the vault's Charted Roots `data.json` (`placesFolder`), never from memory.
- **The plan:** `History/places-plan.json`, committed with the vault. Two parts: `places` (one entry per Place, keyed by a plan key: `title`, `place_type`, `parent`, `aliases`, `reason`, `status` of `proposed` / `approved` / `created`; an existing note carries its `cr_id`) and `plac` (one entry per distinct PLAC string: `count`, and `place` naming a plan key, or `not_place`, or `unidentified` with what is uncertain; `status` of `proposed` / `approved`).
- **The export:** `--ged <file>` on `extract` (default `FamilyTree.ged` at the vault root).

```sh
S=<lib>
python3 $S/vault_verify.py --limit 50          # baseline
python3 $S/places_plan.py extract              # list the PLAC strings into the plan
python3 $S/places_plan.py check                # validate the plan
python3 $S/places_plan.py apply                # dry run
python3 $S/places_plan.py apply --apply        # write the approved places
```

Exit codes: 0 ok; 1 problems found or the write refused; 2 the run could not start (bad flags, unreadable vault, plan or GEDCOM), which is not a pass.

## Steps

1. **Check the vault** — `data.json` is present and `placesFolder` names the gazetteer. Run `vault_verify.py` as the baseline; `apply --apply` compares the suite before and after and calls only the difference a regression.
2. **Extract** — `places_plan.py extract`. It lists each distinct PLAC string with its count and records a string the plugin's own lookups already resolve as `approved` against that note. Re-running on a new export adds only new strings and never drops a reviewed entry. A string that is not a place gets `not_place` filled in at `proposed`; leave those entries alone unless the user disagrees. Commit the plan file now: `apply --apply` checks only the entity folders for a clean tree (`History/` is not among them), but a committed plan keeps the review diffable. Report the totals.
3. **Propose one batch at a time**, largest country first, from your knowledge and the PLAC strings themselves. No web search unless the user asks. Show each batch in this format:

   ```
   Batch: Poland — 14 place names, 212 uses

     Breslau, Schlesien, Preußen, Deutschland   (38 uses)
       → Poland › Lower Silesian Voivodeship › Wrocław
         aliases: Breslau · Schlesien (on Lower Silesian)
         reason: Breslau has been Polish Wrocław since 1945

     Neudorf, Schlesien, Preußen                (2 uses)
       → unidentified: dozens of Neudorfs in Silesia; check the record image
   ```

   Chain, aliases and the Place each belongs to, a reason for any non-obvious mapping, uses, and the unidentified strings with why. Titles are the modern English form; historical and native forms are aliases (`references/modern-borders.md`).
4. **Record the proposal** — edit `History/places-plan.json` directly (it is plain JSON): add the proposed places, set each PLAC entry's `place` (or `unidentified` / `not_place`). Leave `status` as `proposed`. Reuse an existing Place by its plan key rather than adding a twin.
5. **Approval** — the user corrects the batch. Only on their word, set `status: "approved"` on the places and the PLAC entries of that batch, by editing the file. Never approve on your own judgment, and never approve an `unidentified` or `not_place` entry.
6. **Check** — `places_plan.py check`. Exit 1 lists problems: a missing parent, a cycle, an invalid `place_type`, a duplicate title under one parent, a Place that already exists, an approved string that would not resolve to its own planned Place. Fix the plan, usually by adding the alias that disambiguates, and re-run until it is consistent.
7. **Dry run** — `places_plan.py apply` lists the notes it would create and the aliases it would add to existing Places. It refuses on a plan that fails `check`. Show the list.
8. **Apply — only on explicit approval.** The user quits Obsidian; commit the entity folders; tag `pre-organize-places-$(date +%Y%m%d-%H%M)`; then `places_plan.py apply --apply`. It writes approved places only, parents first, and marks them `created` in the plan. It refuses without all three preconditions. Never pass `--allow-obsidian-open`, `--allow-dirty` or `--no-restore-point` unasked.
9. **After** — review the diff, re-run `vault_verify.py`, commit the notes and the updated plan. Then re-run the `sync-gedcom` dry run and report how many place values now resolve and how many remain unresolved, and why. Continue with the next batch from step 3.

## Review mode (later exports)

Run `extract` again: it adds only the strings not yet in the plan. A new string is never linked through an alias until the user has approved it, so propose just those, as above. Also look for:

- **Missing aliases**: a Place the export names in a form it lacks. `extract` records every existing Place it resolves as a `created` entry with its `cr_id`. Add the missing form to that entry's `aliases` in the plan, together with the approved PLAC string that needs it if there is one; `check` validates the new alias and the string in the same batch. On the user's approval run `check`, then `apply --apply`. It adds the aliases the note lacks (case-insensitive, existing order kept) and changes nothing else on it; a second run writes nothing.
- **Likely duplicates**: propose a merge to the user under the core model's merge rule, one merge at a time with their approval. `apply` never merges.
- **An existing Place on a historical chain** (a `Preußen` country note): do not parent new Places under it and do not create a modern twin. Propose a re-parent, retitle or merge to the user instead. The scripts do not guard this; it is on you.

## What the script will not do

- **Restructure an existing Place** — it only adds missing aliases to one. Re-parenting, retitling and merging are hand edits under the core model's merge rule.
- **Create a Place for an entry that is not approved**, or write anything while the plan fails `check`.
- **Geocode** — no coordinates, no lookups.
- **Delete anything**, or edit the `.ged`.

A new Place's note name is its `title`; when that name is taken it becomes `<title>, <parent title>`, and so on up the chain. Links are plain `[[note name]]`.

## Never

- Web-search, geocode or look a place up unless the user explicitly asks.
- Invent a Place for a string that cannot be identified. Unidentified stays unidentified and the PLAC stays unresolved.
- Link a PLAC to a coarser Place than the string names (an unknown village to its region).
- Set `status: "approved"` without the user's word.
- Restructure an existing Place through `apply`.
- Send report contents anywhere external; the tree holds living people.
