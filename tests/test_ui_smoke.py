"""Streamlit AppTest smoke: every page renders without raising.

Drives the actual app.py through Streamlit's headless testing harness so we
exercise the same routing + boot path the browser hits, including dispatch
into each page module. No browser involved.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parent.parent
APP_PATH = ROOT / "app.py"


@pytest.fixture
def fake_vault(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A self-contained config that points at a fresh tmp vault + photo folder."""
    vault = tmp_path / "vault"
    photos = tmp_path / "pics"
    photos.mkdir()
    from PIL import Image
    Image.new("RGB", (50, 50), (200, 180, 140)).save(photos / "a.jpg", "JPEG")

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"vault_path: {vault}\n"
        "git_remote: null\n"
        f"photos_source: {photos}\n"
    )

    # The app reads default_config_path() which points next to app.py.
    # Monkey-patch that to use our tmp config.
    from familyvault import config as cfg_mod
    monkeypatch.setattr(cfg_mod, "default_config_path", lambda: config_path)
    return vault


def _run(at: AppTest) -> AppTest:
    at.run()
    assert not at.exception, f"App raised: {at.exception}"
    return at


def test_login_page_renders(fake_vault: Path):
    at = AppTest.from_file(str(APP_PATH), default_timeout=10)
    _run(at)
    headings = [h.value for h in at.title]
    assert "Welcome" in headings


def test_login_then_home(fake_vault: Path):
    at = AppTest.from_file(str(APP_PATH), default_timeout=10)
    _run(at)
    at.text_input[0].set_value("Chase").run()
    # button[0] is the Enter button
    at.button[0].click().run()
    assert not at.exception
    # Home page heading includes the user name
    headings = [h.value for h in at.title]
    assert any("Chase" in h for h in headings)


def test_freeform_page_renders(fake_vault: Path):
    at = AppTest.from_file(str(APP_PATH), default_timeout=10)
    _run(at)
    at.text_input[0].set_value("Chase").run()
    at.button[0].click().run()  # log in
    # Click "Write a memory in your own words"
    write_btn = next(b for b in at.button if "Write a memory" in b.label)
    write_btn.click().run()
    assert not at.exception
    headings = [h.value for h in at.title]
    assert "Write a memory" in headings


def test_freeform_save_creates_files(fake_vault: Path):
    at = AppTest.from_file(str(APP_PATH), default_timeout=10)
    _run(at)
    at.text_input[0].set_value("Chase").run()
    at.button[0].click().run()
    next(b for b in at.button if "Write a memory" in b.label).click().run()

    # Fill the form
    inputs = {ti.label: ti for ti in at.text_input}
    inputs["What"].set_value("Birthday")
    inputs["Who"].set_value("Mom, Dad")
    inputs["Where"].set_value("Home")
    areas = {ta.label: ta for ta in at.text_area}
    areas["Why"].set_value("A happy day.")
    areas["Story"].set_value("Cake and candles.")
    save = next(b for b in at.button if b.label == "Save memory")
    save.click().run()
    assert not at.exception

    # Verify files
    assert (fake_vault / "People" / "Mom.md").exists()
    assert (fake_vault / "People" / "Dad.md").exists()
    assert (fake_vault / "Places" / "Home.md").exists()
    memories = list((fake_vault / "Memories").glob("*Birthday*.md"))
    assert len(memories) == 1


def test_photo_page_renders(fake_vault: Path):
    """Regression: the photo page must not crash on st.image's numpy chain.

    Catches the bug where `st.image()` blew up with a misleading
    'numpy source directory' error on certain Pillow/numpy combinations.
    """
    at = AppTest.from_file(str(APP_PATH), default_timeout=15)
    _run(at)
    at.text_input[0].set_value("Chase").run()
    at.button[0].click().run()
    next(b for b in at.button if "photo" in b.label.lower()).click().run()
    assert not at.exception
    headings = [h.value for h in at.title]
    assert any("photos" in h.lower() or "moment" in h.lower() for h in headings)


def test_login_button_clickable_without_typing(fake_vault: Path):
    """Regression: Enter button must not be locked behind a committed value."""
    at = AppTest.from_file(str(APP_PATH), default_timeout=10)
    _run(at)
    # Find the form submit button labelled "Enter" — there is exactly one.
    submits = [b for b in at.button if b.label == "Enter"]
    assert len(submits) == 1
    assert submits[0].disabled is False
    # Clicking with no input shows a warning, not a crash.
    submits[0].click().run()
    assert not at.exception


def test_fill_blanks_lists_incomplete(fake_vault: Path):
    # Seed the vault with an incomplete entry by going through the save flow first
    at = AppTest.from_file(str(APP_PATH), default_timeout=10)
    _run(at)
    at.text_input[0].set_value("Chase").run()
    at.button[0].click().run()
    next(b for b in at.button if "Write a memory" in b.label).click().run()
    {ti.label: ti for ti in at.text_input}["What"].set_value("X")
    {ti.label: ti for ti in at.text_input}["Who"].set_value("Aunt May")
    next(b for b in at.button if b.label == "Save memory").click().run()
    # After saving we're still on freeform; go back, then to fill-blanks
    next(b for b in at.button if b.label == "← Back").click().run()
    next(b for b in at.button if "blank entries" in b.label).click().run()

    assert not at.exception
    labels = [b.label for b in at.button]
    assert "Aunt May" in labels
