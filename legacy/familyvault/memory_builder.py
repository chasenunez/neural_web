"""Orchestrate the side effects of saving a memory.

Given parsed 5W input, this module:
  - ensures stub markdown files exist for every person and place mentioned
  - writes the memory file itself with wikilinks back to those stubs
  - returns the list of paths it touched, so the caller can commit them

It deliberately does no UI work and no git work; both are handled elsewhere.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from pathlib import Path

from . import frontmatter, parsing, photos, templates, vault as vault_mod


@dataclass
class MemoryInput:
    title: str           # the "what"
    when: str            # ISO date string, may be ""
    who: str             # raw free-text
    where: str           # raw free-text
    why: str
    story: str
    # Either supply a source file to be copied into the vault, or supply
    # photo_filename pointing to a file already inside vault/Photos.
    source_photo: Path | None = None
    photo_filename: str = ""


@dataclass
class SaveResult:
    memory_path: Path
    created_paths: list[Path] = field(default_factory=list)
    updated_paths: list[Path] = field(default_factory=list)

    @property
    def all_paths(self) -> list[Path]:
        return [self.memory_path, *self.created_paths, *self.updated_paths]


def save_memory(v: vault_mod.Vault, mem: MemoryInput) -> SaveResult:
    """Persist a memory and any stub files it implies. Idempotent on title+date."""
    v.ensure_dirs()

    people = parsing.split_nouns(mem.who)
    places = parsing.split_nouns(mem.where)
    photo_filename = _maybe_copy_photo(v, mem)

    result = SaveResult(memory_path=_memory_path(v, mem))
    if photo_filename:
        result.created_paths.append(v.photos / photo_filename)

    for name in people:
        path, created = _ensure_stub(v, "Person", name)
        (result.created_paths if created else result.updated_paths).append(path)

    for name in places:
        path, created = _ensure_stub(v, "Place", name)
        (result.created_paths if created else result.updated_paths).append(path)

    _write_memory(v, mem, people, places, photo_filename, result.memory_path)
    return result


def _maybe_copy_photo(v: vault_mod.Vault, mem: MemoryInput) -> str:
    """If a source_photo was provided, copy it into vault/Photos and return the
    new filename. Otherwise return the supplied photo_filename (which may be "")."""
    if mem.source_photo is None:
        return mem.photo_filename
    import datetime as _dt
    date = _parse_date(mem.when) or _dt.date.today()
    photo_id = photos.new_photo_id()
    dest = photos.copy_into_vault(mem.source_photo, v.photos, photo_id, date)
    return dest.name


def _parse_date(value: str) -> "_dt.date | None":
    import datetime as _dt
    try:
        return _dt.date.fromisoformat(value.strip())
    except (ValueError, AttributeError):
        return None


def _memory_path(v: vault_mod.Vault, mem: MemoryInput) -> Path:
    date_part = (mem.when or _dt.date.today().isoformat()).strip()
    title_stem = vault_mod.normalize_name(mem.title) or "Untitled"
    return v.folder("Memory") / f"{date_part} {title_stem}.md"


def ensure_stub(v: vault_mod.Vault, type_name: str, display_name: str) -> tuple[Path, bool]:
    """Create an empty templated file if one doesn't exist. Returns (path, created)."""
    path = v.file_for(type_name, display_name)
    if path.exists():
        return path, False
    template = templates.by_type(type_name)
    fm = template.empty_frontmatter()
    fm["name"] = vault_mod.normalize_name(display_name)
    doc = frontmatter.Document(frontmatter=fm, body="")
    frontmatter.write(path, doc)
    return path, True


# Backwards-compat alias for internal callers.
_ensure_stub = ensure_stub


def save_record(
    v: vault_mod.Vault,
    type_name: str,
    path: Path,
    raw_inputs: dict[str, str],
) -> SaveResult:
    """Update an existing record's frontmatter from raw text inputs.

    For LINK/LINKS fields, any newly-mentioned names get their own stub files
    created in the appropriate folder.
    """
    template = templates.by_type(type_name)
    doc = frontmatter.read(path) if path.exists() else frontmatter.Document(
        frontmatter=template.empty_frontmatter(), body=""
    )

    result = SaveResult(memory_path=path)
    fm = dict(doc.frontmatter)

    for key, raw in raw_inputs.items():
        field = template.field(key)
        if field is None:
            continue
        value, names = _coerce(field, raw)
        if value is not None:
            fm[key] = value
        if field.target_type and names:
            for name in names:
                stub_path, created = ensure_stub(v, field.target_type, name)
                (result.created_paths if created else result.updated_paths).append(stub_path)

    new_doc = frontmatter.Document(frontmatter=fm, body=doc.body)
    frontmatter.write(path, new_doc)
    return result


def _coerce(field: "templates.Field", raw: str) -> tuple[object, list[str]]:
    """Turn a UI string into a frontmatter value, plus the display-names that
    should be ensured as stubs (only populated for LINK/LINKS)."""
    raw = (raw or "").strip()
    kind = field.kind
    if kind == templates.Kind.LINK:
        if not raw:
            return "", []
        return vault_mod.display_to_wikilink(raw), [raw]
    if kind == templates.Kind.LINKS:
        names = parsing.split_nouns(raw)
        return [vault_mod.display_to_wikilink(n) for n in names], names
    if kind == templates.Kind.NUMBER:
        if not raw:
            return "", []
        try:
            return float(raw) if "." in raw else int(raw), []
        except ValueError:
            return raw, []  # store as string; user can fix later
    return raw, []


def _write_memory(
    v: vault_mod.Vault,
    mem: MemoryInput,
    people: list[str],
    places: list[str],
    photo_filename: str,
    path: Path,
) -> None:
    template = templates.by_type("Memory")
    fm = template.empty_frontmatter()
    fm["title"] = mem.title.strip()
    fm["when"] = (mem.when or _dt.date.today().isoformat()).strip()
    fm["who"] = [vault_mod.display_to_wikilink(n) for n in people]
    fm["where"] = [vault_mod.display_to_wikilink(n) for n in places]
    fm["why"] = mem.why.strip()
    fm["photo"] = photo_filename
    fm["story"] = mem.story.strip()

    body_lines: list[str] = []
    if photo_filename:
        body_lines.append(f"![[{photo_filename}]]")
        body_lines.append("")
    if mem.story.strip():
        body_lines.append(mem.story.strip())

    doc = frontmatter.Document(frontmatter=fm, body="\n".join(body_lines))
    frontmatter.write(path, doc)
