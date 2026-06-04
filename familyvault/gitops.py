"""Thin wrapper around the git CLI, scoped to the vault directory.

Design notes:
- Uses subprocess directly (no GitPython dep) so failures are debuggable.
- Pull uses ``--rebase --autostash`` for the family use case: 10 users, mostly
  editing different files, so rebase + autostash gives a clean linear history.
- All commands are scoped via ``-C <vault>`` to avoid leaking into other repos.
- Online detection is implicit: any network failure surfaces as a GitError with
  the underlying stderr, and the caller decides how to present it.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitError(RuntimeError):
    """Raised when a git command exits non-zero."""


@dataclass(frozen=True)
class CommandResult:
    args: list[str]
    stdout: str
    stderr: str
    returncode: int


def run(vault: Path, *args: str, check: bool = True) -> CommandResult:
    """Run ``git -C <vault> <args>``. Raises GitError on failure when check=True."""
    cmd = ["git", "-C", str(vault), *args]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    result = CommandResult(cmd, proc.stdout, proc.stderr, proc.returncode)
    if check and proc.returncode != 0:
        raise GitError(f"{' '.join(cmd)} failed: {proc.stderr.strip()}")
    return result


def is_repo(vault: Path) -> bool:
    if not vault.exists():
        return False
    try:
        run(vault, "rev-parse", "--git-dir")
        return True
    except GitError:
        return False


def clone(remote: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["git", "clone", remote, str(dest)], capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise GitError(f"clone failed: {proc.stderr.strip()}")


def pull(vault: Path) -> CommandResult:
    """Rebase pull with autostash. Raises GitError on conflict or network failure."""
    return run(vault, "pull", "--rebase", "--autostash")


def add(vault: Path, paths: list[Path]) -> None:
    if not paths:
        return
    rels = [str(p.relative_to(vault)) for p in paths]
    run(vault, "add", "--", *rels)


def has_changes(vault: Path) -> bool:
    result = run(vault, "status", "--porcelain")
    return bool(result.stdout.strip())


def commit(vault: Path, message: str, author_name: str,
           author_email: str | None = None) -> None:
    email = author_email or f"{_slug(author_name)}@familyvault.local"
    run(
        vault,
        "-c", f"user.name={author_name}",
        "-c", f"user.email={email}",
        "commit", "-m", message,
        "--author", f"{author_name} <{email}>",
    )


def push(vault: Path) -> CommandResult:
    return run(vault, "push")


def save_and_sync(
    vault: Path,
    paths: list[Path],
    message: str,
    author_name: str,
    author_email: str | None = None,
) -> None:
    """Add, commit, pull-rebase, push. Designed for the save flow.

    If push is rejected because a peer pushed first, this pulls once and retries.
    Further conflicts raise GitError for the caller to surface.
    """
    add(vault, paths)
    if not has_changes(vault):
        return
    commit(vault, message, author_name, author_email)
    try:
        push(vault)
    except GitError:
        pull(vault)
        push(vault)


def _slug(name: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in name).strip("-") or "user"
