"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from familyvault import vault as vault_mod


@pytest.fixture
def tmp_vault(tmp_path: Path) -> vault_mod.Vault:
    v = vault_mod.Vault(root=tmp_path / "vault")
    v.ensure_dirs()
    return v
