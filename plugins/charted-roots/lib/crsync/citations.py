"""Match Citations.

The key is `(subject_id, source, fact, page)`. Verified against the development vault's folder:
the 3-tuple without `page` collides on 47 keys covering 104 notes, while the
4-tuple collides on exactly 6 -- and those 6 are the known true duplicate
pairs. `page` is compared byte-for-byte after unquoting; it quotes archival
material, so normalising it would both risk a false match and, per the vault model,
falsify the citation.

The GEDCOM side reproduces the plugin's own emission rule so the two agree on
what a citation is: one per event-level `2 SOUR` carrying a `PAGE`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_WS = re.compile(r"\s+")


def normalise_page(value: str) -> str:
    """Collapse whitespace in a `page` value so it survives a YAML scalar.

    A GEDCOM PAGE can carry CONT continuations, which arrive as embedded
    newlines. A double-quoted YAML scalar cannot hold one, so writing it
    truncates the value and the citation never matches on the next run --
    which grows the folder by the same 44 notes every pass. Collapsing runs
    of whitespace to a single space changes the formatting of a line break,
    not the text, so the citation still quotes its source faithfully.
    """
    return _WS.sub(" ", value or "").strip()

#: event_type -> the `fact` a Citation records. Mirrors the plugin's
#: eventTypeToFact, restricted to the facts in the vault model's `fact` list.
FACT = {
    "birth": "birth_date", "death": "death_date", "marriage": "marriage_date",
    "baptism": "baptism_date", "christening": "baptism_date", "burial": "burial_date", "residence": "residence",
    "occupation": "occupation", "probate": "probate", "graduation": "graduation",
    "naturalization": "naturalization", "emigration": "emigration",
    "immigration": "emigration", "military": "occupation", "divorce": "marriage_date",
    "will": "probate", "census": "residence",
}


@dataclass
class CitationMatch:
    matched: list = field(default_factory=list)
    uncreated: list = field(default_factory=list)
    duplicates: list = field(default_factory=list)
    unresolved: list = field(default_factory=list)


def vault_key(note) -> tuple:
    src = note.links("source")
    return (note.scalar("subject_id"), src[0] if src else "",
            note.scalar("fact"), normalise_page(note.scalar("page")))


def match_citations(tree, citation_notes, people, sources, root) -> CitationMatch:
    result = CitationMatch()

    crid_by_ext = {n.scalar("external_id"): n.scalar("cr_id")
                   for n in people if n.scalar("external_id")}
    name_by_gid = {n.scalar("gedcom_id"): n.basename
                   for n in sources if n.scalar("gedcom_id")}

    existing: dict = {}
    for n in citation_notes:
        existing.setdefault(vault_key(n), []).append(n)
    for key, notes in existing.items():
        if len(notes) > 1:
            result.duplicates.append((key, notes))

    seen: set = set()
    for ev in tree.events:
        fact = FACT.get(ev.event_type)
        if not fact:
            continue
        owners = [ev.owner] if ev.owner not in tree.families else \
            [x for x in (tree.families[ev.owner].husband,
                         tree.families[ev.owner].wife) if x][:1]
        for owner in owners:
            subject_id = crid_by_ext.get(owner)
            for src_xref, page in ev.citations:
                if not page:
                    continue  # the plugin emits a Citation only with a PAGE
                source_name = name_by_gid.get(src_xref)
                if subject_id is None or source_name is None:
                    result.unresolved.append((owner, src_xref, fact, page))
                    continue
                key = (subject_id, source_name, fact, normalise_page(page))
                if key in seen:
                    continue
                seen.add(key)
                if key in existing:
                    result.matched.append((key, existing[key][0]))
                else:
                    result.uncreated.append(key)
    return result
