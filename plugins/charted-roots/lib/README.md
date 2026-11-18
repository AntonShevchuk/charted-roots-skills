# gedcom_sync

Reconciles a GEDCOM export of the upstream tree (`--ged`, default `FamilyTree.ged`) against the vault **without creating duplicates**.

## Why this exists

The Charted Roots importer (v0.22.76) does no duplicate detection except for
Places. Verified in `main.js`:

* `importIndividual` mints a fresh random `cr_id` for every INDI and never
  looks up `external_id`. The only existence check is a filename-collision
  avoider producing `Name 1.md`, `Name 2.md`.
* Sources, Events and Citations behave the same way.
* `external_id` (INDI xref) and `gedcom_id` (SOUR xref) are **written but
  never read back** — the join keys are on disk and simply unused.
* The wizard's "Duplicate handling" radio feeds only `overwriteExisting`,
  which is read solely by the separate-NOTE-file writer. It is a no-op for
  person/event/source/place/citation, and its `skip` option — "skip new ones
  with same cr_id" — can never fire, because `cr_id` is regenerated randomly.

Re-running the wizard therefore adds a second note for every record in the
export rather than updating the one already there. This script does the join
the plugin skips.

## Usage

`<lib>` below is this folder, the plugin's `lib/`.

`vault_verify.py` runs the invariant suite alone: no GEDCOM, never writes,
`--vault` and `--limit` only. It is the baseline before and after any edit,
not just a sync. `gedcom_sync.py --verify` is an alias for it, kept for the
History run records that quote it.

    python3 <lib>/vault_verify.py             # vault invariants, no GEDCOM
    python3 <lib>/gedcom_sync.py              # dry run, full report
    python3 <lib>/gedcom_sync.py --out r.txt  # also write the report to a file
    python3 <lib>/gedcom_sync.py --apply      # write
    python3 <lib>/gedcom_sync.py --only person,source

Python 3, standard library only. No dependencies, no venv, no manifest.

`--only person,source,event,citation,place` scopes a run: the report drops
the sections you did not ask for, and `--apply` runs only those write passes,
which is how a large sync becomes several reviewable diffs. An unrecognised
name stops the run rather than silently narrowing it to nothing. It cannot be
combined with `--create` — new Events name new People by filename and new
Citations name both, so creating one kind without the others would leave
dangling links — and it does not apply to `--verify`, whose invariants are
vault-wide. Only `person`, `source` and `event` have a write pass, so
`--apply` refuses a scope of `place` or `citation` alone; the Event → GEDCOM
sidecar is written only when `event` is in scope.

`--verify` and `--apply` are exclusive, and a flag outside the mode it
belongs to stops the run rather than being ignored: `--out` is dry-run only,
the three `--allow-*`/`--no-restore-point` overrides are `--apply` only, and
`--verify` takes none of `--only`, `--ged`, `--create`, `--adopt-by-name`.

The dry run runs the same preflight as `--apply`: a planned change the writer
would refuse is listed under WOULD REFUSE and the dry run exits 1.

A place the vault already holds is never overwritten. Where the export names
another place, on an Event's `place:` or a Person's `birth_place:` /
`death_place:`, the change is held as a `conflict` (or a `coarsen` when the
export names an ancestor) and listed in section 3. A PLAC that resolves to no
Place note is compared by its leaf against the Place's title and `aliases:`,
so adding the export's form to `aliases:` resolves a naming variant. A
disagreeing pair keyed positionally is usually paired wrong. No ruling can
write a place that does not resolve to a Place note.

A historical PLAC (`Breslau, Schlesien, ...`) links through Place aliases only
when `History/places-plan.json` approves that exact string (see
`/charted-roots:organize-places`), so it resolves PLACs the plugin's wizard
would not, and only on the Place the plan approves it for (a Place added later
that would outscore it gives no link); an unreadable plan turns alias matching
off for the run and prints a warning. An empty Person `birth_place:` /
`death_place:` / `burial_place:` is filled with a `[[Place]]` link once the
PLAC resolves.

Dates are written in two forms (`crsync/dates.py`). A Person's `born` /
`died` must pass the plugin's *Validate date formats* command, so `ABT` is
written `c. 1804`, a range `1850 to 1858`, and `BEF` / `AFT` is dropped to the
bare date -- the validator has no form for them. The Event keeps the
qualifier (`date: BEF 1909`), plus `date_precision`. German month names and
`D.M.YYYY` are read as dates. A respelling that changes nothing but the form
is a `format` change and is applied like `fill` and `refine`.
Relationships come from each family's `_FREL` / `_MREL` pedigree, and are
written only with `--create` (the pass also updates existing notes): birth ->
`father` / `mother` + `children`; step -> `stepfather` / `stepmother`;
adopted -> `adoptive_father` / `adoptive_mother`; guardian -> the plugin's
Guardian relationship, `guardian` on the ward and `ward` on each guardian, both
with parallel `_id` lists and both written (the plugin does not reciprocate
it). Foster and unknown pedigrees write nothing. A list the vault already
holds is extended, never trimmed or reordered.

`fix_person_dates.py` repairs Persons the export does not cover (dry run by
default; `--apply` needs Obsidian closed and People/Events clean in git).

Exit codes: 0 success; 1 a problem found (failed invariant, refused change,
regression, refused precondition); 2 the run could not start (bad flags,
missing vault, unreadable `data.json`, GEDCOM or decisions file).

Dry run is the default; nothing is written without `--apply`, which refuses
to run until Obsidian is closed, the entity folders are clean in git, and a
`pre-gedcom-sync-*` tag marks HEAD.

`--create` also writes notes for GEDCOM records with no vault counterpart.
Add it to a dry run first: section 7 previews every planned note — paths, the
first of each kind in full, the follow-up relationship and citation passes,
and everything the planner left for a human.

## gedcom_check

`gedcom_check.py` lists what to fix in a GEDCOM export before it is imported. It
needs no vault and never edits the `.ged`: it reads the file and prints findings.
Each names the person, the line in the file and a one-line fix to make in the
tree's host (`in Ancestry: ...`, from the HEAD `SOUR`).

    python3 <lib>/gedcom_check.py                       # FamilyTree.ged in the current directory
    python3 <lib>/gedcom_check.py --ged FILE            # another file
    python3 <lib>/gedcom_check.py --only dates,places   # some groups only
    python3 <lib>/gedcom_check.py --json                # all findings as JSON
    python3 <lib>/gedcom_check.py --out report.txt      # also write the report to a file

`--only` takes a comma-separated list of groups (`duplicates`, `marriages`,
`dates`, `places`). `--limit N` shows N findings per check in the text report
(default 20; 0 shows all); `--json` ignores it. Lines the parser skips appear as
`WARNING` lines in the report header.

| Check | Group | Kind | Rule |
|---|---|---|---|
| `dup-vital` | duplicates | fix / review | A person has two or more BIRT, DEAT, BURI or CREM; identical is a fix, differing a review |
| `dup-event-exact` | duplicates | fix | A repeatable fact (RESI, CENS, EVEN ...) recorded twice with the same date and place |
| `dup-marriage` | duplicates | fix / review | One family has two MARR; identical is a fix, differing a review |
| `dup-family` | duplicates | review | Two families for the same couple |
| `marriage-on-person` | marriages | fix / review | A marriage recorded on a person (MARR, or EVEN of type MARR) instead of the family |
| `date-unreadable` | dates | fix | A date that cannot be read |
| `date-invalid` | dates | fix | A date that is not a real calendar day |
| `date-nonstandard` | dates | fix | A date the importer reads but GEDCOM does not allow; the finding gives the standard form |
| `date-order` | dates | review | Dates that cannot be right: death before birth, burial before death, birth before a parent's, a lifespan over 120 years |
| `place-non-place` | places | fix | A PLAC that is a unit or rank, not a place |
| `place-format` | places | fix | Stray spaces or commas in a PLAC |
| `place-variant` | places | fix | One place written several ways (accents, case, spacing); names the most used |
| `place-hierarchy` | places | fix / review | A place that is a shorter form of another with the same leaf; one candidate is a fix, several a review |

Exit codes: 0 no findings; 1 findings; 2 the run could not start (bad flags,
missing or unreadable GEDCOM).

## places_plan

`places_plan.py` builds the Place notes behind historical PLAC strings; the
`organize-places` skill drives it. The reviewed plan is
`History/places-plan.json`: `places` (modern Places, keyed by plan key, with
`title`, `place_type`, `parent`, `aliases`, `reason`, `status` of `proposed` /
`approved` / `created`) and `plac` (each PLAC string with `count` and a `place`
key, or `not_place`, or `unidentified`; `status` `proposed` / `approved`).

    python3 <lib>/places_plan.py extract [--ged FILE]   # list PLAC strings into the plan
    python3 <lib>/places_plan.py check                  # validate; never writes
    python3 <lib>/places_plan.py apply                  # dry run
    python3 <lib>/places_plan.py apply --apply          # write approved places

Alias matching ignores diacritics (`ł`, `ß`), so an accent-only variant (`Wroclaw` for `Wrocław`) needs no alias; a different spelling (`Muenchen` for `München`) still does.

`extract` adds only strings not yet in the plan and refreshes counts; it never
drops a reviewed entry. `check` fails on a missing parent, a cycle, an invalid
`place_type`, a duplicate title under one parent (the last two skip entries recorded
from notes already in the vault), a Place that already exists,
or an approved PLAC that would not resolve to its own planned Place. `apply`
refuses a plan that fails `check`; with `--apply` it writes approved places
only, parents first, adds missing `aliases:` to an existing Place (nothing else
on it changes) and marks each handled place `created`. `--apply` has the same
preconditions as `gedcom_sync.py --apply` (Obsidian closed, entity folders
clean in git, a `pre-organize-places-*` tag on HEAD) and the same
before/after `vault_verify` comparison; `--no-restore-point`,
`--allow-obsidian-open` and `--allow-dirty` are `--apply` only, `--ged` is
`extract` only. Exit codes: 0 success; 1 a plan that fails `check`, a refused
precondition or a regression; 2 the run could not start (bad flags,
unreadable vault, plan or GEDCOM).

## Decisions

`coarsen` and `conflict` changes are held back: the vault value is more
precise, or the two genuinely differ, and applying the export would revert
curated work. Rulings that accept one anyway live in
`History/gedcom-sync-decisions.json`, one entry per person and occasion:

    {
      "external_id": "I100000000001",
      "label": "Johann Example",
      "accept_conflict": ["name", "surnames"],
      "reason": "The register spells it without the umlaut.",
      "decided_by": "user",
      "date": "2026-09-21"
    }

Keyed by the upstream INDI xref, so a rename cannot detach a ruling from the
person it was made about, and per field, because several of these people have
a second disagreement that must stay held. Every entry needs a `reason` — it
is the only record of why the vault's own value lost. With no file, nothing
is accepted. A malformed file stops the run rather than silently accepting
nothing, which would revert every ruling. The dry run reports how many held
changes the rulings still cover.

## Tests

    cd <lib> && python3 -m unittest discover -s tests -t .

Standard library `unittest`, no dependencies, about two seconds. Two of them
read the real vault: every note must survive a parse/render cycle
byte-for-byte, and no frontmatter line may be invisible to the key index.
They skip if the vault is not there, and never write.

`tests/test_vault_verify.py` runs the invariant CLI end to end;
`tests/test_cli.py` runs the dry run and `--apply` end to end
against a throwaway vault with its own git repository, which is what pins the
report's "N notes modified" to the count `git diff` actually shows.

The method for an actual sync — what to check, in what order, and what the
script refuses to do — is the `sync-gedcom` skill.

## How it matches

| Entity | Key | Quality |
|---|---|---|
| Person | `external_id` ↔ INDI xref | exact |
| Source | `gedcom_id` ↔ SOUR xref, or the `_Imported from GEDCOM source S…_` line in the body | exact |
| Event | `<owner>:<TAG>:<ordinal>`, bootstrapped by content then position | most Events key by content; the rest by position, and a handful are indistinguishable and assigned in order |
| Citation | `(subject_id, source, fact, page)` | exact |
| Place | the plugin's own `full_name` and `title\|parent` indexes | agrees with the plugin |

**INDI and SOUR xrefs are stable across re-exports**, which is what makes a
repeated import safe. **FAM xrefs are not** — they are positional integers
that hosted trees (Ancestry, observed) renumber when a family is inserted;
one insertion can renumber most of them. Nothing durable may key on a FAM
xref, so a shared event keys on its couple's two INDI xrefs instead.

`place` is deliberately not part of the Event key: upstream trees often
record historical and native forms (`Deutschland`, `Preußen`, `Danmark`)
against a gazetteer in another language, so many PLAC strings do not resolve
and keying on them would lose the match.

**No counts live in this file.** How many of each resolved, on which export,
and which decisions were left open are measurements, not method: they go in the run
record (`History/GEDCOM Reconciliation - Report.md` where the vault keeps
`History/`) with the date and the export's sha, and they are recomputed rather than trusted. A dry run prints the
current figures in a few seconds.

## Other exporters

Parsing targets Ancestry 5.5.1 exports; two MyHeritage habits are handled too.
A UTF-8 character cut at a `CONC` boundary is rejoined in memory (the file is
never rewritten), including after a bare text line, which MyHeritage writes
instead of `CONT`; the run warns with the line numbers. A `1 EVEN` whose
`2 TYPE` is `MARR` or `Hochzeit` is read as a marriage, `Taufe` as a baptism,
`Konfirmation` as a confirmation, `Verlobung` as an engagement and `Military
Service` as military, so an individual marriage folds into the family marriage
it repeats. Other labels are set aside and listed in the report.

A marriage written on a person rather than the family is listed in the
report's section 8, FIX UPSTREAM, with the host the header names and the fix to
make there: a duplicate of the family marriage is deleted from the person; one
only on the person moves onto the family with that spouse (or the spouse is
added first). The plugin's own import drops both; the sync keeps the
person-only one as a person-level Event until the host is fixed.

GEDCOM tags map to `event_type` exactly as the Charted Roots importer maps them
(`crsync/gedcom.py` `TAG_TO_EVENT`, pinned by a test): `CHR` is `christening`,
`BAPM` is `baptism`, `CONF` is `confirmation`, `ENGA` is `engagement`, and so on.
`_MILT` (Ancestry's military fact, which the importer drops) is `military`.
Bare text lines themselves are still skipped and counted in a warning.

## Layout

    <lib>/gedcom_sync.py      sync CLI
    <lib>/vault_verify.py     invariant CLI (also gedcom_sync.py --verify)
    <lib>/places_plan.py      places plan CLI (extract, check, apply)
    <lib>/fix_person_dates.py one-off: born/died into validator-clean forms
    <lib>/crsync/vault.py     frontmatter reader/writer (line-preserving)
    <lib>/crsync/config.py    folder layout, read from data.json
    <lib>/crsync/gedcom.py    GEDCOM parser, incl. EVEN and OBJE
    <lib>/crsync/dates.py     date forms, and a port of the plugin's date validator
    <lib>/crsync/places.py    the plugin's place cache semantics
    <lib>/crsync/placeplan.py the places plan: extract, check, apply
    <lib>/crsync/match.py     Person and Source joins
    <lib>/crsync/events.py    the Event key cascade
    <lib>/crsync/citations.py Citation join
    <lib>/crsync/verify.py    the invariant suite
    <lib>/crsync/report.py    the dry-run report and the --apply log
    <lib>/crsync/apply.py     the write layer, and its preconditions
    <lib>/crsync/create.py    new notes for records with no counterpart
    <lib>/crsync/decisions.py the accepted-ruling file and its validation
    <lib>/tests/              unittest suite

The writer is a **line patcher**, never a serialiser: it replaces only the
lines of the keys it changes, so every other byte of a note is untouched and
a run produces a reviewable diff. Round-trip is byte-identical across
every note in the vault -- asserted by `tests/test_vault.py`, which
reads them all, rather than claimed by a number here that goes stale
as the vault grows.
