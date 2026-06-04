"""Streamlit entry point for the Family Vault.

Run with: ``streamlit run app.py``.

──────────────────────────────────────────────────────────────────────────────
 Vault repo location is configured in ``config.yaml`` — not in this file.
 The ``git_remote`` setting at the top of ``config.yaml`` is the URL of the
 private GitHub repo where memories will be committed. See README.md.
──────────────────────────────────────────────────────────────────────────────

Boots the config + vault on first request, optionally clones / pulls the
remote, and dispatches to the right page based on session_state.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from familyvault import config as cfg, gitops, vault as vault_mod
from familyvault.ui import (
    fill_blanks,
    freeform,
    home,
    login,
    photo_page,
    theme,
)


def _enable_heic() -> None:
    """Best-effort HEIC/HEIF support for PIL (used by st.image)."""
    try:
        import pillow_heif  # type: ignore

        pillow_heif.register_heif_opener()
    except Exception:
        # pillow-heif is optional. Non-HEIC users don't need it.
        pass


def _boot() -> bool:
    """Load config and prepare the vault. Returns False if boot failed."""
    if "config" in st.session_state:
        return True

    config_path = cfg.default_config_path()
    if not config_path.exists():
        st.title("Family Vault")
        st.error(
            f"Configuration file not found at {config_path}.\n\n"
            "Copy `config.example.yaml` to `config.yaml` and edit it."
        )
        return False

    try:
        config = cfg.load(config_path)
    except Exception as e:
        st.title("Family Vault")
        st.error(f"Could not read {config_path}: {e}")
        return False

    st.session_state.config = config
    st.session_state.vault = vault_mod.Vault(config.vault_path)

    _prepare_vault(config)
    return True


def _prepare_vault(config: cfg.Config) -> None:
    """Clone the remote on first run, pull on subsequent runs."""
    vault = st.session_state.vault
    sync_done_key = "git_sync_done"
    if st.session_state.get(sync_done_key):
        return

    if config.git_remote and not gitops.is_repo(config.vault_path):
        try:
            gitops.clone(config.git_remote, config.vault_path)
        except gitops.GitError as e:
            st.warning(
                f"Could not clone {config.git_remote}: {e}. "
                "Starting in local-only mode."
            )

    vault.ensure_dirs()

    if config.git_remote and gitops.is_repo(config.vault_path):
        try:
            gitops.pull(config.vault_path)
        except gitops.GitError as e:
            st.warning(
                f"Could not pull latest changes: {e}. "
                "You may be offline; saves will queue locally."
            )

    st.session_state[sync_done_key] = True


def _dispatch() -> None:
    page = st.session_state.get("page", "login")
    if not st.session_state.get("user"):
        page = "login"
    routes = {
        "login": login.render,
        "home": home.render,
        "freeform": freeform.render,
        "photo": photo_page.render,
        "fill_blanks": fill_blanks.render,
    }
    routes.get(page, login.render)()


def main() -> None:
    st.set_page_config(
        page_title="Family Vault",
        page_icon=":seedling:",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    theme.inject_css()
    _enable_heic()
    if _boot():
        _dispatch()


main()
