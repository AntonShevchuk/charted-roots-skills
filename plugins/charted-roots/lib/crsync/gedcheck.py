"""Check a GEDCOM on its own, and say what to fix in the host service.

Each check yields `Finding`s; `run` collects the groups asked for. Nothing
here reads or writes the vault, and nothing writes the `.ged`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from . import dates as gedcom_dates
from . import gedcom
from . import places

GROUPS = ["duplicates", "marriages", "dates", "places"]   # also the report order
CHECKS = {"dup-vital": "duplicates", "dup-event-exact": "duplicates",
          "dup-marriage": "duplicates", "dup-family": "duplicates",
          "marriage-on-person": "marriages",
          "date-unreadable": "dates", "date-invalid": "dates",
          "date-nonstandard": "dates", "date-order": "dates",
          "place-non-place": "places", "place-format": "places",
          "place-variant": "places", "place-hierarchy": "places"}

VITAL = ("BIRT", "DEAT", "BURI", "CREM")


@dataclass
class Finding:
    check: str
    group: str
    kind: str      #: "fix" | "review"
    who: str
    line: int
    what: str
    fix: str


def host_name(tree) -> str:
    """The service the export came from, for "fix it in ..." lines."""
    source = (tree.header.get("source") or "").strip()
    low = source.lower()
    if "myheritage" in low:
        return "MyHeritage"
    if "ancestry" in low:
        return "Ancestry"
    if "familysearch" in low:
        return "FamilySearch"
    return source or "the tree's host"


def _person(tree, xref: str) -> str:
    ind = tree.individuals.get(xref)
    return f"{ind.name or '(unnamed)'} (@{xref}@)" if ind else f"@{xref}@"


def _family(tree, xref: str) -> str:
    fam = tree.families.get(xref)
    names = []
    for p in ((fam.husband, fam.wife) if fam else ()):
        ind = tree.individuals.get(p) if p else None
        if ind:
            names.append(ind.name or "(unnamed)")
    return f"{' & '.join(names) or '(no partners)'} (@{xref}@)"


def _spouses(tree, xref: str) -> list:
    """(family xref, the other partner) for each family the person heads."""
    ind = tree.individuals.get(xref)
    out = []
    for f in (ind.fams if ind else []):
        fam = tree.families.get(f)
        if fam is None:
            continue
        other = fam.wife if fam.husband == xref else fam.husband
        out.append((f, _person(tree, other) if other else "no partner"))
    return out


def _label(ev) -> str:
    return (ev.even_type or ev.tag) if ev.tag == "EVEN" else ev.tag


def _where(ev) -> str:
    return f"{ev.date_raw or '(undated)'} at {ev.place_raw or '(no place)'}"


def _dup_vital(tree, host):
    for ind in tree.individuals.values():
        who = _person(tree, ind.xref)
        for tag in VITAL:
            evs = [e for e in ind.events if e.tag == tag]
            if len(evs) < 2:
                continue
            keys = {(e.date, e.precision, places.key(e.place_raw)) for e in evs}
            if len(keys) == 1:
                yield Finding(
                    "dup-vital", "duplicates", "fix", who, evs[1].line,
                    f"{tag} recorded {len(evs)} times, identical "
                    f"({_where(evs[0])})",
                    f"in {host}: delete the duplicate {tag}")
            else:
                yield Finding(
                    "dup-vital", "duplicates", "review", who, evs[1].line,
                    f"{tag} recorded {len(evs)} times, differently: "
                    + "; ".join(_where(e) for e in evs),
                    f"in {host}: keep the correct {tag} and delete the others")


def _dup_event_exact(tree, host):
    owners = [(i.xref, _person(tree, i.xref), i.events)
              for i in tree.individuals.values()]
    owners += [(f.xref, _family(tree, f.xref), f.events)
               for f in tree.families.values()]
    for _, who, events in owners:
        seen: dict = {}
        for ev in events:
            if ev.tag == "MARR" or ev.tag in VITAL:
                continue
            date, place = ev.date_raw.strip(), places.key(ev.place_raw)
            if not date or not place:
                continue
            k = (ev.tag, ev.even_type, date, place)
            if k in seen:
                yield Finding(
                    "dup-event-exact", "duplicates", "fix", who, ev.line,
                    f"{_label(ev)} repeated exactly ({_where(ev)})",
                    f"in {host}: delete the repeated {_label(ev)}")
            seen[k] = ev


def _dup_marriage(tree, host):
    for fam in tree.families.values():
        marrs = [e for e in fam.events if e.tag == "MARR"]
        if len(marrs) < 2:
            continue
        compatible = all(gedcom._same_date(a.date, b.date)
                         for i, a in enumerate(marrs) for b in marrs[i + 1:])
        who = _family(tree, fam.xref)
        what = (f"marriage recorded {len(marrs)} times: "
                + "; ".join(_where(e) for e in marrs))
        if len({(e.date, places.key(e.place_raw)) for e in marrs}) == 1:
            yield Finding(
                "dup-marriage", "duplicates", "fix", who, marrs[1].line,
                what, f"in {host}: delete the duplicate marriage")
        elif compatible:
            yield Finding(
                "dup-marriage", "duplicates", "review", who, marrs[1].line,
                what, f"in {host}: keep the copy with the more precise date "
                f"/ with a place, and delete the others")
        else:
            yield Finding(
                "dup-marriage", "duplicates", "review", who, marrs[1].line,
                what, f"in {host}: keep the correct marriage and delete the "
                f"others")


def _dup_family(tree, host):
    seen: dict = {}
    for fam in tree.families.values():
        if not (fam.husband and fam.wife):
            continue
        couple = tuple(sorted((fam.husband, fam.wife)))
        first = seen.setdefault(couple, fam)
        if first is not fam:
            yield Finding(
                "dup-family", "duplicates", "review", _family(tree, fam.xref),
                fam.line,
                f"same couple as family @{first.xref}@",
                f"in {host}: merge the two families")


def _duplicates(tree, host):
    for gen in (_dup_vital, _dup_event_exact, _dup_marriage, _dup_family):
        yield from gen(tree, host)


def _marriages(tree, host):
    for ind_ev, fam_ev in tree.folded:
        partner = dict(_spouses(tree, ind_ev.owner)).get(fam_ev.owner, "")
        what = f"duplicate of the family marriage @{fam_ev.owner}@" + \
            (f" with {partner}" if partner else "")
        fix = f"in {host}: delete the person-level marriage; the family " \
              f"already holds it"
        if ind_ev.place and fam_ev.place == ind_ev.place:
            fix += (f" (make sure the family keeps the place "
                    f"\"{ind_ev.place}\")")
        elif ind_ev.place:
            fix += (f" (the places differ: person \"{ind_ev.place}\", "
                    f"family \"{fam_ev.place}\" -- keep the right one)")
        yield Finding("marriage-on-person", "marriages", "fix",
                      _person(tree, ind_ev.owner), ind_ev.line, what, fix)
    for ev, why in tree.person_marriages:
        spouses = _spouses(tree, ev.owner)
        names = ", ".join(p for _, p in spouses)
        if why == "no family":
            fix = (f"in {host}: add the spouse, and record the marriage on "
                   f"that family instead of on the person")
        elif len(spouses) == 1:
            fix = (f"in {host}: move the marriage onto the family with "
                   f"{names}" + ("; date it" if why == "undated" else
                                 ", or correct the date if it is the same marriage"))
        else:
            fix = (f"in {host}: move the marriage onto the right family "
                   f"({names})" + ("; date it" if why == "undated" else ""))
        yield Finding("marriage-on-person", "marriages", "review",
                      _person(tree, ev.owner), ev.line,
                      f"only on the person: {why}", fix)


def _all_events(tree):
    """(who, event) for every INDI and FAM event, suppressed EVENs included."""
    for ind in tree.individuals.values():
        who = _person(tree, ind.xref)
        for ev in ind.events:
            yield who, ev
    for fam in tree.families.values():
        who = _family(tree, fam.xref)
        for ev in fam.events:
            yield who, ev
    for _, ev in tree.suppressed:
        yield _person(tree, ev.owner), ev


_REWRITE = "rewrite as D MMM YYYY (or ABT / BEF / AFT / BET ... AND ...)"


def _date_forms(tree, host):
    for who, ev in _all_events(tree):
        label, suggestion = gedcom_dates.classify(ev.date_raw)
        raw, tag = ev.date_raw.strip(), _label(ev)
        if label == "unreadable":
            yield Finding("date-unreadable", "dates", "fix", who, ev.line,
                          f"{tag} date \"{raw}\" cannot be read",
                          f"in {host}: {_REWRITE}")
        elif label == "invalid":
            yield Finding("date-invalid", "dates", "fix", who, ev.line,
                          f"{tag} date \"{raw}\" is not a real calendar day",
                          f"in {host}: correct the date, then {_REWRITE}")
        elif label == "lenient":
            yield Finding("date-nonstandard", "dates", "fix", who, ev.line,
                          f"{tag} date \"{raw}\" is not standard GEDCOM",
                          f"in {host}: write \"{raw}\" as \"{suggestion}\"")


def _first(ind, *tags):
    return next((e for e in ind.events if e.tag in tags), None)


def _date_order(tree, host):
    def order(who, line, what, later_hi, earlier_lo):
        if later_hi and earlier_lo and later_hi < earlier_lo:
            return Finding("date-order", "dates", "review", who, line, what,
                           f"in {host}: check both dates against the sources")

    for ind in tree.individuals.values():
        who = _person(tree, ind.xref)
        birt, deat = _first(ind, "BIRT"), _first(ind, "DEAT")
        buri = _first(ind, "BURI", "CREM")
        b = gedcom_dates.bounds(birt.date_raw) if birt else (None, None)
        d = gedcom_dates.bounds(deat.date_raw) if deat else (None, None)
        u = gedcom_dates.bounds(buri.date_raw) if buri else (None, None)
        found = []
        if birt and deat:
            found.append(order(
                who, deat.line, f"death ({deat.date_raw}) is before birth "
                f"({birt.date_raw})", d[1], b[0]))
            if d[0] and b[1] and int(d[0][:4]) - int(b[1][:4]) > 120:
                found.append(Finding(
                    "date-order", "dates", "review", who, deat.line,
                    f"lifespan over 120 years (born {birt.date_raw}, died "
                    f"{deat.date_raw})",
                    f"in {host}: check both dates against the sources"))
        if buri and deat:
            found.append(order(
                who, buri.line, f"{'cremation' if buri.tag == 'CREM' else 'burial'}"
                f" ({buri.date_raw}) is before death ({deat.date_raw})",
                u[1], d[0]))
        for famc in ind.famc:
            fam = tree.families.get(famc)
            if fam is None or not birt:
                continue
            for tag, parent in (("HUSB", fam.husband), ("WIFE", fam.wife)):
                p = tree.individuals.get(parent) if parent else None
                pb = _first(p, "BIRT") if p else None
                if pb is None or fam.relation(ind.xref, tag) != "birth":
                    continue
                found.append(order(
                    who, birt.line, f"born ({birt.date_raw}) before their "
                    f"parent {p.name or '(unnamed)'} (@{p.xref}@, born "
                    f"{pb.date_raw})", b[1], gedcom_dates.bounds(pb.date_raw)[0]))
        yield from (f for f in found if f)


def _dates(tree, host):
    yield from _date_forms(tree, host)
    yield from _date_order(tree, host)


def _clean_place(raw: str) -> str:
    parts = (" ".join(p.split()) for p in raw.split(","))
    return ", ".join(p for p in parts if p)


def _who(owners) -> str:
    names = list(dict.fromkeys(owners))
    out = ", ".join(names[:3])
    return out + (f" and {len(names) - 3} more" if len(names) > 3 else "")


def _subsequence(small, big) -> bool:
    it = iter(big)
    return all(x in it for x in small)


def _uses(n: int) -> str:
    return f"{n} use{'s' if n != 1 else ''}"


def _places(tree, host):
    by_raw: dict = {}      # PLAC as written -> [(who, event)]
    for who, ev in _all_events(tree):
        if not ev.place_raw.strip():
            continue
        by_raw.setdefault(ev.place_raw, []).append((who, ev))

    def line(uses):
        return min(ev.line for _, ev in uses)

    plac_form = tree.header.get("plac_form", "")
    by_clean: dict = {}    # cleaned string -> [(who, event)]
    for raw, uses in by_raw.items():
        shown = f"\"{raw}\" ({_uses(len(uses))})"
        who = _who(w for w, _ in uses)
        reason = gedcom.non_place_reason(raw)
        if reason:
            yield Finding(
                "place-non-place", "places", "fix", who, line(uses),
                f"PLAC {shown} is not a place (\"{reason}\")",
                f"in {host}: move the unit / rank into the description; "
                f"set PLAC to the place")
        cleaned = _clean_place(raw)
        if not cleaned:
            continue
        if raw != cleaned and re.sub(r",(?=\S)", ", ", raw) != cleaned:
            spaced = ", ".join(" ".join(p.split()) for p in raw.split(","))
            if plac_form and raw in (spaced, re.sub(r",(?=\S)", ", ", spaced)):
                yield Finding(
                    "place-format", "places", "review", who, line(uses),
                    f"PLAC {shown} has empty jurisdiction levels",
                    f"in {host}: empty jurisdiction levels; fill them or "
                    f"leave them if your host's place format needs them")
            else:
                yield Finding(
                    "place-format", "places", "fix", who, line(uses),
                    f"PLAC {shown} has stray spaces or commas",
                    f"in {host}: write \"{raw}\" as \"{cleaned}\"")
        by_clean.setdefault(cleaned, []).extend(uses)

    groups: dict = {}      # fold -> [cleaned strings]
    for cleaned in by_clean:
        groups.setdefault(places.fold(cleaned), []).append(cleaned)

    def ranked(strings):
        return sorted(strings, key=lambda c: (
            -len(by_clean[c]), -sum(ord(ch) > 127 for ch in c), c))

    reps = {}
    for fkey, strings in groups.items():
        order = ranked(strings)
        reps[fkey] = order[0]
        if len(strings) < 2:
            continue
        uses = [u for c in strings for u in by_clean[c]]
        spell = ", ".join(f"\"{c}\" ({len(by_clean[c])})" for c in order)
        if len(by_clean[order[0]]) == len(by_clean[order[1]]):
            fix = f"in {host}: use one spelling, e.g. \"{order[0]}\""
        else:
            fix = (f"in {host}: use one spelling; most used: \"{order[0]}\" "
                   f"({len(by_clean[order[0]])})")
        yield Finding(
            "place-variant", "places", "fix", _who(w for w, _ in uses),
            line(uses), f"one place written {len(strings)} ways: {spell}", fix)

    parts = {f: tuple(places.fold(x) for x in rep.split(", "))
             for f, rep in reps.items()}
    for fkey, rep in sorted(reps.items()):
        leaf, chain = parts[fkey][0], parts[fkey][1:]
        cands = [g for g in reps
                 if g != fkey and parts[g][0] == leaf
                 and len(parts[g]) > len(parts[fkey])
                 and _subsequence(chain, parts[g][1:])]
        # only the maximal forms: drop one that another candidate extends
        fuller = sorted(
            reps[g] for g in cands
            if not any(h != g and len(parts[h]) > len(parts[g])
                       and _subsequence(parts[g][1:], parts[h][1:])
                       for h in cands))
        if not fuller:
            continue
        uses = [u for c in groups[fkey] for u in by_clean[c]]
        who, ln = _who(w for w, _ in uses), line(uses)
        quoted = ", ".join(f"\"{f}\"" for f in fuller)
        if chain:
            yield Finding(
                "place-hierarchy", "places", "review", who, ln,
                f"\"{rep}\" is a shorter form of another place",
                f"in {host}: standardise to the fuller form: {quoted}")
        elif len(fuller) == 1:
            yield Finding(
                "place-hierarchy", "places", "fix", who, ln,
                f"\"{rep}\" has no parents; \"{fuller[0]}\" has the same leaf",
                f"in {host}: use \"{fuller[0]}\"")
        else:
            yield Finding(
                "place-hierarchy", "places", "review", who, ln,
                f"\"{rep}\" has no parents; several places share the leaf",
                f"in {host}: decide which one is meant: {quoted}?")


#: Adding a check group is one entry here.
_RUNNERS = {"duplicates": _duplicates, "marriages": _marriages,
            "dates": _dates, "places": _places}


def run(tree, only: set | None = None) -> list:
    """Findings for the groups in `only` (default all), by group then line."""
    host = host_name(tree)
    out = []
    for group in GROUPS:
        if (only is not None and group not in only) or group not in _RUNNERS:
            continue
        out.extend(sorted(_RUNNERS[group](tree, host), key=lambda f: f.line))
    return out


def parse_only(value: str) -> set | None:
    """`--only` text to a set of group names; None means every group."""
    names = {p.strip().lower() for p in (value or "").split(",") if p.strip()}
    if not names:
        return None
    bad = sorted(names - set(GROUPS))
    if bad:
        raise ValueError(f"unknown group {', '.join(bad)}; "
                         f"valid groups: {', '.join(GROUPS)}")
    return names
