"""Freeform memory page: 5W fields + a story textarea."""

from __future__ import annotations

import datetime as _dt

import streamlit as st

from .. import memory_builder
from . import _save


def render() -> None:
    st.title("Write a memory")
    st.write("Tell the story as completely or briefly as you like.")
    st.write("")

    with st.form("freeform_memory", clear_on_submit=False):
        title = st.text_input("What", placeholder="A short title for this memory")
        when = st.date_input("When", value=_dt.date.today())
        who = st.text_input("Who", placeholder="Names, separated by commas")
        where = st.text_input("Where", placeholder="Places, separated by commas")
        why = st.text_area("Why", height=80,
                           placeholder="Why does this memory matter?")
        story = st.text_area("Story", height=260,
                             placeholder="Tell it in your own words")
        submitted = st.form_submit_button("Save memory")

    st.write("")
    if st.button("← Back"):
        st.session_state.page = "home"
        st.rerun()

    if submitted:
        if not title.strip():
            st.warning("Please give the memory a short title.")
            return
        mem = memory_builder.MemoryInput(
            title=title,
            when=when.isoformat(),
            who=who,
            where=where,
            why=why,
            story=story,
        )
        result = memory_builder.save_memory(st.session_state.vault, mem)
        _save.commit_memory(result, "Add memory")
