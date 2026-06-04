"""Configuration loading for the family vault."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass(frozen=True)
class User:
    name: str
    email: Optional[str] = None


@dataclass(frozen=True)
class Config:
    vault_path: Path
    git_remote: Optional[str]
    photos_source: Optional[Path]
    users: list[User] = field(default_factory=list)

    def user_by_name(self, name: str) -> User:
        normalized = name.strip()
        for user in self.users:
            if user.name.lower() == normalized.lower():
                return user
        return User(name=normalized)


def load(path: Path) -> Config:
    """Load configuration from a YAML file. Raises FileNotFoundError if missing."""
    raw = yaml.safe_load(path.read_text()) or {}
    return _from_dict(raw, base=path.parent)


def _from_dict(raw: dict, base: Path) -> Config:
    vault = _resolve(raw.get("vault_path", "./vault"), base)
    photos_raw = raw.get("photos_source")
    photos = _resolve(photos_raw, base) if photos_raw else None
    users = [User(**u) for u in (raw.get("users") or [])]
    return Config(
        vault_path=vault,
        git_remote=raw.get("git_remote"),
        photos_source=photos,
        users=users,
    )


def _resolve(value: str, base: Path) -> Path:
    """Expand ~ and resolve relative paths against base."""
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = (base / p).resolve()
    return p


def default_config_path() -> Path:
    """Where to look for config by default."""
    return Path(__file__).resolve().parent.parent / "config.yaml"
