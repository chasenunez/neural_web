"""Shared save helper for the memory-writing pages."""

from __future__ import annotations

import streamlit as st

from .. import gitops, memory_builder


def commit_memory(result: memory_builder.SaveResult, action_label: str) -> None:
    """Surface success/warning + run git sync if a remote is configured."""
    user = st.session_state.user
    config = st.session_state.config

    if config.git_remote:
        try:
            gitops.save_and_sync(
                config.vault_path,
                result.all_paths,
                f"{action_label} ({user.name})",
                user.name,
                user.email,
            )
            st.success(f"Saved and synced — {result.memory_path.name}")
        except gitops.GitError as e:
            st.warning(
                f"Saved locally — git sync failed ({e}). Your changes are safe "
                "and will sync next time the vault can reach the remote."
            )
    else:
        st.success(f"Saved — {result.memory_path.name}")

    if result.created_paths:
        new_names = [p.stem for p in result.created_paths if p.suffix == ".md"]
        if new_names:
            st.caption("New blank entries created: " + ", ".join(sorted(set(new_names))))
