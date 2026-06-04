"""Vault directory layout, file enumeration, and slug rules.

A vault is a plain folder of markdown files organized by type (People, Places,
Memories) plus a Photos folder. Naming is deterministic so that a person named
"Mary Smith" always lives at ``People/Mary Smith.md`` regardless of who types it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from . import frontmatter, templates

_BAD_FILE_CHARS = re.compile(r"[\\/:*?\"<>|]")
_MULTI_SPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class Vault:
    root: Path

    def folder(self, type_name: str) -> Path:
        return self.root / templates.by_type(type_name).folder

    @property
    def photos(self) -> Path:
        return self.root / "Photos"

    @property
    def templates_folder(self) -> Path:
        return self.root / "Templates"

    def file_for(self, type_name: str, display_name: str) -> Path:
        """Path where a file with this display name should live. Idempotent."""
        return self.folder(type_name) / f"{normalize_name(display_name)}.md"

    def exists(self, type_name: str, display_name: str) -> bool:
        return self.file_for(type_name, display_name).exists()

    def ensure_dirs(self) -> None:
        for t in templates.ALL:
            (self.root / t.folder).mkdir(parents=True, exist_ok=True)
        self.photos.mkdir(parents=True, exist_ok=True)
        self.templates_folder.mkdir(parents=True, exist_ok=True)

    def list_files(self, type_name: str) -> list[Path]:
        folder = self.folder(type_name)
        if not folder.exists():
            return []
        return sorted(p for p in folder.glob("*.md") if p.is_file())

    def incomplete_files(self, type_name: str) -> list[Path]:
        """Files where at least one frontmatter field is blank."""
        template = templates.by_type(type_name)
        out: list[Path] = []
        for path in self.list_files(type_name):
            doc = frontmatter.read(path)
            if any(_is_blank(doc.frontmatter.get(f.key)) for f in template.fields):
                out.append(path)
        return out


def normalize_name(name: str) -> str:
    """Turn a free-form name into a stable filename stem.

    Rules:
    - Strip surrounding whitespace
    - Collapse internal whitespace to single spaces
    - Remove characters illegal on common filesystems
    - Strip apostrophes (so "Grandma's House" → "Grandmas House")
    - Title-case (so "mary smith" and "Mary Smith" collide)
    """
    s = name.strip()
    s = s.replace("'", "").replace("’", "")  # straight + curly apostrophe
    s = _BAD_FILE_CHARS.sub("", s)
    s = _MULTI_SPACE.sub(" ", s)
    return s.title() if s else s


def display_to_wikilink(display_name: str) -> str:
    """Build the [[wikilink]] form for a display name."""
    return f"[[{normalize_name(display_name)}]]"


def wikilinks_to_displays(values: Iterable[str]) -> list[str]:
    """Reverse of display_to_wikilink for a list of frontmatter values."""
    out: list[str] = []
    for v in values:
        if not isinstance(v, str):
            continue
        s = v.strip()
        if s.startswith("[[") and s.endswith("]]"):
            s = s[2:-2]
        if s:
            out.append(s)
    return out


def _is_blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, tuple, dict)):
        return len(value) == 0
    return False
