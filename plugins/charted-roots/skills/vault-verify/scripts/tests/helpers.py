"""Fixtures: a synthetic vault on disk, and GEDCOM text in a temp file.

Nothing here touches the real vault. Every test builds the notes it needs, so
a check that fails names a fixture, not whatever the vault happened to hold
the day the test was written.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from crsync import config

FOLDERS = {
    "people": "Charted Roots/People",
    "events": "Charted Roots/Events",
    "citations": "Charted Roots/Citations",
    "sources": "Charted Roots/Sources",
    "places": "Charted Roots/Places",
}


def frontmatter(**keys) -> str:
    """Render a frontmatter block. A list value becomes a block list."""
    lines = ["---"]
    for key, value in keys.items():
        if isinstance(value, (list, tuple)):
            lines.append(f"{key}:")
            lines.extend(f"  - {v}" for v in value)
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"


class VaultCase(unittest.TestCase):
    """A TestCase with an empty vault tree under `self.root`."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        for rel in FOLDERS.values():
            os.makedirs(os.path.join(self.root, rel), exist_ok=True)
        self.cfg = config.Config(root=self.root, settings={
            f"{k}Folder": v for k, v in
            (("people", FOLDERS["people"]), ("events", FOLDERS["events"]),
             ("citations", FOLDERS["citations"]), ("sources", FOLDERS["sources"]),
             ("places", FOLDERS["places"]))
        })
        self.addCleanup(self._tmp.cleanup)

    def write(self, rel: str, text: str) -> str:
        """Write `text` to a vault-relative path, creating parents."""
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def person(self, name: str, body: str = "", **keys) -> str:
        keys.setdefault("cr_type", "person")
        keys.setdefault("cr_id", "aaa-000-aaa-000")
        keys.setdefault("name", name)
        return self.write(f"{FOLDERS['people']}/{name}.md",
                          frontmatter(**keys) + body)

    def citation(self, name: str, **keys) -> str:
        keys.setdefault("cr_type", "citation")
        keys.setdefault("cr_id", "ccc-000-ccc-000")
        return self.write(f"{FOLDERS['citations']}/{name}.md", frontmatter(**keys))

    def read(self, rel: str) -> str:
        with open(os.path.join(self.root, rel), encoding="utf-8") as fh:
            return fh.read()


def ged(text: str) -> str:
    """Write GEDCOM text to a temp file and return its path.

    The caller's TemporaryDirectory is not used: several GEDCOM tests need no
    vault at all.
    """
    fd, path = tempfile.mkstemp(suffix=".ged")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text if text.endswith("\n") else text + "\n")
    return path


def find_vault(start: str) -> str:
    """The nearest ancestor holding `.obsidian/`, else `start`'s root."""
    d = os.path.dirname(os.path.abspath(start))
    while True:
        if os.path.isdir(os.path.join(d, ".obsidian")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return d
        d = parent
