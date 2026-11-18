"""Vault layout, read from the plugin's own settings.

Every folder in a Charted Roots vault is configured, not conventional, so nothing here
hardcodes a path. The vault model: read `data.json` before assuming where
something lives.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

DATA_JSON = ".obsidian/plugins/charted-roots/data.json"

_DEFAULTS = {
    "peopleFolder": "Charted Roots/People",
    "eventsFolder": "Charted Roots/Events",
    "citationsFolder": "Charted Roots/Citations",
    "sourcesFolder": "Charted Roots/Sources",
    "placesFolder": "Charted Roots/Places",
    "mediaFolders": ["Charted Roots/Archive"],
}


@dataclass
class Config:
    root: str
    settings: dict = field(default_factory=dict)

    def _folder(self, key: str) -> str:
        return os.path.join(self.root, self.settings.get(key) or _DEFAULTS[key])

    @property
    def people(self) -> str:
        return self._folder("peopleFolder")

    @property
    def events(self) -> str:
        return self._folder("eventsFolder")

    @property
    def citations(self) -> str:
        return self._folder("citationsFolder")

    @property
    def sources(self) -> str:
        return self._folder("sourcesFolder")

    @property
    def places(self) -> str:
        return self._folder("placesFolder")

    @property
    def media(self) -> list[str]:
        folders = self.settings.get("mediaFolders") or _DEFAULTS["mediaFolders"]
        return [os.path.join(self.root, f) for f in folders]

    @property
    def entity_folders(self) -> dict:
        return {
            "person": self.people,
            "event": self.events,
            "citation": self.citations,
            "source": self.sources,
            "place": self.places,
        }

    @property
    def entity_paths(self) -> list[str]:
        """The entity folders as vault-relative git pathspecs, in order."""
        out = []
        for folder in self.entity_folders.values():
            rel = os.path.relpath(folder, self.root)
            if rel not in out:
                out.append(rel)
        return out

    @property
    def bidirectional_sync(self) -> bool:
        return bool(self.settings.get("enableBidirectionalSync")) and bool(
            self.settings.get("syncOnFileModify")
        )

    @property
    def custom_source_types(self) -> set:
        return {t.get("id") for t in self.settings.get("customSourceTypes") or []}

    @property
    def custom_place_types(self) -> set:
        return {t.get("id") for t in self.settings.get("customPlaceTypes") or []}


def load(root: str = ".") -> Config:
    path = os.path.join(root, DATA_JSON)
    settings: dict = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            settings = json.load(fh)
    return Config(root=os.path.abspath(root), settings=settings)


#: The plugin's hardcoded cr_type vocabulary. Never invent one.
CR_TYPES = {
    "person", "place", "event", "source", "citation", "map", "organization",
    "schema", "universe", "proof_summary", "timeline-export", "research_project",
    "research_report", "individual_research_note", "research_journal",
    "research_log_entry", "note",
}

#: source_type built-ins shipped by the plugin; anything else must be registered
#: in customSourceTypes.
BUILTIN_SOURCE_TYPES = {
    "vital_record", "obituary", "census", "church_record", "court_record",
    "land_deed", "probate", "military", "immigration", "photo",
    "correspondence", "newspaper", "oral_history", "custom",
}

PLACE_TYPES = {"country", "state", "county", "city", "township", "locality", "region"}


#: Conventional frontmatter key order per `cr_type`, derived from the vault by
#: pairwise majority across every note, then normalised so a companion `_id`
#: always follows its base key. Used only to place a *new* key; existing keys
#: are never reordered, because rewriting a note's whole block to this taste
#: would bury the real change in a diff.
KEY_ORDER = {
    "event": [
        "cr_type", "cr_id", "title", "event_type", "date_precision", "date",
        "date_end", "persons", "place", "confidence", "description",
        "sources", "organizations",
    ],
    "person": [
        "cr_id", "cr_type", "name", "aliases", "born", "died", "birth_place",
        "death_place", "given_name", "surnames", "name_suffix", "burial_place",
        "burial_date", "sex", "occupation", "external_id", "external_id_source",
        "father", "father_id", "mother", "mother_id",
        "stepfather", "stepfather_id", "stepmother", "stepmother_id",
        "adoptive_father", "adoptive_father_id",
        "adoptive_mother", "adoptive_mother_id",
        "spouse", "spouse_id",
        "spouse1", "spouse1_id", "spouse1_marriage_date",
        "spouse1_marriage_location", "spouse1_divorce_date",
        "spouse2", "spouse2_id", "spouse2_marriage_date",
        "spouse2_marriage_location",
        "children", "children_id", "citations", "media", "group_name",
    ],
    "place": [
        "cr_type", "cr_id", "title", "name", "place_type", "parent_place",
        "parent_place_id", "full_name", "aliases", "historical_names",
        "coordinates_lat", "coordinates_long",
    ],
    "source": [
        "cr_type", "cr_id", "title", "source_type", "source_date", "author",
        "repository", "confidence", "gedcom_id", "source_parent",
        "source_parent_id", "media", "persons",
    ],
    "citation": [
        "cr_type", "cr_id", "source", "subject", "subject_id", "fact", "page",
    ],
}
