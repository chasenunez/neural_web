"""Schema definitions for each markdown type in the vault.

Each Template describes one type (Person, Place, Memory). Field order is the
order shown in the UI: most important first, least important last. A field's
``kind`` decides how the value is rendered into YAML frontmatter.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Kind(str, Enum):
    """How a field's value is stored and edited."""

    TEXT = "text"          # single-line string
    LONGTEXT = "longtext"  # multi-line string (textarea in UI)
    DATE = "date"          # ISO date string YYYY-MM-DD
    URL = "url"            # validated as a URL
    LINK = "link"          # single wikilink to another vault file
    LINKS = "links"        # list of wikilinks
    NUMBER = "number"


@dataclass(frozen=True)
class Field:
    key: str          # YAML key in frontmatter
    label: str        # Human label shown in UI
    kind: Kind
    target_type: str | None = None  # for LINK/LINKS: which Template type


@dataclass(frozen=True)
class Template:
    type_name: str     # e.g. "Person"
    folder: str        # vault subfolder, e.g. "People"
    fields: tuple[Field, ...]

    def empty_frontmatter(self) -> dict[str, Any]:
        """Build a frontmatter dict with every field present but blank."""
        out: dict[str, Any] = {"type": self.type_name.lower()}
        for f in self.fields:
            out[f.key] = _blank(f.kind)
        return out

    def field(self, key: str) -> Field | None:
        for f in self.fields:
            if f.key == key:
                return f
        return None


def _blank(kind: Kind) -> Any:
    if kind == Kind.LINKS:
        return []
    return ""


PERSON = Template(
    type_name="Person",
    folder="People",
    fields=(
        Field("name", "Name", Kind.TEXT),
        Field("lives_in", "Lives in", Kind.LINK, target_type="Place"),
        Field("birthdate", "Birthdate", Kind.DATE),
        Field("birthplace", "Birthplace", Kind.LINK, target_type="Place"),
        Field("parents", "Parents", Kind.LINKS, target_type="Person"),
        Field("siblings", "Siblings", Kind.LINKS, target_type="Person"),
        Field("partner", "Partner", Kind.LINK, target_type="Person"),
        Field("children", "Children", Kind.LINKS, target_type="Person"),
        Field("core_memories", "Core Memories", Kind.LINKS, target_type="Memory"),
        Field("paternal_grandparents", "Paternal Grandparents", Kind.LINKS, target_type="Person"),
        Field("maternal_grandparents", "Maternal Grandparents", Kind.LINKS, target_type="Person"),
        Field("extended_family", "Extended Family", Kind.LINKS, target_type="Person"),
        Field("occupation", "Occupation", Kind.TEXT),
        Field("degrees", "Degrees", Kind.LONGTEXT),
        Field("past_addresses", "Past Addresses", Kind.LINKS, target_type="Place"),
        Field("friends", "Friends", Kind.LINKS, target_type="Person"),
        Field("employers", "Employers", Kind.LONGTEXT),
    ),
)


PLACE = Template(
    type_name="Place",
    folder="Places",
    fields=(
        Field("name", "Name", Kind.TEXT),
        Field("maps_link", "Google Maps link", Kind.URL),
        Field("latitude", "Latitude", Kind.NUMBER),
        Field("longitude", "Longitude", Kind.NUMBER),
        Field("address", "Address", Kind.TEXT),
        Field("notes", "Notes", Kind.LONGTEXT),
    ),
)


MEMORY = Template(
    type_name="Memory",
    folder="Memories",
    fields=(
        Field("title", "Title (what)", Kind.TEXT),
        Field("when", "When", Kind.DATE),
        Field("who", "Who", Kind.LINKS, target_type="Person"),
        Field("where", "Where", Kind.LINKS, target_type="Place"),
        Field("why", "Why", Kind.LONGTEXT),
        Field("photo", "Photo", Kind.TEXT),  # filename only, embedded in body
        Field("story", "Story", Kind.LONGTEXT),
    ),
)


ALL: tuple[Template, ...] = (PERSON, PLACE, MEMORY)


def by_type(type_name: str) -> Template:
    for t in ALL:
        if t.type_name.lower() == type_name.lower():
            return t
    raise KeyError(f"Unknown template type: {type_name}")
