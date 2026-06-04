"""Fill-in-blank entries page: list incomplete files, edit one at a time."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from .. import frontmatter, memory_builder, templates, vault as vault_mod
from . import _save


def render() -> None:
    if "fill_target" in st.session_state:
        _render_editor()
    else:
        _render_list()


def _render_list() -> None:
    st.title("Help fill in blank entries")
    st.write("These entries were created automatically and need details.")
    st.write("")
    v = st.session_state.vault

    any_shown = False
    for type_name in ("Person", "Place"):
        files = v.incomplete_files(type_name)
        if not files:
            continue
        any_shown = True
        st.subheader(f"{type_name}s")
        for f in files:
            if st.button(f.stem, key=f"pick-{f}", use_container_width=True):
                st.session_state.fill_target = {"type": type_name, "path": str(f)}
                st.rerun()
        st.write("")

    if not any_shown:
        st.info("Every entry is complete. Nothing to do here right now.")

    if st.button("← Back"):
        st.session_state.page = "home"
        st.rerun()


def _render_editor() -> None:
    target = st.session_state.fill_target
    type_name: str = target["type"]
    file_path = Path(target["path"])
    template = templates.by_type(type_name)
    doc = frontmatter.read(file_path)

    st.title(file_path.stem)
    st.caption(f"{type_name} · empty fields shown at the top")
    st.write("")

    fields_sorted = _empty_first(template, doc.frontmatter)

    inputs: dict[str, str] = {}
    with st.form("fill"):
        for field in fields_sorted:
            current = _to_str(doc.frontmatter.get(field.key))
            hint = field.display_hint()
            if field.kind == templates.Kind.LONGTEXT:
                inputs[field.key] = st.text_area(
                    field.label, value=current, height=120,
                    help=hint or None,
                )
            else:
                inputs[field.key] = st.text_input(
                    field.label, value=current,
                    placeholder=hint or None,
                    help=hint or None,
                )
        submitted = st.form_submit_button("Save")

    st.write("")
    if st.button("← Back to list"):
        st.session_state.pop("fill_target", None)
        st.rerun()

    if submitted:
        result = memory_builder.save_record(
            st.session_state.vault, type_name, file_path, inputs
        )
        _save.commit_memory(result, f"Fill {file_path.stem}")
        st.session_state.pop("fill_target", None)


def _empty_first(template: templates.Template, fm: dict) -> list[templates.Field]:
    """Return template fields with currently-empty ones first, preserving
    template order within each group."""
    empties: list[templates.Field] = []
    filled: list[templates.Field] = []
    for f in template.fields:
        (empties if _is_blank(fm.get(f.key)) else filled).append(f)
    return empties + filled


def _is_blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, tuple)):
        return len(value) == 0
    return False


def _to_str(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(vault_mod.wikilinks_to_displays(value))
    if isinstance(value, str):
        s = value.strip()
        if s.startswith("[[") and s.endswith("]]"):
            return s[2:-2]
        return s
    return str(value)
