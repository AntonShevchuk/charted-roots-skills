"""Rulings the user has made on individual held changes, kept as data.

`coarsen` and `conflict` changes are held back by default, because applying
them would revert curated work. A few have been reviewed and accepted anyway.
Each such ruling is a *run record*, not a method: it names one person, one
field and one reason, it accumulates as the tree is worked on, and it is
exactly what the vault model says belongs in `History/` rather than in the tool.
Accepting one more conflict is then a data edit, and the reason travels with
it instead of living in a code comment.

The file is optional. With no file, nothing is accepted and every coarsen and
conflict stays held -- the safe direction.

    History/gedcom-sync-decisions.json

    {
      "decisions": [
        {
          "external_id": "I100000000001",
          "label": "Johann Example",
          "accept_conflict": ["name", "surnames"],
          "reason": "The register spells it without the umlaut.",
          "decided_by": "user",
          "date": "2026-09-21"
        }
      ]
    }

`external_id` is the join key on purpose: a rename cannot detach a ruling from
the person it was made about. Several people have a second, unresolved
disagreement, so acceptance is per field and never per person.

Two entries may name the same person -- one ruling per occasion is the point,
and their fields are unioned. A single dict keyed by external_id cannot do
that: a repeated key silently discards the earlier entry and its reason.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

#: Under `History/`, beside the Event -> GEDCOM sidecar.
FILENAME = "gedcom-sync-decisions.json"

_ENTRY_KEYS = {"external_id", "label", "accept_coarsen", "accept_conflict",
               "reason", "decided_by", "date"}
_ACCEPT_KEYS = ("accept_coarsen", "accept_conflict")


class DecisionsError(Exception):
    """The file exists but cannot be trusted. Never fall back to empty.

    Empty means "accept nothing", which is safe; but silently treating an
    unreadable file as empty would revert every accepted ruling on the next
    run, which reads as the tool changing its mind.
    """


@dataclass
class Decisions:
    path: str = ""
    entries: list = field(default_factory=list)
    #: external_id -> {field}, unioned across entries
    coarsen_exempt: dict = field(default_factory=dict)
    conflict_accepted: dict = field(default_factory=dict)
    #: external_ids ruled on by more than one entry, for the report
    repeated: list = field(default_factory=list)

    @property
    def rel_path(self) -> str:
        return os.path.join("History", FILENAME)

    def counts(self) -> tuple:
        return (sum(len(v) for v in self.coarsen_exempt.values()),
                sum(len(v) for v in self.conflict_accepted.values()))


def _fail(path: str, detail: str) -> None:
    raise DecisionsError(f"{path}: {detail}")


def _check_entry(path: str, i: int, entry) -> None:
    where = f"decisions[{i}]"
    if not isinstance(entry, dict):
        _fail(path, f"{where} is not an object")
    unknown = sorted(set(entry) - _ENTRY_KEYS)
    if unknown:
        _fail(path, f"{where} has unknown keys {unknown}; "
                    f"allowed: {sorted(_ENTRY_KEYS)}")
    xref = entry.get("external_id")
    if not isinstance(xref, str) or not xref.strip():
        _fail(path, f"{where} needs a non-empty external_id")
    for key in _ACCEPT_KEYS:
        value = entry.get(key, [])
        if not isinstance(value, list) or not all(
                isinstance(f, str) and f.strip() for f in value):
            _fail(path, f"{where} {key} must be a list of field names")
    if not any(entry.get(key) for key in _ACCEPT_KEYS):
        _fail(path, f"{where} ({xref}) accepts nothing -- "
                    f"give it accept_coarsen or accept_conflict, or delete it")
    reason = entry.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        _fail(path, f"{where} ({xref}) has no reason. Every ruling needs one: "
                    f"it is the only record of why the vault's own value lost")


def load(root: str) -> Decisions:
    """Read the decisions file under `root`. A missing file accepts nothing."""
    path = os.path.join(root, "History", FILENAME)
    out = Decisions(path=path)
    if not os.path.exists(path):
        return out
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, ValueError) as exc:
        _fail(path, str(exc))
    if not isinstance(raw, dict) or not isinstance(raw.get("decisions"), list):
        _fail(path, 'expected an object with a "decisions" list')

    seen: set = set()
    for i, entry in enumerate(raw["decisions"]):
        _check_entry(path, i, entry)
        xref = entry["external_id"].strip()
        if xref in seen:
            out.repeated.append(xref)
        seen.add(xref)
        for key, target in (("accept_coarsen", out.coarsen_exempt),
                            ("accept_conflict", out.conflict_accepted)):
            fields = {f.strip() for f in entry.get(key, [])}
            if fields:
                target.setdefault(xref, set()).update(fields)
        out.entries.append(entry)
    return out
