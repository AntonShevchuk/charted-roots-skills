"""Place resolution, matching the plugin's own cache semantics.

The GEDCOM importer is the one place the plugin *does* deduplicate: it indexes
existing Place notes by normalised `full_name` and by `title|parent_place`,
then updates in place. This module reproduces those two indexes so the script
and the plugin agree on what an existing place is, and adds a diagnostic for
the notes that are invisible to the plugin's matcher.
"""

from __future__ import annotations

import re
import unicodedata

from . import vault

_WS = re.compile(r'\s+')
#: The importer expands these before matching, so `NY` and `New York` collide.
_US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
    "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
    "DC": "District of Columbia",
}


def normalise(place: str) -> str:
    """Trim, collapse whitespace and expand US state abbreviations."""
    parts = []
    for seg in (place or "").split(","):
        seg = _WS.sub(" ", seg.strip())
        if not seg:
            continue
        expanded = _US_STATES.get(seg.upper().rstrip("."))
        if expanded:
            parts.append(expanded)
            continue
        words = seg.split(" ")
        if len(words) >= 2:
            tail = _US_STATES.get(words[-1].upper().rstrip("."))
            if tail:
                parts.append(" ".join(words[:-1]))
                parts.append(tail)
                continue
        parts.append(seg)
    return ", ".join(parts)


def key(place: str) -> str:
    return unicodedata.normalize("NFC", normalise(place)).casefold()


class Index:
    """The plugin's two lookups, plus a note of what they cannot see."""

    def __init__(self, notes: list):
        self.notes = notes
        self.by_full_name: dict = {}
        self.by_title_parent: dict = {}
        self.invisible: list = []
        for n in notes:
            title = n.scalar("title") or n.scalar("name")
            full = n.scalar("full_name")
            if full:
                self.by_full_name.setdefault(key(full), n)
            parent = n.scalar("parent_place")
            if n.scalar("title") and parent:
                bare = parent.strip().removeprefix("[[").removesuffix("]]")
                self.by_title_parent.setdefault(
                    f"{key(n.scalar('title'))}|{key(bare)}", n)
            # What the plugin's matcher cannot reach, and therefore duplicates.
            reasons = []
            if not n.scalar("title"):
                reasons.append("no title:")
            if not full:
                reasons.append("no full_name:")
            if parent and "|" in parent:
                reasons.append("piped parent_place breaks the title|parent key")
            if reasons:
                self.invisible.append((n, "; ".join(reasons)))

    def find(self, place: str):
        if not place:
            return None
        k = key(place)
        hit = self.by_full_name.get(k)
        if hit is not None:
            return hit
        parts = normalise(place).split(", ")
        if len(parts) >= 2:
            # The plugin's second lookup: leaf title against its parent's name.
            for n in self.notes:
                if key(n.scalar("title") or "") == key(parts[0]):
                    parent = (n.scalar("parent_place") or "").strip()
                    bare = parent.removeprefix("[[").removesuffix("]]")
                    if key(bare.split("|")[0]) == key(", ".join(parts[1:])):
                        return n
        return None

    # -- comparing a vault link with a GEDCOM PLAC ----------------------

    def by_link(self, link: str):
        """The Place note a `"[[Name]]"` or `[[Name|alias]]` value names, or None."""
        bare = (link or "").strip().removeprefix("[[").removesuffix("]]")
        bare = bare.split("|")[0].strip()
        if not bare:
            return None
        if not hasattr(self, "_by_basename"):
            self._by_basename = {n.basename: n for n in self.notes}
        return self._by_basename.get(bare)

    def ancestors(self, note) -> list:
        """The chain above `note`, nearest first. Stops at a cycle or a gap."""
        out, seen = [], {note.path}
        current = self.by_link(note.scalar("parent_place"))
        while current is not None and current.path not in seen:
            out.append(current)
            seen.add(current.path)
            current = self.by_link(current.scalar("parent_place"))
        return out

    @staticmethod
    def names(note) -> set:
        """Every name a Place note answers to, as match keys."""
        forms = [note.scalar("title"), note.scalar("name"), note.basename,
                 *note.as_list("aliases")]
        return {key(f) for f in forms if f}

    def compare(self, link: str, plac: str) -> str:
        """How a GEDCOM PLAC relates to the Place a vault value links to.

        "" when they agree, or when there is nothing to compare; "coarsen"
        when the PLAC names one of the vault place's ancestors, so the vault
        is the more precise; "conflict" otherwise.

        A PLAC that resolves to a note is compared by note. One that does not
        -- most, since upstream records historical and native forms -- is
        compared by its leaf against the names of the vault place and its
        ancestors: `Smolensk, Smolensk, Russia` agrees with `[[Smolensk
        Russia]]`, while `Aralsk, Kyzylorda, Kazakhstan` does not. A form
        the vault does not know is reported rather than assumed equal, which
        makes adding it to `aliases:` the fix.
        """
        vault_note = self.by_link(link)
        if vault_note is None or not (plac or "").strip():
            return ""
        chain = self.ancestors(vault_note)
        ged_note = self.find(plac)
        if ged_note is not None:
            if ged_note.path == vault_note.path:
                return ""
            if any(a.path == ged_note.path for a in chain):
                return "coarsen"
        leaf = key(normalise(plac).split(", ")[0])
        if _same_name(leaf, self.names(vault_note)):
            return ""
        if any(_same_name(leaf, self.names(a)) for a in chain):
            return "coarsen"
        return "conflict"


_WORD = re.compile(r"[^\w]+")


def _same_name(leaf: str, names: set) -> bool:
    """Whether a PLAC leaf names the same place as any of `names`.

    One side's words contained in the other's: `Kings` is `Kings County`,
    `Halle an der Saale` is `Halle`, `Altona (Ottensen)` is `Altona`. Loose on
    purpose -- a miss is reported as a conflict every run, so it has to be a
    real disagreement to be worth reading.
    """
    words = {w for w in _WORD.split(leaf) if w}
    if not words:
        return False
    for name in names:
        other = {w for w in _WORD.split(name) if w}
        if other and (words <= other or other <= words):
            return True
    return False


def load(folder: str) -> Index:
    return Index(list(vault.iter_notes(folder)))
