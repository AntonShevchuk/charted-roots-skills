"""Render what a run has to say, both halves of it.

Decisions a human must make come first, because a report that buries them on
page four does not get read. Every count is recomputed, never carried over.

`render` returns the whole dry run as one string. `ApplyLog` emits `--apply`
line by line, because that half writes as it goes and a crash in the middle
must still leave a record of which passes had already run. Both live here so
the two paths cannot end up describing the same run differently.
"""

from __future__ import annotations

import collections
import hashlib
import os
import sys
from dataclasses import dataclass, field

from . import apply as apply_mod
from . import events
from . import gedcom
from . import match
from . import vault

BAR = "=" * 78


@dataclass
class CreationPreview:
    """What `--create` would write, so it can be read before it is written.

    Creation is the largest and least reversible half of a sync -- hundreds of
    new notes plus a both-sides relationship rewrite -- so it needs the same
    dry run as everything else. Without this the only way to see the plan was
    to execute it.
    """

    plan: object
    rel_changes: dict = field(default_factory=dict)
    migrations: list = field(default_factory=list)
    #: Paths whose `citations:` would be recomputed, from a dry rebuild.
    relisted: list = field(default_factory=list)


def _frontmatter_lines(new, indent: str) -> list:
    """A planned note's frontmatter, for the preview. Bodies are templated.

    Quoted exactly as `NewNote.text()` would write it, so the preview shows
    the bytes that would land rather than the planner's raw values -- an
    unquoted `[[...]]` in frontmatter is invalid YAML, and a preview that
    showed one would send the reader hunting for a bug that is not there.
    """
    out = []
    for key, value in new.fm.items():
        if isinstance(value, list):
            out.append(f"{indent}{key}:")
            out.extend(f"{indent}  - {vault.quote(str(v))}" for v in value)
        else:
            out.append(f"{indent}{key}: {vault.quote(str(value))}")
    return out


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _histogram(counter, indent="      ") -> list:
    out = []
    for k, v in counter.most_common():
        out.append(f"{indent}{v:5}  {k}")
    return out


def render(cfg, tree, ged_path, person_plan, source_plan, event_match,
           citation_match, place_index, obsidian_running, limit=10,
           decisions=None, creation=None, only=None, blocked=None) -> str:
    L: list = []
    a = L.append

    def want(entity: str) -> bool:
        """Whether `--only` leaves this entity type in scope."""
        return only is None or entity in only

    a(BAR)
    a("GEDCOM RECONCILIATION -- dry run (nothing is written without --apply)")
    a(BAR)
    a(f"  ged    {os.path.relpath(ged_path, cfg.root)}  "
      f"{os.path.getsize(ged_path):,} bytes  sha256 {sha256(ged_path)}")
    a(f"         {tree.header.get('source','?')} {tree.header.get('version','?')}, "
      f"exported {tree.header.get('date','?')}")
    a(f"  vault  {cfg.root}")
    if obsidian_running is None:
        obsidian = "cannot tell -- apply would refuse"
    elif obsidian_running:
        obsidian = "RUNNING -- apply would refuse"
    else:
        obsidian = "closed"
    a(f"  plugin bidirectional sync: {'ON' if cfg.bidirectional_sync else 'off'}"
      f"   Obsidian: {obsidian}")
    if only is not None:
        a(f"  scope  --only {', '.join(sorted(only))}"
          f"   -- this report is partial by request")
    a("")

    # -- 0. decisions -------------------------------------------------
    a("-- 0. DECISIONS REQUIRED " + "-" * 53)
    if want("person"):
        candidates = person_plan.of("person", "candidate")
        a(f"  Person notes that already exist under another identity   "
          f"{len(candidates):5}")
        for act in candidates[:limit]:
            a(f"        {act.label}")
            a(f"            {act.path}")
            a(f"            {act.note}")
        if len(candidates) > limit:
            a(f"        ... and {len(candidates) - limit} more")
    if want("place"):
        a(f"  Places invisible to the plugin's matcher                 "
          f"{len(place_index.invisible):5}")
        for note, why in place_index.invisible:
            a(f"        {note.basename:42} {why}")
    if want("citation"):
        a(f"  Citation duplicates already in the vault                 "
          f"{len(citation_match.duplicates):5}  (reported, never deleted)")
    if want("place"):
        nonplace = [(e, gedcom.non_place_reason(e.place))
                    for e in tree.events if e.place]
        nonplace = [(e, why) for e, why in nonplace if why]
        a(f"  Non-place values in a GEDCOM PLAC line                   "
          f"{len(nonplace):5}")
        if nonplace:
            a("        A rank, unit or recruiting office in PLAC. The vault model: a")
            a("        non-place in a place: field means the event needs fixing")
            a("        first -- so these are reported, never written as a place.")
            for e, why in nonplace[:limit]:
                a(f"        [{why}] {e.owner}  {e.place[:52]}")
    a("")

    # -- 1. people ----------------------------------------------------
    if want("person"):
        pc = person_plan.counts("person")
        a("-- 1. PERSON " + "-" * 65)
        a(f"  ged {len(tree.individuals)}   vault notes indexed by external_id "
          f"{pc.get('match',0) + pc.get('update',0)}")
        a(f"      matched, unchanged      {pc.get('match', 0):5}")
        a(f"      matched, would update   {pc.get('update', 0):5}")
        a(f"      candidate adoption      {pc.get('candidate', 0):5}   -> section 0")
        a(f"      would create            {pc.get('create', 0):5}")
        a(f"      orphaned (vault only)   {pc.get('orphan', 0):5}   never deleted")
        a(f"      ambiguous               {pc.get('ambiguous', 0):5}")
        by_class = collections.Counter()
        by_field = collections.Counter()
        for act in person_plan.of("person", "update"):
            for ch in act.changes:
                by_class[ch.kind] += 1
                by_field[f"{ch.field} [{ch.kind}]"] += 1
        if by_class:
            a("")
            a("  field changes by class")
            a(f"      fill     {by_class.get('fill', 0):5}  vault empty -- safe")
            a(f"      refine   {by_class.get('refine', 0):5}  GEDCOM more precise -- safe")
            a(f"      format   {by_class.get('format', 0):5}  same date, respelt for the plugin's validator -- safe")
            a(f"      case     {by_class.get('case', 0):5}  differs only by letter case")
            a(f"      variant  {by_class.get('variant', 0):5}  export holds the vault's form as an alternate name")
            a(f"      coarsen  {by_class.get('coarsen', 0):5}  vault more precise -- applying loses data")
            a(f"      conflict {by_class.get('conflict', 0):5}  genuinely different -- needs a decision")
            a("")
            a("  by field")
            L.extend(_histogram(by_field))
        if decisions is not None:
            a("")
            if not decisions.entries:
                a(f"  rulings   no {decisions.rel_path} -- every coarsen and "
                  f"conflict stays held")
            else:
                cov_coarsen, cov_conflict = apply_mod.count_accepted(
                    person_plan, "person", decisions)
                a(f"  rulings in {decisions.rel_path}")
                a(f"      entries                 {len(decisions.entries):5}")
                a(f"      coarsen changes covered {cov_coarsen:5}   "
                  f"--apply would write these")
                a(f"      conflicts covered       {cov_conflict:5}   "
                  f"--apply would write these")
                idle = max(0, sum(decisions.counts()) - cov_coarsen - cov_conflict)
                if idle:
                    # Two reasons, and the report cannot tell them apart: the
                    # values agree now (the ruling did its job upstream and is
                    # spent), or the person is a candidate this run does not
                    # match without --adopt-by-name.
                    a(f"      ruled fields not in this plan {idle:5}   "
                      f"already agreed, or the person is unmatched this run")
        a("")

    # -- 2. sources ---------------------------------------------------
    if want("source"):
        sc = source_plan.counts("source")
        a("-- 2. SOURCE " + "-" * 65)
        a(f"  ged {len(tree.sources)}")
        a(f"      matched, unchanged      {sc.get('match', 0):5}")
        a(f"      matched, would update   {sc.get('update', 0):5}")
        a(f"      would create            {sc.get('create', 0):5}")
        a(f"      orphaned                {sc.get('orphan', 0):5}   never deleted")
        a("")

    # -- 3. events ----------------------------------------------------
    if want("event"):
        ec = event_match.counts()
        a("-- 3. EVENT " + "-" * 66)
        a(f"  ged blocks {len(tree.events)}   vault Events "
          f"{len(event_match.pairs) + len(event_match.unkeyed)}")
        a(f"      keyed by content        {ec.get('content', 0):5}")
        a(f"      keyed by corroboration  {ec.get('corroborated', 0):5}   date and place agree")
        a(f"      keyed positionally      {ec.get('positional', 0):5}   order only; dates do not contradict")
        a(f"      unkeyed (vault only)    {ec.get('unkeyed', 0):5}   archive-derived; left alone")
        a(f"      would create            {ec.get('uncreated', 0):5}")
        a(f"      arbitrary but stable    {len(event_match.arbitrary):5}   indistinguishable, assigned in order")
        a("")
        a("  would create, by type")
        L.extend(_histogram(collections.Counter(e.event_type for e in event_match.uncreated)))
        a("")
        a("  vault Events with no GEDCOM block, by type")
        L.extend(_histogram(collections.Counter(
            n.scalar("event_type") for n, _ in event_match.unkeyed)))
        a("")
        disagree = [(pair, c) for pair in event_match.pairs
                    for c in events.event_changes(pair, place_index, match.Change)
                    if c.field == "place"]
        a(f"  place disagrees with the export {len(disagree):5}   held; never written")
        if disagree:
            a("        A positional pair here is probably paired wrong -- the")
            a("        places say the two sides are different occurrences.")
            a("        Otherwise fix one side, or add the PLAC form to the")
            a("        Place's aliases: if both name the same place.")
        # positional first: those are the ones the matcher may have got wrong
        disagree.sort(key=lambda pc: (pc[0].stage != "positional",
                                      pc[0].vault_note.basename))
        for pair, c in disagree[:limit]:
            a(f"        [{c.kind:8}] {pair.stage:10} {pair.vault_note.basename}")
            a(f"              vault {c.old}  export {pair.ged_event.place}")
        if len(disagree) > limit:
            a(f"        ... and {len(disagree) - limit} more")
        a("")

    # -- 4. citations -------------------------------------------------
    if want("citation"):
        a("-- 4. CITATION " + "-" * 63)
        a(f"      matched                 {len(citation_match.matched):5}   "
          f"key (subject_id, source, fact, page)")
        a(f"      would create            {len(citation_match.uncreated):5}")
        a(f"      duplicates in vault     {len(citation_match.duplicates):5}   worklist, not deleted")
        a(f"      unresolved              {len(citation_match.unresolved):5}   "
          f"subject or source not yet in the vault")
        a("")

    # -- 5. suppressed ------------------------------------------------
    if want("event"):
        a("-- 5. SUPPRESSED (never become Events) " + "-" * 39)
        sup = collections.Counter(d for d, _ in tree.suppressed)
        a(f"  {len(tree.suppressed)} EVEN blocks")
        for kind, n in sup.most_common():
            a(f"      {n:5}  {kind}")
        a("        The vault model: a newspaper notice, obituary or index card is a Source,")
        a("        never an Event, and its publication date is not an event date.")
        for _, ev in tree.suppressed[:limit]:
            a(f"        {ev.owner}  {ev.date or '(undated)':12} {ev.even_type[:46]}")
        if tree.folded:
            a(f"  {len(tree.folded)} individual MARR blocks folded into the family's marriage")
            for ind_ev, fam_ev in tree.folded[:limit]:
                a(f"        {ind_ev.owner} -> {fam_ev.owner}  {fam_ev.date}")
        a("")

    # -- 6. media -----------------------------------------------------
    a("-- 6. MEDIA (OBJE) " + "-" * 59)
    a(f"  {len(tree.media)} records, 0 importable -- every one has an empty `1 FILE`.")
    a("  The image lives on Ancestry's servers behind `1 _OID`; `2 TITL` is a")
    a("  caption, not a path. The plugin dropping these is correct.")
    a("")

    # -- 7. creation --------------------------------------------------
    if creation is not None:
        plan = creation.plan
        counts = plan.counts()
        a("-- 7. CREATION (--create) " + "-" * 52)
        a(f"  would create             {len(plan.all):5} notes")
        for kind in ("person", "source", "event", "citation"):
            a(f"      {kind:9}           {counts.get(kind, 0):5}")
        def row(label: str, value: int, tail: str = "") -> None:
            a(f"      {label:<38}{value:5}" + (f"   {tail}" if tail else ""))

        a("")
        a("  not created")
        unassigned = [n for n in plan.sources if "source_type" not in n.fm]
        row("People that look like an existing note", len(plan.skipped_people),
            "-> section 0, needs --adopt-by-name")
        row("Events the vault already holds", len(plan.already_present),
            "capped by count; the matcher could not pair them")
        row("Citations with no resolvable subject", len(plan.skipped_citations),
            "no vault Person carries the subject's cr_id")
        a("")
        a("  would need a hand afterwards")
        row("Sources with no source_type", len(unassigned),
            "set by hand; `document` is never valid")
        row("place values left off a new note", len(plan.unresolved_places),
            "unresolvable against the gazetteer")
        row("legacy `spouse:` notes, several spouses", len(creation.migrations))
        a("")
        a("  follow-up passes in the same run")
        row("People rewritten for relationships", len(creation.rel_changes),
            "both sides, because Obsidian is closed for --apply")
        row("People whose citations: is recomputed", len(creation.relisted),
            "against the Citations on disk now, not the ones above")
        for _, name, count in creation.migrations[:limit]:
            a(f"        {name}: {count} spouses, legacy `spouse:` form")
        annotated = [n for n in plan.all if n.note]
        if annotated:
            a("")
            a("  flagged by the planner")
            for new in annotated[:limit]:
                a(f"      {os.path.basename(new.path)[:-3]}")
                a(f"          {new.note}")
            if len(annotated) > limit:
                a(f"      ... and {len(annotated) - limit} more")
        a("")
        a("  planned notes -- paths, then the first of each kind in full")
        a("  (frontmatter only; bodies are templated)")
        for kind, group in (("source", plan.sources), ("person", plan.people),
                            ("event", plan.events), ("citation", plan.citations)):
            if not group:
                continue
            a("")
            a(f"      {kind} -- {len(group)}")
            for new in group[:limit]:
                a(f"        {os.path.relpath(new.path, cfg.root)}")
            if len(group) > limit:
                a(f"        ... and {len(group) - limit} more")
            L.extend(_frontmatter_lines(group[0], "          "))
        a("")

    if blocked:
        a("-- WOULD REFUSE " + "-" * 62)
        a(f"  Planned changes the writer refuses                       "
          f"{len(blocked):5}  --apply stops before writing anything")
        for act, reason in blocked[:limit]:
            a(f"        {act.entity:8} {act.label}  <- {act.key}  {act.path}")
            a(f"            {reason}")
        if len(blocked) > limit:
            a(f"        ... and {len(blocked) - limit} more")
        a("")

    a(BAR)
    a("  WOULD WRITE: nothing (dry run). Re-run with "
      + ("--apply --create" if creation is not None else "--apply")
      + " to execute.")
    a(BAR)
    return "\n".join(L)


class ApplyLog:
    """Every line `--apply` prints, so the driver is left a call sequence.

    `out` and `err` are callables taking one line; a test captures into a
    list instead of stdout. `limit` caps the detail under any one finding,
    matching the dry run's --limit.
    """

    def __init__(self, out=None, err=None, limit: int = 10):
        self.out = out or (lambda line: print(line))
        self.err = err or (lambda line: print(line, file=sys.stderr))
        self.limit = limit

    # -- before anything is written ------------------------------------

    def preconditions(self, checks) -> None:
        self.out("Preconditions")
        for c in checks:
            self.out(f"  [{'OK   ' if c.ok else 'BLOCK'}] {c.name}: {c.detail}")
            if not c.ok:
                self.out(f"            {c.remedy}")

    def refuse_preconditions(self) -> None:
        self.err("\nRefusing to write.")

    def baseline(self, before) -> None:
        """Invariants already failing. Named so a later failure reads as new."""
        self.out("\nBaseline invariants")
        for r in before:
            if not r.ok:
                self.out(f"  [note] pre-existing: {r.name} -- {r.detail}")

    def scope(self, scope) -> None:
        if scope is None:
            return
        self.out(f"\nScope: --only {', '.join(sorted(scope))} -- "
                 f"every other pass is skipped")

    def rulings(self, decisions) -> None:
        n_coarsen, n_conflict = decisions.counts()
        self.out(f"\nRulings: {len(decisions.entries)} in {decisions.rel_path} "
                 f"({n_coarsen} coarsen exemptions, "
                 f"{n_conflict} accepted conflicts)"
                 if decisions.entries else
                 f"\nRulings: no {decisions.rel_path} -- "
                 f"every coarsen and conflict stays held")

    def adoptions(self, actions) -> None:
        for act in actions:
            self.out(f"  adopting {act.label}  <- {act.key}")

    def case(self, n_case: int, direction: int) -> None:
        if not n_case:
            self.out("\nCase changes: none")
        elif direction:
            self.out(f"\nCase changes: {n_case}, direction uniform "
                     f"({direction:+d}) -- safe to apply")
        else:
            self.out(f"\nCase changes: {n_case}, direction MIXED -- "
                     f"all held back")

    def blocked(self, pairs) -> None:
        """(action, reason) pairs from the preflight. Nothing has been written."""
        self.err("\nPlanned changes that could not be written:")
        for act, reason in pairs[:self.limit]:
            self.err(f"  {act.entity:8} {act.label}  <- {act.key}  {act.path}")
            self.err(f"           {reason}")
        if len(pairs) > self.limit:
            self.err(f"  ... and {len(pairs) - self.limit} more")
        self.err("Refusing to write: that is a matcher, indexing or "
                 "frontmatter bug, and writing the rest of the run would "
                 "hide it.")

    # -- the write passes ----------------------------------------------

    def applying(self, direction: int) -> None:
        self.out("Applying fill + refine" + (" + case" if direction else "")
                 + " changes, plus reviewed coarsen exemptions")

    def pass_skipped(self, entity: str) -> None:
        self.out(f"  {entity:8}    - skipped, not in --only")

    def field_pass(self, entity: str, written, skipped) -> None:
        held = sum(len(h) for _, h in skipped)
        applied = sum(len(c) for _, c in written)
        self.out(f"  {entity:8} {len(written):4} notes, "
                 f"{applied:4} fields written, "
                 f"{held:4} held back (case/coarsen/conflict)")

    def event_pass(self, written, held) -> None:
        n_fields = sum(len(c) for _, c in written)
        n_held = sum(len(h) for _, h in held)
        self.out(f"  event    {len(written):4} notes, "
                 f"{n_fields:4} fields written, "
                 f"{n_held:4} held back (coarsen/conflict)")

    def place_pass(self) -> None:
        self.out("  place       - no write pass exists; Places are never "
                 "created or updated by a sync")

    # -- creation ------------------------------------------------------

    def creation_plan(self, plan) -> None:
        self.out("\nCreating notes")
        for kind, count in plan.counts().items():
            self.out(f"  {kind:8} {count:4}")
        pad = f"  {'':8}      "
        if plan.skipped_people:
            self.out(f"{pad}{len(plan.skipped_people)} People NOT created -- "
                     f"each looks like an existing note (see section 0)")
        unassigned = [n for n in plan.sources if "source_type" not in n.fm]
        if unassigned:
            self.out(f"{pad}{len(unassigned)} Sources have no source_type -- "
                     f"set by hand; `document` is never valid")
        if plan.unresolved_places:
            self.out(f"{pad}{len(plan.unresolved_places)} place values left "
                     f"off, unresolvable against the gazetteer")
        if plan.already_present:
            self.out(f"{pad}{len(plan.already_present)} Events NOT created -- "
                     f"the vault already holds one the matcher could not pair")
        if plan.skipped_citations:
            self.out(f"{pad}{len(plan.skipped_citations)} Citations NOT "
                     f"created -- no vault Person carries the subject's cr_id")

    def relationships(self, touched) -> None:
        self.out(f"  relations {len(touched):4} People rewritten "
                 f"(both sides; Obsidian is closed so nothing syncs them "
                 f"for us)")

    def spouse_migrations(self, migrations) -> None:
        for _, name, count in migrations:
            self.out(f"  {'':8}      {name}: {count} spouses but the note "
                     f"uses the legacy `spouse:` form -- migrate by hand")

    def citation_lists(self, relisted) -> None:
        self.out(f"  citations {len(relisted):4} People had `citations:` "
                 f"recomputed")

    def sidecar(self, mapping, rel_path: str) -> None:
        self.out(f"  events   {len(mapping):4} keys written to {rel_path}")

    # -- after ---------------------------------------------------------

    def invariants(self, after) -> None:
        """The suite as it stands after the run, at the caller's --limit.

        It was fixed at three items per check, so --limit meant one thing in
        a dry run and another here.
        """
        self.out("\nRe-running invariants")
        for a in after:
            self.out(a.render(limit=self.limit))

    def lost(self, lost) -> None:
        self.err(f"\n{len(lost)} planned changes were never written -- "
                 f"their notes left the index mid-run")

    def regressed(self, names) -> None:
        self.err(f"\nREGRESSED: {', '.join(names)}")

    def done(self, n_modified: int, paths=()) -> None:
        spec = " ".join(f"'{p}'" for p in paths)
        self.out(f"\n{n_modified} notes modified. "
                 f"Review with: git diff" + (f" -- {spec}" if spec else ""))
