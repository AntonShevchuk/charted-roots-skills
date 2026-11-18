"""A GEDCOM 5.5.1 reader for Ancestry exports.

Written against the Ancestry export of the vault it was developed on, and deliberately covering
the two things the Charted Roots parser drops on the floor:

* ``1 EVEN`` blocks, distinguished only by their ``2 TYPE`` line. The plugin's
  tag map has no ``EVEN`` key, so the block and every child line under it are
  discarded. That export had 64 of them, carrying real immigration and
  emigration events plus their source citations.
* ``0 @O..@ OBJE`` records whose ``1 FILE`` is empty -- the plugin requires a
  non-empty FILE, but Ancestry puts the identifying data in ``2 TITL`` and
  ``1 _OID``, so all 50 are lost.
"""

from __future__ import annotations

import codecs
import io
import re
import sys
from dataclasses import dataclass, field

from . import dates

_LINE = re.compile(r'^(\d+)\s+(?:(@[^@]+@)\s+)?(\S+)(?:\s(.*))?$')
#: Byte lines split as universal-newline text mode does: CR, LF or CRLF.
_BYTE_LINES = re.compile(rb"[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+$")
_CONC_PREFIX = re.compile(rb"[ \t]*([0-9]+) CONC ")
_BYTE_LINE = re.compile(rb"^[ \t]*([0-9]+)\s+(?:@[^@]+@\s+)?(\S+)(?:\s(.*))?$")
#: How many line numbers a warning lists before summarising the rest.
_WARN_LINES = 20

#: GEDCOM tag -> the vault's `event_type`, exactly as the Charted Roots
#: importer maps them (its `Yoe` table, plugin 0.22.76), so a note the sync
#: creates carries the type the plugin's own import would give it. `_MILT`
#: is extra: Ancestry's military fact, which the plugin's importer drops.
TAG_TO_EVENT = {
    "BIRT": "birth", "DEAT": "death", "MARR": "marriage", "DIV": "divorce",
    "BURI": "burial", "CREM": "cremation", "ADOP": "adoption",
    "GRAD": "graduation", "RETI": "retirement", "CENS": "census",
    "RESI": "residence", "OCCU": "occupation", "EDUC": "education",
    "PROB": "probate", "WILL": "will", "NATU": "naturalization",
    "MILI": "military", "IMMI": "immigration", "EMIG": "emigration",
    "BAPM": "baptism", "CHR": "christening", "CHRA": "adult_christening",
    "CONF": "confirmation", "FCOM": "first_communion", "ORDN": "ordination",
    "BARM": "bar_mitzvah", "BASM": "bas_mitzvah", "BLES": "blessing",
    "ENGA": "engagement", "MARB": "marriage_bann", "MARC": "marriage_contract",
    "MARL": "marriage_license", "MARS": "marriage_settlement",
    "ANUL": "annulment", "DIVF": "divorce_filed",
    "_MILT": "military",
}

#: `2 TYPE` prefixes under a `1 EVEN` block. Travel becomes a real Event.
#: Everything else is either a shared event counted once elsewhere, or a
#: derivative record that the vault model says is a Source and never an Event.
EVEN_TRAVEL = {"arrival": "immigration", "departure": "emigration"}
#: `2 TYPE` labels that are a standard fact written as EVEN. MyHeritage
#: exports some marriages as `1 EVEN` / `2 TYPE MARR`, and German-language
#: trees label baptisms, weddings, confirmations and engagements. They are read as that tag, so an
#: individual marriage folds into the FAM marriage it repeats.
EVEN_STANDARD = {"marr": "MARR", "hochzeit": "MARR", "taufe": "BAPM",
                 "konfirmation": "CONF", "verlobung": "ENGA",
                 "military service": "MILI"}
EVEN_DERIVATIVE_PREFIXES = ("obituary", "testament", "marriage license")
#: A shared event yields one EVEN block per individual, so these must collapse
#: to the single FAM-level Event rather than being counted per person.
EVEN_SHARED_PREFIXES = ("marriage of",)

#: Tokens that mark a PLAC value as something other than a place -- a rank, a
#: unit, or a recruiting office. The vault model: a non-place in a `place:` field
#: means the *event* needs fixing first, so these are reported rather than
#: written. Matched case-insensitively as whole words where possible.
NON_PLACE_MARKERS = (
    "regiment", "bataillon", "battalion", "landwehr", "infanterie",
    "infantry", "zahlmeister", "paymaster", "рвк", "военкомат",
)


def non_place_reason(place: str) -> str:
    """Why this PLAC value is not a place, or '' if it looks like one."""
    low = (place or "").lower()
    for marker in NON_PLACE_MARKERS:
        if marker in low:
            return marker
    return ""


@dataclass
class Node:
    level: int
    tag: str
    value: str = ""
    xref: str = ""
    children: list = field(default_factory=list)
    line: int = 0         #: 1-based physical line in the file

    def first(self, tag: str):
        for c in self.children:
            if c.tag == tag:
                return c
        return None

    def val(self, tag: str, default: str = "") -> str:
        c = self.first(tag)
        return c.value if c is not None else default

    def all(self, tag: str) -> list:
        return [c for c in self.children if c.tag == tag]


@dataclass
class Event:
    owner: str            #: INDI or FAM xref, without @
    tag: str              #: the GEDCOM tag, or EVEN
    event_type: str       #: the vault's event_type
    date_raw: str = ""
    date: str = ""        #: ISO, or a BEF/ABT form the vault also permits
    precision: str = "unknown"
    place: str = ""
    #: the PLAC as written; `place` may also be filled by marriage folding
    place_raw: str = ""
    line: int = 0         #: line of the event's tag in the file
    description: str = ""
    even_type: str = ""   #: the `2 TYPE` line, for EVEN blocks
    #: (source xref, page) pairs from `2 SOUR` / `3 PAGE`
    citations: list = field(default_factory=list)
    #: index of this event among the owner's events of the same type
    ordinal: int = 0
    shared: bool = False  #: a FAM event, or an EVEN naming two people
    #: For a FAM event, the couple's INDI xrefs, sorted. FAM xrefs are
    #: positional integers that Ancestry RENUMBERS when a family is inserted
    #: (verified: adding one family shifted 41 of 131), so they cannot key
    #: anything durable. INDI xrefs are stable, so the couple identifies the
    #: family across exports.
    couple: tuple = ()
    #: An individual MARR that repeats one of the person's FAM marriages. It
    #: stays on the person, so its citations still resolve, but it is never
    #: paired or created as an Event of its own.
    folded: bool = False


@dataclass
class Individual:
    xref: str
    name: str = ""
    #: Every `1 NAME` after the first. Ancestry records a maiden name and a
    #: married name as separate NAME blocks, each with its own `2 SOUR`, and
    #: the vault often holds the alternate rather than Ancestry's primary.
    #: Reading only the first makes that look like a conflict.
    alt_names: list = field(default_factory=list)
    given: str = ""
    surname: str = ""
    suffix: str = ""
    sex: str = ""
    famc: list = field(default_factory=list)
    fams: list = field(default_factory=list)
    events: list = field(default_factory=list)
    media: list = field(default_factory=list)
    citations: list = field(default_factory=list)
    line: int = 0


@dataclass
class Family:
    xref: str
    husband: str = ""
    wife: str = ""
    children: list = field(default_factory=list)
    events: list = field(default_factory=list)
    #: child xref -> {"HUSB": rel, "WIFE": rel}, from Ancestry's `2 _FREL` /
    #: `2 _MREL` under `1 CHIL`, lowercased. Absent means a birth child.
    pedigree: dict = field(default_factory=dict)
    line: int = 0

    def relation(self, child: str, parent_tag: str) -> str:
        """How `child` relates to the HUSB or WIFE: "birth", "step", ..."""
        return self.pedigree.get(child, {}).get(parent_tag, "") or "birth"


@dataclass
class SourceRec:
    xref: str
    title: str = ""
    author: str = ""
    publisher: str = ""
    repository: str = ""


@dataclass
class MediaObj:
    xref: str
    title: str = ""
    form: str = ""
    mtype: str = ""
    oid: str = ""
    file: str = ""       #: the `1 FILE` value, stripped


def normalise_date(raw: str) -> tuple:
    """GEDCOM date -> (Event form, date_precision). See `dates.from_gedcom`."""
    return dates.from_gedcom(raw)


def classify_even(even_type: str) -> tuple:
    """An EVEN block's `2 TYPE` -> (event_type|None, disposition).

    Disposition is one of: standard, travel, shared, derivative, unknown.
    """
    t = (even_type or "").strip().lower()
    if t in EVEN_STANDARD:
        return TAG_TO_EVENT[EVEN_STANDARD[t]], "standard"
    if t in EVEN_TRAVEL:
        return EVEN_TRAVEL[t], "travel"
    for prefix in EVEN_SHARED_PREFIXES:
        if t.startswith(prefix):
            return None, "shared"
    for prefix in EVEN_DERIVATIVE_PREFIXES:
        if t.startswith(prefix):
            return None, "derivative"
    if t == "death":
        return "death", "travel"  # a plain restatement; matched, never created
    return None, "unknown"


def _cut_utf8_tail(data: bytes) -> int:
    """Length of an incomplete UTF-8 sequence at the end of `data`, or 0."""
    decoder = codecs.getincrementaldecoder("utf-8")()
    try:
        decoder.decode(data)
    except UnicodeDecodeError:
        return 0
    return len(decoder.getstate()[0])


def _completes_utf8(tail: bytes, value: bytes) -> bool:
    """Whether the first bytes of `value` complete the cut sequence `tail`."""
    for size in range(1, 4):
        try:
            (tail + value[:size]).decode("utf-8")
        except UnicodeDecodeError:
            continue
        return True
    return False


def _join_conc_split_characters(raw: bytes) -> tuple:
    """Move a UTF-8 character cut at a CONC boundary onto the CONC line.

    Some exporters (MyHeritage among them) declare `CHAR UTF-8` but wrap long
    values into CONC lines by byte count, so a multibyte character starts at
    the end of one line and ends at the start of the next CONC value. Each
    line is invalid UTF-8 on its own. CONC appends without a separator, so
    the joined value holds the whole character.

    Only related lines are joined: the CONC must continue the value directly
    above it -- its parent one level up, or a CONC/CONT sibling at the same
    level. A cut before CONT (which starts a new line of text), before an
    unrelated line, in a file declaring another charset, or in GEDCOM 7
    (which has no CONC) is left alone, so decoding still fails. Bytes move
    only when they complete a character; total length is unchanged.

    Returns (bytes, 1-based numbers of the CONC lines that were joined).
    """
    lines = _BYTE_LINES.findall(raw)
    charset = version = b""
    parent = b""  # the HEAD's current level-1 tag
    for line in lines[1:]:
        parts = line.split(None, 2)
        if not parts or parts[0] == b"0":
            break
        value = parts[2].strip() if len(parts) == 3 else b""
        if parts[0] == b"1":
            parent = parts[1] if len(parts) > 1 else b""
            if parent == b"CHAR":
                charset = value
        elif parts[0] == b"2" and parent == b"GEDC" and parts[1:2] == [b"VERS"]:
            version = value
    if charset.upper() != b"UTF-8" or version.startswith(b"7"):
        return raw, []
    joined: list = []
    for index in range(len(lines) - 1):
        conc = _CONC_PREFIX.match(lines[index + 1])
        if conc is None:
            continue
        body = lines[index].rstrip(b"\r\n")
        previous = _BYTE_LINE.match(body)
        if previous is None:
            # A bare text line: MyHeritage breaks multi-line values with raw
            # newlines instead of CONT. It belongs to the nearest GEDCOM line
            # above it, which is what the CONC must continue.
            if not body.strip():
                continue
            back = index - 1
            while back >= 0 and _BYTE_LINE.match(lines[back].rstrip(b"\r\n")) is None:
                back -= 1
            if back < 0:
                continue
            previous = _BYTE_LINE.match(lines[back].rstrip(b"\r\n"))
        elif not previous.group(3):
            continue
        level, prev_level = int(conc.group(1)), int(previous.group(1))
        if previous.group(2) in (b"CONC", b"CONT"):
            related = level == prev_level
        else:
            related = level == prev_level + 1
        if not related:
            continue
        cut = _cut_utf8_tail(body)
        value = lines[index + 1][conc.end():]
        if cut and _completes_utf8(body[-cut:], value):
            lines[index] = body[:-cut] + lines[index][len(body):]
            lines[index + 1] = conc.group() + body[-cut:] + value
            joined.append(index + 2)
    return b"".join(lines), joined


def _decode(path: str, warnings: list) -> str:
    """Read the file as UTF-8, recovering characters split across CONC.

    Anything still undecodable raises UnicodeDecodeError, as before.
    """
    with open(path, "rb") as fh:
        raw = fh.read()
    if raw.startswith(codecs.BOM_UTF8):
        raw = raw[len(codecs.BOM_UTF8):]
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        raw, joined = _join_conc_split_characters(raw)
        text = raw.decode("utf-8")
    if joined:
        warnings.append(
            f"{path}: rejoined a UTF-8 character split across a CONC boundary "
            f"on {len(joined)} line(s): {_line_list(joined)}. Recovered in "
            f"memory only; the file itself is still invalid UTF-8.")
    return text


def _line_list(numbers: list) -> str:
    shown = ", ".join(map(str, numbers[:_WARN_LINES]))
    more = len(numbers) - _WARN_LINES
    return shown + (f" and {more} more" if more > 0 else "")


def _tree(path: str, warnings: list | None = None) -> list:
    """Parse the file into level-0 records, folding CONT/CONC.

    Lines that do not parse as GEDCOM are skipped and counted in `warnings`.
    """
    if warnings is None:
        warnings = []
    roots: list = []
    stack: list = []
    skipped: list = []
    text = _decode(path, warnings)
    # newline=None splits on CR, LF and CRLF exactly as text-mode open() did.
    with io.StringIO(text, newline=None) as fh:
        for number, raw in enumerate(fh, 1):
            line = raw.rstrip("\n").rstrip("\r")
            if not line.strip():
                continue
            m = _LINE.match(line)
            if not m:
                skipped.append(number)
                continue
            level = int(m.group(1))
            xref = (m.group(2) or "").strip("@")
            tag = m.group(3)
            value = m.group(4) or ""

            if tag in ("CONT", "CONC") and stack:
                target = stack[-1][1]
                target.value += ("\n" if tag == "CONT" else "") + value
                continue

            node = Node(level=level, tag=tag, value=value, xref=xref,
                        line=number)
            while stack and stack[-1][0] >= level:
                stack.pop()
            if stack:
                stack[-1][1].children.append(node)
            else:
                roots.append(node)
            stack.append((level, node))
    if skipped:
        warnings.append(f"{path}: skipped {len(skipped)} line(s) that do not "
                        f"parse as GEDCOM: {_line_list(skipped)}")
    return roots


def _read_citations(node: Node) -> list:
    out = []
    for s in node.all("SOUR"):
        xref = s.value.strip("@") if s.value.startswith("@") else ""
        if xref:
            out.append((xref, s.val("PAGE")))
    return out


def _read_event(owner: str, node: Node) -> Event | None:
    tag = node.tag
    if tag == "EVEN":
        even_type = node.val("TYPE")
        event_type, disposition = classify_even(even_type)
        tag = EVEN_STANDARD[even_type.strip().lower()] \
            if disposition == "standard" else "EVEN"
        ev = Event(owner=owner, tag=tag, event_type=event_type or "",
                   even_type=even_type)
        ev.shared = disposition == "shared"
    elif tag in TAG_TO_EVENT:
        ev = Event(owner=owner, tag=tag, event_type=TAG_TO_EVENT[tag])
    else:
        return None
    ev.date_raw = node.val("DATE")
    ev.date, ev.precision = normalise_date(ev.date_raw)
    ev.place = node.val("PLAC")
    ev.place_raw = ev.place
    ev.line = node.line
    ev.description = node.value.strip() if node.value.strip() not in ("", "Y") else ""
    ev.citations = _read_citations(node)
    return ev


def _assign_ordinals(events: list) -> None:
    seen: dict = {}
    for ev in events:
        key = (ev.owner, ev.event_type)
        ev.ordinal = seen.get(key, 0)
        seen[key] = ev.ordinal + 1


@dataclass
class Tree:
    individuals: dict = field(default_factory=dict)
    families: dict = field(default_factory=dict)
    sources: dict = field(default_factory=dict)
    media: dict = field(default_factory=dict)
    header: dict = field(default_factory=dict)
    #: EVEN blocks that were parsed but deliberately not turned into Events
    suppressed: list = field(default_factory=list)
    #: (individual MARR, FAM MARR) pairs folded into one event
    folded: list = field(default_factory=list)
    #: (individual MARR, reason) for a marriage only on the person: it stays
    #: a person-level Event here, and the plugin's own import drops it
    person_marriages: list = field(default_factory=list)
    #: Problems met while reading: skipped lines, recovered characters
    warnings: list = field(default_factory=list)

    @property
    def events(self) -> list:
        out = []
        for i in self.individuals.values():
            out.extend(i.events)
        for f in self.families.values():
            out.extend(f.events)
        return out


def parse(path: str, warn=None) -> Tree:
    """Read the file into a Tree.

    Reading problems go to `tree.warnings` and are each passed to `warn`
    (default: printed to stderr), so a damaged file never loses data silently.
    """
    tree = Tree()
    records = _tree(path, tree.warnings)
    if warn is None:
        def warn(message):
            print(f"warning: {message}", file=sys.stderr)
    for message in tree.warnings:
        warn(message)
    for rec in records:
        if rec.tag == "HEAD":
            sour = rec.first("SOUR")
            plac = rec.first("PLAC")
            tree.header = {
                "source": sour.value if sour else "",
                "version": (rec.first("GEDC").val("VERS") if rec.first("GEDC") else ""),
                "date": rec.val("DATE"),
                "charset": rec.val("CHAR"),
                #: the HEAD's `1 PLAC` / `2 FORM`: empty components in a
                #: PLAC are then positional placeholders the host writes
                "plac_form": plac.val("FORM") if plac else "",
            }
        elif rec.tag == "INDI":
            ind = Individual(xref=rec.xref, line=rec.line)
            all_names = rec.all("NAME")
            if all_names:
                name = all_names[0]
                ind.name = name.value.replace("/", "").strip()
                ind.given = name.val("GIVN")
                ind.surname = name.val("SURN")
                ind.suffix = name.val("NSFX")
                seen = {ind.name}
                for extra in all_names[1:]:
                    value = extra.value.replace("/", "").strip()
                    if value and value not in seen:
                        seen.add(value)
                        ind.alt_names.append(value)
                # Ancestry keeps married and alternate names as an Also Known
                # As fact, not in the surname field. See the upstream-ancestry convention, "Names in
                # the upstream tree".
                for fact in rec.all("FACT"):
                    if fact.val("TYPE").strip().upper() != "AKA":
                        continue
                    value = (fact.val("NOTE") or fact.value).strip()
                    if value and value not in seen:
                        seen.add(value)
                        ind.alt_names.append(value)
            ind.sex = rec.val("SEX")
            ind.famc = [c.value.strip("@") for c in rec.all("FAMC")]
            ind.fams = [c.value.strip("@") for c in rec.all("FAMS")]
            ind.media = [c.value.strip("@") for c in rec.all("OBJE") if c.value.startswith("@")]
            ind.citations = _read_citations(rec)
            for child in rec.children:
                ev = _read_event(ind.xref, child)
                if ev is not None:
                    ind.events.append(ev)
            _assign_ordinals(ind.events)
            tree.individuals[ind.xref] = ind
        elif rec.tag == "FAM":
            fam = Family(xref=rec.xref, line=rec.line)
            fam.husband = rec.val("HUSB").strip("@")
            fam.wife = rec.val("WIFE").strip("@")
            fam.children = [c.value.strip("@") for c in rec.all("CHIL")]
            for chil in rec.all("CHIL"):
                rel = {tag: chil.val(sub).strip().lower()
                       for tag, sub in (("HUSB", "_FREL"), ("WIFE", "_MREL"))
                       if chil.val(sub).strip()}
                if rel:
                    fam.pedigree[chil.value.strip("@")] = rel
            couple = tuple(sorted(x for x in (fam.husband, fam.wife) if x))
            for child in rec.children:
                ev = _read_event(fam.xref, child)
                if ev is not None:
                    ev.shared = True
                    ev.couple = couple
                    fam.events.append(ev)
            _assign_ordinals(fam.events)
            tree.families[fam.xref] = fam
        elif rec.tag == "SOUR":
            src = SourceRec(xref=rec.xref, title=rec.val("TITL"), author=rec.val("AUTH"))
            publ = rec.first("PUBL")
            if publ is not None:
                src.publisher = publ.value
            repo = rec.first("REPO")
            if repo is not None:
                src.repository = repo.value.strip("@")
            tree.sources[src.xref] = src
        elif rec.tag == "OBJE":
            fil = rec.first("FILE")
            obj = MediaObj(xref=rec.xref, oid=rec.val("_OID"),
                           file=(fil.value.strip() if fil is not None else ""))
            if fil is not None:
                obj.title = fil.val("TITL")
                form = fil.first("FORM")
                if form is not None:
                    obj.form = form.value
                    obj.mtype = form.val("_MTYPE")
            tree.media[obj.xref] = obj

    # EVEN blocks that will never become Events, recorded so a run can say so.
    for ind in tree.individuals.values():
        for ev in list(ind.events):
            if ev.tag != "EVEN":
                continue
            _, disposition = classify_even(ev.even_type)
            if disposition != "travel":
                ind.events.remove(ev)
                tree.suppressed.append((disposition, ev))
        _assign_ordinals(ind.events)
    _fold_marriages(tree)
    return tree


def _same_date(a: str, b: str) -> bool:
    """Both dated, and one is the other or a more precise form of it."""
    return bool(a and b) and (a.startswith(b) or b.startswith(a))


def _fold_marriages(tree: Tree) -> None:
    """Fold an individual `1 MARR` into the family marriage it repeats.

    Ancestry can carry one marriage twice: on the FAM, and as a MARR fact on
    one spouse's INDI -- often the copy holding the place. Created from both,
    the couple's timeline shows the marriage twice. The INDI copy folds when
    exactly one of the person's FAM marriages has a compatible date; an
    undated one cannot be told from a second marriage and is left alone. A
    place only the INDI copy carries moves onto the FAM event.
    """
    for ind in tree.individuals.values():
        for ev in ind.events:
            if ev.tag != "MARR":
                continue
            targets = [fe for f in ind.fams if f in tree.families
                       for fe in tree.families[f].events
                       if fe.tag == "MARR" and _same_date(ev.date, fe.date)]
            if len(targets) != 1:
                fams = [f for f in ind.fams if f in tree.families]
                if not fams:
                    why = "no family"
                elif not ev.date:
                    why = "undated"
                elif not targets:
                    why = "no family marriage on this date"
                else:
                    why = "several family marriages on this date"
                tree.person_marriages.append((ev, why))
                continue
            ev.folded = True
            if not targets[0].place:
                targets[0].place = ev.place
            tree.folded.append((ev, targets[0]))
