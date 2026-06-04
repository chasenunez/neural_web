from pathlib import Path

from familyvault import config as cfg


def test_load_minimal(tmp_path: Path):
    f = tmp_path / "config.yaml"
    f.write_text("vault_path: ./vault\n")
    c = cfg.load(f)
    assert c.vault_path == (tmp_path / "vault").resolve()
    assert c.git_remote is None
    assert c.photos_source is None
    assert c.users == []


def test_load_full(tmp_path: Path):
    f = tmp_path / "config.yaml"
    f.write_text(
        "vault_path: ./vault\n"
        "git_remote: git@github.com:x/y.git\n"
        "photos_source: ./pics\n"
        "users:\n"
        "  - name: Mom\n"
        "    email: mom@example.com\n"
        "  - name: Dad\n"
    )
    c = cfg.load(f)
    assert c.git_remote == "git@github.com:x/y.git"
    assert c.photos_source == (tmp_path / "pics").resolve()
    assert len(c.users) == 2
    assert c.user_by_name("mom").email == "mom@example.com"
    assert c.user_by_name("Dad").email is None
    assert c.user_by_name("Unknown").name == "Unknown"


def test_user_by_name_case_insensitive(tmp_path: Path):
    f = tmp_path / "config.yaml"
    f.write_text(
        "vault_path: ./v\n"
        "users:\n"
        "  - name: Mary Smith\n"
        "    email: m@x.com\n"
    )
    c = cfg.load(f)
    assert c.user_by_name("MARY SMITH").email == "m@x.com"


def test_absolute_path_preserved(tmp_path: Path):
    f = tmp_path / "config.yaml"
    abs_path = tmp_path / "abs_vault"
    f.write_text(f"vault_path: {abs_path}\n")
    c = cfg.load(f)
    assert c.vault_path == abs_path
