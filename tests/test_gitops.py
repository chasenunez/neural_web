"""Tests for the git wrapper against a real local git repo (no network).

Each test creates a bare 'remote' and a working clone in tmp_path so the full
commit / push / pull round-trip is exercised without touching GitHub.
"""

import subprocess
from pathlib import Path

import pytest

from familyvault import gitops


def _run(args: list[str], cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


def _init_local_remote(tmp_path: Path) -> tuple[Path, Path]:
    """Create a bare repo (the 'remote') and a working clone of it."""
    remote = tmp_path / "remote.git"
    remote.mkdir()
    _run(["git", "init", "--bare", "--initial-branch=main"], remote)

    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", str(remote), str(clone)],
        check=True, capture_output=True,
    )
    # First commit so the branch exists on the remote.
    (clone / "seed.md").write_text("seed\n")
    _run(["git", "add", "seed.md"], clone)
    _run(["git", "-c", "user.name=seed", "-c", "user.email=s@e.com",
          "commit", "-m", "seed"], clone)
    _run(["git", "push", "origin", "main"], clone)
    return remote, clone


def test_is_repo(tmp_path: Path):
    assert gitops.is_repo(tmp_path) is False
    _, clone = _init_local_remote(tmp_path)
    assert gitops.is_repo(clone) is True


def test_clone_creates_working_copy(tmp_path: Path):
    remote, _ = _init_local_remote(tmp_path)
    dest = tmp_path / "fresh"
    gitops.clone(str(remote), dest)
    assert (dest / "seed.md").exists()
    assert gitops.is_repo(dest)


def test_save_and_sync_commits_and_pushes(tmp_path: Path):
    remote, clone = _init_local_remote(tmp_path)
    new_file = clone / "memory.md"
    new_file.write_text("hello")
    gitops.save_and_sync(
        clone, [new_file], "Add memory", "Mom", "mom@example.com"
    )
    log = subprocess.run(
        ["git", "-C", str(clone), "log", "--oneline"],
        capture_output=True, text=True, check=True,
    )
    assert "Add memory" in log.stdout

    # And the remote has it
    fresh = tmp_path / "fresh"
    gitops.clone(str(remote), fresh)
    assert (fresh / "memory.md").exists()


def test_save_and_sync_no_changes_is_safe(tmp_path: Path):
    _, clone = _init_local_remote(tmp_path)
    gitops.save_and_sync(clone, [], "Noop", "Mom")  # should not raise


def test_has_changes(tmp_path: Path):
    _, clone = _init_local_remote(tmp_path)
    assert gitops.has_changes(clone) is False
    (clone / "x.md").write_text("x")
    _run(["git", "-C", str(clone), "add", "x.md"], Path("."))
    assert gitops.has_changes(clone) is True


def test_save_and_sync_recovers_from_diverged_remote(tmp_path: Path):
    """Simulate: peer pushed first, our push fails, save_and_sync pulls + retries."""
    remote, clone = _init_local_remote(tmp_path)
    # Peer makes their own clone and pushes a different file
    peer = tmp_path / "peer"
    gitops.clone(str(remote), peer)
    (peer / "peer.md").write_text("peer")
    _run(["git", "-C", str(peer), "add", "peer.md"], Path("."))
    _run(["git", "-C", str(peer), "-c", "user.name=p", "-c", "user.email=p@e",
          "commit", "-m", "peer"], Path("."))
    _run(["git", "-C", str(peer), "push"], Path("."))

    # Now we make a non-conflicting change and try to push
    ours = clone / "ours.md"
    ours.write_text("ours")
    gitops.save_and_sync(clone, [ours], "Ours", "Mom", "m@e.com")

    # Both files end up on the remote
    fresh = tmp_path / "fresh"
    gitops.clone(str(remote), fresh)
    assert (fresh / "ours.md").exists()
    assert (fresh / "peer.md").exists()
