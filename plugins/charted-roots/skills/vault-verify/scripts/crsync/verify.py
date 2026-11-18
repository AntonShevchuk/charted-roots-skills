"""Vault invariants.

Each check returns a Result. Nothing here writes, and nothing needs a GEDCOM,
so this runs standalone as a baseline before and after any sync.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from . import config, dates, vault

_FENCED = re.compile(r'^([ \t]*)(`{3,}|~{3,}).*?^\1\2[ \t]*$', re.M | re.S)
_INLINE_CODE = re.compile(r'`[^`\n]*`')
# Inside a markdown table the alias pipe is escaped as `\|`, so the target can
# end with a stray backslash; `#`/`^` start a heading or block anchor.
_WIKILINK = re.compile(r'!?\[\[([^\]\n]+?)\]\]')


def link_target(raw: str) -> str:
    """The note a wikilink body names, minus alias and anchor."""
    # An anchor is `#heading` or `#^block`; a bare `^` is legal in a filename
    # and several archive-coded scans use one.
    t = raw.split('|', 1)[0].split('#', 1)[0]
    return t.rstrip('\\').strip()

#: Relational properties whose `_id` companion must stay parallel.
ID_COMPANIONS = [
    "father", "mother", "children", "parents", "stepfather", "stepmother",
    "adoptive_father", "adoptive_mother", "source_parent", "parent_place",
    "subject", "sources", "guardian", "ward",
] + [f"spouse{i}" for i in range(1, 6)] + ["spouse"]


@dataclass
class Result:
    name: str
    ok: bool
    detail: str = ""
    items: list = field(default_factory=list)

    def render(self, limit: int = 10) -> str:
        mark = "PASS" if self.ok else "FAIL"
        out = [f"  [{mark}] {self.name}" + (f" -- {self.detail}" if self.detail else "")]
        for item in self.items[:limit]:
            out.append(f"         {item}")
        if len(self.items) > limit:
            out.append(f"         ... and {len(self.items) - limit} more")
        return "\n".join(out)


def mask_code(text: str) -> str:
    """Blank out fenced blocks and inline code spans.

    `History/` deliberately quotes wikilinks to deleted notes; a naive scan
    reports them as broken.
    """
    text = _FENCED.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    return _INLINE_CODE.sub("", text)


class Index:
    """Every markdown note in the vault, loaded once."""

    def __init__(self, cfg: config.Config):
        self.cfg = cfg
        self.notes: dict = {}          # abs path -> Note
        self.by_basename: dict = {}    # basename -> [paths]
        self.by_cr_id: dict = {}       # cr_id -> [Note]
        self.attachments: set = set()  # non-md names, with and without extension
        self.attachment_count = 0      # non-md files on disk
        self._load()

    def _load(self):
        # Obsidian ignores dot-folders (.git, .obsidian, .claude, ...), so a
        # note there is no vault note and must not collide with one.
        skip = {"node_modules", "tools"}
        for dirpath, dirnames, filenames in os.walk(self.cfg.root):
            dirnames[:] = [d for d in dirnames
                           if d not in skip and not d.startswith(".")]
            for name in filenames:
                path = os.path.join(dirpath, name)
                if name.endswith(".md"):
                    note = vault.parse(path)
                    self.notes[path] = note
                    self.by_basename.setdefault(name[:-3], []).append(path)
                    crid = note.scalar("cr_id")
                    if crid:
                        self.by_cr_id.setdefault(crid, []).append(note)
                elif not name.startswith("."):
                    self.attachment_count += 1
                    self.attachments.add(name)
                    self.attachments.add(os.path.splitext(name)[0])

    def of_type(self, cr_type: str) -> list:
        return [n for n in self.notes.values() if n.scalar("cr_type") == cr_type]

    def in_folder(self, folder: str) -> list:
        folder = os.path.abspath(folder) + os.sep
        return [n for p, n in self.notes.items() if p.startswith(folder)]

    def resolves(self, target: str) -> bool:
        """True if a wikilink target names a note or attachment in the vault.

        Targets come in three shapes: a bare basename (the vault convention),
        a vault-relative path, and either of those with an explicit `.md`.
        """
        for t in {target.strip(), os.path.basename(target.strip())}:
            if not t:
                continue
            if t in self.by_basename or t in self.attachments:
                return True
            if t.endswith(".md") and t[:-3] in self.by_basename:
                return True
        return False


def check_frontmatter_parses(idx: Index) -> Result:
    bad = [os.path.relpath(n.path, idx.cfg.root) for n in idx.notes.values() if n.malformed]
    return Result("frontmatter blocks close", not bad,
                  f"{len(idx.notes)} notes scanned, {len(bad)} unterminated", bad)


def check_frontmatter_lines(idx: Index) -> Result:
    """Every frontmatter line must read as a key, a list item, or blank.

    A line this reader cannot classify is invisible to its span index: it
    sits inside the preceding key's span, so writing *that* key would splice
    the line away. The writer refuses such a note, which makes this check the
    way it gets found -- before a sync needs to write to it.
    """
    bad = []
    for n in idx.notes.values():
        rel = os.path.relpath(n.path, idx.cfg.root)
        for line in n.unparsed:
            bad.append(f"{rel}: {line.strip()!r}")
    return Result("every frontmatter line parses", not bad,
                  f"{len(bad)} lines the key index cannot see", bad)


def check_cr_id_unique(idx: Index) -> Result:
    dups = {k: v for k, v in idx.by_cr_id.items() if len(v) > 1}
    items = [f"{k}: " + ", ".join(os.path.relpath(n.path, idx.cfg.root) for n in v)
             for k, v in dups.items()]
    return Result("cr_id unique vault-wide", not dups,
                  f"{len(idx.by_cr_id)} ids, {len(dups)} duplicated", items)


def check_cr_type_valid(idx: Index) -> Result:
    bad = []
    for n in idx.notes.values():
        t = n.scalar("cr_type")
        if t and t not in config.CR_TYPES:
            bad.append(f"{os.path.relpath(n.path, idx.cfg.root)}: cr_type={t!r}")
    return Result("cr_type from the plugin vocabulary", not bad,
                  f"{len(bad)} invalid", bad)


def check_filenames(idx: Index) -> Result:
    bad = []
    for path in idx.notes:
        stem = os.path.basename(path)[:-3]
        if stem != stem.strip():
            bad.append(os.path.relpath(path, idx.cfg.root))
    dupes = {b: p for b, p in idx.by_basename.items() if len(p) > 1}
    items = bad + [f"basename not unique: {b}" for b in sorted(dupes)]
    return Result("filenames trimmed and unique", not items,
                  f"{len(bad)} padded, {len(dupes)} colliding", items)


def check_citation_subject_ids(idx: Index) -> Result:
    """A Citation's subject_id must equal the subject Person's cr_id."""
    bad = []
    for c in idx.of_type("citation"):
        subj = c.links("subject")
        sid = c.scalar("subject_id")
        rel = os.path.relpath(c.path, idx.cfg.root)
        if not subj:
            bad.append(f"{rel}: no subject wikilink")
            continue
        paths = idx.by_basename.get(subj[0])
        if not paths:
            bad.append(f"{rel}: subject [[{subj[0]}]] does not resolve")
            continue
        person = idx.notes[paths[0]]
        if person.scalar("cr_id") != sid:
            bad.append(f"{rel}: subject_id={sid} but [[{subj[0]}]] is {person.scalar('cr_id')}")
    return Result("Citation subject_id matches the Person's cr_id", not bad,
                  f"{len(bad)} mismatched", bad)


def check_citation_backlinks(idx: Index) -> Result:
    """Both directions: every Citation listed on its subject, and no phantoms."""
    citations = idx.of_type("citation")
    by_name = {c.basename: c for c in citations}
    listed_on: dict = {}
    phantom = []
    for p in idx.of_type("person"):
        for target in p.links("citations"):
            if target not in by_name:
                phantom.append(f"{p.basename}: citations lists [[{target}]] which is not a Citation")
            listed_on.setdefault(target, []).append(p.basename)

    missing = []
    for c in citations:
        subj = c.links("subject")
        if not subj:
            continue
        owners = listed_on.get(c.basename, [])
        if subj[0] not in owners:
            missing.append(f"{c.basename} -> not in [[{subj[0]}]] citations:")
    items = missing + phantom
    return Result("Citation <-> Person citations: both directions", not items,
                  f"{len(missing)} not listed on subject, {len(phantom)} phantom entries", items)


def check_id_companions(idx: Index) -> Result:
    """Each relational property and its `_id` twin must stay parallel."""
    bad = []
    for n in idx.notes.values():
        rel = os.path.relpath(n.path, idx.cfg.root)
        for key in ID_COMPANIONS:
            idkey = f"{key}_id"
            if key not in n.fm and idkey not in n.fm:
                continue
            vals = [v for v in n.as_list(key) if str(v).strip()]
            ids = [v for v in n.as_list(idkey) if str(v).strip()]
            if not vals and not ids:
                continue
            if idkey not in n.fm:
                continue  # no companion declared; place: and persons: legitimately have none
            if len(vals) != len(ids):
                bad.append(f"{rel}: {key} has {len(vals)} but {idkey} has {len(ids)}")
    return Result("relational properties parallel with their _id twin", not bad,
                  f"{len(bad)} desynchronised", bad)


def check_id_targets(idx: Index) -> Result:
    """Each `_id` value must be the cr_id of the note its wikilink names."""
    bad = []
    for n in idx.notes.values():
        rel = os.path.relpath(n.path, idx.cfg.root)
        for key in ID_COMPANIONS:
            idkey = f"{key}_id"
            if idkey not in n.fm:
                continue
            names = n.links(key)
            ids = [v for v in n.as_list(idkey) if str(v).strip()]
            if len(names) != len(ids):
                continue  # already reported by check_id_companions
            for name, want in zip(names, ids):
                paths = idx.by_basename.get(name)
                if not paths:
                    continue  # reported by the link check
                got = idx.notes[paths[0]].scalar("cr_id")
                if got and got != want:
                    bad.append(f"{rel}: {idkey} says {want} but [[{name}]] is {got}")
    return Result("_id values point at the right note", not bad, f"{len(bad)} wrong", bad)


def check_links(idx: Index) -> Result:
    """No dangling wikilinks, with fenced blocks and code spans masked."""
    broken: list = []
    documentation: list = []
    for path, n in idx.notes.items():
        rel = os.path.relpath(path, idx.cfg.root)
        targets = {link_target(m.group(1)) for m in _WIKILINK.finditer(mask_code(n.body))}
        for key in n.fm:
            targets.update(link_target(t) for t in n.links(key))
        for t in sorted(targets):
            if t and not idx.resolves(t):
                (documentation if rel.startswith("History" + os.sep) else broken
                 ).append(f"{rel}: [[{t}]]")
    detail = f"{len(broken)} dangling"
    if documentation:
        detail += f" ({len(documentation)} more in History/, which quotes dead links by design)"
    return Result("wikilinks resolve", not broken, detail, broken)


def check_event_shape(idx: Index) -> Result:
    """Events need a date or an explicit `date_precision: unknown`."""
    bad = []
    for e in idx.of_type("event"):
        prec = e.scalar("date_precision")
        if not e.scalar("date") and prec and prec != "unknown":
            bad.append(f"{e.basename}: date_precision={prec} but no date")
    return Result("Events with a specific precision carry a date", not bad,
                  f"{len(bad)} missing a date the import should have carried", bad)


def check_source_types(idx: Index) -> Result:
    valid = config.BUILTIN_SOURCE_TYPES | idx.cfg.custom_source_types
    bad = []
    for s in idx.of_type("source"):
        t = s.scalar("source_type")
        if t and t not in valid:
            bad.append(f"{s.basename}: source_type={t!r}")
    return Result("source_type registered", not bad,
                  f"{len(bad)} unregistered (source_type: document is never valid)", bad)


def check_place_types(idx: Index) -> Result:
    valid = config.PLACE_TYPES | idx.cfg.custom_place_types
    bad = []
    for p in idx.of_type("place"):
        t = p.scalar("place_type")
        if t and t not in valid:
            bad.append(f"{p.basename}: place_type={t!r}")
    return Result("place_type from the closed list", not bad, f"{len(bad)} invalid", bad)


def check_person_dates(idx: Index) -> Result:
    """`born` / `died` pass the plugin's *Validate date formats* command."""
    bad = []
    for p in idx.notes.values():
        # The command skips notes without a cr_id and calendar notes.
        if not p.scalar("cr_id") or p.scalar("fc-calendar"):
            continue
        for key in ("born", "died"):
            value = p.scalar(key)
            if value:
                err = dates.plugin_error(value, idx.cfg.settings)
                if err:
                    bad.append(f"{p.basename}: {key}={value!r}")
    return Result("born/died pass the plugin's date validator", not bad,
                  f"{len(bad)} rejected (c. YYYY, a to b; no BEF/AFT)", bad)


_LINK = re.compile(r'\[\[([^\]]+)\]\]')


def check_person_places(idx: Index) -> Result:
    """Person place fields resolve to a Place note, as the plugin resolves them.

    A port of the plugin's place references (`loadPlaceReferences`): every
    `birth_place`, `death_place`, `burial_place` and `spouseN_marriage_location`
    must name a Place by title, `aliases:`, `full_name` or filename -- as a
    wikilink, an `_id`, or plain text. One that does not is what the plugin's
    Data Quality calls a "missing place note"; this counts distinct values,
    as it does.
    """
    by_id, by_name = {}, {}
    for p in idx.of_type("place"):
        if not p.scalar("cr_id"):
            continue
        by_id[p.scalar("cr_id")] = p
        for name in [p.scalar("name") or p.scalar("title") or p.basename,
                     p.basename, p.scalar("full_name"), *p.as_list("aliases")]:
            if name:
                by_name.setdefault(name.lower().strip(), p)

    def resolves(raw: str, place_id: str) -> bool:
        m = _LINK.search(raw)
        if m:
            return m.group(1).lower().strip() in by_name
        if place_id:
            return place_id in by_id
        return raw.lower().strip() in by_name

    missing: dict = {}
    for n in idx.of_type("person"):
        refs = [(k, n.scalar(k), n.scalar(f"{k}_id"))
                for k in ("birth_place", "death_place", "burial_place")]
        i = 1
        while n.scalar(f"spouse{i}") or n.scalar(f"spouse{i}_id"):
            refs.append((f"spouse{i}_marriage_location",
                         n.scalar(f"spouse{i}_marriage_location"), ""))
            i += 1
        for key, raw, place_id in refs:
            if raw and not resolves(raw, place_id):
                missing.setdefault(raw, []).append(f"{n.basename}.{key}")
    items = [f"{raw!r}: {len(where)} ({where[0]}{', ...' if len(where) > 1 else ''})"
             for raw, where in sorted(missing.items(), key=lambda kv: -len(kv[1]))]
    return Result("Person places resolve to a Place note", not missing,
                  f"{len(missing)} missing place notes (the plugin's count)", items)


CHECKS = [
    check_frontmatter_parses,
    check_frontmatter_lines,
    check_cr_id_unique,
    check_cr_type_valid,
    check_filenames,
    check_citation_subject_ids,
    check_citation_backlinks,
    check_id_companions,
    check_id_targets,
    check_links,
    check_event_shape,
    check_source_types,
    check_place_types,
    check_person_dates,
    check_person_places,
]


def run(cfg: config.Config, idx: Index | None = None) -> list:
    idx = idx or Index(cfg)
    return [check(idx) for check in CHECKS]


def regressions(before: list, after: list) -> list:
    """Names of checks that passed before a run and fail after it.

    Paired by name, not by position. Both lists come from the same `CHECKS`
    today, so zipping them happens to work -- but a check inserted anywhere
    above the end would shift every comparison by one and report a
    pre-existing failure as this run's fault, which is the one thing this
    comparison exists to tell apart.

    A check present only in `after` counts as a regression: when the two runs
    disagree about what was checked, the loud reading is the safe one.
    """
    was_ok = {r.name: r.ok for r in before}
    return [r.name for r in after if not r.ok and was_ok.get(r.name, True)]
