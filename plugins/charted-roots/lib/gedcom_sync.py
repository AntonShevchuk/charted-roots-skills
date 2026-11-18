#!/usr/bin/env python3
"""Dedup-aware GEDCOM reconciliation for the Charted Roots vault.

The Charted Roots importer (v0.22.76) does no duplicate detection except for
Places: it mints a fresh random cr_id per record and resolves the resulting
filename collisions as `Name 1.md`. It writes `external_id` and `gedcom_id`
but never reads them back. This script does the join the plugin skips.

    python3 <lib>/gedcom_sync.py              dry run, full report
    python3 <lib>/gedcom_sync.py --apply      write

Dry run is the default; nothing is written without --apply. The vault
invariants run standalone as <lib>/vault_verify.py; `--verify` here is an
alias kept for the History run records that quote it.

Exit codes: 0 success; 1 the run found a problem (a failed invariant, a
planned change the writer would refuse, a regression, a refused
precondition); 2 the run could not start (bad flags, unreadable vault,
GEDCOM or decisions file).
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass

import vault_verify
from crsync import apply as apply_mod
from crsync import (
    citations, config, create, decisions, events, gedcom, match, places,
    report, vault, verify,
)

#: Entity types a run can be scoped to with `--only`. Singular is canonical;
#: the plural spellings are accepted as aliases.
ENTITY_TYPES = ["person", "source", "event", "citation", "place"]
_ONLY_ALIASES = {"people": "person", "persons": "person", "sources": "source",
                 "events": "event", "citations": "citation", "places": "place"}

#: Entity types `--apply` has a write pass for. Citations are only created
#: (`--create`) and Places never written, so a scope of those alone would
#: run every precondition and write nothing.
WRITABLE_TYPES = {"person", "source", "event"}

#: The Event -> GEDCOM sidecar, under History/ beside the decisions file.
EVENT_MAP = "gedcom-import-map.json"

DEFAULT_GED = "FamilyTree.ged"

#: Flags that mean something in only some modes, the modes they belong to,
#: and why, where the reason is not obvious. A flag outside its modes is an
#: error: silently ignoring it would let `--verify --apply` or `--apply --out`
#: look like it did what it said.
_MODE_FLAGS = {
    "--only": (("report", "apply"), "the invariants are vault-wide"),
    "--ged": (("report", "apply"), "the invariants read no GEDCOM"),
    "--out": (("report",), "--apply prints its log; redirect it instead"),
    "--create": (("report", "apply"), ""),
    "--adopt-by-name": (("report", "apply"), ""),
    "--no-restore-point": (("apply",), "it overrides a write precondition"),
    "--allow-obsidian-open": (("apply",), "it overrides a write precondition"),
    "--allow-dirty": (("apply",), "it overrides a write precondition"),
}


class UsageError(Exception):
    """A flag combination the run refuses. Exits 2."""


class InputError(Exception):
    """An input the run cannot read. Exits 2."""


@dataclass(frozen=True)
class Options:
    """What a command needs from the command line, resolved and checked."""

    scope: set[str] | None     # None means every entity type
    ged_path: str
    limit: int
    create: bool
    adopt_by_name: bool
    out: str
    require_restore_point: bool
    allow_obsidian: bool
    allow_dirty: bool


@dataclass
class Reconciliation:
    """The vault and GEDCOM, loaded and matched. A matcher out of scope is None."""

    ged_path: str
    tree: gedcom.Tree
    people: list
    sources: list
    event_notes: list
    citation_notes: list
    place_index: places.Index
    decisions: decisions.Decisions
    person_plan: match.Plan | None
    source_plan: match.Plan | None
    event_match: events.EventMatch | None
    citation_match: citations.CitationMatch | None

    def allnotes(self) -> list:
        return (self.people + self.sources + self.event_notes
                + self.citation_notes + self.place_index.notes)

    def entity_plans(self) -> list[tuple[str, match.Plan | None]]:
        """The entities with a field pass, in write order."""
        return [("person", self.person_plan), ("source", self.source_plan)]


def parse_only(value: str) -> set[str] | None:
    """`--only` as a set of canonical entity types, or None for "everything".

    An unrecognised name is an error rather than an empty scope: a typo that
    silently narrowed a run to nothing would look like a vault with no work
    left to do.
    """
    names = [n.strip().lower() for n in value.split(",") if n.strip()]
    if not names:
        return None
    scope, unknown = set(), []
    for name in names:
        canonical = _ONLY_ALIASES.get(name, name)
        if canonical not in ENTITY_TYPES:
            unknown.append(name)
        else:
            scope.add(canonical)
    if unknown:
        raise ValueError(f"--only: unknown entity type(s) {', '.join(unknown)}. "
                         f"Valid: {', '.join(ENTITY_TYPES)}")
    return scope


def in_scope(scope: set[str] | None, entity: str) -> bool:
    return scope is None or entity in scope


def resolve_ged_path(root: str, ged: str) -> str:
    """The GEDCOM to read: `--ged` as given if absolute, else under the vault."""
    return ged if os.path.isabs(ged) else os.path.join(root, ged)


def _reconcile(cfg: config.Config, opts: Options) -> Reconciliation:
    """Load everything and run the matchers the scope asks for.

    `--create` is only accepted with the full scope, so it always finds every
    matcher's output here.
    """
    scope = opts.scope
    try:
        tree = gedcom.parse(opts.ged_path)
    except (OSError, UnicodeDecodeError) as exc:
        raise InputError(f"GEDCOM unreadable: {exc}") from None
    people = list(vault.iter_notes(cfg.people))
    sources = list(vault.iter_notes(cfg.sources))
    event_notes = list(vault.iter_notes(cfg.events))
    citation_notes = list(vault.iter_notes(cfg.citations))
    place_index = places.load(cfg.places)
    return Reconciliation(
        ged_path=opts.ged_path, tree=tree, people=people, sources=sources,
        event_notes=event_notes, citation_notes=citation_notes,
        place_index=place_index, decisions=decisions.load(cfg.root),
        person_plan=(match.match_people(tree, people, cfg.root,
                                        adopt=opts.adopt_by_name,
                                        place_index=place_index)
                     if in_scope(scope, "person") else None),
        source_plan=(match.match_sources(tree, sources, cfg.root)
                     if in_scope(scope, "source") else None),
        event_match=(events.match_events(tree, event_notes, people,
                                         place_index, cfg.root)
                     if in_scope(scope, "event") else None),
        citation_match=(citations.match_citations(
                            tree, citation_notes, people, sources, cfg.root)
                        if in_scope(scope, "citation") else None),
    )


def _preflight(cfg: config.Config, r: Reconciliation) -> tuple[int, list]:
    """The case direction, and every planned field change the writer refuses.

    Shared by the dry run and `--apply`, so a dry run that looks clean is one
    `--apply` will not then refuse.
    """
    direction = (apply_mod.case_direction(r.person_plan, "person")
                 if r.person_plan is not None else 0)
    notes_by_path = {n.path: n for n in r.people + r.sources}
    blocked = [pair for entity, plan in r.entity_plans() if plan is not None
               for pair in apply_mod.preflight(
                   plan, entity, notes_by_path, cfg.root,
                   allow_case=bool(direction) and entity == "person",
                   decisions=r.decisions)]
    return direction, blocked


def _creation(cfg: config.Config, r: Reconciliation) -> tuple:
    """Plan every new note and its follow-up passes. Writes nothing.

    Shared by the dry run and `--apply` so the preview cannot drift from what
    is written. Relationships are computed from the in-memory plan, not from
    the notes on disk, so the order relative to the writes does not matter.
    """
    allnotes = r.allnotes()
    cplan = create.plan_creation(
        r.tree, cfg, r.place_index, r.person_plan,
        r.source_plan, r.event_match, r.citation_match, allnotes)
    rels, migrations = create.relationship_updates(
        r.tree, cfg, allnotes, cplan.people, r.place_index)
    new_xrefs = {n.fm["external_id"] for n in cplan.people}
    rel_changes = create.relationship_changes(rels, allnotes, new_xrefs)
    return allnotes, cplan, rel_changes, migrations


def _count_case(plan: match.Plan) -> int:
    return sum(1 for kind in ("update", "adopt")
               for act in plan.of("person", kind)
               for c in act.changes if c.kind == match.CASE)


def _write_creation(cfg: config.Config, r: Reconciliation,
                    log: report.ApplyLog) -> set[str]:
    """Create the new notes, then the two passes that depend on them.

    Order matters and belongs here rather than in the writer: Events and
    Citations link to Sources and People by filename, the relationship pass
    needs the new People to exist on disk, and `citations:` is recomputed
    last because it reads the Citations this run just wrote.
    """
    allnotes, cplan, rel_changes, migrations = _creation(cfg, r)
    log.creation_plan(cplan)
    modified = {n.path for n in apply_mod.write_new_notes(cplan, dry=False)}

    touched = apply_mod.write_relationships(
        rel_changes, allnotes, cplan, dry=False)
    log.relationships(touched)
    log.spouse_migrations(migrations)

    relisted = apply_mod.rebuild_citation_lists(cfg, dry=False)
    log.citation_lists(relisted)
    return modified | set(touched) | set(relisted)


def cmd_apply(cfg: config.Config, opts: Options) -> int:
    """Write, in order, and report every step through `log`.

    Every line this prints lives in `report.ApplyLog`, so the dry run and
    `--apply` cannot describe the same run differently. What stays here is
    the order of the passes, the scope, and the decision to refuse.
    """
    scope = opts.scope
    log = report.ApplyLog(limit=opts.limit)

    checks = apply_mod.check_preconditions(
        cfg, require_restore_point=opts.require_restore_point,
        allow_obsidian=opts.allow_obsidian, allow_dirty=opts.allow_dirty)
    log.preconditions(checks)
    if any(not c.ok for c in checks):
        log.refuse_preconditions()
        return 1

    before = verify.run(cfg)
    log.baseline(before)

    r = _reconcile(cfg, opts)
    log.scope(scope)
    log.rulings(r.decisions)
    if opts.adopt_by_name and r.person_plan is not None:
        log.adoptions(r.person_plan.of("person", "adopt"))

    direction, blocked = _preflight(cfg, r)
    if r.person_plan is not None:
        log.case(_count_case(r.person_plan), direction)
    if blocked:
        log.blocked(blocked)
        return 1

    log.applying(direction)
    #: Every note actually rewritten. A Person can be touched by the field
    #: pass, the relationship pass and the citation rebuild in one run, so
    #: only a set of paths answers "how many notes will the diff show".
    modified: set[str] = set()
    lost = []
    notes_by_path = {n.path: n for n in r.people + r.sources}
    for entity, plan in r.entity_plans():
        if plan is None:
            log.pass_skipped(entity)
            continue
        written, skipped, missing = apply_mod.apply_field_updates(
            plan, entity, notes_by_path, cfg.root, dry=False,
            allow_case=bool(direction) and entity == "person",
            decisions=r.decisions)
        log.field_pass(entity, written, skipped)
        modified.update(os.path.join(cfg.root, act.path) for act, _ in written)
        lost += missing

    if r.event_match is not None:
        written, held = apply_mod.apply_event_updates(
            r.event_match, r.place_index, dry=False)
        log.event_pass(written, held)
        modified.update(pair.vault_note.path for pair, _ in written)
    else:
        log.pass_skipped("event")
    if in_scope(scope, "place"):
        log.place_pass()

    if opts.create:
        modified |= _write_creation(cfg, r, log)

    # The sidecar maps Events to GEDCOM keys, so it is part of the event pass
    # and scoped with it.
    if r.event_match is not None:
        sidecar = os.path.join(cfg.root, "History", EVENT_MAP)
        mapping = apply_mod.write_event_keys(
            r.event_match, sidecar, report.sha256(r.ged_path), dry=False)
        log.sidecar(mapping, os.path.relpath(sidecar, cfg.root))

    after = verify.run(cfg)
    regressed = verify.regressions(before, after)
    log.invariants(after)
    if lost:
        log.lost(lost)
    if regressed:
        log.regressed(regressed)
    if regressed or lost:
        return 1
    log.done(len(modified), cfg.entity_paths)
    return 0


def cmd_report(cfg: config.Config, opts: Options) -> int:
    """The dry run. Exits 1 where `--apply` would refuse a planned change."""
    r = _reconcile(cfg, opts)
    _, blocked = _preflight(cfg, r)
    creation = None
    if opts.create:
        _, cplan, rel_changes, migrations = _creation(cfg, r)
        creation = report.CreationPreview(
            plan=cplan, rel_changes=rel_changes, migrations=migrations,
            relisted=apply_mod.rebuild_citation_lists(cfg, dry=True))
    text = report.render(cfg, r.tree, r.ged_path, r.person_plan,
                         r.source_plan, r.event_match, r.citation_match,
                         r.place_index, apply_mod.obsidian_running(),
                         limit=opts.limit, decisions=r.decisions,
                         creation=creation, only=opts.scope, blocked=blocked)
    print(text)
    if opts.out:
        with open(opts.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print(f"\nreport written to {opts.out}")
    return 1 if blocked else 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gedcom_sync.py",
        description="Reconcile a GEDCOM export against the vault without creating duplicates.",
    )
    p.add_argument("--vault", default=".", help="vault root (default: cwd)")
    p.add_argument("--ged", default=None,
                   help=f"GEDCOM file (default: {DEFAULT_GED})")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true",
                      help="alias for vault_verify.py: run vault invariants and exit")
    mode.add_argument("--apply", action="store_true", help="write changes (default is a dry run)")
    p.add_argument("--only", default="",
                   help="scope the run to these entity types, comma-separated: "
                        + ",".join(ENTITY_TYPES) + " (default: all)")
    p.add_argument("--out", default="", help="write the report to this file as well")
    p.add_argument("--no-restore-point", action="store_true",
                   help="skip the git-tag restore-point precondition")
    p.add_argument("--allow-obsidian-open", action="store_true",
                   help="write even though Obsidian is running (races the plugin)")
    p.add_argument("--allow-dirty", action="store_true",
                   help="write even though the entity folders have uncommitted changes")
    p.add_argument("--create", action="store_true",
                   help="create notes for GEDCOM records with no vault "
                        "counterpart; preview it on a dry run first")
    p.add_argument("--adopt-by-name", action="store_true",
                   help="treat a name match against a vault-native Person as a match")
    p.add_argument("--limit", type=int, default=10, help="max detail lines per finding")
    return p


def _check_mode_flags(p: argparse.ArgumentParser, args: argparse.Namespace,
                      mode: str) -> None:
    for flag, (modes, why) in _MODE_FLAGS.items():
        dest = flag.lstrip("-").replace("-", "_")
        if mode in modes or getattr(args, dest) == p.get_default(dest):
            continue
        shown = {"verify": "--verify", "apply": "--apply",
                 "report": "a dry run"}[mode]
        raise UsageError(f"{flag} does not apply to {shown}"
                         + (f": {why}." if why else "."))


def _options(p: argparse.ArgumentParser, args: argparse.Namespace,
             root: str) -> Options:
    """Check the flags against each other and resolve them. Raises UsageError."""
    mode = "verify" if args.verify else "apply" if args.apply else "report"
    _check_mode_flags(p, args, mode)
    try:
        scope = parse_only(args.only)
    except ValueError as exc:
        raise UsageError(str(exc)) from None
    if args.create and scope is not None and scope != set(ENTITY_TYPES):
        raise UsageError(
            "--create cannot be combined with a partial --only: new Events "
            "and Citations link to new People and Sources by filename, so "
            "creating one kind without the others leaves dangling links.")
    if args.apply and scope is not None and not scope & WRITABLE_TYPES:
        raise UsageError(
            f"--apply --only {','.join(sorted(scope))} has nothing to write: "
            f"only {', '.join(sorted(WRITABLE_TYPES))} have a write pass.")
    return Options(
        scope=scope,
        ged_path=resolve_ged_path(root, args.ged or DEFAULT_GED),
        limit=args.limit, create=args.create, adopt_by_name=args.adopt_by_name,
        out=args.out, require_restore_point=not args.no_restore_point,
        allow_obsidian=args.allow_obsidian_open, allow_dirty=args.allow_dirty)


def main(argv: list[str] | None = None) -> int:
    p = _build_parser()
    args = p.parse_args(argv)

    cfg = vault_verify.load_config(args.vault)
    if cfg is None:
        return 2

    try:
        opts = _options(p, args, cfg.root)
    except UsageError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.verify:
        return vault_verify.cmd_verify(cfg, opts.limit)

    if not os.path.exists(opts.ged_path):
        print(f"No GEDCOM at {opts.ged_path}", file=sys.stderr)
        return 2

    try:
        return (cmd_apply if args.apply else cmd_report)(cfg, opts)
    except decisions.DecisionsError as exc:
        # Never fall back to "accept nothing": that would quietly revert every
        # reviewed ruling on the next run.
        print(f"Decisions file unusable: {exc}", file=sys.stderr)
        return 2
    except InputError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
