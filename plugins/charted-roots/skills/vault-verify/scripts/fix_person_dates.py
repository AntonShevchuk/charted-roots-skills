#!/usr/bin/env python3
"""Rewrite Person `born` / `died` into forms the plugin's date validator accepts.

One-off repair for dates written before `crsync/dates.py` existed (`ABT 1804`,
`BEF 1909`, `1850-1858`, `25 Dez 1914`). A sync fixes the Persons the export
matches; this covers the rest. Dry run by default.

    python3 <vault-verify>/scripts/fix_person_dates.py
    python3 <vault-verify>/scripts/fix_person_dates.py --apply

Nothing is lost:

* `ABT` -> `c.`, ranges -> `a to b`, native month names -> ISO: respellings.
* `BEF` / `AFT` -> the bare date (the Event's, if it is more precise), only when the Person's one Birth / Death
  Event carries the qualifier -- or can be given it, because its `date:` is
  that same bare date (then the Event gets `BEF <date>` +
  `date_precision: estimated`). Otherwise the value is held for a human.
* A value with no clean form is held and listed.

`--apply` refuses while Obsidian runs or the People / Events folders have
uncommitted changes: the clean tree is the way back.

Exit codes: 0 nothing left to fix (or applied); 1 changes pending or held;
2 the run could not start.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field

from crsync import apply as apply_mod
from crsync import config, dates, vault

FIELDS = {"born": "birth", "died": "death"}


@dataclass
class Fix:
    note: vault.Note
    key: str
    old: str
    new: str
    event: vault.Note | None = None     # an Event to give the qualifier
    event_date: str = ""


@dataclass
class Plan:
    fixes: list = field(default_factory=list)
    held: list = field(default_factory=list)      # (note, key, value, reason)


def _event_index(events: list) -> dict:
    """(person basename, event_type) -> [Event notes]."""
    out: dict = {}
    for ev in events:
        et = ev.scalar("event_type")
        if et not in FIELDS.values():
            continue
        for person in ev.links("persons") + ev.links("person"):
            out.setdefault((person, et), []).append(ev)
    return out


def plan(cfg: config.Config) -> Plan:
    settings = cfg.settings
    events = _event_index(list(vault.iter_notes(cfg.events)))
    out = Plan()
    for note in vault.iter_notes(cfg.people):
        if not note.scalar("cr_id"):
            continue
        for key, etype in FIELDS.items():
            value = note.scalar(key)
            if not value or not dates.plugin_error(value, settings):
                continue
            new = dates.person_form(value)
            if not new or dates.plugin_error(new, settings):
                out.held.append((note, key, value, "no form the validator accepts"))
                continue
            meaning = dates.meaning(value)
            if meaning[0] not in ("BEF", "AFT"):
                out.fixes.append(Fix(note, key, value, new))
                continue
            # The qualifier must survive on the Event before the Person drops it.
            candidates = events.get((note.basename, etype), [])
            if len(candidates) != 1:
                out.held.append((note, key, value,
                                 f"{len(candidates)} {etype} Events -- the "
                                 f"qualifier needs exactly one to live on"))
                continue
            ev = candidates[0]
            have = dates.meaning(ev.scalar("date"))
            if have == meaning:
                out.fixes.append(Fix(note, key, value, new))
            elif (have and have[0] == meaning[0] and not have[2]
                  and have[1].startswith(meaning[1])):
                # The Event is the more precise record of the same bound
                # (`BEF 1889-02-01` against `BEF 1889`): take its date.
                out.fixes.append(Fix(note, key, value, have[1]))
            elif have == ("", meaning[1], ""):
                out.fixes.append(Fix(note, key, value, new, ev,
                                     f"{meaning[0]} {meaning[1]}"))
            else:
                out.held.append((note, key, value,
                                 f"Event {ev.basename} has date "
                                 f"{ev.scalar('date')!r}"))
    return out


def _rel(cfg, note) -> str:
    return os.path.relpath(note.path, cfg.root)


def preconditions(cfg) -> list:
    checks = []
    running = apply_mod.obsidian_running()
    checks.append(apply_mod.Precondition(
        "Obsidian is closed", running is False,
        "cannot tell" if running is None else ("running" if running else "not running"),
        "Quit Obsidian: it rewrites notes from its own buffers."))
    folders = [os.path.relpath(f, cfg.root) for f in (cfg.people, cfg.events)]
    ok, dirty = apply_mod._git(cfg.root, "status", "--porcelain", "--", *folders)
    checks.append(apply_mod.Precondition(
        "People and Events are clean in git", ok and not dirty,
        "git status failed" if not ok else
        (f"{len(dirty.splitlines())} modified" if dirty else "clean"),
        "Commit first, so this run's diff stands alone and can be reverted."))
    return checks


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="fix_person_dates.py", description=__doc__.split("\n")[0])
    p.add_argument("--vault", default=".", help="vault root (default: cwd)")
    p.add_argument("--apply", action="store_true", help="write the fixes")
    args = p.parse_args(argv)

    if not os.path.isdir(args.vault):
        print(f"No vault at {args.vault}", file=sys.stderr)
        return 2
    cfg = config.load(args.vault)
    result = plan(cfg)

    print(f"Person dates the plugin's validator rejects: "
          f"{len(result.fixes) + len(result.held)}")
    print(f"  fixable {len(result.fixes)}   held {len(result.held)}\n")
    for f in result.fixes:
        line = f"  {_rel(cfg, f.note)}: {f.key} {f.old!r} -> {f.new!r}"
        if f.event is not None:
            line += f"   + Event {f.event.basename}: date {f.event_date!r}"
        print(line)
    if result.held:
        print("\nHeld -- fix by hand:")
        for note, key, value, why in result.held:
            print(f"  {_rel(cfg, note)}: {key} {value!r} -- {why}")

    if not args.apply:
        print("\nDry run: nothing written. Re-run with --apply.")
        return 1 if (result.fixes or result.held) else 0

    checks = preconditions(cfg)
    for c in checks:
        print(f"  [{'ok' if c.ok else 'REFUSED'}] {c.name} -- {c.detail}")
        if not c.ok:
            print(f"        {c.remedy}")
    if not all(c.ok for c in checks):
        return 1

    touched = {}
    for f in result.fixes:
        f.note.set(f.key, f.new)
        touched[f.note.path] = f.note
        if f.event is not None:
            f.event.set("date", f.event_date)
            f.event.set("date_precision", "estimated")
            touched[f.event.path] = f.event
    for note in touched.values():
        if note.dirty:
            note.save()
    print(f"\nWrote {len(touched)} notes. Re-run vault_verify.py.")
    return 1 if result.held else 0


if __name__ == "__main__":
    sys.exit(main())
