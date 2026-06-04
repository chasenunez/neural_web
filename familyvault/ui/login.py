"""Login page: a single name field, no auth."""

import streamlit as st


def render() -> None:
    st.title("Welcome")
    st.write("Type your name to enter the vault.")
    st.write("")
    name = st.text_input("Your name", label_visibility="collapsed",
                         placeholder="Your name")
    st.write("")
    if st.button("Enter", disabled=not name.strip()):
        st.session_state.user = st.session_state.config.user_by_name(name)
        st.session_state.page = "home"
        st.rerun()
