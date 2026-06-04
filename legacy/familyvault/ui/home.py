"""Home page: pick one of the three memory flows."""

import streamlit as st


def render() -> None:
    user = st.session_state.user
    st.title(f"Hello, {user.name}")
    st.write("How would you like to add to the vault today?")
    st.write("")

    if st.button("Write a memory in your own words", use_container_width=True):
        _go("freeform")
    if st.button("Let a photo prompt a memory", use_container_width=True):
        st.session_state.pop("photo_pick", None)
        _go("photo")
    if st.button("Help fill in blank entries", use_container_width=True):
        _go("fill_blanks")

    st.write("")
    st.write("")
    if st.button("Log out"):
        for k in ("user", "page", "photo_pick", "fill_target"):
            st.session_state.pop(k, None)
        st.rerun()


def _go(page: str) -> None:
    st.session_state.page = page
    st.rerun()
