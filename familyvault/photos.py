"""Pick photos from a user folder and copy them into the vault."""

from __future__ import annotations

import datetime as _dt
import os
import random
import secrets
import shutil
from pathlib import Path

_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".gif"}


def index_folder(root: Path) -> list[Path]:
    """Recursively list image files in a folder, sorted for determinism."""
    if not root.exists() or not root.is_dir():
        return []
    out: list[Path] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if Path(name).suffix.lower() in _EXTENSIONS:
                out.append(Path(dirpath) / name)
    out.sort()
    return out


def pick_random(files: list[Path], rng: random.Random | None = None) -> Path | None:
    if not files:
        return None
    return (rng or random).choice(files)


def new_photo_id() -> str:
    """6-char URL-safe id, plenty for a personal vault."""
    return secrets.token_hex(3)


def vault_name(source: Path, photo_id: str, date: _dt.date | None = None) -> str:
    """Build the destination filename: YYYY-MM-DD_<id>.<ext>."""
    d = date or _dt.date.today()
    ext = source.suffix.lower() or ".jpg"
    return f"{d.isoformat()}_{photo_id}{ext}"


def copy_into_vault(source: Path, photos_dir: Path, photo_id: str,
                    date: _dt.date | None = None) -> Path:
    """Copy a source image into the vault's Photos folder under a stable name."""
    photos_dir.mkdir(parents=True, exist_ok=True)
    dest = photos_dir / vault_name(source, photo_id, date)
    shutil.copy2(source, dest)
    return dest
