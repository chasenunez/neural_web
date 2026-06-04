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
    hint: str | None = None         # short usage hint shown next to the input

    def display_hint(self) -> str:
        """Return the hint shown under the input. Falls back to a sensible
        default for the field's Kind when no explicit hint was set."""
        if self.hint is not None:
            return self.hint
        return _DEFAULT_HINTS.get(self.kind, "")


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


_DEFAULT_HINTS: dict[Kind, str] = {
    Kind.LINK: "One name",
    Kind.LINKS: "Separate multiple names with commas",
    Kind.DATE: "YYYY-MM-DD",
    Kind.URL: "Paste a full URL",
    Kind.NUMBER: "A number",
}


PERSON = Template(
    type_name="Person",
    folder="People",
    fields=(
        Field("name", "Name", Kind.TEXT,
              hint="First and last, e.g. Mary Smith"),
        Field("lives_in", "Lives in", Kind.LINK, target_type="Place",
              hint="A city, town, or specific place"),
        Field("birthdate", "Birthdate", Kind.DATE),
        Field("birthplace", "Birthplace", Kind.LINK, target_type="Place"),
        Field("parents", "Parents", Kind.LINKS, target_type="Person",
              hint="Two names, separated by a comma"),
        Field("siblings", "Siblings", Kind.LINKS, target_type="Person",
              hint="Separate multiple names with commas"),
        Field("partner", "Partner", Kind.LINK, target_type="Person"),
        Field("children", "Children", Kind.LINKS, target_type="Person",
              hint="Separate multiple names with commas"),
        Field("core_memories", "Core Memories", Kind.LINKS, target_type="Memory",
              hint="Reference existing memories by title"),
        Field("paternal_grandparents", "Paternal Grandparents", Kind.LINKS, target_type="Person",
              hint="Two names, separated by a comma"),
        Field("maternal_grandparents", "Maternal Grandparents", Kind.LINKS, target_type="Person",
              hint="Two names, separated by a comma"),
        Field("extended_family", "Extended Family", Kind.LINKS, target_type="Person",
              hint="Aunts, uncles, cousins — comma-separated"),
        Field("occupation", "Occupation", Kind.TEXT),
        Field("degrees", "Degrees", Kind.LONGTEXT,
              hint="One per line, e.g. BA English — Boston U — 2004"),
        Field("past_addresses", "Past Addresses", Kind.LINKS, target_type="Place",
              hint="Cities or places they've lived, comma-separated"),
        Field("friends", "Friends", Kind.LINKS, target_type="Person",
              hint="Separate multiple names with commas"),
        Field("employers", "Employers", Kind.LONGTEXT,
              hint="One per line, e.g. Acme Corp — 2010 to 2015"),
    ),
)


PLACE = Template(
    type_name="Place",
    folder="Places",
    fields=(
        Field("name", "Name", Kind.TEXT,
              hint="What you'd call this place in conversation"),
        Field("maps_link", "Google Maps link", Kind.URL,
              hint="Paste a Google Maps URL — coordinates will be extracted"),
        Field("latitude", "Latitude", Kind.NUMBER,
              hint="Decimal degrees, e.g. 42.3601"),
        Field("longitude", "Longitude", Kind.NUMBER,
              hint="Decimal degrees, e.g. -71.0589"),
        Field("address", "Address", Kind.TEXT),
        Field("notes", "Notes", Kind.LONGTEXT,
              hint="Anything else worth remembering about this place"),
    ),
)


MEMORY = Template(
    type_name="Memory",
    folder="Memories",
    fields=(
        Field("title", "Title (what)", Kind.TEXT,
              hint="A short title for this memory"),
        Field("when", "When", Kind.DATE),
        Field("who", "Who", Kind.LINKS, target_type="Person",
              hint="People present — separate multiple names with commas"),
        Field("where", "Where", Kind.LINKS, target_type="Place",
              hint="Places involved — separate multiple with commas"),
        Field("why", "Why", Kind.LONGTEXT,
              hint="Why does this moment matter?"),
        Field("photo", "Photo", Kind.TEXT),  # filename only, embedded in body
        Field("story", "Story", Kind.LONGTEXT,
              hint="Tell it in your own words"),
    ),
)


ALL: tuple[Template, ...] = (PERSON, PLACE, MEMORY)


def by_type(type_name: str) -> Template:
    for t in ALL:
        if t.type_name.lower() == type_name.lower():
            return t
    raise KeyError(f"Unknown template type: {type_name}")
