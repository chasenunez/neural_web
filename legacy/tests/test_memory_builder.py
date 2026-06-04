"""End-to-end tests for the memory orchestrator."""

import datetime as dt
from pathlib import Path

from familyvault import frontmatter, memory_builder, vault as vault_mod


def test_save_memory_creates_stubs(tmp_vault: vault_mod.Vault):
    mem = memory_builder.MemoryInput(
        title="First swimming lesson",
        when="2026-06-04",
        who="Mom and Dad",
        where="The community pool",
        why="They cheered me on.",
        story="It was sunny.",
    )
    result = memory_builder.save_memory(tmp_vault, mem)

    assert result.memory_path.exists()
    assert (tmp_vault.folder("Person") / "Mom.md").exists()
    assert (tmp_vault.folder("Person") / "Dad.md").exists()
    assert (tmp_vault.folder("Place") / "The Community Pool.md").exists()


def test_save_memory_stub_uses_template_fields(tmp_vault: vault_mod.Vault):
    mem = memory_builder.MemoryInput(
        title="A day", when="2026-06-04",
        who="Sue", where="", why="", story="",
    )
    memory_builder.save_memory(tmp_vault, mem)
    doc = frontmatter.read(tmp_vault.folder("Person") / "Sue.md")
    assert doc.frontmatter["name"] == "Sue"
    assert "lives_in" in doc.frontmatter
    assert doc.frontmatter["lives_in"] == ""
    assert doc.frontmatter["parents"] == []


def test_save_memory_records_wikilinks(tmp_vault: vault_mod.Vault):
    mem = memory_builder.MemoryInput(
        title="Picnic", when="2026-06-04",
        who="Mom, Dad", where="Park", why="", story="A nice day.",
    )
    result = memory_builder.save_memory(tmp_vault, mem)
    doc = frontmatter.read(result.memory_path)
    assert doc.frontmatter["who"] == ["[[Mom]]", "[[Dad]]"]
    assert doc.frontmatter["where"] == ["[[Park]]"]
    assert "A nice day" in doc.body


def test_save_memory_does_not_clobber_existing_stub(tmp_vault: vault_mod.Vault):
    existing = tmp_vault.file_for("Person", "Mom")
    frontmatter.write(existing, frontmatter.Document(
        {"name": "Mom", "occupation": "Doctor"}, "Notes.",
    ))

    mem = memory_builder.MemoryInput(
        title="Hello", when="2026-06-04",
        who="Mom", where="", why="", story="",
    )
    memory_builder.save_memory(tmp_vault, mem)

    doc = frontmatter.read(existing)
    assert doc.frontmatter["occupation"] == "Doctor"
    assert "Notes." in doc.body


def test_save_memory_copies_photo(tmp_vault: vault_mod.Vault, tmp_path: Path):
    src = tmp_path / "snap.jpg"
    src.write_bytes(b"binary data")
    mem = memory_builder.MemoryInput(
        title="Lake day", when="2026-06-04",
        who="Mom", where="Lake", why="", story="",
        source_photo=src,
    )
    result = memory_builder.save_memory(tmp_vault, mem)

    photos = list(tmp_vault.photos.glob("*.jpg"))
    assert len(photos) == 1
    copied = photos[0]
    assert copied.name.startswith("2026-06-04_")
    assert copied.name.endswith(".jpg")

    doc = frontmatter.read(result.memory_path)
    assert doc.frontmatter["photo"] == copied.name
    assert f"![[{copied.name}]]" in doc.body


def test_save_record_updates_existing_file(tmp_vault: vault_mod.Vault):
    person_path = tmp_vault.file_for("Person", "Mary")
    memory_builder.ensure_stub(tmp_vault, "Person", "Mary")

    inputs = {
        "name": "Mary",
        "lives_in": "Boston",
        "occupation": "Teacher",
        "siblings": "Tom, Beth",
    }
    result = memory_builder.save_record(tmp_vault, "Person", person_path, inputs)

    doc = frontmatter.read(person_path)
    assert doc.frontmatter["lives_in"] == "[[Boston]]"
    assert doc.frontmatter["occupation"] == "Teacher"
    assert doc.frontmatter["siblings"] == ["[[Tom]]", "[[Beth]]"]

    # New linked stubs were created
    assert (tmp_vault.folder("Place") / "Boston.md").exists()
    assert (tmp_vault.folder("Person") / "Tom.md").exists()
    assert (tmp_vault.folder("Person") / "Beth.md").exists()

    # And the result mentions them
    created_names = {p.stem for p in result.created_paths}
    assert {"Boston", "Tom", "Beth"} <= created_names


def test_ensure_stub_idempotent(tmp_vault: vault_mod.Vault):
    p1, created1 = memory_builder.ensure_stub(tmp_vault, "Person", "Sue")
    p2, created2 = memory_builder.ensure_stub(tmp_vault, "Person", "Sue")
    assert p1 == p2
    assert created1 is True
    assert created2 is False


def test_normalize_collapses_duplicates(tmp_vault: vault_mod.Vault):
    """'mary smith' and 'Mary Smith' must produce the same file."""
    p1, c1 = memory_builder.ensure_stub(tmp_vault, "Person", "mary smith")
    p2, c2 = memory_builder.ensure_stub(tmp_vault, "Person", "Mary Smith")
    assert p1 == p2
    assert c1 is True
    assert c2 is False


def test_save_memory_uses_today_when_when_blank(tmp_vault: vault_mod.Vault):
    mem = memory_builder.MemoryInput(
        title="Untitled", when="",
        who="", where="", why="", story="",
    )
    result = memory_builder.save_memory(tmp_vault, mem)
    today = dt.date.today().isoformat()
    assert result.memory_path.name.startswith(today)
