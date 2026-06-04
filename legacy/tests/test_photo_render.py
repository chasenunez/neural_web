"""Test the data-URI image renderer used by the photo flow."""

from __future__ import annotations

import base64
from pathlib import Path

from PIL import Image

from familyvault.ui.photo_page import _image_data_uri


def _save_test_jpeg(path: Path) -> None:
    Image.new("RGB", (60, 40), (140, 160, 180)).save(path, "JPEG")


def test_jpeg_uses_bytes_directly(tmp_path: Path):
    path = tmp_path / "snap.jpg"
    _save_test_jpeg(path)
    uri, mime = _image_data_uri(path)
    assert mime == "image/jpeg"
    assert uri.startswith("data:image/jpeg;base64,")
    # And the base64 payload decodes to the file bytes (no re-encoding)
    payload = uri.split(",", 1)[1]
    assert base64.b64decode(payload) == path.read_bytes()


def test_png_keeps_png_mime(tmp_path: Path):
    path = tmp_path / "snap.png"
    Image.new("RGBA", (10, 10), (0, 0, 0, 0)).save(path, "PNG")
    uri, mime = _image_data_uri(path)
    assert mime == "image/png"
    assert uri.startswith("data:image/png;base64,")


def test_unknown_extension_converted_to_jpeg(tmp_path: Path):
    """A non-browser-native extension should be converted to JPEG via PIL.

    We use .tiff here because pillow-heif may not be installed everywhere; the
    code path is the same for HEIC.
    """
    path = tmp_path / "snap.tiff"
    Image.new("RGB", (20, 20), (50, 100, 150)).save(path, "TIFF")
    uri, mime = _image_data_uri(path)
    assert mime == "image/jpeg"
    assert uri.startswith("data:image/jpeg;base64,")
