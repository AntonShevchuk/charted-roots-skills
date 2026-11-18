"""Create the notes a GEDCOM record has no counterpart for.

Creation is the largest and least reversible half of a sync, so it is gated
behind `--create` and never runs by default.

What this deliberately does **not** create:

* **Places.** Only a quarter of the export's PLAC strings resolve to a Place
  note, because upstream records historical and native forms (`Deutschland`,
  `Preußen`, `Danmark`) against an English gazetteer. Minting the rest would
  add hundreds of notes on an anachronistic chain, and the vault model is explicit
  that the place hierarchy is a schema decision and its own deliberate pass.
  An unresolved place is left off the new note and reported.
* **Anything on the suppression list.** Obituary, testament and press-notice
  `EVEN` blocks are Sources reporting an event, not events.
* **A per-document Source for an imported Event.** The vault model forbids it.
"""

from __future__ import annotations

import os
import random
import re
import unicodedata
from dataclasses import dataclass, field

from . import citations as citations_mod
from . import dates
from . import events as events_mod
from . import gedcom
from . import places as places_mod
from . import vault
from .config import BUILTIN_SOURCE_TYPES

_RNG = random.SystemRandom()
#: The plugin's own sanitiser, so a name produces the same filename here.
_STRIP = re.compile(r'[\\/:*?"<>|()\[\]{}]')
_WS = re.compile(r'\s+')

PERSON_BODY = """# Research Notes

```charted-roots-media
columns: 3
size: medium
editable: true
```

```charted-roots-timeline
sort: chronological
```

```charted-roots-relationships
type: immediate
```
"""


def mint_cr_id(taken: set) -> str:
    """A cr_id in the plugin's `lll-ddd-lll-ddd` shape, rejected into `taken`.

    The plugin mints without checking, which is a latent collision; this
    rejects against every cr_id in the vault and every one minted this run.
    """
    letters = "abcdefghijklmnopqrstuvwxyz"
    while True:
        value = "%s-%s-%s-%s" % (
            "".join(_RNG.choice(letters) for _ in range(3)),
            "".join(str(_RNG.randrange(10)) for _ in range(3)),
            "".join(_RNG.choice(letters) for _ in range(3)),
            "".join(str(_RNG.randrange(10)) for _ in range(3)),
        )
        if value not in taken:
            taken.add(value)
            return value


#: Filesystems cap a name at 255 bytes; leave room for a collision suffix and
#: `.md`.
_NAME_BYTES = 240


def _unescape(name: str) -> str:
    """Ancestry HTML-escapes `>` in hierarchical titles (`ARCHION … &gt; …`).

    A literal `>` cannot be a filename -- Obsidian refuses it and the plugin's
    rule strips it -- so the separator becomes `→`. `&amp;` is plain `&`, which a
    filename can hold. The `title:` keeps the
    export's text; only the name changes.
    """
    return name.replace("&gt;", "→").replace("&amp;", "&")


def _clip_bytes(text: str, limit: int) -> str:
    while len(text.encode()) > limit:
        text = text[:-1]
    return text


def sanitise(name: str, cap: int | None = 100) -> str:
    """The plugin's filename rule: strip the illegal set, collapse, cap at 100.

    `cap=None` keeps the whole name up to the filesystem's byte limit -- for
    Sources, whose title is the name, and a title cut at 100 characters no
    longer says which register it is.
    """
    cleaned = _STRIP.sub("", unicodedata.normalize("NFC", _unescape(name))).strip()
    cleaned = _WS.sub(" ", cleaned)
    cleaned = cleaned[:cap] if cap is not None else _clip_bytes(cleaned, _NAME_BYTES)
    return (cleaned.strip() or "Unknown")


def unique_path(folder: str, stem: str, used: set, sep: str = " ",
                cap: int | None = 100) -> str:
    """A free path for `stem`, disambiguating the plugin's way with ` N`.

    Events pass `sep="-"`: the importer numbers a person's repeated events
    `Residence of X-1`, `-2`, and `events.filename_ordinal` reads only that
    form. A space suffix would sort every new Event as the first occurrence.

    The suffix is fitted *inside* the 100-character cap. Appending it and
    truncating afterwards regenerates the same name for any stem already at
    the cap -- several Source titles are -- and loops forever.
    """
    base = sanitise(stem, cap)
    candidate = os.path.join(folder, f"{base}.md")
    n = 1
    while candidate in used or os.path.exists(candidate):
        suffix = f"{sep}{n}"
        trimmed = (base[:cap - len(suffix)] if cap is not None else base).strip()
        candidate = os.path.join(folder, f"{trimmed}{suffix}.md")
        n += 1
        if n > 1000:
            raise RuntimeError(f"cannot find a free filename for {stem!r}")
    used.add(candidate)
    return candidate


#: A filename is at most 255 bytes; a Citation stem gets what `.md` and any
#: collision suffix leave.
_NAME_MAX = 255

#: Tried in turn, and only on a Citation name that would not fit otherwise:
#: the standard German abbreviations first, then `Kirchenkreis`. A name that
#: fits keeps its source title whole.
_ABBREVIATIONS = (
    (("Landeskirchliches Archiv", "LKA"),
     ("Evangelisch-Lutherischen", "Ev.-Luth."),
     ("Evangelischen", "Ev.")),
    (("Kirchenkreis", "KK"),),
)


def _clean(text: str) -> str:
    return _WS.sub(" ", _STRIP.sub("", unicodedata.normalize(
        "NFC", _unescape(text))))


def citation_stem(source_name: str, subject: str, fact: str,
                  suffix: str = "") -> str:
    """`Citation - <source> - <person> <fact>`, never cut at the fact.

    Citations are not held to the plugin's 100-character cap -- the import
    wrote them at up to 217 -- because the tail is what tells one person's
    citations apart. Cutting at 100 dropped person and fact from every long
    Source title. A name over the filesystem limit abbreviates the source
    part (`_ABBREVIATIONS`), and only if that is not enough cuts its end.
    """
    limit = _NAME_MAX - len(".md") - len(suffix.encode())
    head = _clean(f"Citation - {source_name}").strip()
    tail = _clean(f" - {subject} {fact}").rstrip()
    for step in ((),) + _ABBREVIATIONS:
        for long, short in step:
            head = head.replace(long, short)
        if len((head + tail).encode()) <= limit:
            return head + tail
    room = limit - len(tail.encode()) - len("…".encode())
    return _clip_bytes(head, room).rstrip() + "…" + tail


def citation_path(folder: str, source_name: str, subject: str, fact: str,
                  used: set) -> str:
    """A free path for a citation, ` N` after the fact as the import did."""
    n = 0
    while True:
        suffix = f" {n}" if n else ""
        stem = citation_stem(source_name, subject, fact, suffix)
        candidate = os.path.join(folder, f"{stem}{suffix}.md")
        if candidate not in used and not os.path.exists(candidate):
            used.add(candidate)
            return candidate
        n += 1
        if n > 1000:
            raise RuntimeError(f"cannot find a free filename for {stem!r}")


@dataclass
class NewNote:
    path: str
    fm: dict
    body: str
    kind: str
    note: str = ""

    def text(self) -> str:
        lines = ["---"]
        for key, value in self.fm.items():
            if isinstance(value, list):
                if not value:
                    lines.append(f"{key}:")
                    continue
                lines.append(f"{key}:")
                lines.extend(f"  - {vault.quote(str(v))}" for v in value)
            elif value == "" or value is None:
                lines.append(f"{key}:")
            else:
                lines.append(f"{key}: {vault.quote(str(value))}")
        lines.append("---")
        return "\n".join(lines) + "\n" + self.body


@dataclass
class CreationPlan:
    people: list = field(default_factory=list)
    sources: list = field(default_factory=list)
    events: list = field(default_factory=list)
    citations: list = field(default_factory=list)
    #: (xref, PLAC) pairs left off a new note because the place is unknown
    unresolved_places: list = field(default_factory=list)
    #: GEDCOM source ids with no vault Source, so a Citation cannot be made
    skipped_citations: list = field(default_factory=list)
    #: INDI not created because they look like an existing note
    skipped_people: list = field(default_factory=list)
    #: GEDCOM events the matcher could not pair but the vault already holds
    already_present: list = field(default_factory=list)

    @property
    def all(self) -> list:
        return self.people + self.sources + self.events + self.citations

    def counts(self) -> dict:
        return {"person": len(self.people), "source": len(self.sources),
                "event": len(self.events), "citation": len(self.citations)}


def _place_link(plac: str, place_index, unresolved: list, owner: str):
    """A `[[Place]]` link, or None when the PLAC names nothing in the vault."""
    if not plac:
        return None
    if gedcom.non_place_reason(plac):
        unresolved.append((owner, plac, "not a place"))
        return None
    note = place_index.find(plac)
    if note is None:
        unresolved.append((owner, plac, "no Place note"))
        return None
    return f"[[{note.basename}]]"


def build_person(ind, cfg, place_index, taken_ids, used_paths, unresolved) -> NewNote:
    """A new Person note: scalars only. Relationships come in a later pass."""
    fm = {
        "cr_id": mint_cr_id(taken_ids),
        "cr_type": "person",
        "name": ind.name or "Unknown",
    }
    birth = next((e for e in ind.events if e.event_type == "birth"), None)
    death = next((e for e in ind.events if e.event_type == "death"), None)
    burial = next((e for e in ind.events if e.event_type == "burial"), None)
    born = dates.person_form(birth.date) if birth is not None else ""
    died = dates.person_form(death.date) if death is not None else ""
    if born:
        fm["born"] = born
    if died:
        fm["died"] = died
    if birth is not None:
        link = _place_link(birth.place, place_index, unresolved, ind.xref)
        if link:
            fm["birth_place"] = link
    if death is not None:
        link = _place_link(death.place, place_index, unresolved, ind.xref)
        if link:
            fm["death_place"] = link
    if burial is not None:
        if burial.date:
            fm["burial_date"] = burial.date
        link = _place_link(burial.place, place_index, unresolved, ind.xref)
        if link:
            fm["burial_place"] = link
    if ind.given:
        fm["given_name"] = ind.given
    if ind.surname:
        fm["surnames"] = [s.strip() for s in ind.surname.split(",") if s.strip()]
    if ind.suffix:
        fm["name_suffix"] = ind.suffix
    if ind.sex in ("M", "F"):
        fm["sex"] = ind.sex
    occupation = next((e for e in ind.events if e.event_type == "occupation"), None)
    if occupation is not None and occupation.description:
        fm["occupation"] = occupation.description
    fm["external_id"] = ind.xref
    fm["external_id_source"] = "gedcom"
    if ind.alt_names:
        fm["aliases"] = list(ind.alt_names)

    path = unique_path(cfg.people, ind.name or "Unknown", used_paths)
    note = ""
    if os.path.basename(path)[:-3] != sanitise(ind.name or "Unknown"):
        note = "filename disambiguated; another note already uses this name"
    return NewNote(path, fm, PERSON_BODY, "person", note)


#: Keyword -> registered source_type. `document` is never valid, and `custom`
#: is a smell, so an unmatched title is reported rather than guessed at.
_SOURCE_TYPE_HINTS = [
    ("census", "census"), ("baptism", "church_record"), ("marriage", "church_record"),
    ("burial", "church_record"), ("kirchenb", "church_record"),
    ("taufregister", "church_record"), ("heiratsregister", "church_record"),
    ("sterberegister", "church_record"), ("bestattungen", "church_record"),
    ("lutheran", "church_record"), ("evangelische", "church_record"),
    ("birth", "vital_record"), ("death", "vital_record"),
    ("personenstandsregister", "vital_record"),
    ("obituary", "obituary"), ("newspaper", "newspaper"), ("newspapers.com", "newspaper"),
    ("passenger", "immigration"), ("emigration", "immigration"),
    ("naturalization", "immigration"), ("arriving", "immigration"),
    ("draft", "military"), ("military", "military"), ("veteran", "military"),
    ("probate", "probate"), ("will", "probate"),
    ("directory", "directory"), ("adressbuch", "directory"),
    ("yearbook", "education"), ("school", "education"),
    ("cemetery", "cemetery"), ("grave", "cemetery"), ("memorial", "cemetery"),
    ("family tree", "compiled_genealogy"), ("genealog", "compiled_genealogy"),
    ("tree", "compiled_genealogy"),
]


def infer_source_type(title: str, registered: set) -> str | None:
    low = (title or "").lower()
    for needle, kind in _SOURCE_TYPE_HINTS:
        if needle in low and kind in registered:
            return kind
    return None


def build_source(src, cfg, taken_ids, used_paths, registered) -> NewNote:
    fm = {
        "cr_type": "source",
        "cr_id": mint_cr_id(taken_ids),
        "title": src.title or f"Source {src.xref}",
    }
    kind = infer_source_type(src.title, registered)
    note = ""
    if kind:
        fm["source_type"] = kind
    else:
        note = "source_type unassigned -- set it by hand rather than `document`"
    if src.author:
        fm["author"] = src.author
    if src.publisher:
        fm["repository"] = src.publisher
    fm["confidence"] = "unknown"
    fm["gedcom_id"] = src.xref

    body = [f"# {fm['title']}", ""]
    if src.author:
        body += [f"**Author:** {src.author}", ""]
    if src.publisher:
        body += [f"**Publisher:** {src.publisher}", ""]
    body += [f"_Imported from GEDCOM source {src.xref}_", ""]
    path = unique_path(cfg.sources, fm["title"], used_paths, cap=None)
    return NewNote(path, fm, "\n".join(body), "source", note)


#: How an event_type renders in a title.
_TITLE = {
    "birth": "Birth", "death": "Death", "marriage": "Marriage", "divorce": "Divorce",
    "burial": "Burial", "baptism": "Baptism", "residence": "Residence",
    "occupation": "Occupation", "naturalization": "Naturalization",
    "probate": "Probate", "graduation": "Graduation", "emigration": "Emigration",
    "immigration": "Immigration", "census": "Census", "will": "Will",
    "military": "Military service",
}


def build_event(ev, tree, cfg, place_index, taken_ids, used_paths,
                name_of, unresolved) -> NewNote | None:
    participants = [name_of(x) for x in events_mod._owner_people(ev, tree)]
    participants = [p for p in participants if p]
    if not participants:
        return None
    label = _TITLE.get(ev.event_type, ev.event_type.capitalize())
    if len(participants) == 2:
        title = f"{label} of {participants[0]} and {participants[1]}"
    else:
        title = f"{label} of {participants[0]}"

    fm = {
        "cr_type": "event",
        "cr_id": mint_cr_id(taken_ids),
        "title": title,
        "event_type": ev.event_type,
        "date_precision": ev.precision if ev.date else "unknown",
    }
    if ev.date:
        fm["date"] = events_mod.event_date(ev)
    fm["persons"] = [f"[[{p}]]" for p in participants]
    link = _place_link(ev.place, place_index, unresolved, ev.owner)
    if link:
        fm["place"] = link
    fm["confidence"] = "unknown"
    if ev.description:
        fm["description"] = ev.description

    path = unique_path(cfg.events, title, used_paths, sep="-")
    return NewNote(path, fm, f"# {title}\n", "event")


def build_citation(key, cfg, taken_ids, used_paths, name_of_crid) -> NewNote | None:
    subject_id, source_name, fact, page = key
    subject = name_of_crid(subject_id)
    if not subject:
        return None
    fm = {
        "cr_type": "citation",
        "cr_id": mint_cr_id(taken_ids),
        "source": f"[[{source_name}]]",
        "subject": f"[[{subject}]]",
        "subject_id": subject_id,
        "fact": fact,
        "page": page,
    }
    path = citation_path(cfg.citations, source_name, subject, fact, used_paths)
    return NewNote(path, fm, "", "citation")


def plan_creation(tree, cfg, place_index, person_plan, source_plan,
                  event_match, citation_match, existing_notes) -> CreationPlan:
    """Everything that would be created, with no writes."""
    plan = CreationPlan()
    taken_ids = {n.scalar("cr_id") for n in existing_notes if n.scalar("cr_id")}
    used_paths: set = set()
    registered = config_registered(cfg)

    # -- Sources first: Events and Citations link to them by name.
    for action in source_plan.of("source", "create"):
        src = tree.sources[action.key]
        plan.sources.append(build_source(src, cfg, taken_ids, used_paths, registered))

    # -- People next: Events name them by filename. A person who looks like
    # an existing vault-native note is never created; creating a second note
    # for someone already researched here is the duplication this script
    # exists to prevent, and the resolution is a human call.
    for action in person_plan.of("person", "candidate"):
        plan.skipped_people.append(action)
    for action in person_plan.of("person", "create"):
        ind = tree.individuals[action.key]
        plan.people.append(build_person(ind, cfg, place_index, taken_ids,
                                        used_paths, plan.unresolved_places))

    # A participant's note may be brand new, so resolve names through both the
    # existing vault and this run's plan.
    name_by_xref = {}
    for note in existing_notes:
        ext = note.scalar("external_id")
        if ext:
            name_by_xref[ext] = note.basename
    for new in plan.people:
        name_by_xref[new.fm["external_id"]] = os.path.basename(new.path)[:-3]

    def name_of(xref):
        return name_by_xref.get(xref)

    # -- Events.
    #
    # `uncreated` is not sufficient on its own. Where a person has events the
    # matcher cannot tell apart -- two undated residences, say -- neither the
    # content nor the positional stage can pair them, so they stay in
    # `uncreated` even though the vault already holds them. Creating from that
    # list alone adds the same event on every run, forever.
    #
    # So creation is capped by a count: for each (participant, type, date) the
    # vault may hold no more than the export does, and only the shortfall is
    # created. That converges whether or not the matcher could pair them.
    #
    # Only Events the matcher left *unpaired* count. One already paired with
    # another block is that block's Event: counting it too let a 1993
    # Riverton residence stand in for a missing 1993 Springfield one.
    suppressed = {events_mod.ged_key(ev) for _, ev in tree.suppressed}
    ext_by_basename = {n.basename: n.scalar("external_id")
                       for n in existing_notes if n.scalar("external_id")}
    paired = {p.vault_note.path for p in event_match.pairs}
    have_counts: dict = {}
    for note in existing_notes:
        if note.scalar("cr_type") != "event" or note.path in paired:
            continue
        for person in note.links("persons"):
            xref = ext_by_basename.get(person)
            if xref:
                have_counts[(xref, note.scalar("event_type"),
                             note.scalar("date"))] = have_counts.get(
                    (xref, note.scalar("event_type"), note.scalar("date")), 0) + 1

    for ev in event_match.uncreated:
        if events_mod.ged_key(ev) in suppressed:
            continue
        owners = events_mod._owner_people(ev, tree)
        slot = (sorted(owners)[0], ev.event_type, events_mod.event_date(ev))
        if have_counts.get(slot, 0) > 0:
            have_counts[slot] -= 1
            plan.already_present.append(ev)
            continue
        built = build_event(ev, tree, cfg, place_index, taken_ids, used_paths,
                            name_of, plan.unresolved_places)
        if built is not None:
            plan.events.append(built)
            for owner in owners:
                key = (owner, ev.event_type, events_mod.event_date(ev))
                have_counts[key] = have_counts.get(key, 0)

    # -- Citations. A Source minted this run is addressable by its title.
    crid_by_ext = {}
    for note in existing_notes:
        ext = note.scalar("external_id")
        if ext:
            crid_by_ext[ext] = note.scalar("cr_id")
    for new in plan.people:
        crid_by_ext[new.fm["external_id"]] = new.fm["cr_id"]
    name_by_crid = {v: name_by_xref[k] for k, v in crid_by_ext.items()
                    if k in name_by_xref}

    def name_of_crid(crid):
        return name_by_crid.get(crid)

    # Re-derive the Citation candidates with this run's new Sources included.
    # The matcher ran before they existed, so it filed every citation whose
    # Source was missing as "unresolved" -- 299 of them -- which would
    # otherwise only appear on a second run.
    source_name_by_gid = {}
    for note in existing_notes:
        if note.scalar("gedcom_id"):
            source_name_by_gid[note.scalar("gedcom_id")] = note.basename
    for new in plan.sources:
        source_name_by_gid[new.fm["gedcom_id"]] = os.path.basename(new.path)[:-3]

    existing_keys = {
        citations_mod.vault_key(n) for n in existing_notes
        if n.scalar("cr_type") == "citation"
    }
    wanted: list = []
    seen_keys: set = set()
    for ev in tree.events:
        fact = citations_mod.FACT.get(ev.event_type)
        if not fact:
            continue
        owners = [ev.owner] if ev.owner not in tree.families else \
            [x for x in (tree.families[ev.owner].husband,
                         tree.families[ev.owner].wife) if x][:1]
        for owner in owners:
            subject_id = crid_by_ext.get(owner)
            for src_xref, page in ev.citations:
                if not page or subject_id is None:
                    continue
                source_name = source_name_by_gid.get(src_xref)
                if source_name is None:
                    continue
                key = (subject_id, source_name, fact,
                       citations_mod.normalise_page(page))
                if key in existing_keys or key in seen_keys:
                    continue
                seen_keys.add(key)
                wanted.append(key)

    for key in wanted:
        built = build_citation(key, cfg, taken_ids, used_paths, name_of_crid)
        if built is None:
            plan.skipped_citations.append(key)
        else:
            plan.citations.append(built)
    return plan


def config_registered(cfg) -> set:
    return BUILTIN_SOURCE_TYPES | cfg.custom_source_types


def spouse_form(note) -> str:
    """Which spouse convention a note already uses: legacy, numbered or none.

    The vault model: some notes use a legacy unnumbered `spouse` / `spouse_id`, no
    note should use both forms, and when adding a spouse you follow the form
    that note already uses. 71 notes in the development vault would otherwise gain a second form.
    """
    if note is None:
        return "numbered"
    if "spouse" in note.fm or "spouse_id" in note.fm:
        return "legacy"
    if any(k[:6] == "spouse" and k[6:7].isdigit() for k in note.fm):
        return "numbered"
    return "numbered"


#: `_FREL` / `_MREL` values that make the HUSB / WIFE a birth parent.
BIRTH = {"birth", "natural", "biological"}

#: Which child-side property each pedigree writes, per parent role. A value
#: not listed here, nor in GUARDIAN (foster, unknown, ...), writes nothing:
#: a birth link would be false.
PARENT_KEYS = {
    **{rel: {"HUSB": "father", "WIFE": "mother"} for rel in BIRTH},
    "step": {"HUSB": "stepfather", "WIFE": "stepmother"},
    "adopted": {"HUSB": "adoptive_father", "WIFE": "adoptive_mother"},
}

#: Pedigrees written as the plugin's built-in Guardian relationship: `guardian`
#: on the ward, its inverse `ward` on each guardian. Both are lists (a child
#: can have a guardian couple), each with a parallel `_id` list. The plugin
#: does not write the inverse of a custom relationship, so both sides are
#: written here; it keeps them off the family tree.
GUARDIAN = {"guardian"}

#: List properties whose `<key>_id` companion is parallel and moves with it.
PAIRED_LISTS = ("children", "guardian", "ward")


def relationship_updates(tree, cfg, existing_notes, new_people,
                         place_index=None) -> tuple:
    """(rels, migrations) -- relationships to write, and notes needing a decision.

    Both sides are written here. Obsidian must be closed for `--apply`, so the
    plugin's reciprocal sync is not running and the vault model's instruction for
    that case applies: write both sides by hand. `children` and `children_id`
    are built from one ordered list, so they cannot desynchronise.
    """
    if place_index is None:
        place_index = places_mod.load(cfg.places)
    by_xref = {}
    note_by_xref = {}
    for note in existing_notes:
        ext = note.scalar("external_id")
        if ext:
            by_xref[ext] = (note.basename, note.scalar("cr_id"))
            note_by_xref[ext] = note
    for new in new_people:
        by_xref[new.fm["external_id"]] = (
            os.path.basename(new.path)[:-3], new.fm["cr_id"])

    rels: dict = {}
    migrations: list = []
    spouses: dict = {}
    links: dict = {}      # (xref, "guardian" | "ward") -> [(name, cr_id)]

    def add_link(xref, key, target):
        if xref not in by_xref:
            return
        have = links.setdefault((xref, key), [])
        if target not in have:
            have.append(target)

    def put(xref, key, value):
        if xref in by_xref:
            rels.setdefault(xref, {})[key] = value

    for fam in tree.families.values():
        parents = (("HUSB", fam.husband), ("WIFE", fam.wife))

        for child in fam.children:
            for tag, parent_xref in parents:
                parent = by_xref.get(parent_xref)
                key = PARENT_KEYS.get(fam.relation(child, tag), {}).get(tag)
                if parent and key:
                    put(child, key, f"[[{parent[0]}]]")
                    put(child, f"{key}_id", parent[1])
                if parent and child in by_xref and fam.relation(child, tag) in GUARDIAN:
                    add_link(child, "guardian", parent)
                    add_link(parent_xref, "ward", by_xref[child])

        for tag, parent_xref in parents:
            # `children` holds birth children only; a step or adoptive
            # parent is recorded on the child's side alone.
            kids = [by_xref[c] for c in fam.children
                    if c in by_xref and fam.relation(c, tag) in BIRTH]
            if kids and parent_xref in by_xref:
                existing = rels.get(parent_xref, {})
                names = [n for n in existing.get("children", [])]
                ids = list(existing.get("children_id", []))
                for name, crid in kids:
                    link = f"[[{name}]]"
                    if link not in names:
                        names.append(link)
                        ids.append(crid)
                put(parent_xref, "children", names)
                put(parent_xref, "children_id", ids)

        marriage = next((e for e in fam.events if e.event_type == "marriage"), None)
        for a, b in ((fam.husband, fam.wife), (fam.wife, fam.husband)):
            if a not in by_xref or b not in by_xref:
                continue
            spouses.setdefault(a, []).append((by_xref[b], marriage))

    for (xref, key), targets in links.items():
        # Keep what the vault already lists, in its order; add what is missing.
        note = note_by_xref.get(xref)
        names = note.as_list(key) if note is not None else []
        ids = note.as_list(f"{key}_id") if note is not None else []
        if len(names) != len(ids):
            continue          # a desynced pair is a human fix, not a sync's
        for name, crid in targets:
            if crid not in ids:
                names.append(f"[[{name}]]")
                ids.append(crid)
        put(xref, key, names)
        put(xref, f"{key}_id", ids)

    for xref, partners in spouses.items():
        form = spouse_form(note_by_xref.get(xref))
        if form == "legacy":
            (name, crid), marriage = partners[0]
            put(xref, "spouse", f"[[{name}]]")
            put(xref, "spouse_id", crid)
            if len(partners) > 1:
                migrations.append((xref, note_by_xref[xref].basename, len(partners)))
            continue
        for slot, ((name, crid), marriage) in enumerate(partners, start=1):
            put(xref, f"spouse{slot}", f"[[{name}]]")
            put(xref, f"spouse{slot}_id", crid)
            if marriage is not None and marriage.date:
                put(xref, f"spouse{slot}_marriage_date", marriage.date)
            if marriage is not None and marriage.place:
                # A Place link, as on every other place field. A PLAC that
                # resolves to no Place note is not written: the plugin counts
                # plain text as a missing place note. A link the vault already
                # holds is curated and kept.
                key = f"spouse{slot}_marriage_location"
                have = note_by_xref[xref].scalar(key) if xref in note_by_xref else ""
                hit = place_index.find(marriage.place)
                if hit is not None and "[[" not in have:
                    put(xref, key, f"[[{hit.basename}]]")
    return rels, migrations


def relationship_changes(rels, existing_notes, new_paths) -> dict:
    """Narrow `rels` to what actually differs from the vault.

    Without this a sync rewrites every note it computed a relationship for,
    including reordering children lists that were already correct. The vault model:
    where an existing note's list order differs but the set matches, leave it
    alone -- reordering a correct pair is churn and risks the very desync it
    pretends to prevent.
    """
    by_xref = {}
    for note in existing_notes:
        ext = note.scalar("external_id")
        if ext:
            by_xref[ext] = note

    out: dict = {}
    for xref, wanted in rels.items():
        note = by_xref.get(xref)
        if note is None:
            # A note created this run: it carries no relationships yet, so
            # everything computed for it is new.
            if xref in new_paths:
                out[xref] = wanted
            continue
        diff = {}
        for key, value in wanted.items():
            if isinstance(value, list):
                have = note.as_list(key)
                if set(have) == set(value):
                    continue          # same set, keep the vault's order
                if len(have) > len(value):
                    continue          # the vault knows more; never trim
                diff[key] = value
            else:
                if str(note.scalar(key) or "") != str(value):
                    diff[key] = value
        # A list and its `_id` companion move together or not at all.
        for key in PAIRED_LISTS:
            if (key in diff) != (f"{key}_id" in diff):
                diff.pop(key, None)
                diff.pop(f"{key}_id", None)
        if diff:
            out[xref] = diff
    return out
