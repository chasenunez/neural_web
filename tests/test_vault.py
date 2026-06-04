from pathlib import Path

from familyvault import frontmatter, vault as vault_mod


def test_normalize_name_basic():
    assert vault_mod.normalize_name("mary smith") == "Mary Smith"


def test_normalize_name_apostrophe():
    assert vault_mod.normalize_name("grandma's house") == "Grandmas House"
    assert vault_mod.normalize_name("grandma’s house") == "Grandmas House"


def test_normalize_name_collapses_whitespace():
    assert vault_mod.normalize_name("  Mary    Smith  ") == "Mary Smith"


def test_normalize_name_strips_unsafe():
    assert vault_mod.normalize_name("Mary/Smith?") == "Marysmith"


def test_display_to_wikilink():
    assert vault_mod.display_to_wikilink("mary smith") == "[[Mary Smith]]"


def test_wikilinks_to_displays():
    values = ["[[Mary Smith]]", "[[John]]", ""]
    assert vault_mod.wikilinks_to_displays(values) == ["Mary Smith", "John"]


def test_file_for_uses_normalized_name(tmp_vault: vault_mod.Vault):
    path = tmp_vault.file_for("Person", "mary smith")
    assert path.name == "Mary Smith.md"
    assert path.parent == tmp_vault.folder("Person")


def test_ensure_dirs_creates_expected(tmp_vault: vault_mod.Vault):
    assert (tmp_vault.root / "People").is_dir()
    assert (tmp_vault.root / "Places").is_dir()
    assert (tmp_vault.root / "Memories").is_dir()
    assert (tmp_vault.root / "Photos").is_dir()


def test_list_files_sorted(tmp_vault: vault_mod.Vault):
    (tmp_vault.folder("Person") / "Beta.md").write_text("---\n---\n")
    (tmp_vault.folder("Person") / "Alpha.md").write_text("---\n---\n")
    names = [p.name for p in tmp_vault.list_files("Person")]
    assert names == ["Alpha.md", "Beta.md"]


def test_incomplete_files_detects_blank(tmp_vault: vault_mod.Vault):
    blank = tmp_vault.file_for("Person", "Alice")
    full = tmp_vault.file_for("Person", "Bob")
    frontmatter.write(blank, frontmatter.Document({"name": "Alice", "lives_in": ""}, ""))
    fm_full = {
        "type": "person", "name": "Bob", "lives_in": "[[Home]]",
        "birthdate": "1990-01-01", "birthplace": "[[Hospital]]",
        "parents": ["[[X]]"], "siblings": ["[[Y]]"], "partner": "[[Z]]",
        "children": ["[[Kid]]"], "core_memories": ["[[Mem]]"],
        "paternal_grandparents": ["[[A]]"], "maternal_grandparents": ["[[B]]"],
        "extended_family": ["[[C]]"], "occupation": "Engineer",
        "degrees": "BS", "past_addresses": ["[[Old]]"],
        "friends": ["[[F]]"], "employers": "Acme",
    }
    frontmatter.write(full, frontmatter.Document(fm_full, ""))

    incomplete = tmp_vault.incomplete_files("Person")
    assert blank in incomplete
    assert full not in incomplete
