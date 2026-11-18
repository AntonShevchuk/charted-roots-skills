#!/usr/bin/env python3
"""Plan and write the modern Place notes behind a GEDCOM's historical PLACs.

    python3 <lib>/places_plan.py extract    list the PLAC strings into the plan
    python3 <lib>/places_plan.py check      validate the reviewed plan
    python3 <lib>/places_plan.py apply      show what would be written
    python3 <lib>/places_plan.py apply --apply    write the approved places

The plan is `History/places-plan.json`. `extract` and `apply --apply` write;
`check` and a bare `apply` never do.

Exit codes, as for gedcom_sync.py: 0 success; 1 the run found a problem (a
plan that fails `check`, a refused precondition, a regression); 2 the run
could not start (bad flags, unreadable vault, plan or GEDCOM).
"""

from __future__ import annotations

import argparse
import os
import sys

import vault_verify
from crsync import apply as apply_mod
from crsync import config, gedcom, placeplan, places, report, vault, verify
from gedcom_sync import DEFAULT_GED, InputError, UsageError, resolve_ged_path

TAG_PREFIX = "pre-organize-places"

#: Flag -> (commands it belongs to, why).
_MODE_FLAGS = {
    "--ged": (("extract",), "only extract reads the GEDCOM"),
    "--apply": (("apply",), ""),
    "--no-restore-point": (("apply",), "it overrides a write precondition"),
    "--allow-obsidian-open": (("apply",), "it overrides a write precondition"),
    "--allow-dirty": (("apply",), "it overrides a write precondition"),
}

#: Flags that only make sense together with --apply.
_NEEDS_APPLY = ("no_restore_point", "allow_obsidian_open", "allow_dirty")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="places_plan.py",
        description="Plan and create Place notes for historical GEDCOM PLACs.")
    p.add_argument("command", choices=["extract", "check", "apply"])
    p.add_argument("--vault", default=".", help="vault root (default: cwd)")
    p.add_argument("--ged", default=None,
                   help=f"GEDCOM file (default: {DEFAULT_GED})")
    p.add_argument("--apply", action="store_true",
                   help="write the notes (default is a dry run)")
    p.add_argument("--no-restore-point", action="store_true",
                   help="skip the git-tag restore-point precondition")
    p.add_argument("--allow-obsidian-open", action="store_true",
                   help="write even though Obsidian is running")
    p.add_argument("--allow-dirty", action="store_true",
                   help="write even though the entity folders have "
                        "uncommitted changes")
    return p


def _check_flags(args: argparse.Namespace) -> None:
    for flag, (commands, why) in _MODE_FLAGS.items():
        dest = flag.lstrip("-").replace("-", "_")
        if args.command in commands or not getattr(args, dest):
            continue
        raise UsageError(f"{flag} does not apply to {args.command}"
                         + (f": {why}." if why else "."))
    if not args.apply:
        for dest in _NEEDS_APPLY:
            if getattr(args, dest):
                raise UsageError(
                    f"--{dest.replace('_', '-')} only applies with --apply.")


def _problems(cfg: config.Config, plan: placeplan.Plan) -> list[str]:
    return placeplan.check(plan, cfg, list(vault.iter_notes(cfg.places)))


def cmd_extract(cfg: config.Config, ged_path: str) -> int:
    try:
        tree = gedcom.parse(ged_path)
    except (OSError, UnicodeDecodeError) as exc:
        raise InputError(f"GEDCOM unreadable: {exc}") from None
    plan = placeplan.load(cfg.root)
    res = placeplan.extract(plan, placeplan.count_placs(tree),
                            places.load(cfg.places), root=cfg.root)
    placeplan.save(cfg.root, plan)
    print(f"{len(plan.plac)} PLAC strings in {placeplan.PLAN_PATH}: "
          f"{len(res.added)} new ({len(res.resolved)} already resolved), "
          f"{len(res.updated)} counts refreshed")
    return 0


def cmd_check(cfg: config.Config) -> int:
    plan = placeplan.load(cfg.root)
    problems = _problems(cfg, plan)
    for line in problems:
        print(f"  {line}")
    print(f"{len(problems)} problem(s)" if problems else "plan is consistent")
    return 1 if problems else 0


def _print_result(res: placeplan.ApplyResult, dry: bool) -> None:
    verb = "would create" if dry else "created"
    for path in res.created:
        print(f"  {verb} {path}")
    for path in res.aliased:
        print(f"  {'would add' if dry else 'added'} aliases to {path}")
    print(f"{len(res.created)} created, {len(res.aliased)} aliased"
          + (" (dry run; pass --apply to write)" if dry else ""))


def cmd_apply(cfg: config.Config, args: argparse.Namespace) -> int:
    plan = placeplan.load(cfg.root)
    problems = _problems(cfg, plan)
    if problems:
        print("The plan fails check:", file=sys.stderr)
        for line in problems:
            print(f"  {line}", file=sys.stderr)
        print("Refusing to write.", file=sys.stderr)
        return 1
    if not args.apply:
        _print_result(placeplan.apply_plan(plan, cfg, dry=True), dry=True)
        return 0

    log = report.ApplyLog()
    checks = apply_mod.check_preconditions(
        cfg, require_restore_point=not args.no_restore_point,
        allow_obsidian=args.allow_obsidian_open, allow_dirty=args.allow_dirty,
        tag_prefix=TAG_PREFIX)
    log.preconditions(checks)
    if any(not c.ok for c in checks):
        log.refuse_preconditions()
        return 1

    before = verify.run(cfg)
    log.baseline(before)
    try:
        result = placeplan.apply_plan(plan, cfg, dry=False)
    except OSError as exc:
        print(f"Write failed: {exc}. Some Place notes may be written; "
              f"restore from the {TAG_PREFIX}-* tag and re-run.",
              file=sys.stderr)
        return 1
    _print_result(result, dry=False)
    after = verify.run(cfg)
    log.invariants(after)
    regressed = verify.regressions(before, after)
    if regressed:
        log.regressed(regressed)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    p = _build_parser()
    args = p.parse_args(argv)
    try:
        _check_flags(args)
    except UsageError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    cfg = vault_verify.load_config(args.vault)
    if cfg is None:
        return 2
    try:
        if args.command == "extract":
            ged_path = resolve_ged_path(cfg.root, args.ged or DEFAULT_GED)
            if not os.path.exists(ged_path):
                print(f"No GEDCOM at {ged_path}", file=sys.stderr)
                return 2
            return cmd_extract(cfg, ged_path)
        if args.command == "check":
            return cmd_check(cfg)
        return cmd_apply(cfg, args)
    except placeplan.PlanError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except InputError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
