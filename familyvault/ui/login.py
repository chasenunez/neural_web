"""Login page: a single name field, no auth.

Wrapped in st.form so both Enter-in-the-textbox and the button submit work,
and so the button is always clickable (Streamlit only commits widget values
on submit / Enter, which would otherwise leave the button stuck-disabled).
"""

import streamlit as st


def render() -> None:
    st.title("Welcome")
    st.write("Type your name to enter the vault.")
    st.write("")

    with st.form("login", clear_on_submit=False):
        name = st.text_input(
            "Your name",
            label_visibility="collapsed",
            placeholder="Your name",
        )
        submitted = st.form_submit_button("Enter")

    if submitted:
        if not name.strip():
            st.warning("Please type a name to continue.")
            return
        st.session_state.user = st.session_state.config.user_by_name(name)
        st.session_state.page = "home"
        st.rerun()
