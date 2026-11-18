"""Read and write Charted Roots notes.

Charted Roots frontmatter is a narrow subset of YAML: flat ``key: value``
pairs and block lists of ``- item``. No nested maps, no flow collections, no
anchors. That is small enough to handle exactly, which matters more than
generality -- an unescaped ``"`` inside a double-quoted scalar makes Obsidian
parse *no* properties on the note, silently.

The model is line-preserving on purpose. A note is kept as its original lines
and only the keys actually changed are spliced, so a run leaves no diff noise
on the hand-curated layer. Re-quoting every scalar to this module's own taste
would rewrite 1600+ notes on the first run and bury the real changes.
"""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass, field
from typing import Iterator

from .config import KEY_ORDER

# A dash and a dot are legal in a YAML key and other plugins emit them
# (`cover-image`, `date-created`). A key this does not match is not
# skipped quietly -- see `unparsed`.
_KEY = re.compile(r'^([A-Za-z_][A-Za-z0-9_.-]*):(?:[ \t]+(.*))?[ \t]*$')
_LIST_ITEM = re.compile(r'^[ \t]+-[ \t]+(.*?)[ \t]*$')
_EMPTY_LIST_ITEM = re.compile(r'^[ \t]+-[ \t]*$')
_WIKILINK = re.compile(r'\[\[([^\]\n]+?)\]\]')
_WS_RUN = re.compile(r'\s+')
# Scalars safe to emit bare. Unicode letters are fine; the characters that
# actually break a bare YAML scalar are the structural ones.
# A comma is only special in YAML *flow* context; this writer always emits
# block context, and the Places folder keeps `full_name` as a plain scalar.
_BARE_UNSAFE = re.compile(r'''[:#\[\]{}|>&*!%@`"'\\]|^[ \t-]|[ \t]$''')
_RESERVED = {"true", "false", "null", "yes", "no", "on", "off", "~", ""}


def write_atomic(path: str, text: str) -> None:
    """Replace `path` with `text` in one step, creating parents if needed.

    A crash, a full disk or an interrupted run leaves either the old file or
    the new one and never a half-written note, which matters because this
    vault *is* the record and the plugin may read it while a run is in
    progress. The temporary file is created in the target directory so
    `os.replace` stays on one filesystem, and is removed if anything fails
    before the rename -- otherwise a failed write leaves `.crsync-*` litter
    in an entity folder, where Obsidian would index it.
    """
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".crsync-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def unquote(value: str) -> str:
    """Strip one layer of YAML quoting, honouring backslash escapes."""
    v = value.strip()
    if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        return v[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if len(v) >= 2 and v[0] == "'" and v[-1] == "'":
        return v[1:-1].replace("''", "'")
    return v


def needs_quoting(value: str) -> bool:
    if value.lower() in _RESERVED:
        return False if value == "" else True
    if _WIKILINK.search(value):
        # The vault model: unquoted [[...]] is invalid YAML in frontmatter.
        return True
    return bool(_BARE_UNSAFE.search(value))


def quote(value: str) -> str:
    """Render a scalar for frontmatter, escaping inner quotes.

    A newline cannot live in a single-line YAML scalar, so any run of
    whitespace is collapsed. Writing one silently truncates the value on the
    next read, which is how a citation stops matching itself.

    Escaping changes the quoting, never the text, so this is safe to apply to
    a Citation ``page:`` value that must be preserved verbatim.
    """
    value = _WS_RUN.sub(" ", str(value)).strip() if "\n" in str(value) else str(value)
    if not needs_quoting(value):
        return value
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'


@dataclass
class Note:
    """A vault note: parsed frontmatter over preserved source lines."""

    path: str
    #: key -> str for scalars, list[str] for block lists. Insertion-ordered.
    fm: dict = field(default_factory=dict)
    body: str = ""
    #: True when the file opened with `---` but never closed it. Nothing was
    #: parsed, so the note is readable but not writable -- see `set`.
    malformed: bool = False
    #: True when the file has no frontmatter block at all (Archive notes).
    has_frontmatter: bool = True
    #: Frontmatter lines that are neither a key, a list item, nor blank.
    #: They are invisible to the span index -- each sits inside the preceding
    #: key's span -- so a note carrying one is readable but not writable.
    unparsed: list = field(default_factory=list)

    _lines: list[str] = field(default_factory=list, repr=False)
    #: key -> (start, end) half-open span into _lines
    _spans: dict = field(default_factory=dict, repr=False)
    dirty: bool = field(default=False, repr=False)

    @property
    def basename(self) -> str:
        return os.path.basename(self.path)[:-3]

    @property
    def writable(self) -> bool:
        return not self.unwritable_reason()

    def unwritable_reason(self) -> str:
        """Why this note cannot be patched, or "" if it can.

        Two ways, and nothing in Obsidian warns about either. An unclosed
        `---` block was never parsed, so writing would put a second block
        above the original. And a line the key pattern does not recognise
        sits inside the preceding key's span, so a write to *that* key would
        splice the line away -- silently, and only for some keys, which is
        the worst shape a data loss can have.
        """
        if self.malformed:
            return "frontmatter block never closes"
        if self.unparsed:
            return (f"frontmatter line the key index cannot see: "
                    f"{self.unparsed[0].strip()!r}")
        return ""

    def get(self, key: str, default=None):
        return self.fm.get(key, default)

    def scalar(self, key: str, default: str = "") -> str:
        v = self.fm.get(key, default)
        if isinstance(v, list):
            return v[0] if v else default
        return v if v is not None else default

    def as_list(self, key: str) -> list[str]:
        v = self.fm.get(key)
        if v is None or v == "":
            return []
        return list(v) if isinstance(v, list) else [v]

    def links(self, key: str) -> list[str]:
        """Wikilink targets under `key`, whether it holds a scalar or a list."""
        out = []
        for item in self.as_list(key):
            for m in _WIKILINK.finditer(str(item)):
                target = m.group(1).split('|', 1)[0].split('#', 1)[0]
                out.append(target.rstrip('\\').strip())
        return out

    # -- mutation -------------------------------------------------------

    def _render_key(self, key: str, value) -> list[str]:
        if isinstance(value, list):
            if not value:
                return [f"{key}:"]
            return [f"{key}:"] + [f"  - {quote(str(v))}" for v in value]
        if value is None or value == "":
            return [f"{key}:"]
        return [f"{key}: {quote(str(value))}"]

    def _refuse_if_unwritable(self) -> None:
        """Fail loudly rather than write a note this module cannot read back.

        Both reasons need a human, and both are reported by the invariant
        suite so the note is found before a run needs it. A malformed Source
        can reach a write even so, because `match_sources` falls back to
        reading the `_Imported from GEDCOM source S…_` line out of the body.
        """
        reason = self.unwritable_reason()
        if reason:
            raise ValueError(f"{self.path or '<note>'}: {reason}; refusing to "
                             f"write. Fix the frontmatter by hand first.")

    def set(self, key: str, value) -> bool:
        """Set `key`, splicing only its lines. Returns True if anything changed."""
        self._refuse_if_unwritable()
        if key in self.fm and self.fm[key] == value:
            return False
        new_lines = self._render_key(key, value)
        if key in self._spans:
            start, end = self._spans[key]
            if self._lines[start:end] == new_lines:
                self.fm[key] = value
                return False
            self._lines[start:end] = new_lines
            self._reindex()
        else:
            self._lines[self._insertion_point(key):self._insertion_point(key)] = new_lines
            self._reindex()
        self.fm[key] = value
        self.dirty = True
        return True

    def _insertion_point(self, key: str) -> int:
        """Where a new key belongs, by the convention for this cr_type.

        After the last key that conventionally precedes it, or before the
        first that follows. Falls back to the end for an unknown key or type,
        which is what every key did before this existed.
        """
        order = KEY_ORDER.get(self.fm.get("cr_type", ""))
        if not order or key not in order:
            return len(self._lines)
        rank = order.index(key)
        after = None
        for existing, (start, end) in self._spans.items():
            if existing in order and order.index(existing) < rank:
                if after is None or end > after:
                    after = end
        if after is not None:
            return after
        before = None
        for existing, (start, end) in self._spans.items():
            if existing in order and order.index(existing) > rank:
                if before is None or start < before:
                    before = start
        return before if before is not None else len(self._lines)

    def remove(self, key: str) -> bool:
        self._refuse_if_unwritable()
        if key not in self._spans:
            return False
        start, end = self._spans[key]
        del self._lines[start:end]
        self.fm.pop(key, None)
        self._reindex()
        self.dirty = True
        return True

    def _reindex(self) -> None:
        self._spans = _index(self._lines)

    def text(self) -> str:
        if not self.has_frontmatter:
            return self.body
        return "---\n" + "\n".join(self._lines) + "\n---\n" + self.body

    def save(self) -> None:
        self._refuse_if_unwritable()
        write_atomic(self.path, self.text())
        self.dirty = False


def _index(lines: list[str]) -> dict:
    """Map each key to the half-open line span it owns."""
    spans: dict = {}
    current = None
    start = 0
    for i, raw in enumerate(lines):
        if _LIST_ITEM.match(raw) or _EMPTY_LIST_ITEM.match(raw):
            continue
        m = _KEY.match(raw)
        if not m:
            continue
        if current is not None:
            spans[current] = (start, i)
        current = m.group(1)
        start = i
    if current is not None:
        spans[current] = (start, len(lines))
    return spans


def _unparsed(lines: list[str]) -> list:
    """Frontmatter lines that are neither a key, a list item, nor blank.

    Nested maps, flow collections and block scalars all land here: this
    reader handles the flat subset the vault actually uses, and says so
    rather than dropping what it does not understand.
    """
    return [raw for raw in lines
            if raw.strip() and not (_KEY.match(raw) or _LIST_ITEM.match(raw)
                                    or _EMPTY_LIST_ITEM.match(raw))]


def _parse_values(lines: list[str]) -> dict:
    fm: dict = {}
    pending = None
    for raw in lines:
        if not raw.strip():
            continue
        item = _LIST_ITEM.match(raw)
        if item and pending is not None:
            if not isinstance(fm.get(pending), list):
                fm[pending] = []
            fm[pending].append(unquote(item.group(1)))
            continue
        if _EMPTY_LIST_ITEM.match(raw) and pending is not None:
            continue
        m = _KEY.match(raw)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        if value is None or value.strip() == "":
            fm[key] = ""
            pending = key
        else:
            fm[key] = unquote(value)
            pending = None
    return fm


def parse(path: str) -> Note:
    with open(path, encoding="utf-8") as fh:
        return parse_text(fh.read(), path)


def parse_text(text: str, path: str = "") -> Note:
    if not text.startswith("---\n"):
        return Note(path=path, body=text, has_frontmatter=False)

    end = text.find("\n---", 3)
    while end != -1 and text[end + 4:end + 5] not in ("", "\n"):
        end = text.find("\n---", end + 1)
    if end == -1:
        # Keep the whole file as the body: `text()` then renders it back
        # unchanged, and `set`/`save` refuse rather than write a second block.
        return Note(path=path, body=text, malformed=True, has_frontmatter=False)

    lines = text[4:end + 1].rstrip("\n").split("\n")
    if lines == [""]:
        lines = []
    # text[end:end+4] is the closing "\n---"; the newline after it terminates
    # that line and belongs to the delimiter, not the body.
    body = text[end + 4:]
    if body.startswith("\n"):
        body = body[1:]

    note = Note(path=path, fm=_parse_values(lines), body=body, _lines=lines,
                unparsed=_unparsed(lines))
    note._reindex()
    return note


def iter_notes(folder: str) -> Iterator[Note]:
    if not os.path.isdir(folder):
        return
    for name in sorted(os.listdir(folder)):
        if name.endswith(".md"):
            yield parse(os.path.join(folder, name))
