"""Join a parsed GEDCOM against the vault.

Produces a Plan of actions; nothing here writes. The join keys are the ones
the plugin already stores but never reads back:

    Person  external_id  <-> INDI xref
    Source  gedcom_id    <-> SOUR xref

Both are stable across Ancestry re-exports, which is what makes a repeated
import safe. Events have no such key and are handled in `events.py`.
"""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass, field

from . import dates, gedcom, vault

#: Person fields the importer owns. Everything else on a Person note --
#: citations, media, aliases, group_name, the body -- is vault-only and is
#: never written by a sync.
PERSON_OWNED = ["name", "given_name", "surnames", "name_suffix", "sex",
                "born", "died"]
#: Source fields the importer owns. Not `confidence`, `source_type`,
#: `source_parent`, `source_date` or `media` -- those are curated in the vault.
SOURCE_OWNED = ["title", "author", "repository"]

SEX = {"M": "M", "F": "F"}


#: How a single field disagrees. "GEDCOM wins" is only obviously right for
#: `fill` and `refine`; the others need a policy, because Ancestry's export
#: normalises casing and drops qualifiers the vault curates deliberately.
FILL = "fill"          # vault empty, GEDCOM has a value
CASE = "case"          # differ only by letter case (von/Von)
REFINE = "refine"      # GEDCOM strictly more precise
COARSEN = "coarsen"    # vault strictly more precise; applying would lose data
CONFLICT = "conflict"  # genuinely different values
VARIANT = "variant"    # the export carries the vault's form as an alternate
FORMAT = "format"      # same date, respelt into the form the plugin validates


def _as_text(value) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value or "")


def _classify_date(o: str, n: str) -> str:
    """`born` / `died`: compare what the two values mean, not how they read.

    Pure respellings (`ABT 1804` -> `c. 1804`, `1850-1858` -> `1850 to 1858`,
    `25 Dez 1914` -> `1914-12-25`) and the deliberate `BEF` / `AFT` drop are
    `format`: safe, nothing is lost that the Event does not keep.
    """
    mo, mn = dates.meaning(o), dates.meaning(n)
    if mo is None or mn is None:
        return CONFLICT
    if mo == mn:
        return FORMAT
    (qo, so, eo), (qn, sn, en) = mo, mn
    if qo in ("BEF", "AFT") and not qn and (so, eo) == (sn, en):
        return FORMAT
    if eo or en:
        return CONFLICT
    if qo == "ABT" and not qn and so == sn:
        # `c. 1820` -> `1820` drops a curated qualifier.
        return COARSEN
    if qo == qn or (qo in ("BEF", "AFT") and not qn):
        if sn.startswith(so) and len(sn) > len(so):
            return REFINE     # 1884 -> 1884-05
        if so.startswith(sn) and len(so) > len(sn):
            return COARSEN
    return CONFLICT


def classify(field_name: str, old, new) -> str:
    o, n = _as_text(old).strip(), _as_text(new).strip()
    if not o:
        return FILL
    if o == n:
        return ""
    if field_name in ("born", "died"):
        return _classify_date(o, n)
    if field_name == "date" and dates.meaning(o) is not None \
            and dates.meaning(o) == dates.meaning(n):
        return FORMAT     # an Event date respelt: `15 Okt 1795` -> `1795-10-15`
    if o.lower() == n.lower():
        return CASE
    if n.startswith(o) or (o in n and len(n) > len(o)):
        return REFINE
    if o.startswith(n) or (n in o and len(o) > len(n)):
        return COARSEN
    return CONFLICT


@dataclass
class Change:
    field: str
    old: object
    new: object
    kind: str = ""

    def __post_init__(self):
        if not self.kind:
            self.kind = classify(self.field, self.old, self.new)

    def __iter__(self):
        return iter((self.field, self.old, self.new))

    def __str__(self) -> str:
        return f"{self.field} [{self.kind}]: {_as_text(self.old)!r} -> {_as_text(self.new)!r}"


@dataclass
class Action:
    kind: str          #: create | update | match | orphan | ambiguous
    entity: str        #: person | source | event | citation | place
    key: str           #: the GEDCOM xref, or the vault basename
    label: str = ""
    path: str = ""
    changes: list = field(default_factory=list)   #: (field, old, new)
    note: str = ""

    def __str__(self) -> str:
        head = f"{self.label or self.key}"
        if self.changes:
            return f"{head} -- " + "; ".join(str(c) for c in self.changes)
        return head + (f" -- {self.note}" if self.note else "")


@dataclass
class Plan:
    actions: list = field(default_factory=list)

    def add(self, action: Action) -> None:
        self.actions.append(action)

    def of(self, entity: str, kind: str | None = None) -> list:
        return [a for a in self.actions
                if a.entity == entity and (kind is None or a.kind == kind)]

    def counts(self, entity: str) -> dict:
        out: dict = {}
        for a in self.of(entity):
            out[a.kind] = out.get(a.kind, 0) + 1
        return out


def person_projection(ind: gedcom.Individual) -> dict:
    """The importer-owned fields a Person note should carry for this INDI."""
    out: dict = {"name": ind.name.strip()}
    if ind.alt_names:
        # Not a field; carried so _compare can tell an alternate spelling
        # apart from a genuine disagreement.
        out["_alt_names"] = list(ind.alt_names)
    if ind.given:
        out["given_name"] = ind.given
    if ind.surname:
        out["surnames"] = [s.strip() for s in ind.surname.split(",") if s.strip()]
    if ind.suffix:
        out["name_suffix"] = ind.suffix
    if ind.sex in SEX:
        out["sex"] = SEX[ind.sex]

    # The Person carries the form the plugin's date validator accepts
    # (`born: c. 1804`, `1850 to 1858`, `BEF` dropped); the Event keeps
    # `date: 1804` + `date_precision: estimated`, or `BEF 1909`. A date with
    # no clean form is left off rather than written unreadable.
    for tag, key in (("birth", "born"), ("death", "died")):
        ev = next((e for e in ind.events if e.event_type == tag), None)
        form = dates.person_form(ev.date) if ev is not None else ""
        if form:
            out[key] = form
    return out


def source_projection(src: gedcom.SourceRec) -> dict:
    out = {"title": src.title.strip()}
    if src.author:
        out["author"] = src.author.strip()
    if src.publisher:
        # The plugin fills `repository` from PUBL, not REPO. Keep that, so a
        # sync does not fight the notes the plugin already wrote.
        out["repository"] = src.publisher.strip()
    return out


def alias_backfill(note: vault.Note, ind: gedcom.Individual) -> list | None:
    """Every name form the export knows, minus the one the vault displays.

    The vault keeps its own `name` as the display form; the export's primary
    (Ancestry's maiden name) and any other alternate go into `aliases:` so the
    form a record used stays searchable (the upstream-ancestry
    convention) -- and `aliases` has no GEDCOM representation on export, so nothing
    else will ever put them there.

    Returns the merged list, or None when it already matches. Existing entries
    are kept and stay in front; the one thing this removes is an alias that
    has become identical to the display name, which happens when a name is
    corrected after the alias was recorded.
    """
    display = namekey(note.scalar("name"))
    have = [a for a in note.as_list("aliases") if namekey(a) != display]
    seen = {namekey(a) for a in have}
    merged = list(have)
    for candidate in [ind.name, *ind.alt_names]:
        key = namekey(candidate)
        if not key or key == display or key in seen:
            continue
        seen.add(key)
        merged.append(candidate.strip())
    return merged if merged != note.as_list("aliases") else None


def _compare(note: vault.Note, projection: dict, owned: list) -> list:
    changes = []
    alts = projection.get("_alt_names") or []
    for key in owned:
        if key not in projection:
            continue
        want = projection[key]
        have = note.as_list(key) if isinstance(want, list) else note.get(key)
        if _as_text(have) == _as_text(want):
            continue
        if key in ("name", "given_name", "surnames") and alts:
            # Ancestry's surname field holds the maiden name and keeps married
            # and alternate forms as separate NAME blocks or an AKA fact, so
            # the vault holding the other form is the convention working, not
            # a disagreement. the upstream-ancestry convention.
            current = _as_text(have).casefold()
            folded = [a.casefold() for a in alts]
            if any(current == a for a in folded):
                continue
            if current and any(current in a for a in folded):
                changes.append(Change(key, have, want, kind=VARIANT))
                continue
        changes.append(Change(key, have, want))
    return changes


def namekey(s: str) -> str:
    """NFC-normalised, casefolded. Never NFKD -- that decomposes Cyrillic."""
    return unicodedata.normalize("NFC", (s or "").strip()).casefold()


def _birth_year(value: str) -> str:
    v = str(value or "")
    for token in v.replace("ABT", " ").replace("BEF", " ").replace("AFT", " ").split():
        if len(token) >= 4 and token[:4].isdigit():
            return token[:4]
    return ""


def _tokens(text: str) -> set:
    """Name words long enough to be distinctive, NFC and casefolded."""
    folded = unicodedata.normalize("NFC", text or "").casefold()
    return {w for w in re.split(r"[^\w]+", folded) if len(w) > 2}


def find_adoptions(tree: gedcom.Tree, people: list, matched: set) -> list:
    """Unmapped INDI that look like an existing vault-native Person note.

    The user researches a person here first and adds them upstream later, so
    an INDI with no `external_id` counterpart is not automatically new. These
    notes carry prose and citations; creating a second one for the same person
    is the duplication this whole script exists to prevent.

    An exact name match is not enough on its own. The same person is recorded
    `Олександр Семенович Прикладенко` here and `Александр Семенович Прикладенко`
    upstream, or `Erik Holm (Vestby)` against `Erik Holm Lund, Vestby`,
    so a name-equality test misses them and creation duplicates the note. A
    shared birth date plus an overlapping distinctive name word catches those.

    Every hit is a *candidate*, never an automatic match: a same-date pair can
    also be twins, which is why the sex mismatch is reported rather than
    silently resolved.
    """
    native = [n for n in people if not n.scalar("external_id")]
    by_name: dict = {}
    for n in native:
        for key in {namekey(n.scalar("name")), namekey(n.basename)}:
            if key:
                by_name.setdefault(key, []).append(n)

    out = []
    for xref, ind in sorted(tree.individuals.items()):
        if xref in matched:
            continue
        ged_birth = next((e.date for e in ind.events if e.event_type == "birth"), "")
        ged_tokens = _tokens(ind.name) | _tokens(ind.given) | _tokens(ind.surname)
        seen: dict = {}

        for cand in by_name.get(namekey(ind.name), []):
            seen[cand.path] = (cand, ["name matches exactly"])

        for cand in native:
            if cand.path in seen:
                continue
            vault_birth = cand.scalar("born")
            if not (ged_birth and vault_birth):
                continue
            shared = ged_tokens & (
                _tokens(cand.scalar("name")) | _tokens(cand.basename)
                | _tokens(" ".join(cand.as_list("surnames")))
                | _tokens(" ".join(cand.as_list("aliases"))))
            if not shared:
                continue
            exact = dates.meaning(ged_birth) == dates.meaning(vault_birth)
            same_year = _birth_year(ged_birth) == _birth_year(vault_birth)
            if exact:
                why = [f"birth exact ({vault_birth})"]
            elif same_year and len(shared) >= 2:
                why = [f"birth year ({vault_birth} / {ged_birth})"]
            else:
                continue
            why.append("shares " + ", ".join(sorted(shared)))
            seen[cand.path] = (cand, why)

        for cand, why in seen.values():
            ged_sex = ind.sex if ind.sex in ("M", "F") else ""
            vault_sex = cand.scalar("sex")
            if ged_sex and vault_sex and ged_sex != vault_sex:
                why.append(f"SEX DIFFERS ({vault_sex} vs {ged_sex}) -- "
                           f"possibly twins, not the same person")
            if cand.as_list("citations"):
                why.append(f"{len(cand.as_list('citations'))} citations")
            out.append((xref, ind, cand, why))
    return out


#: Person place fields, and the GEDCOM event each summarises.
PERSON_PLACES = {"birth_place": "birth", "death_place": "death"}


def _place_changes(note: vault.Note, ind: gedcom.Individual, place_index) -> list:
    """Held changes where the export names another place than the vault.

    Only a disagreement is reported -- an empty vault field is left for
    creation to fill -- and `new` is a wikilink only when the PLAC resolves,
    so an accepted ruling can never write raw PLAC text into the field.
    """
    if place_index is None:
        return []
    changes = []
    for field_name, event_type in PERSON_PLACES.items():
        have = note.scalar(field_name)
        ev = next((e for e in ind.events if e.event_type == event_type), None)
        if not have or ev is None or not ev.place:
            continue
        kind = place_index.compare(have, ev.place)
        if kind:
            resolved = place_index.find(ev.place)
            new = f"[[{resolved.basename}]]" if resolved is not None else ev.place
            changes.append(Change(field_name, have, new, kind=kind))
    return changes


def match_people(tree: gedcom.Tree, people: list, root: str,
                 adopt: bool = False, place_index=None) -> Plan:
    plan = Plan()
    by_ext: dict = {}
    for n in people:
        ext = n.scalar("external_id")
        if ext:
            by_ext.setdefault(ext, []).append(n)

    adoptions = {}
    for xref, ind, cand, why in find_adoptions(tree, people, set(by_ext)):
        adoptions.setdefault(xref, []).append((ind, cand, why))

    for ext, notes in sorted(by_ext.items()):
        if len(notes) > 1:
            plan.add(Action("ambiguous", "person", ext,
                            label=", ".join(n.basename for n in notes),
                            note="several notes share this external_id"))

    for xref, ind in sorted(tree.individuals.items()):
        notes = by_ext.get(xref)
        if not notes and xref in adoptions:
            cands = adoptions[xref]
            if len(cands) == 1 and adopt:
                _, cand, why = cands[0]
                changes = [Change("external_id", None, xref),
                           Change("external_id_source", None, "gedcom")]
                changes += _compare(cand, person_projection(ind), PERSON_OWNED)
                changes += _place_changes(cand, ind, place_index)
                plan.add(Action("adopt", "person", xref, label=cand.basename,
                                path=os.path.relpath(cand.path, root), changes=changes,
                                note="; ".join(why)))
            else:
                plan.add(Action("candidate", "person", xref, label=ind.name,
                                path=", ".join(os.path.relpath(c.path, root) for _, c, _ in cands),
                                note="matches a vault-native note by name -- "
                                     + "; ".join(cands[0][2])
                                     + "; needs --adopt-by-name after review"))
            continue
        if not notes:
            plan.add(Action("create", "person", xref, label=ind.name or "(unnamed)",
                            changes=[Change(k, None, v) for k, v in person_projection(ind).items()]))
            continue
        note = notes[0]
        changes = _compare(note, person_projection(ind), PERSON_OWNED)
        changes += _place_changes(note, ind, place_index)
        merged = alias_backfill(note, ind)
        if merged is not None:
            changes.append(Change("aliases", note.as_list("aliases"), merged, kind=FILL))
        kind = "update" if changes else "match"
        plan.add(Action(kind, "person", xref, label=note.basename,
                        path=os.path.relpath(note.path, root), changes=changes))

    for ext, notes in sorted(by_ext.items()):
        if ext not in tree.individuals:
            plan.add(Action("orphan", "person", ext, label=notes[0].basename,
                            path=os.path.relpath(notes[0].path, root),
                            note="external_id not present upstream; never deleted"))
    return plan


def match_sources(tree: gedcom.Tree, sources: list, root: str) -> Plan:
    plan = Plan()
    by_gid: dict = {}
    for n in sources:
        gid = n.scalar("gedcom_id")
        if not gid:
            # The body keeps `_Imported from GEDCOM source S…_`, so a stripped
            # frontmatter key is still recoverable.
            for line in n.body.splitlines():
                if line.startswith("_Imported from GEDCOM source "):
                    gid = line[len("_Imported from GEDCOM source "):].strip(" _;").split(";")[0]
                    break
        if gid:
            by_gid.setdefault(gid, []).append(n)

    for gid, notes in sorted(by_gid.items()):
        if len(notes) > 1:
            plan.add(Action("ambiguous", "source", gid,
                            label=", ".join(n.basename for n in notes),
                            note="several notes share this gedcom_id"))

    for xref, src in sorted(tree.sources.items()):
        notes = by_gid.get(xref)
        if not notes:
            plan.add(Action("create", "source", xref, label=src.title or "(untitled)",
                            changes=[Change(k, None, v) for k, v in source_projection(src).items()]))
            continue
        note = notes[0]
        changes = _compare(note, source_projection(src), SOURCE_OWNED)
        plan.add(Action("update" if changes else "match", "source", xref,
                        label=note.basename, path=os.path.relpath(note.path, root),
                        changes=changes))

    for gid, notes in sorted(by_gid.items()):
        if gid not in tree.sources:
            plan.add(Action("orphan", "source", gid, label=notes[0].basename,
                            path=os.path.relpath(notes[0].path, root),
                            note="gedcom_id not present upstream; never deleted"))
    return plan
