"""The reviewed plan that maps historical PLAC strings to modern Place notes.

The plan lives in the vault at `History/places-plan.json`, so the user can
review and edit it between runs. `places` holds the modern Place notes that
should exist, keyed by a plan key; `plac` maps each GEDCOM PLAC string to one
of them, or marks it as not a place or unidentified.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from . import places, vault

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
