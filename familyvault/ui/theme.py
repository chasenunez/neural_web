"""Shared visual styling for the Streamlit UI.

Aim: calm, minimal, generous whitespace, soft serif type. The base palette is
defined in .streamlit/config.toml so Streamlit's widget chrome matches; this
module layers a small CSS overlay on top to hide framework UI and tune spacing.
"""

import streamlit as st

_CSS = """
<style>
#MainMenu, footer, header[data-testid="stHeader"] {visibility: hidden;}
section[data-testid="stSidebar"] {display: none;}

.block-container {
  max-width: 720px;
  padding-top: 4rem;
  padding-bottom: 4rem;
}

h1, h2, h3 {
  font-family: 'Iowan Old Style', Georgia, 'Times New Roman', serif;
  font-weight: 400;
  letter-spacing: 0.01em;
  color: #3A3A3A;
}

p, label, .stMarkdown {
  font-family: 'Iowan Old Style', Georgia, 'Times New Roman', serif;
  color: #3A3A3A;
}

.stTextInput input, .stTextArea textarea, .stDateInput input {
  font-family: 'Iowan Old Style', Georgia, serif;
  font-size: 1rem;
  padding: 0.7rem 0.9rem;
  background-color: #FFFEFB;
  border: 1px solid #E2DDD2;
  border-radius: 6px;
}

.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: #8FA68E;
  box-shadow: 0 0 0 2px rgba(143, 166, 142, 0.18);
}

.stButton > button {
  background-color: #8FA68E;
  color: #FAF7F2;
  border: none;
  padding: 0.65rem 1.6rem;
  border-radius: 6px;
  font-family: 'Iowan Old Style', Georgia, serif;
  font-size: 1rem;
}

.stButton > button:hover {
  background-color: #7A9279;
  color: #FAF7F2;
}

[data-testid="stForm"] {
  border: none;
  padding: 0;
}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
