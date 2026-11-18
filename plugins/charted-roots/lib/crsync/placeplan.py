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

from . import gedcom, places, vault

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


def approved_placs(plan: Plan) -> set[str]:
    """Normalised PLAC keys whose mapping and target place are both approved."""
    out = set()
    for e in plan.plac.values():
        if e.status != "approved" or not e.place or e.not_place or e.unidentified:
            continue
        target = plan.places.get(e.place)
        if target is not None and target.status in {"approved", "created"}:
            out.add(places.key(e.plac))
    return out


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


def _record_note(plan: Plan, index: places.Index, note, root: str) -> str:
    """Record an existing Place note, and its ancestors, as created places."""
    chain = [note] + index.ancestors(note)
    keys = [n.scalar("cr_id") or n.basename for n in chain]
    for i, n in enumerate(chain):
        if keys[i] in plan.places:
            continue
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
