"""Photo-prompted memory page.

Picks a random image from the configured personal photo folder, shows it, and
asks the same 5W questions as the freeform flow. Re-rolling is one click.

Images are displayed via an inline ``<img>`` data URI rather than ``st.image``
because Streamlit's image pipeline pulls in numpy for processing, and on some
Pillow/numpy version combinations that fails with a confusing import error.
The browser handles JPEG/PNG/WebP/GIF natively; HEIC/HEIF is transparently
converted to JPEG via Pillow + pillow_heif.
"""

from __future__ import annotations

import base64
import datetime as _dt
import io
from pathlib import Path

import streamlit as st

from .. import memory_builder, photos, templates
from . import _save

_MEM = templates.MEMORY

# Browsers can render these formats directly.
_BROWSER_NATIVE = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def _hint(key: str) -> str:
    f = _MEM.field(key)
    return f.display_hint() if f else ""


def _image_data_uri(path: Path) -> tuple[str, str]:
    """Return ``(data_uri, mime)`` for an image path.

    For browser-native formats the file bytes are used as-is. For HEIC/HEIF
    (common on iPhones) the image is converted to JPEG via Pillow so any
    browser can render it.
    """
    ext = path.suffix.lower()
    if ext in _BROWSER_NATIVE:
        mime = "image/jpeg" if ext in {".jpg", ".jpeg"} else f"image/{ext.lstrip('.')}"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{encoded}", mime

    # Non-native formats (HEIC/HEIF) — convert to JPEG.
    from PIL import Image  # local import keeps the page importable without Pillow

    img = Image.open(path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}", "image/jpeg"


def _render_image(path: Path) -> None:
    try:
        uri, _ = _image_data_uri(path)
    except Exception as e:
        st.warning(f"Could not display {path.name}: {e}. Try another.")
        return
    st.markdown(
        f'<img src="{uri}" alt="{path.name}" '
        'style="width:100%;height:auto;border-radius:8px;display:block;">',
        unsafe_allow_html=True,
    )


def render() -> None:
    st.title("A moment from your photos")
    config = st.session_state.config

    if not config.photos_source:
        st.error("No `photos_source` configured. Edit config.yaml to set one.")
        if st.button("← Back"):
            _back()
        return

    pick_path = _ensure_pick(config.photos_source)
    if pick_path is None:
        if st.button("← Back"):
            _back()
        return

    _render_image(pick_path)
    st.caption(pick_path.name)

    with st.form("photo_memory", clear_on_submit=False):
        title = st.text_input("What", placeholder=_hint("title"))
        when = st.date_input("When", value=_dt.date.today())
        who = st.text_input("Who", placeholder=_hint("who"), help=_hint("who"))
        where = st.text_input("Where", placeholder=_hint("where"), help=_hint("where"))
        why = st.text_area("Why", height=80, placeholder=_hint("why"))
        story = st.text_area("Story", height=240, placeholder=_hint("story"))
        submitted = st.form_submit_button("Save memory")

    st.write("")
    cols = st.columns(2)
    if cols[0].button("Try a different photo"):
        st.session_state.pop("photo_pick", None)
        st.rerun()
    if cols[1].button("← Back"):
        _back()

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
            source_photo=pick_path,
        )
        result = memory_builder.save_memory(st.session_state.vault, mem)
        _save.commit_memory(result, "Add memory with photo")
        st.session_state.pop("photo_pick", None)


def _ensure_pick(folder: Path) -> Path | None:
    if "photo_pick" in st.session_state:
        return Path(st.session_state.photo_pick)
    files = photos.index_folder(folder)
    if not files:
        st.error(f"No images found under {folder}.")
        return None
    pick = photos.pick_random(files)
    st.session_state.photo_pick = str(pick)
    return pick


def _back() -> None:
    st.session_state.pop("photo_pick", None)
    st.session_state.page = "home"
    st.rerun()
