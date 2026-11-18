"""The reviewed plan that maps historical PLAC strings to modern Place notes.

The plan lives in the vault at `History/places-plan.json`, so the user can
review and edit it between runs. `places` holds the modern Place notes that
should exist, keyed by a plan key; `plac` maps each GEDCOM PLAC string to one
of them, or marks it as not a place or unidentified.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from dataclasses import dataclass, field

from . import config, create, gedcom, places, vault

PLAN_PATH = "History/places-plan.json"
VERSION = 1
STATUSES = {"proposed", "approved", "created"}
PLAC_STATUSES = {"proposed", "approved"}


class PlanError(Exception):
    """The plan file cannot be read as a plan."""


@dataclass
class PlannedPlace:
    key: str
    title: str
    place_type: str
    parent: str = ""
    aliases: list[str] = field(default_factory=list)
    reason: str = ""
    status: str = "proposed"
    cr_id: str = ""      # set for an existing or created note
    file: str = ""


@dataclass
class PlacEntry:
    plac: str
    count: int = 0
    place: str = ""
    not_place: str = ""
    unidentified: str = ""
    status: str = "proposed"


@dataclass
class Plan:
    places: dict[str, PlannedPlace] = field(default_factory=dict)
    plac: dict[str, PlacEntry] = field(default_factory=dict)


def _dump_place(p: PlannedPlace) -> dict:
    out = {"title": p.title, "place_type": p.place_type}
    for name in ("parent", "reason", "cr_id", "file"):
        if getattr(p, name):
            out[name] = getattr(p, name)
    if p.aliases:
        out["aliases"] = list(p.aliases)
    if p.status != "proposed":
        out["status"] = p.status
    return out


def _dump_plac(e: PlacEntry) -> dict:
    out = {}
    if e.count:
        out["count"] = e.count
    for name in ("place", "not_place", "unidentified"):
        if getattr(e, name):
            out[name] = getattr(e, name)
    if e.status != "proposed":
        out["status"] = e.status
    return out


def save(root: str, plan: Plan) -> None:
    data = {
        "version": VERSION,
        "places": {k: _dump_place(p) for k, p in plan.places.items()},
        "plac": {k: _dump_plac(e) for k, e in plan.plac.items()},
    }
    text = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    vault.write_atomic(os.path.join(root, PLAN_PATH), text)


def load(root: str) -> Plan:
    path = os.path.join(root, PLAN_PATH)
    if not os.path.exists(path):
        return Plan()
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        raise PlanError(f"{PLAN_PATH}: cannot read: {exc}") from exc
    if (not isinstance(data, dict) or data.get("version") != VERSION
            or not isinstance(data.get("places", {}), dict)
            or not isinstance(data.get("plac", {}), dict)):
        raise PlanError(f"{PLAN_PATH}: not a version {VERSION} places plan")
    plan = Plan()
    try:
        for key, raw in data.get("places", {}).items():
            plan.places[key] = PlannedPlace(
                key=key, title=raw["title"], place_type=raw["place_type"],
                parent=raw.get("parent", ""),
                aliases=list(raw.get("aliases", [])),
                reason=raw.get("reason", ""),
                status=raw.get("status", "proposed"),
                cr_id=raw.get("cr_id", ""), file=raw.get("file", ""))
        for plac, raw in data.get("plac", {}).items():
            plan.plac[plac] = PlacEntry(
                plac=plac, count=raw.get("count", 0),
                place=raw.get("place", ""),
                not_place=raw.get("not_place", ""),
                unidentified=raw.get("unidentified", ""),
                status=raw.get("status", "proposed"))
    except (KeyError, TypeError, AttributeError) as exc:
        raise PlanError(f"{PLAN_PATH}: malformed entry: {exc!r}") from exc
    return plan


def approved_targets(plan: Plan) -> dict[str, str]:
    """Approved PLAC key -> its target's identity: `cr_id`, else its file.

    A PLAC counts when its mapping and target place are both approved. The
    identity is what `places.Index` compares an alias hit against; it is empty
    for a target that has no note yet, which then accepts any hit.
    """
    out = {}
    for e in plan.plac.values():
        if e.status != "approved" or not e.place or e.not_place or e.unidentified:
            continue
        target = plan.places.get(e.place)
        if target is not None and target.status in {"approved", "created"}:
            out[places.key(e.plac)] = target.cr_id or target.file
    return out


def approved_placs(plan: Plan) -> set[str]:
    """Normalised PLAC keys whose mapping and target place are both approved."""
    return set(approved_targets(plan))


def count_placs(tree: gedcom.Tree) -> Counter:
    """How often each PLAC string occurs, one count per underlying event.

    A marriage can sit on the FAM and again on a spouse's INDI; the parser
    marks the INDI copy `folded` and has already moved its place onto the FAM
    event, so only the FAM event counts.
    """
    counts: Counter = Counter()
    for ind in tree.individuals.values():
        for ev in ind.events:
            if ev.place and not ev.folded:
                counts[ev.place] += 1
    for fam in tree.families.values():
        for ev in fam.events:
            if ev.place:
                counts[ev.place] += 1
    return counts


@dataclass
class ExtractResult:
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    resolved: list[str] = field(default_factory=list)


def _same_file(note, file: str, root: str) -> bool:
    if not file:
        return False
    want = os.path.normpath(os.path.join(root, file) if root else file)
    got = os.path.normpath(note.path)
    return got == want or (
        not root and not os.path.isabs(want) and got.endswith(os.sep + want))


def real_note(place: PlannedPlace, existing: list, root: str = ""):
    """The existing note a plan entry names, or None: by `cr_id`, then `file`.

    One answer for every status, so `check`, `assign_basenames`, `apply_plan`
    and `extract` agree on which entries already have a note.
    """
    if place.cr_id:
        for n in existing:
            if n.scalar("cr_id") == place.cr_id:
                return n
    if place.file:
        for n in existing:
            if _same_file(n, place.file, root):
                return n
    return None


def _record_note(plan: Plan, index: places.Index, note, root: str) -> str:
    """Record an existing Place note, and its ancestors, as created places.

    A note the plan already has an entry for (by `cr_id`, then `file`) keeps
    that entry's key; an entry is never overwritten.
    """
    chain = [note] + index.ancestors(note)
    keys, fresh = [], []
    for n in chain:
        found = next((k for k, p in plan.places.items()
                      if real_note(p, [n], root) is not None), None)
        if found is None:
            base = found = n.scalar("cr_id") or n.basename
            i = 2
            while found in plan.places or found in keys:
                found, i = f"{base} {i}", i + 1
            fresh.append(len(keys))
        keys.append(found)
    for i in fresh:
        n = chain[i]
        path = os.path.relpath(n.path, root) if root else n.path
        plan.places[keys[i]] = PlannedPlace(
            key=keys[i], title=n.scalar("title") or n.basename,
            place_type=n.scalar("place_type") or "",
            parent=keys[i + 1] if i + 1 < len(chain) else "",
            aliases=list(n.as_list("aliases")), status="created",
            cr_id=n.scalar("cr_id") or "", file=path.replace(os.sep, "/"))
    return keys[0]


def extract(plan: Plan, counts: Counter, index: places.Index,
            root: str = "") -> ExtractResult:
    """Fill the PLAC worklist from `counts`, never undoing a review.

    An existing entry only has its count refreshed (0 when the string left
    the export). A new string already found by the plugin's own lookups is
    recorded as approved against that note; a non-place is marked; the rest
    wait as proposed. `root` makes recorded file paths vault-relative.
    """
    res = ExtractResult()
    for plac, entry in plan.plac.items():
        n = counts.get(plac, 0)
        if entry.count != n:
            entry.count = n
            res.updated.append(plac)
    for plac, n in counts.items():
        if plac in plan.plac:
            continue
        entry = PlacEntry(plac=plac, count=n)
        note = index.find(plac)
        if note is not None:
            entry.place = _record_note(plan, index, note, root)
            entry.status = "approved"
            res.resolved.append(plac)
        else:
            entry.not_place = gedcom.non_place_reason(plac)
        plan.plac[plac] = entry
        res.added.append(plac)
    return res


# -- check ---------------------------------------------------------------


def _chain(plan: Plan, place: PlannedPlace) -> list[PlannedPlace]:
    """`place` and its ancestors, nearest first. Stops at a gap or a cycle."""
    out, seen, cur = [], set(), place
    while cur is not None and cur.key not in seen:
        out.append(cur)
        seen.add(cur.key)
        cur = plan.places.get(cur.parent) if cur.parent else None
    return out


def basename_for(place: PlannedPlace, plan: Plan, taken: set) -> str:
    """The note name: the title, else `title, parent`, then each ancestor.

    `taken` is compared case-insensitively, since the places folder may sit on
    a case-insensitive filesystem. A name that is still taken once the chain
    runs out gets a number.
    """
    low = {t.casefold() for t in taken}
    titles = [p.title for p in _chain(plan, place)]
    for n in range(1, len(titles) + 1):
        name = create.sanitise(", ".join(titles[:n]))
        if name.casefold() not in low:
            return name
    base, n = create.sanitise(", ".join(titles)), 2
    while f"{base} {n}".casefold() in low:
        n += 1
    return f"{base} {n}"


def _full_name(place: PlannedPlace, plan: Plan) -> str:
    return ", ".join(p.title for p in _chain(plan, place))


def render_note(place: PlannedPlace, plan: Plan, basenames: dict,
                cr_ids: dict) -> str:
    """The text of a new Place note. `basenames` and `cr_ids` are by plan key."""
    parent = plan.places.get(place.parent) if place.parent else None
    lines = ["---", "cr_type: place", f"cr_id: {cr_ids.get(place.key, '')}",
             f"title: {vault.quote(place.title)}",
             f"place_type: {vault.quote(place.place_type)}"]
    link = ""
    if parent is not None:
        link = f"[[{basenames.get(parent.key, parent.title)}]]"
        lines.append(f'parent_place: "{link}"')
        if cr_ids.get(parent.key):
            lines.append(f"parent_place_id: {cr_ids[parent.key]}")
    lines.append(f"full_name: {vault.quote(_full_name(place, plan))}")
    aliases = [a for a in place.aliases if isinstance(a, str)] \
        if isinstance(place.aliases, list) else []
    if aliases:
        lines.append("aliases:")
        lines.extend(f"  - {vault.quote(a)}" for a in aliases)
    lines.append("---")
    text = "\n".join(lines) + "\n"
    if link:
        text += f"**Part of:** {link}\n"
    return text


def _validate(plan: Plan, cfg: config.Config, existing: list) -> list[str]:
    problems = []
    types = config.PLACE_TYPES | cfg.custom_place_types
    reported = set()
    # Entries `extract` recorded from notes already in the vault describe the
    # vault as it is; the plan cannot fix them, so the type and duplicate-title
    # rules skip them.
    recorded = {k for k, p in plan.places.items() if p.status == "created"
                and real_note(p, existing, cfg.root) is not None}
    for key, p in plan.places.items():
        if p.status not in STATUSES:
            problems.append(f"{key}: unknown status {p.status!r}")
        if (not isinstance(p.aliases, list)
                or not all(isinstance(a, str) for a in p.aliases)):
            problems.append(f"{key}: aliases must be a list of strings")
        if p.place_type not in types and key not in recorded:
            problems.append(f"{key}: place_type {p.place_type!r} is not valid")
        if p.parent and p.parent not in plan.places:
            problems.append(f"{key}: parent {p.parent!r} not in plan")
        seen, cur = [], p
        while cur is not None and cur.key not in seen:
            seen.append(cur.key)
            cur = plan.places.get(cur.parent) if cur.parent else None
        if cur is not None:
            loop = seen[seen.index(cur.key):]
            if frozenset(loop) not in reported:
                reported.add(frozenset(loop))
                problems.append(
                    f"{key}: parent cycle {' -> '.join(loop + [cur.key])}")
    firsts: dict = {}
    for key, p in plan.places.items():
        if key in recorded:
            continue
        slot = (p.parent, places.key(p.title))
        if slot in firsts:
            problems.append(
                f"{key}: same title as {firsts[slot]!r} under parent "
                f"{p.parent or '(none)'!r}")
        else:
            firsts[slot] = key
    for plac, e in plan.plac.items():
        if e.status not in PLAC_STATUSES:
            problems.append(f"{plac}: unknown status {e.status!r}")
        if e.place and e.place not in plan.places:
            problems.append(f"{plac}: place {e.place!r} not in plan")
        if e.status == "approved" and not (e.not_place or e.unidentified):
            target = plan.places.get(e.place)
            if not e.place:
                problems.append(f"{plac}: approved, but maps to no place")
            elif target is not None and target.status not in {
                    "approved", "created"}:
                problems.append(
                    f"{plac}: approved, but place {e.place!r} is not approved")
    return problems


def assign_basenames(plan: Plan, existing: list, root: str = "") -> dict:
    """Plan key -> note basename, for every place in the plan.

    An entry whose note exists (see `real_note`) keeps that note's name, in
    any status; a created entry whose note is missing keeps its file's name.
    The rest are named in a fixed order, approved before proposed and
    otherwise in plan order, each taking a name no existing note or earlier
    place holds. `check` and `apply_plan` both call this, so the names they
    use cannot differ.
    """
    taken = {n.basename for n in existing}
    out = {}
    for key, p in plan.places.items():
        note = real_note(p, existing, root)
        if note is not None:
            out[key] = note.basename
        elif p.status == "created":
            out[key] = (os.path.splitext(os.path.basename(p.file))[0]
                        or p.title)
    pending = [k for k in plan.places if k not in out]
    pending.sort(key=lambda k: plan.places[k].status != "approved")
    for key in pending:
        out[key] = basename_for(plan.places[key], plan, taken)
        taken.add(out[key])
    return out


def _with_aliases(note, want: list):
    """An in-memory copy of `note` with the plan's aliases merged in."""
    if not isinstance(want, list):
        return note
    merged = _merged_aliases(note.as_list("aliases"), want)
    if merged == note.as_list("aliases"):
        return note
    copy = vault.parse_text(note.text(), note.path)
    try:
        copy.set("aliases", merged)
    except ValueError:
        return note
    return copy


def check(plan: Plan, cfg: config.Config, existing: list) -> list[str]:
    """Problems that must be fixed before `apply`; an empty list means OK.

    Never writes. The last test is the one that matters: every approved PLAC,
    looked up in the vault as it will be after `apply`, must land on its own
    planned Place and on no other.
    """
    problems = _validate(plan, cfg, existing)

    # Note names and ids: real where the entry has a note, simulated for the
    # rest. A real note is indexed with the plan's aliases overlaid, as it
    # will be once `apply` has added them.
    basenames = assign_basenames(plan, existing, cfg.root)
    taken_ids = {n.scalar("cr_id") for n in existing if n.scalar("cr_id")}
    taken_ids |= {p.cr_id for p in plan.places.values() if p.cr_id}
    cr_ids, real, fresh, pending = {}, {}, {}, []
    for key, p in plan.places.items():
        note = real_note(p, existing, cfg.root)
        if note is None:
            if p.status == "created":
                problems.append(f"{key}: created, but its note was not found")
            else:
                pending.append(key)
            continue
        cr_ids[key] = note.scalar("cr_id") or p.cr_id
        real[key] = (_with_aliases(note, p.aliases)
                     if p.status in {"approved", "created"} else note)
    for key in pending:
        cr_ids[key] = create.mint_cr_id(taken_ids)
    for key, p in plan.places.items():
        if p.status == "approved" and p.parent in plan.places and (
                plan.places[p.parent].status not in {"approved", "created"}):
            problems.append(
                f"{key}: approved, but parent {p.parent!r} is not")
    for key in pending:
        p = plan.places[key]
        if p.status == "approved":
            fresh[key] = vault.parse_text(
                render_note(p, plan, basenames, cr_ids),
                os.path.join(cfg.places, basenames[key] + ".md"))

    # A non-created place must not duplicate a note the plugin already sees.
    current = places.Index(list(existing))
    for key in pending:
        p = plan.places[key]
        hit = current.by_full_name.get(places.key(_full_name(p, plan)))
        how = "full_name"
        parent = plan.places.get(p.parent) if p.parent else None
        if hit is None and parent is not None:
            hit = current.by_title_parent.get(
                f"{places.key(p.title)}|{places.key(basenames[parent.key])}")
            how = "title and parent"
        if (hit is not None and p.cr_id
                and hit.scalar("cr_id") == p.cr_id):
            hit = None      # the note this entry itself names
        if hit is not None:
            problems.append(
                f"{key}: already exists as '{hit.basename}' (same {how})")

    # Every approved string must resolve to its own planned place. The index
    # gets the targets, as the sync does, so a hit on any other place is none.
    approved = approved_placs(plan)
    targets = approved_targets(plan)
    expected = {**real, **fresh}
    for plac, e in plan.plac.items():
        if places.key(plac) in approved and e.place in expected:
            note = expected[e.place]
            targets[places.key(plac)] = (cr_ids.get(e.place)
                                         or os.path.relpath(
                                             note.path, cfg.root))
    on_disk = {n.path: n for n in real.values()}
    notes = [on_disk.get(n.path, n) for n in existing] + list(fresh.values())
    index = places.Index(notes, approved=targets)
    loose = places.Index(notes, approved=approved)    # to name a wrong hit
    for plac, e in plan.plac.items():
        if places.key(plac) not in approved or e.place not in expected:
            continue
        want = expected[e.place]
        got = index.find(plac)
        if got is not want:
            other = loose.find(plac)
            where = f"'{other.basename}'" if other is not None else "no Place"
            problems.append(
                f"{plac}: resolves to {where}, not its planned place "
                f"{e.place!r} ('{want.basename}')")
    return problems


# -- apply ---------------------------------------------------------------


@dataclass
class ApplyResult:
    created: list[str] = field(default_factory=list)
    aliased: list[str] = field(default_factory=list)


def _merged_aliases(have: list, want: list) -> list:
    """`have`, then each of `want` not already there (case-insensitive)."""
    out, seen = list(have), {str(a).casefold() for a in have}
    for a in want:
        if isinstance(a, str) and a.casefold() not in seen:
            out.append(a)
            seen.add(a.casefold())
    return out


def apply_plan(plan: Plan, cfg: config.Config, dry: bool = True) -> ApplyResult:
    """Write the approved places, parents before children.

    A place whose `cr_id` names a note already in the places folder only gains
    the aliases it lacks, as does a `created` place whose note exists; any other approved place becomes a new note. A real
    run then records `status`, `cr_id` and `file` on each place it handled and
    saves the plan. Names come from `assign_basenames`, the same call `check`
    makes, so the files written are the ones `check` validated.
    """
    res = ApplyResult()
    existing = list(vault.iter_notes(cfg.places))
    basenames = assign_basenames(plan, existing, cfg.root)
    by_id = {n.scalar("cr_id"): n for n in existing if n.scalar("cr_id")}

    taken_ids = set(by_id)
    for folder in cfg.entity_folders.values():
        if folder != cfg.places:
            taken_ids |= {n.scalar("cr_id") for n in vault.iter_notes(folder)
                          if n.scalar("cr_id")}
    taken_ids |= {p.cr_id for p in plan.places.values() if p.cr_id}

    todo = [p for p in plan.places.values() if p.status == "approved"]
    # Stable, so plan order holds within a depth.
    todo.sort(key=lambda p: len(_chain(plan, p)))

    notes, cr_ids = {}, {}
    for key, p in plan.places.items():
        note = real_note(p, existing, cfg.root)
        if note is not None:
            notes[key] = note
            cr_ids[key] = note.scalar("cr_id") or p.cr_id
        elif p.status == "created" and p.cr_id:
            cr_ids[key] = p.cr_id
    for p in todo:
        if p.key not in notes:
            cr_ids[p.key] = create.mint_cr_id(taken_ids)

    def rel(path: str) -> str:
        return os.path.relpath(path, cfg.root).replace(os.sep, "/")

    def add_aliases(note, want) -> None:
        merged = _merged_aliases(note.as_list("aliases"), want)
        if merged != note.as_list("aliases"):
            res.aliased.append(rel(note.path))
            if not dry:
                note.set("aliases", merged)
                note.save()

    handled = {}
    for p in todo:
        if p.key in notes:
            add_aliases(notes[p.key], p.aliases)
            handled[p.key] = rel(notes[p.key].path)
        else:
            path = os.path.join(cfg.places, basenames[p.key] + ".md")
            res.created.append(rel(path))
            if not dry:
                vault.write_atomic(
                    path, render_note(p, plan, basenames, cr_ids))
            handled[p.key] = rel(path)

    # A created place whose note exists may have gained aliases in the plan.
    for p in plan.places.values():
        if p.status == "created" and p.key in notes:
            add_aliases(notes[p.key], p.aliases)

    if not dry and handled:
        for key, path in handled.items():
            place = plan.places[key]
            place.status, place.cr_id, place.file = "created", cr_ids[key], path
        save(cfg.root, plan)
    return res
