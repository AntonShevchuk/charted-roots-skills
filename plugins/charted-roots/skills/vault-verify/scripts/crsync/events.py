"""Match vault Events to GEDCOM event blocks.

Events are the hard case: nothing on an Event note links it to the GEDCOM.
The durable key this module assigns is positional --

    <owner xref>:<TAG>:<ordinal>

-- where the owner is the INDI xref, or for a shared event the couple's two
INDI xrefs joined, so a marriage is one key and therefore one Event with two
`persons:` rather than one per spouse. The FAM xref is deliberately *not*
used: Ancestry renumbers FAM xrefs when a family is inserted (verified --
adding one family shifted 41 of 131), while INDI xrefs are stable. The ordinal is the 0-based index among level-1 blocks
with the same tag on that record, in file order.

Bootstrapping that key onto the existing unkeyed Events is a cascade, each
stage claiming only unambiguous 1:1 pairs:

  1. content      -- (owner, event_type, date), unless the places contradict
  2. corroborated -- within (owner, event_type): a compatible date plus an
                     agreeing place, or an exact date, taken as mutual best
                     matches
  3. positional   -- what is left, when both sides have the same number of
                     entries and no pair's dates contradict
  4. unkeyed      -- reported, never guessed

Order alone is not evidence. Residences in particular are curated here --
dates widened to ranges, occurrences added from other documents -- so the
vault's filename order drifts from the export's, and zipping the two paired
each Event with another occurrence's date. A group whose dates contradict is
left unpaired: the vault side stays unkeyed, the export side becomes a
creation candidate, which is what two genuinely different sets are.

`place` corroborates and vetoes but never keys on its own. Most GEDCOM PLAC
strings resolve to no Place note, because upstream records historical and
native forms (`Deutschland`, `Preußen`, `Danmark`) against an English
gazetteer, so they are compared by name (`places.Index.compare`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import gedcom, places

_SEQ_SUFFIX = re.compile(r'-(\d+)$')


def ged_key(ev: gedcom.Event) -> str:
    if ev.couple:
        # Keyed on the couple, not the FAM xref: Ancestry renumbers FAM xrefs
        # when a family is inserted, but INDI xrefs are stable.
        owner = "+".join(ev.couple)
        return f"{owner}:{ev.tag}:{ev.ordinal}"
    if ev.tag == "EVEN":
        slug = re.sub(r'[^a-z0-9]+', '-', (ev.even_type or "").lower()).strip('-')[:24]
        return f"{ev.owner}:EVEN/{slug}:{ev.ordinal}"
    return f"{ev.owner}:{ev.tag}:{ev.ordinal}"


def filename_ordinal(basename: str) -> int:
    """`Residence of X-2` -> 2; the unsuffixed base sorts first.

    A trailing `-N` is a sequence number, not a duplicate marker, and encodes
    the document order the import saw.
    """
    m = _SEQ_SUFFIX.search(basename)
    return int(m.group(1)) if m else 0


@dataclass
class Pair:
    vault_note: object = None
    ged_event: object = None
    stage: str = ""
    key: str = ""
    note: str = ""


@dataclass
class EventMatch:
    pairs: list = field(default_factory=list)
    unkeyed: list = field(default_factory=list)      # vault Events with no GEDCOM block
    uncreated: list = field(default_factory=list)    # GEDCOM blocks with no vault Event
    arbitrary: list = field(default_factory=list)    # indistinguishable, assigned in order

    def counts(self) -> dict:
        out: dict = {}
        for p in self.pairs:
            out[p.stage] = out.get(p.stage, 0) + 1
        out["unkeyed"] = len(self.unkeyed)
        out["uncreated"] = len(self.uncreated)
        return out


def _owner_people(ev: gedcom.Event, tree: gedcom.Tree) -> set:
    """The INDI xrefs a GEDCOM event concerns."""
    if ev.owner in tree.families:
        fam = tree.families[ev.owner]
        return {x for x in (fam.husband, fam.wife) if x}
    return {ev.owner}


def match_events(tree: gedcom.Tree, event_notes: list, people: list,
                 place_index: places.Index, root: str) -> EventMatch:
    result = EventMatch()

    ext_by_basename = {n.basename: n.scalar("external_id") for n in people}

    # -- vault side: group by (participant external_id, event_type)
    vault_groups: dict = {}
    for note in event_notes:
        et = note.scalar("event_type")
        owners = {ext_by_basename.get(p) for p in note.links("persons")}
        owners.discard(None)
        owners.discard("")
        if not owners:
            result.unkeyed.append((note, "no participant carries an external_id"))
            continue
        for owner in owners:
            vault_groups.setdefault((owner, et), []).append(note)
    for group in vault_groups.values():
        group.sort(key=lambda n: filename_ordinal(n.basename))

    # -- GEDCOM side: the same grouping, one entry per participant
    ged_groups: dict = {}
    for ev in tree.events:
        if not ev.event_type or ev.folded:
            continue
        for owner in _owner_people(ev, tree):
            ged_groups.setdefault((owner, ev.event_type), []).append(ev)
    for group in ged_groups.values():
        group.sort(key=lambda e: (e.ordinal, e.date))

    claimed_notes: set = set()
    claimed_ged: set = set()

    def claim(note, ev, stage, note_text=""):
        claimed_notes.add(note.path)
        claimed_ged.add(ged_key(ev))
        result.pairs.append(Pair(note, ev, stage, ged_key(ev), note_text))

    def unclaimed(key, gevents):
        return ([n for n in vault_groups.get(key, []) if n.path not in claimed_notes],
                [e for e in gevents if ged_key(e) not in claimed_ged])

    def by_content(veto_place: bool) -> None:
        for key, gevents in ged_groups.items():
            vnotes, gremain = unclaimed(key, gevents)
            by_date_v: dict = {}
            by_date_g: dict = {}
            for n in vnotes:
                by_date_v.setdefault(n.scalar("date"), []).append(n)
            for e in gremain:
                by_date_g.setdefault(event_date(e), []).append(e)
            for date, ns in by_date_v.items():
                es = by_date_g.get(date, [])
                if len(ns) != 1 or len(es) != 1:
                    continue
                if veto_place and _place_score(ns[0], es[0], place_index) < 0:
                    continue
                claim(ns[0], es[0], "content")

    # -- stage 1: content, 1:1 on date. A contradicting place only defers the
    #    pair: the same date at another place is often another occurrence
    #    that stage 2 pairs better, and otherwise the second pass takes it.
    by_content(veto_place=True)

    # -- stage 2: corroborated, mutual best matches on date and place
    for key, gevents in ged_groups.items():
        vnotes, gremain = unclaimed(key, gevents)
        for n, e, tied in _mutual_best(vnotes, gremain, place_index):
            claim(n, e, "corroborated")
            if tied:
                result.arbitrary.append((n, ged_key(e)))
    by_content(veto_place=False)

    # -- stage 3: positional, only when the counts agree and no date
    #    contradicts -- except for an event a person has once, where a 1:1
    #    remainder is the same event and a date difference is a conflict to
    #    report, not a second occurrence to create.
    for key, gevents in ged_groups.items():
        vnotes, gremain = unclaimed(key, gevents)
        if not vnotes or not gremain or len(vnotes) != len(gremain):
            continue
        once = key[1] in ONCE_TYPES and len(vnotes) == 1
        if not once and any(_date_score(n.scalar("date"), event_date(e)) is None
                            for n, e in zip(vnotes, gremain)):
            continue
        indistinguishable = len({(n.scalar("date"), n.scalar("place")) for n in vnotes}) == 1 \
            and len(vnotes) > 1
        for n, e in zip(vnotes, gremain):
            claim(n, e, "positional")
            if indistinguishable:
                result.arbitrary.append((n, ged_key(e)))

    # -- whatever is left
    for key, vnotes in vault_groups.items():
        for n in vnotes:
            if n.path not in claimed_notes and not any(
                    p.vault_note is n for p in result.pairs):
                result.unkeyed.append((n, "no GEDCOM block for this person and type"))
    seen_unkeyed = set()
    result.unkeyed = [u for u in result.unkeyed
                      if not (u[0].path in seen_unkeyed or seen_unkeyed.add(u[0].path))]

    for ev in tree.events:
        if ev.event_type and not ev.folded and ged_key(ev) not in claimed_ged:
            result.uncreated.append(ev)
    # one entry per block, not per participant
    seen = set()
    result.uncreated = [e for e in result.uncreated
                        if not (ged_key(e) in seen or seen.add(ged_key(e)))]
    return result


_YEAR = re.compile(r"\b(\d{4})\b")

#: Event types a person has at most once. For a marriage the owner is the
#: couple, so it is once per couple.
ONCE_TYPES = {"birth", "death", "burial", "marriage"}

#: The least score a stage-2 pair needs: an exact date, or a compatible date
#: with the place agreeing. A year alone is a guess. An agreeing place alone
#: is enough where one side has no date at all -- there is nothing to
#: contradict it, and the mutual-best rule still refuses a tie.
_CORROBORATED = 3


def _span(date) -> tuple | None:
    """(first, last) year a date covers, or None when it names no year."""
    text = str(date or "").strip()
    years = [int(y) for y in _YEAR.findall(text)]
    if not years:
        return None
    if text.upper().startswith("BEF"):
        return (0, years[0])
    if text.upper().startswith("AFT"):
        return (years[0], 9999)
    return (min(years), max(years))


def _date_score(vault_date, ged_date) -> int | None:
    """3 same date, 2 export inside the vault's span, 1 overlapping, 0 no
    evidence either way, None when the two contradict."""
    if not vault_date or not ged_date:
        return 0
    if str(vault_date) == str(ged_date):
        return 3
    v, g = _span(vault_date), _span(ged_date)
    if v is None or g is None:
        return 0
    if v[0] <= g[0] and g[1] <= v[1]:
        return 2
    if g[0] <= v[1] and v[0] <= g[1]:
        return 1
    return None


def _place_score(note, ev, place_index) -> int:
    """2 agree, 1 export names an ancestor, 0 nothing to compare, -2 contradict."""
    have = note.scalar("place")
    if not have or not ev.place or place_index.by_link(have) is None:
        return 0
    return {"": 2, "coarsen": 1}.get(place_index.compare(have, ev.place), -2)


def _mutual_best(vnotes: list, gevents: list, place_index) -> list:
    """(note, event, tied) for pairs each side scores strictly highest,
    repeated until none is left.

    A tie is not a match: two candidates equally good for one note means the
    evidence does not decide, and the pair is left for a later stage. The one
    exception is a tie among vault notes that are themselves identical -- the
    same date and place, as import-era undated residences often are. Which of
    them takes which block changes nothing, so a block of k identical notes
    tied with k blocks pairs in order, flagged `tied` as arbitrary but stable.
    """
    scores = {}
    for i, n in enumerate(vnotes):
        for j, e in enumerate(gevents):
            d = _date_score(n.scalar("date"), event_date(e))
            if d is None:
                continue
            p = _place_score(n, e, place_index)
            if d + p >= _CORROBORATED or (d == 0 and p == 2):
                scores[i, j] = d + p

    def sig(i):
        return (vnotes[i].scalar("date"), vnotes[i].scalar("place"))

    out, used_v, used_g = [], set(), set()
    while True:
        live = {k: v for k, v in scores.items()
                if k[0] not in used_v and k[1] not in used_g}
        found = False
        for (i, j), total in live.items():
            row = [v for (a, _), v in live.items() if a == i]
            col = [v for (_, b), v in live.items() if b == j]
            if total == max(row) == max(col) and row.count(total) == 1 \
                    and col.count(total) == 1:
                out.append((vnotes[i], gevents[j], False))
                used_v.add(i)
                used_g.add(j)
                found = True
                break
        if not found:
            block = _identical_block(live, sig)
            if block is None:
                return out
            rows, cols = block
            for i, j in zip(rows, cols):
                out.append((vnotes[i], gevents[j], True))
                used_v.add(i)
                used_g.add(j)


def _identical_block(live: dict, sig):
    """(rows, cols) where k identical vault notes tie on exactly k blocks.

    Every note in the block must score its best, equally, on every block in
    it, and no note outside it may compete for those blocks.
    """
    for (i, j), total in sorted(live.items()):
        rows = sorted({a for (a, b), v in live.items() if b == j and v == total})
        cols = sorted({b for (a, b), v in live.items() if a == i and v == total})
        if len(rows) < 2 or len(rows) != len(cols):
            continue
        if len({sig(r) for r in rows}) != 1:
            continue
        if any(live.get((r, c)) != total for r in rows for c in cols):
            continue
        if any(v > total for (a, _), v in live.items() if a in rows):
            continue
        if any(a not in rows and v >= total
               for (a, b), v in live.items() if b in cols):
            continue
        return rows, cols
    return None


#: Event fields the importer owns outright. `title` is deliberately absent:
#: it is derived from the participants' names, the filename is the real
#: identity, and rewriting it on every upstream rename is pure churn.
#: `persons` is absent because it is what the match is built on, and
#: `confidence` because `unknown` is the import default and anything else was
#: set by hand. `sources` is never touched -- 671 Events carry it and much of
#: it is archive-derived evidence the export has never heard of.
EVENT_OWNED = ["date", "date_precision", "date_end"]
#: Written only when the vault Event has nothing there. Overwriting either is
#: a data-quality decision, not a sync -- though a `place` the export
#: disagrees with is still reported and held (see `event_changes`).
EVENT_FILL_ONLY = ["place", "description"]


#: Only `ABT` moves. The vault model pairs `born: c. 1804` on the Person with
#: `date: 1804` + `date_precision: estimated` on the Event -- but it also
#: lists `BEF YYYY` among the Event date forms, and "before 1818" says more
#: than "1818", so a BEF/AFT qualifier stays on the Event.
_QUALIFIERS = ("ABT ",)


def event_date(ev) -> str:
    """The Event form of a GEDCOM date: bare, with the qualifier stripped."""
    value = ev.date or ""
    for q in _QUALIFIERS:
        if value.upper().startswith(q):
            return value[len(q):].strip()
    return value


def event_projection(ev, place_index) -> dict:
    """The importer-owned fields a vault Event should carry for this block."""
    out: dict = {}
    if ev.date:
        out["date"] = event_date(ev)
        out["date_precision"] = ev.precision
    if ev.description:
        out["description"] = ev.description
    if ev.place:
        # A PLAC only becomes a `place:` link when it resolves to a real Place
        # note. Most do not -- upstream records historical and native forms
        # against an English gazetteer -- and the vault model is explicit that a
        # non-place in a place: field means the event needs fixing first.
        note = place_index.find(ev.place)
        if note is not None:
            out["place"] = f"[[{note.basename}]]"
    return out


def event_changes(pair, place_index, change_cls) -> list:
    """Classified changes for one matched Event, or [].

    `date` and `date_precision` are one fact, so the precision change takes
    the date change's classification when the two move together. Judging them
    separately calls a precision shift a conflict while the date it describes
    is a safe refinement.
    """
    note, ev = pair.vault_note, pair.ged_event
    projection = event_projection(ev, place_index)
    changes = []

    date_kind = None
    if "date" in projection and str(note.scalar("date") or "") != str(projection["date"]):
        change = change_cls("date", note.scalar("date"), projection["date"])
        date_kind = change.kind
        changes.append(change)

    if "date_precision" in projection:
        have, want = note.scalar("date_precision"), projection["date_precision"]
        if str(have or "") != str(want):
            if date_kind:
                kind = date_kind
            elif (have or "") in ("", "unknown"):
                # `unknown` is the import default -- unassessed, not doubtful.
                kind = "fill"
            elif have == "estimated":
                # `estimated` pairs with the Person's `ABT` and records a
                # judgement the export cannot express. Losing it because the
                # GEDCOM dropped the qualifier is a downgrade.
                kind = "coarsen"
            else:
                kind = None
            changes.append(change_cls("date_precision", have, want, kind=kind or ""))

    if "date_end" in projection and str(note.scalar("date_end") or "") != str(projection["date_end"]):
        changes.append(change_cls("date_end", note.scalar("date_end"), projection["date_end"]))

    for key in EVENT_FILL_ONLY:
        if key in projection and not note.scalar(key):
            changes.append(change_cls(key, "", projection[key]))

    # A place the vault already holds is never overwritten, but one the
    # export disagrees with is reported: filling only the empty case let an
    # upstream correction vanish, and a date fill then paired the new date
    # with the old place.
    have_place = note.scalar("place")
    if have_place and ev.place:
        kind = place_index.compare(have_place, ev.place)
        if kind:
            changes.append(change_cls("place", have_place,
                                      projection.get("place") or ev.place,
                                      kind=kind))
    return changes
