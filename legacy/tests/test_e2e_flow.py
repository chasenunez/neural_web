"""End-to-end integration test: simulate a full session at the data layer.

Walks through every flow the UI exposes (freeform → photo → fill-blanks) and
asserts the resulting vault state matches what a user would expect to see.
This catches integration bugs that unit tests would miss.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from PIL import Image

from familyvault import frontmatter, memory_builder, vault as vault_mod


def _make_image(path: Path) -> None:
    Image.new("RGB", (100, 100), (180, 200, 160)).save(path, "JPEG")


def test_full_user_session(tmp_path: Path) -> None:
    # ── Setup: fresh vault, fresh photos folder ────────────────────────────
    vault = vault_mod.Vault(root=tmp_path / "vault")
    vault.ensure_dirs()

    photo_src = tmp_path / "pics" / "vacation.jpg"
    photo_src.parent.mkdir()
    _make_image(photo_src)

    # ── Flow 1: freeform write ─────────────────────────────────────────────
    mem1 = memory_builder.MemoryInput(
        title="The first day of school",
        when="2026-06-04",
        who="Mom, Dad and grandma",
        where="Riverside Elementary",
        why="A big milestone for the family.",
        story="We took photos at the front steps. Mom cried a little.",
    )
    r1 = memory_builder.save_memory(vault, mem1)

    # Memory file
    assert r1.memory_path.exists()
    doc = frontmatter.read(r1.memory_path)
    assert doc.frontmatter["title"] == "The first day of school"
    assert doc.frontmatter["who"] == ["[[Mom]]", "[[Dad]]", "[[Grandma]]"]
    assert doc.frontmatter["where"] == ["[[Riverside Elementary]]"]
    assert "Mom cried" in doc.body

    # Stubs created for each new noun
    assert (vault.folder("Person") / "Mom.md").exists()
    assert (vault.folder("Person") / "Dad.md").exists()
    assert (vault.folder("Person") / "Grandma.md").exists()
    assert (vault.folder("Place") / "Riverside Elementary.md").exists()

    # Each stub follows the Person template
    mom_doc = frontmatter.read(vault.folder("Person") / "Mom.md")
    assert mom_doc.frontmatter["type"] == "person"
    assert mom_doc.frontmatter["name"] == "Mom"
    assert mom_doc.frontmatter["parents"] == []

    # ── Flow 2: photo-prompted memory ──────────────────────────────────────
    mem2 = memory_builder.MemoryInput(
        title="Beach day",
        when="2026-06-05",
        who="Mom and Sue",  # one existing, one new
        where="Riverside Elementary",  # existing → must not duplicate
        why="",
        story="Sun and sand.",
        source_photo=photo_src,
    )
    r2 = memory_builder.save_memory(vault, mem2)

    # Photo was copied with the right naming
    photo_files = list(vault.photos.glob("*.jpg"))
    assert len(photo_files) == 1
    photo_filename = photo_files[0].name
    assert photo_filename.startswith("2026-06-05_")

    # Memory references the copied photo
    doc2 = frontmatter.read(r2.memory_path)
    assert doc2.frontmatter["photo"] == photo_filename
    assert f"![[{photo_filename}]]" in doc2.body

    # Existing stubs were not duplicated
    assert len(list((vault.folder("Person")).glob("Mom*.md"))) == 1
    # The new person stub exists
    assert (vault.folder("Person") / "Sue.md").exists()

    # ── Flow 3: fill in a blank entry ──────────────────────────────────────
    mom_path = vault.folder("Person") / "Mom.md"
    inputs = {
        "name": "Mom",
        "lives_in": "Riverside",
        "occupation": "Architect",
        "children": "Chase, Sam",
        "siblings": "Aunt Linda",
    }
    r3 = memory_builder.save_record(vault, "Person", mom_path, inputs)

    mom_after = frontmatter.read(mom_path)
    assert mom_after.frontmatter["occupation"] == "Architect"
    assert mom_after.frontmatter["lives_in"] == "[[Riverside]]"
    assert mom_after.frontmatter["children"] == ["[[Chase]]", "[[Sam]]"]
    assert mom_after.frontmatter["siblings"] == ["[[Aunt Linda]]"]

    # New stubs were created for the newly-mentioned names
    assert (vault.folder("Place") / "Riverside.md").exists()
    assert (vault.folder("Person") / "Chase.md").exists()
    assert (vault.folder("Person") / "Sam.md").exists()
    assert (vault.folder("Person") / "Aunt Linda.md").exists()

    # ── Verify incomplete_files surfaces what needs filling ────────────────
    incomplete = {p.stem for p in vault.incomplete_files("Person")}
    # Mom was just filled in for several fields but birthdate is still empty,
    # so Mom remains incomplete; that's the intended behaviour.
    assert "Dad" in incomplete
    assert "Grandma" in incomplete
    assert "Sue" in incomplete

    # ── Verify the memory list still references the touched files ─────────
    memories = vault.list_files("Memory")
    assert len(memories) == 2
    names = sorted(m.name for m in memories)
    assert names[0].startswith("2026-06-04 ")
    assert names[1].startswith("2026-06-05 ")
