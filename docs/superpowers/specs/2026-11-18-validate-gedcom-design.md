# validate-gedcom: a standalone GEDCOM checker that lists upstream fixes

## Intent

A GEDCOM export carries mistakes made in the host tree (Ancestry, MyHeritage, …):
the same birth recorded twice, a marriage on a person instead of the family,
dates the parser cannot read, the same town spelled three ways. Today the few
checks that exist are buried in the `gedcom_sync.py` dry-run report, which
needs a vault, and some disappear under `--only`. The user wants the export
checked **on its own**, with the result being a **list of fixes to make in the
host** — then re-export. The `.ged` is never edited (project rule: changes go
upstream by hand).

## Goals

- `lib/gedcom_check.py`: a CLI that reads one `.ged`, needs no vault, writes
  nothing, and prints every finding as *who / where / what is wrong / the fix
  in <host>*.
- `lib/crsync/gedcheck.py`: the checks, as pure functions over a parsed
  `gedcom.Tree`, unit-tested.
- `skills/validate-gedcom/SKILL.md`: runs the script and presents the fixes to
  the user as a table grouped by person.
- One source of upstream fixes: section 8 of the sync report
  (`report.upstream_marriage_fixes`) moves into `gedcheck`.

## Non-goals

- Editing or rewriting the `.ged`, or producing a corrected copy.
- Comparing against the vault (that is `gedcom_sync.py`'s job), including
  resolving PLACs against Place notes.
- Full genealogical plausibility (mother's age at birth, generation gaps,
  sibling spacing). Only the small chronology set below.
- GEDCOM 5.5.1 grammar validation (tag legality, level jumps, xref
  cross-references beyond what the checks need).
- Being a gate: `gedcom_sync.py` does not refuse to run on findings.

## Anti-goals

- A check that buries the user in noise: legitimate repeats (several RESI,
  CENS, OCCU; two people in different Springfields) must not be reported.
- A finding without a concrete fix line. Every finding says what to do in the
  host.
- Two copies of a check that can drift (the marriage logic, the non-place
  markers, date parsing, place folding are reused, not re-implemented).

## Constraints

- Python 3.10+, standard library only; tests run from `lib/` with
  `python3 -m unittest discover -s tests -t .`; fixtures fictional, built via
  `tests/helpers.ged`.
- Parsing stays in `crsync/gedcom.py` (`gedcom.parse`). Date reading stays in
  `crsync/dates.py`. Place normalisation uses `crsync/places.key` / `fold`.
- The core model file is near the session-hook's 9,800-byte cap; this work
  does not touch it.
- Skill name follows the imperative verb–object rule: `validate-gedcom`.
- Skills never send data externally; the tree holds living people.

## Approaches considered

- **A. Separate script + module (chosen).** `gedcom_check.py` +
  `crsync/gedcheck.py`, reusing the parser; the sync report keeps only counts
  and a pointer. Testable, matches the user's "separate script", and takes
  non-sync checks out of the sync report.
- **B. A `--check` mode on `gedcom_sync.py`.** Less code, but contradicts the
  ask and adds another row to `_MODE_FLAGS`, whose every flag would need a
  "not with `--check`" rule.
- **C. Skill only.** Claude reads the `.ged` per prose instructions.
  Non-deterministic, slow on large exports, untestable; the checks are
  mechanical.

The user picked A.

## Design

### Parser change

`gedcom._tree` records the 1-based source line on each `Node` (`line: int`),
and `_read_event` copies it to `Event.line`. INDI/FAM records keep their line
too (`Individual.line`, `Family.line`). `Event` also keeps `place_raw`, the
PLAC as written, because `_fold_marriages` copies a person-level place onto
the family event. Nothing else in parsing changes.

### What the checks read *(builder's call)*

- **Events only:** INDI and FAM events, **including** the suppressed EVEN
  blocks in `tree.suppressed`. They are never synced, but their DATE and PLAC
  still come from the host and are worth fixing there. DATE and PLAC lines
  outside events (citation `DATA`/`DATE`, `CHAN`, PLAC under SOUR) are not
  checked.
- **Places as written:** `place-*` checks use `place_raw`, so a folded
  marriage's place is counted once.
- **Duplicates on the tree as parsed:** `EVEN` / `TYPE MARR`, `Hochzeit` and
  the like count as MARR, because that is what the host recorded. MARRs already
  reported under `marriage-on-person` (`ev.folded`) are left out of
  `dup-marriage` and `dup-event-exact`, so nothing is reported twice.

### Finding

```python
@dataclass
class Finding:
    check: str        # e.g. "dup-vital"
    group: str        # duplicates | dates | places | marriages
    kind: str         # "fix" (mechanical) | "review" (needs the user's judgement)
    who: str          # "Anna Example (@I12@)", or the family "… & … (@F3@)", or "" for a place
    line: int         # GEDCOM line of the offending record, 0 if none
    what: str         # what is wrong, one line
    fix: str          # "in Ancestry: …", one line
```

`gedcheck.run(tree, only=None) -> list[Finding]`, ordered by group then
person. Host name comes from the HEAD (`report.host_name`, moved into
`gedcheck` and imported back by `report`).

### Checks

**duplicates**
- `dup-vital` — an INDI with more than one BIRT, DEAT, BURI or CREM.
  Same date and place → `fix`: "delete the duplicate". Otherwise → `review`:
  "two conflicting births (A at P1, B at P2): keep the one the evidence
  supports, delete or demote the other". (Today the sync numbers the second one
  by ordinal and could create a second birth Event.)
- `dup-event-exact` — any other event tag repeated on one owner with the same
  date *and* place (both non-empty) → `fix`. Different values are never
  reported for repeatable tags.
- `dup-marriage` — a FAM with more than one MARR. `what` lists every copy as
  `date at place`. Identical `date` and `places.key(place)` on all copies →
  `fix`: "delete the duplicate". Compatible but different dates
  (`gedcom._same_date`) or different places → `review`: keep the copy with the
  more precise date / with a place. Incompatible dates → `review`.
- `dup-family` — two FAMs with the same couple (sorted INDI xrefs, both
  present) → `review`: "merge the two families".

**marriages** (moved from sync section 8, same wording)
- `marriage-on-person` — `tree.folded` (duplicate of the family marriage) and
  `tree.person_marriages` (only on the person), with the existing fix text.

**dates**
A new `dates.classify(raw) -> (label, suggestion)` sorts every DATE into
`standard`, `standard-unparsed`, `lenient` or `unreadable`. It recognises the
GEDCOM 5.5.1 date grammar, so `gedcheck` never relies on `from_gedcom`'s
`unknown` alone. *(builder's call)*

- `standard-unparsed` is **not reported**. These are valid GEDCOM that the
  sync just can't turn into an ISO date: an open period (`FROM 1850`,
  `TO 1860`), `INT … (…)`, a bare `(phrase)`, a calendar escape
  (`@#DJULIAN@ …`), a dual year (`1750/51`), and `B.C.`.
- `date-unreadable` — label `unreadable`, including a `BET x AND y` or
  `FROM x TO y` where one side doesn't parse → `fix`: "rewrite as
  D MMM YYYY (or ABT / BEF / AFT / BET … AND …)".
- `date-invalid` — reads, but is not a calendar date (31 FEB, month 13), via
  `datetime.date` → `fix`.
- `date-nonstandard` — label `lenient`: anything GEDCOM 5.5.1 doesn't define,
  such as German month names, `D.M.YYYY`, ISO, `c.`/`ca.`/`circa`/`~`,
  `YYYY-YYYY`, full or dotted month names (`December`, `Dec.`), spelled-out
  keywords (`About`, `Before`, `After`) → `fix`, with the suggested standard
  form (`25 DEC 1914`, `ABT 1804`, `BET 1850 AND 1858`).
  **Letter case alone is not flagged** (`25 Dec 1914` is fine), and neither is
  a trailing dot on a GEDCOM keyword (`Abt.`, `Bef.`, `BET. … AND`, `CAL.`,
  `EST.`): Ancestry writes them everywhere, so they count as standard like
  case does. *(builder's call)*
- `date-order` — death before birth; burial/cremation before death; a child
  born before a parent's birth; lifespan over 120 years. Compared on the
  earliest/latest bounds so `ABT`/ranges do not false-positive → `review`.

**places**
- `place-non-place` — `gedcom.non_place_reason` hits → `fix`: "move the unit /
  rank into the description; set PLAC to the place".
- `place-format` — leading/trailing spaces, doubled spaces, a space before a
  comma, an empty component (`a, , b`) or a trailing comma → `fix` with the
  cleaned string. When the HEAD declares `1 PLAC` / `2 FORM` (recorded in
  `tree.header["plac_form"]`), empty components are positional placeholders:
  a string whose only issue is empty components is a `review` instead.
- `place-variant` — distinct PLAC strings equal under `places.fold` +
  whitespace normalisation (case, accents, US-state abbreviations) → `fix`:
  "use one spelling; most used: X (n)". Ranked by use count, then by more
  non-ASCII characters (the accented form), then alphabetically; when the top
  count is shared the fix reads "use one spelling, e.g. X". One finding per
  variant group, not per event.
- `place-hierarchy` — same leaf where one string's parent chain is a strict
  subsequence of another's (`Berlin, Germany` vs `Berlin, Brandenburg,
  Germany`) → `review`: "standardise to the fuller form". Leaves with unrelated
  parents (`Springfield, Illinois` / `Springfield, Ohio`) are not reported.
  Leaves and chains are compared after `places.fold`. Only the maximal fuller
  forms are listed: a candidate that another candidate extends is dropped, so
  nested forms give one finding per shorter string. A strict subsequence
  must not be empty, so a **bare leaf** is handled on its own
  *(builder's call)*:
  - exactly one fuller form → `fix`: "use <the fuller form>";
  - several fuller forms → `review`: "which one is meant: A, B …?";
  - no fuller form → not reported.

Place findings carry the PLAC string and the count of events using it; `who`
lists up to three people and "and N more".

### CLI: `gedcom_check.py`

```
python3 <lib>/gedcom_check.py [--ged FILE] [--only GROUPS] [--json] [--out FILE] [--limit N]
```

- `--ged` default `FamilyTree.ged`, relative to the current directory.
- `--only duplicates,dates,places,marriages`; unknown name → exit 2 (same
  rule as `gedcom_sync --only`).
- Text output: a header (file, size, sha256, host, export date, read warnings
  from the parser), then a summary table of counts per check, then findings
  grouped by check, `--limit` per check (default 20; `0` = all).
- `--json`: the full list of findings as JSON objects (no limit), for the
  skill.
- `--out`: also write the text report to a file.
- Exit codes: 0 no findings; 1 findings; 2 could not start (bad flags,
  missing/undecodable file).

### Sync report changes (`report.py`)

- Section 8 becomes **GEDCOM CHECK**: one count line per check group plus
  "run `gedcom_check.py` for the fix list". Shown regardless of `--only`.
- Section 0 "Non-place values in a GEDCOM PLAC line" keeps its count (it
  explains sync behaviour) and drops its detail lines in favour of the
  pointer.
- Section 6 (media): count records with an empty `1 FILE` instead of asserting
  "every one has an empty FILE" (wrong for non-Ancestry exports).
- `tests/test_cli.py` FIX UPSTREAM tests move to the new tests or are adjusted.

### Skill: `skills/validate-gedcom/SKILL.md`

- Triggers: a new export arrived; "check / validate / lint the GEDCOM";
  before `sync-gedcom`.
- Runs `python3 <lib>/gedcom_check.py --ged <file> --json` from the vault root
  (or wherever the file is; no vault needed).
- Presents a table per person: person (name + xref as the `.ged` holds it),
  line, what is wrong, the fix in <host>; `review` findings separated and
  explained as decisions only the user can make; place findings as their own
  table.
- Never edits the `.ged`, never sends anything external; offers to save the
  fix list to a file the user names.
- `sync-gedcom` SKILL.md step 2: replace the section 8 bullet with "run
  `validate-gedcom` first, or point to its section in the report".

### Docs and housekeeping

- `lib/README.md`: a `gedcom_check` section (flags, checks, exit codes).
- Repo `CLAUDE.md`: list `gedcom_check.py` among the CLIs and `validate-gedcom`
  among its users.
- Bump the plugin version in `plugins/charted-roots/.claude-plugin/plugin.json`.

## Left to the builder

- Exact text wording of fix lines (keep them one line, host-named, concrete).
- Internal structure of `gedcheck.py` (one function per check is expected).
- Whether `Finding` lives in `gedcheck.py` or a tiny shared module.

## Considered and deferred (sync script)

- `_reconcile` loads every entity folder even under a narrow `--only`.
  Matchers and creation cross-reference people, sources and events, so lazy
  loading risks subtle breakage for a small saving; not in this work.
- The sync gives a second BIRT/DEAT its own ordinal and could create a second
  birth or death Event. Changing that is sync behaviour and out of scope here.
  `dup-vital` reports it so it gets fixed upstream. It's a candidate follow-up.
