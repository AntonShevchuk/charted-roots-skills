# validate-gedcom Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A standalone, vault-free GEDCOM checker (`gedcom_check.py` + `crsync/gedcheck.py`) that lists every problem in an export as a fix to make in the host tree, plus a `validate-gedcom` skill that presents those fixes.

**Architecture:** `crsync/gedcom.py` gains source line numbers and the raw PLAC on each event; `crsync/dates.py` gains `classify` and `bounds`. `crsync/gedcheck.py` runs pure checks over a parsed `gedcom.Tree` and returns `Finding`s; it absorbs `report.upstream_marriage_fixes` and `report.host_name`. `lib/gedcom_check.py` is the CLI. The sync report keeps only counts and a pointer.

**Tech Stack:** Python 3.10+ standard library, `unittest`; skill prose in Markdown.

**Spec:** `docs/superpowers/specs/2026-11-18-validate-gedcom-design.md`

## Global Constraints

- Standard library only; code in `plugins/charted-roots/lib/`; tests run from `lib/` with `python3 -m unittest discover -s tests -t .`.
- GEDCOM fixtures via `tests/helpers.ged(text)`; fictional names only (`Anna Muster`, `Karl Beispiel`, …).
- Parsing stays in `crsync/gedcom.py`; date reading in `crsync/dates.py`; place normalisation via `places.key` / `places.fold`. No re-implementation.
- The `.ged` is never written. `gedcom_check.py` writes nothing except `--out`.
- Every finding has a one-line `fix` starting `in <host>: `.
- No text added to `skills/verify-vault/references/charted-roots-model.md`.
- Skill name `validate-gedcom`; never sends data externally.
- Exit codes: 0 no findings; 1 findings; 2 could not start.

## Review Focus

1. An export that writes months in mixed case (`25 Dec 1914`, `Abt 1804`) yields no date findings — test in Task 2.
2. Repeatable facts (three RESI with different dates; two CENS in one year at different places) yield no duplicate finding — test in Task 3.
3. One leaf under unrelated parents (`Springfield, Illinois` / `Springfield, Ohio`) yields no hierarchy finding — test in Task 5.
4. A file with unparseable lines still runs: warnings appear in the header, exit is not 2 — test in Task 6.
5. An undecodable file exits 2 with a one-line message, no traceback — test in Task 6.

---

### Task 1: Line numbers, raw PLAC and FILE in the parser

**Files:**
- Modify: `plugins/charted-roots/lib/crsync/gedcom.py` (`Node`, `Event`, `Individual`, `Family`, `MediaObj`, `_tree`, `_read_event`, `parse`)
- Test: `plugins/charted-roots/lib/tests/test_gedcom.py` (new class `SourceLines`)

**Interfaces:**
- Produces: `Node.line: int`, `Event.line: int`, `Event.place_raw: str`, `Individual.line: int`, `Family.line: int`, `MediaObj.file: str` (the `1 FILE` value, stripped; `""` if absent). All default `0` / `""`.

- [ ] **Step 1: Write the failing tests**

```python
class SourceLines(unittest.TestCase):
    def test_events_and_records_carry_their_line(self):
        tree = gedcom.parse(ged(SMALL), warn=lambda m: None)
        ind = tree.individuals["I1"]
        self.assertEqual(ind.line, 8)                    # "0 @I1@ INDI"
        birt = next(e for e in ind.events if e.tag == "BIRT")
        self.assertEqual(birt.line, 17)                  # "1 BIRT"
        self.assertEqual(tree.families["F1"].line, 50)

    def test_place_raw_survives_marriage_folding(self):
        # INDI MARR with a place folds into a FAM MARR without one;
        # the FAM event gets .place but keeps place_raw == "".
        ...
        self.assertEqual(fam_ev.place, "Musterdorf")
        self.assertEqual(fam_ev.place_raw, "")
        self.assertEqual(ind_ev.place_raw, "Musterdorf")

    def test_media_file(self):
        # "0 @O1@ OBJE / 1 FILE" → file == ""; "1 FILE a.jpg" → "a.jpg"
```

Line numbers count every physical line, including CONT/CONC and blank ones (they are what an editor shows).

- [ ] **Step 2: Run** `python3 -m unittest tests.test_gedcom.SourceLines` — expect FAIL (`AttributeError: line`).
- [ ] **Step 3: Implement.** `_tree` passes `number` into `Node(line=number)`; `_read_event` sets `ev.line = node.line` and `ev.place_raw = ev.place`; INDI/FAM records copy `rec.line`; OBJE sets `obj.file = (fil.value.strip() if fil else "")`.
- [ ] **Step 4: Run the whole suite** — expect all PASS.
- [ ] **Step 5: Commit** `git commit -m "Record source lines and raw PLAC on parsed GEDCOM events"`

---

### Task 2: `dates.classify` and `dates.bounds`

**Files:**
- Modify: `plugins/charted-roots/lib/crsync/dates.py`
- Test: `plugins/charted-roots/lib/tests/test_dates.py` (new classes `Classify`, `Bounds`)

**Interfaces:**
- Produces: `classify(raw: str) -> tuple[str, str]` — `(label, suggestion)`, label one of `"empty"`, `"standard"`, `"standard-unparsed"`, `"lenient"`, `"invalid"`, `"unreadable"`; `suggestion` is the GEDCOM 5.5.1 form for `"lenient"`, else `""`.
- Produces: `bounds(raw: str) -> tuple[str | None, str | None]` — earliest and latest ISO day (`YYYY-MM-DD`) the date can mean; `(None, None)` when it does not read.

Label rules (case is ignored throughout; letter case alone never makes a date `lenient`):
- `standard`: GEDCOM 5.5.1 grammar *and* `from_gedcom` reads it — `[D] [MON] YYYY` with English 3-letter months; `ABT|CAL|EST|BEF|AFT <date>`; `BET <date> AND <date>`; `FROM <date> TO <date>`.
- `standard-unparsed`: valid grammar that `from_gedcom` returns as `unknown` — `FROM <date>` / `TO <date>` alone, `INT <date> (<text>)`, `(<text>)`, a leading `@#D…@` calendar escape, a dual year `YYYY/YY`, a `B.C.` suffix.
- `invalid`: reads, but a day/month is not on the calendar (`datetime.date` raises) — `31 FEB 1850`, `1850-13-05`.
- `lenient`: reads through any other path — German months, `D.M.YYYY`, ISO, `c.`/`ca.`/`circa`/`~`/`About`/`Before`/`After`, dotted keywords (`Abt.`, `BET.`), full or dotted month names (`December`, `Dec.`), `YYYY-YYYY`.
- `unreadable`: everything else, including a `BET`/`FROM…TO` with an unreadable side.

Suggestion: rebuild from the raw tokens, each date part keeping its own precision (`25 DEC 1914`, `DEC 1914`, `1914`); qualifiers map `about/circa/cir/ca./c./~ → ABT`, `before → BEF`, `after → AFT`, dotted `CAL./EST./BET.` lose the dot; `YYYY-YYYY → BET YYYY AND YYYY`.

Bounds: year → Jan 1..Dec 31; month → 1st..last day; `ABT x` → x's year −10 .. +10; `BEF x` → (None, x.hi); `AFT x` → (x.lo, None); range → (a.lo, b.hi).

- [ ] **Step 1: Write the failing tests**

```python
class Classify(unittest.TestCase):
    def test_labels(self):
        cases = {
            "": ("empty", ""),
            "25 DEC 1914": ("standard", ""),
            "25 Dec 1914": ("standard", ""),          # case alone is fine
            "Abt 1804": ("standard", ""),
            "BET 1850 AND 1858": ("standard", ""),
            "FROM 1850": ("standard-unparsed", ""),
            "INT 1850 (from age)": ("standard-unparsed", ""),
            "(about the war)": ("standard-unparsed", ""),
            "@#DJULIAN@ 1 JAN 1700": ("standard-unparsed", ""),
            "1750/51": ("standard-unparsed", ""),
            "31 FEB 1850": ("invalid", ""),
            "25 Dez 1914": ("lenient", "25 DEC 1914"),
            "1.6.1824": ("lenient", "1 JUN 1824"),
            "1914-12-25": ("lenient", "25 DEC 1914"),
            "c. 1804": ("lenient", "ABT 1804"),
            "Abt. 1804": ("lenient", "ABT 1804"),
            "December 1914": ("lenient", "DEC 1914"),
            "BET. 1 Jan 1850 AND 1858": ("lenient", "BET 1 JAN 1850 AND 1858"),
            "1850-1858": ("lenient", "BET 1850 AND 1858"),
            "25 Foo 1914": ("unreadable", ""),
            "BET 1850 AND sometime": ("unreadable", ""),
        }
        for raw, want in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(dates.classify(raw), want)

class Bounds(unittest.TestCase):
    def test_bounds(self):
        self.assertEqual(dates.bounds("1850"), ("1850-01-01", "1850-12-31"))
        self.assertEqual(dates.bounds("FEB 1852"), ("1852-02-01", "1852-02-29"))
        self.assertEqual(dates.bounds("ABT 1850"), ("1840-01-01", "1860-12-31"))
        self.assertEqual(dates.bounds("BEF 1900"), (None, "1900-12-31"))
        self.assertEqual(dates.bounds("AFT 3 MAR 1900"), ("1900-03-03", None))
        self.assertEqual(dates.bounds("BET 1850 AND 1858"), ("1850-01-01", "1858-12-31"))
        self.assertEqual(dates.bounds("nonsense"), (None, None))
```

- [ ] **Step 2: Run** `python3 -m unittest tests.test_dates` — expect FAIL (`no attribute 'classify'`).
- [ ] **Step 3: Implement** `classify` and `bounds` in `crsync/dates.py`, reusing `single`, `_strip_prefix`, `MONTHS` and `from_gedcom`.
- [ ] **Step 4: Run the whole suite** — expect all PASS.
- [ ] **Step 5: Commit** `git commit -m "Classify GEDCOM dates as standard, lenient or unreadable"`

---

### Task 3: `gedcheck` core — Finding, run, duplicates, marriages

**Files:**
- Create: `plugins/charted-roots/lib/crsync/gedcheck.py`
- Modify: `plugins/charted-roots/lib/crsync/report.py` (move `host_name`, `_person`, `_spouses`, `upstream_marriage_fixes` out; `report` imports `gedcheck.host_name`)
- Test: `plugins/charted-roots/lib/tests/test_gedcheck.py` (classes `Duplicates`, `Marriages`, `Run`)

**Interfaces:**
- Consumes: Task 1 fields.
- Produces:

```python
GROUPS = ["duplicates", "marriages", "dates", "places"]   # also the report order
CHECKS = {"dup-vital": "duplicates", "dup-event-exact": "duplicates",
          "dup-marriage": "duplicates", "dup-family": "duplicates",
          "marriage-on-person": "marriages",
          "date-unreadable": "dates", "date-invalid": "dates",
          "date-nonstandard": "dates", "date-order": "dates",
          "place-non-place": "places", "place-format": "places",
          "place-variant": "places", "place-hierarchy": "places"}

@dataclass
class Finding:
    check: str; group: str; kind: str   # kind: "fix" | "review"
    who: str; line: int; what: str; fix: str

def host_name(tree) -> str                     # moved verbatim from report
def run(tree, only: set[str] | None = None) -> list[Finding]   # ordered by GROUPS, then line
def parse_only(value: str) -> set[str] | None  # ValueError on an unknown group
```

`who`: INDI → `"Anna Muster (@I1@)"`; FAM → `"Karl Beispiel & Anna Muster (@F1@)"`; places (Task 5) → up to three people then `"and N more"`.

Rules (from the spec):
- `dup-vital`: >1 of BIRT/DEAT/BURI/CREM on one INDI. All share `(date, places.key(place_raw))` → `fix` "delete the duplicate"; else `review`, `what` lists each `date at place`. `line` = the second occurrence.
- `dup-event-exact`: any other tag except MARR, on one owner, repeated with equal non-empty `date_raw` (stripped) and equal non-empty `places.key(place_raw)` → `fix`.
- `dup-marriage`: a FAM with >1 MARR: all pairs `gedcom._same_date` → `fix`; else `review`.
- `dup-family`: two FAMs with the same non-empty two-person `couple` → `review` "merge the two families".
- `marriage-on-person`: the `upstream_marriage_fixes` logic, same `what` / `fix` wording; `tree.folded` → `fix`, `tree.person_marriages` → `review`.

- [ ] **Step 1: Write the failing tests** (GEDCOM in the test module; Ancestry header so the host is `Ancestry`)

```python
class Duplicates(unittest.TestCase):
    def test_identical_births_are_a_fix(self):
        f = only(check(TWO_SAME_BIRTHS), "dup-vital")
        self.assertEqual((f.kind, f.who), ("fix", "Anna Muster (@I1@)"))
        self.assertTrue(f.fix.startswith("in Ancestry: "))
    def test_conflicting_births_are_a_review(self):
        f = only(check(TWO_DIFFERENT_BIRTHS), "dup-vital")
        self.assertEqual(f.kind, "review")
        self.assertIn("1 JUN 1824", f.what); self.assertIn("1825", f.what)
    def test_repeatable_facts_are_not_duplicates(self):       # Review Focus 2
        self.assertEqual(check(THREE_RESI_TWO_CENS), [])
    def test_exact_repeat_of_a_fact(self):
        self.assertEqual(only(check(TWO_SAME_RESI), "dup-event-exact").kind, "fix")
    def test_two_marriages_in_one_family(self): ...          # same date → fix; different → review
    def test_two_families_for_one_couple(self):
        self.assertEqual(only(check(TWO_FAMS), "dup-family").kind, "review")
    def test_even_type_marr_counts_as_marr(self): ...         # 1 EVEN/2 TYPE MARR + FAM MARR same date → marriage-on-person only, no dup-marriage

class Marriages(unittest.TestCase):
    def test_same_findings_as_the_old_section_8(self):
        # Port PERSON_MARRIAGES from tests/test_cli.py and its assertions:
        # "in MyHeritage", "delete the person-level marriage", "Anna Meyer (@I2@)",
        # "no family", "add the spouse".

class Run(unittest.TestCase):
    def test_only_filters_by_group(self): ...
    def test_unknown_group_raises(self):
        with self.assertRaises(ValueError): gedcheck.parse_only("dupes")
```

(`check(text)` = `gedcheck.run(gedcom.parse(ged(text), warn=lambda m: None))`; `only(findings, check)` asserts exactly one finding of that check and returns it.)

- [ ] **Step 2: Run** `python3 -m unittest tests.test_gedcheck` — expect FAIL (`No module named crsync.gedcheck`).
- [ ] **Step 3: Implement** `crsync/gedcheck.py` with the dup and marriage checks; `run` skips groups not in `only`; move the helpers out of `report.py` and import `host_name` back there (section 8 still calls the marriage logic until Task 7 — keep it working by having report call `gedcheck.run(tree, {"marriages"})` and printing `who` / `what` / `fix`).
- [ ] **Step 4: Run the whole suite** — expect all PASS, including the existing `test_cli.PersonMarriages`.
- [ ] **Step 5: Commit** `git commit -m "Add gedcheck: duplicate and person-level marriage findings"`

---

### Task 4: Date checks

**Files:**
- Modify: `plugins/charted-roots/lib/crsync/gedcheck.py`
- Test: `plugins/charted-roots/lib/tests/test_gedcheck.py` (class `Dates`)

**Interfaces:**
- Consumes: `dates.classify`, `dates.bounds` (Task 2); `Finding` (Task 3).

Events checked: every INDI and FAM event **plus** each `ev` in `tree.suppressed`.
- `classify` → `unreadable` = `date-unreadable` (`fix`: "rewrite as D MMM YYYY (or ABT / BEF / AFT / BET … AND …)"); `invalid` = `date-invalid` (`fix`); `lenient` = `date-nonstandard` (`fix`: `in <host>: write "<raw>" as "<suggestion>"`); `empty` / `standard` / `standard-unparsed` = nothing.
- `date-order` (`review`), on each INDI's first BIRT / DEAT / BURI|CREM, comparing `bounds`; a rule fires only when both sides have the needed bound and `later.hi < earlier.lo`:
  death before birth; burial/cremation before death; child's birth before a **birth** parent's birth (`Family.relation(child, "HUSB"/"WIFE") == "birth"`); lifespan: `death.lo` year − `birth.hi` year > 120.

- [ ] **Step 1: Write the failing tests**

```python
class Dates(unittest.TestCase):
    def test_each_label_maps_to_its_check(self):
        fs = check(DATES)          # one event each: "25 Foo 1914", "31 FEB 1850", "25 Dez 1914", "FROM 1850"
        self.assertEqual(sorted(f.check for f in fs),
                         ["date-invalid", "date-nonstandard", "date-unreadable"])
        self.assertIn('"25 DEC 1914"', only(fs, "date-nonstandard").fix)
    def test_suppressed_even_dates_are_checked(self): ...    # 1 EVEN / 2 TYPE Obituary / 2 DATE 25 Dez 1914 → date-nonstandard
    def test_death_before_birth(self): ...
    def test_burial_before_death(self): ...
    def test_child_born_before_parent(self): ...
    def test_step_child_older_than_step_parent_is_fine(self): ...   # _FREL Step
    def test_lifespan_over_120(self): ...
    def test_about_dates_do_not_false_positive(self):
        self.assertEqual(check(BIRT_ABT_1850_DEAT_1845), [])
```

- [ ] **Step 2: Run** `python3 -m unittest tests.test_gedcheck.Dates` — expect FAIL.
- [ ] **Step 3: Implement** the two date checks in `gedcheck.py`.
- [ ] **Step 4: Run the whole suite** — expect all PASS.
- [ ] **Step 5: Commit** `git commit -m "gedcheck: unreadable, invalid, non-standard and out-of-order dates"`

---

### Task 5: Place checks

**Files:**
- Modify: `plugins/charted-roots/lib/crsync/gedcheck.py`
- Test: `plugins/charted-roots/lib/tests/test_gedcheck.py` (class `Places`)

**Interfaces:**
- Consumes: `gedcom.non_place_reason`, `places.fold`, `Event.place_raw`.

Input: the distinct non-empty `place_raw` strings over the same events as Task 4, each with its count and the people using it. One finding per **string** (or per group), never per event; `what` quotes the PLAC and its count.
- `place-non-place`: `non_place_reason(raw)` → `fix` "move the unit / rank into the description; set PLAC to the place".
- `place-format`: leading/trailing space, a doubled space, a space before a comma, an empty component, a trailing comma → `fix` `write "<raw>" as "<cleaned>"` (parts stripped, collapsed, empties dropped, joined with `", "`). A missing space after a comma alone is not reported.
- `place-variant`: group the *cleaned* strings by `places.fold`; a group with ≥2 distinct cleaned strings → `fix` "use one spelling; most used: X (n)" (tie → alphabetical first).
- `place-hierarchy`: on one representative per fold group (most used), split on `", "`; leaf = first part, chain = the rest (compared folded). For each string A, fuller = strings with the same leaf whose chain has A's chain as a strict, ordered, not-necessarily-contiguous subsequence. A with a non-empty chain and ≥1 fuller → `review` "standardise to the fuller form: …". A with an empty chain: exactly 1 fuller → `fix` "use <fuller>"; ≥2 → `review` "which one is meant: A, B?"; 0 → nothing.

- [ ] **Step 1: Write the failing tests**

```python
class Places(unittest.TestCase):
    def test_non_place(self): ...                 # "Infanterie-Regiment 51" → fix
    def test_format(self):
        f = only(check(PLAC("Berlin ,  Preußen,")), "place-format")
        self.assertIn('"Berlin, Preußen"', f.fix)
    def test_no_space_after_comma_alone_is_fine(self): ...
    def test_variant_case_and_accents(self):
        f = only(check(PLACS("Wrocław, Polska", "Wroclaw, Polska", "wrocław, polska")), "place-variant")
        self.assertIn("Wrocław, Polska", f.fix)
    def test_hierarchy_fuller_form(self):         # "Berlin, Germany" + "Berlin, Brandenburg, Germany" → review
    def test_bare_leaf_one_fuller_is_a_fix(self):
    def test_bare_leaf_two_fuller_is_a_review(self):
    def test_unrelated_parents_are_fine(self):    # Review Focus 3
        self.assertEqual(check(PLACS("Springfield, Illinois", "Springfield, Ohio")), [])
    def test_folded_marriage_place_counted_once(self): ...
    def test_who_lists_three_then_and_more(self): ...
```

- [ ] **Step 2: Run** `python3 -m unittest tests.test_gedcheck.Places` — expect FAIL.
- [ ] **Step 3: Implement** the four place checks in `gedcheck.py`.
- [ ] **Step 4: Run the whole suite** — expect all PASS.
- [ ] **Step 5: Commit** `git commit -m "gedcheck: non-place, format, variant and hierarchy place findings"`

---

### Task 6: `gedcom_check.py` CLI and README

**Files:**
- Create: `plugins/charted-roots/lib/gedcom_check.py`
- Modify: `plugins/charted-roots/lib/README.md` (new `## gedcom_check` section after `gedcom_sync`'s usage)
- Test: `plugins/charted-roots/lib/tests/test_gedcom_check_cli.py`

**Interfaces:**
- Consumes: `gedcheck.run`, `gedcheck.parse_only`, `gedcheck.host_name`, `gedcheck.GROUPS`, `report.sha256`, `gedcom.parse`.
- Produces: `main(argv: list[str] | None = None) -> int`.

Flags: `--ged` (default `FamilyTree.ged`, relative to cwd), `--only` (groups), `--json`, `--out FILE`, `--limit N` (default 20; 0 = all; per check; text only).
Text: header (path, size, sha256, host, HEAD export date, each `tree.warnings` line as `WARNING …`), a summary table (count per check, grouped, with fix/review split), then per check its findings as `who  line N` / `what` / `fix`. JSON: `{"ged", "host", "exported", "sha256", "warnings", "findings": [asdict(f)]}`, `ensure_ascii=False`, no limit. `--out` writes what was printed. Missing file → `No GEDCOM at <path>` on stderr, 2; `OSError`/`UnicodeDecodeError` → `GEDCOM unreadable: <exc>` on stderr, 2; bad `--only` → message, 2. Parse with `warn=lambda m: None` (warnings go into the header instead of stderr).

- [ ] **Step 1: Write the failing tests** (call `gedcom_check.main([...])` with redirected stdout/stderr, as `test_places_plan_cli.CliCase.run_cli` does)

```python
def test_clean_file_exits_0(self): ...
def test_findings_exit_1_and_are_listed(self): ...     # "dup-vital", "in Ancestry:"
def test_json_is_complete_and_parseable(self):
    data = json.loads(out); self.assertEqual(data["host"], "Ancestry")
    self.assertEqual({"check","group","kind","who","line","what","fix"}, set(data["findings"][0]))
def test_limit_zero_shows_all(self): ...
def test_only_unknown_group_exits_2(self): ...
def test_missing_file_exits_2(self): ...
def test_undecodable_file_exits_2_without_traceback(self):   # Review Focus 5: write b"0 HEAD\n1 NAME \xff\xfe\n"
    self.assertEqual(code, 2); self.assertIn("GEDCOM unreadable", err); self.assertNotIn("Traceback", err)
def test_skipped_lines_warn_in_header(self):                  # Review Focus 4
    self.assertNotEqual(code, 2); self.assertIn("WARNING", out); self.assertIn("skipped 1 line", out)
def test_out_writes_the_report(self): ...
def test_writes_nothing_else(self): ...                       # directory listing unchanged
```

- [ ] **Step 2: Run** `python3 -m unittest tests.test_gedcom_check_cli` — expect FAIL (`No module named gedcom_check`).
- [ ] **Step 3: Implement** `gedcom_check.py` (module docstring in the style of `gedcom_sync.py`: purpose, usage, exit codes).
- [ ] **Step 4: Run the whole suite** — expect all PASS.
- [ ] **Step 5: Write the README section**: usage, flags, the check table (check, group, fix/review, one-line rule), exit codes, "never edits the `.ged`".
- [ ] **Step 6: Commit** `git commit -m "Add gedcom_check.py: list GEDCOM fixes without a vault"`

---

### Task 7: Sync report keeps counts and a pointer

**Files:**
- Modify: `plugins/charted-roots/lib/crsync/report.py` (section 0 non-place detail, section 6 media, section 8)
- Modify: `plugins/charted-roots/lib/README.md` (mention that the fix list lives in `gedcom_check.py`)
- Test: `plugins/charted-roots/lib/tests/test_cli.py` (`PersonMarriages`, plus new tests)

**Interfaces:**
- Consumes: `gedcheck.run`, `gedcheck.GROUPS`.

- Section 8 becomes `-- 8. GEDCOM CHECK (fix in <host>) ---…`: one line per group with its count (`duplicates`, `marriages`, `dates`, `places`), then `run gedcom_check.py --ged <path> for the fix list`. Computed from `gedcheck.run(tree)` (no `only`), shown whatever `--only` is; omitted when there are no findings.
- Section 0 non-place line keeps its count; the detail lines are replaced by `        details: gedcom_check.py --only places`.
- Section 6: `{n} records, {e} with an empty `1 FILE` (not importable).` Drop the Ancestry-specific sentences.

- [ ] **Step 1: Update/write the failing tests**

```python
class PersonMarriages(CliCase):
    def test_report_counts_and_points_to_gedcom_check(self):
        section = out[out.index("GEDCOM CHECK"):]
        self.assertIn("in MyHeritage", section)
        self.assertRegex(section, r"marriages\s+2")
        self.assertIn("gedcom_check.py", section)
        self.assertNotIn("delete the person-level marriage", out)
    def test_section_shows_under_only(self): ...      # --only source still shows it
    def test_a_clean_tree_has_no_such_section(self):  # keep, assert "GEDCOM CHECK" absent
class Media(CliCase):
    def test_counts_empty_file_records(self): ...    # one empty FILE, one "1 FILE a.jpg" → "2 records, 1 with an empty"
```

- [ ] **Step 2: Run** `python3 -m unittest tests.test_cli` — expect the new tests to FAIL.
- [ ] **Step 3: Implement** the three report changes; delete the now-unused marriage rendering.
- [ ] **Step 4: Run the whole suite** — expect all PASS.
- [ ] **Step 5: Commit** `git commit -m "Sync report: count GEDCOM findings and point to gedcom_check"`

---

### Task 8: `validate-gedcom` skill, docs, version

**Files:**
- Create: `plugins/charted-roots/skills/validate-gedcom/SKILL.md`
- Modify: `plugins/charted-roots/skills/sync-gedcom/SKILL.md` (step 2's "Section 8, FIX UPSTREAM" bullet)
- Modify: `CLAUDE.md` (CLI list and users of `lib/`)
- Modify: `plugins/charted-roots/.claude-plugin/plugin.json` (`version` `0.5.3` → `0.6.0`; add `validate-gedcom` to `description`)
- Modify: `.claude-plugin/marketplace.json` (`description`: mention checking GEDCOM exports)

SKILL.md content (frontmatter `name: validate-gedcom`; `description:` "Use when a GEDCOM export arrives, before sync-gedcom, or when asked to check, validate or lint a .ged file. Lists duplicate events, bad dates and inconsistent place names as fixes to make in the host tree (Ancestry, MyHeritage, …); never edits the file."):
- `<lib>` = `${CLAUDE_SKILL_DIR}/../../lib`; run `python3 <lib>/gedcom_check.py --ged <file> --json`; no vault needed. Exit 2 = did not run; say why.
- Present: header line (file, host, export date, warnings); then **Fixes** as a table per person — person (name + xref as the `.ged` holds it), line, what is wrong, the fix in <host>; then **Your decisions** (`review` findings) with one line on why each needs the user; then **Places** as their own table (PLAC, count, fix). Summarise counts first if there are more than ~40 findings and offer the full list.
- Never edit the `.ged`; changes are made in the host, then re-export and re-run. Never send findings externally (living people). Offer to save the fix list to a file the user names.
- Point to `<lib>/README.md` for the check list.

sync-gedcom step 2: replace the FIX UPSTREAM bullet with: "**Section 8, GEDCOM CHECK** — counts only. Run the `validate-gedcom` skill (ideally before the sync) for the fix list."

- [ ] **Step 1: Write the skill and the edits above.**
- [ ] **Step 2: Verify**: run `python3 plugins/charted-roots/lib/gedcom_check.py --ged <a test fixture written to the scratchpad> --json` from the repo root and confirm the JSON shape the skill describes; run the whole suite from `lib/` — all PASS; `python3 -m json.tool` on both edited JSON files succeeds.
- [ ] **Step 3: Commit** `git commit -m "Add the validate-gedcom skill"`
