import datetime as dt
import random
from pathlib import Path

from familyvault import photos


def test_index_folder_finds_images(tmp_path: Path):
    (tmp_path / "a.jpg").write_bytes(b"x")
    (tmp_path / "b.PNG").write_bytes(b"x")
    (tmp_path / "c.txt").write_bytes(b"x")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "d.heic").write_bytes(b"x")

    found = photos.index_folder(tmp_path)
    names = sorted(p.name for p in found)
    assert names == ["a.jpg", "b.PNG", "d.heic"]


def test_index_folder_missing(tmp_path: Path):
    assert photos.index_folder(tmp_path / "nope") == []


def test_pick_random_deterministic_with_seed(tmp_path: Path):
    files = [tmp_path / f"{i}.jpg" for i in range(5)]
    for f in files:
        f.write_bytes(b"x")
    rng = random.Random(42)
    pick = photos.pick_random(files, rng)
    assert pick in files


def test_pick_random_empty():
    assert photos.pick_random([]) is None


def test_new_photo_id_unique_and_short():
    ids = {photos.new_photo_id() for _ in range(100)}
    assert all(len(i) == 6 for i in ids)
    assert len(ids) >= 99  # extremely unlikely to collide


def test_vault_name_format():
    name = photos.vault_name(Path("foo.HEIC"), "abc123", dt.date(2026, 6, 4))
    assert name == "2026-06-04_abc123.heic"


def test_copy_into_vault(tmp_path: Path):
    src = tmp_path / "original.jpg"
    src.write_bytes(b"original")
    photos_dir = tmp_path / "vault" / "Photos"
    dest = photos.copy_into_vault(src, photos_dir, "abc123", dt.date(2026, 6, 4))
    assert dest.exists()
    assert dest.read_bytes() == b"original"
    assert dest.name == "2026-06-04_abc123.jpg"
