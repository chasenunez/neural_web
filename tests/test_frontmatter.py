from pathlib import Path

from familyvault import frontmatter


def test_roundtrip_simple():
    doc = frontmatter.Document(
        frontmatter={"title": "Hello", "tags": ["a", "b"]},
        body="Hello world.\n",
    )
    parsed = frontmatter.parse(doc.render())
    assert parsed.frontmatter["title"] == "Hello"
    assert parsed.frontmatter["tags"] == ["a", "b"]
    assert parsed.body.strip() == "Hello world."


def test_parse_missing_frontmatter():
    parsed = frontmatter.parse("# Just a heading\n")
    assert parsed.frontmatter == {}
    assert parsed.body.startswith("# Just a heading")


def test_parse_empty_frontmatter_block():
    parsed = frontmatter.parse("---\n---\n\nBody\n")
    assert parsed.frontmatter == {}
    assert parsed.body.strip() == "Body"


def test_unicode_roundtrip():
    doc = frontmatter.Document(
        frontmatter={"name": "Café Olé", "place": "São Paulo"},
        body="A trip to São Paulo.",
    )
    parsed = frontmatter.parse(doc.render())
    assert parsed.frontmatter["name"] == "Café Olé"
    assert parsed.frontmatter["place"] == "São Paulo"


def test_write_and_read(tmp_path: Path):
    path = tmp_path / "sub" / "file.md"
    doc = frontmatter.Document(frontmatter={"a": 1}, body="hi")
    frontmatter.write(path, doc)
    again = frontmatter.read(path)
    assert again.frontmatter == {"a": 1}
    assert again.body.strip() == "hi"


def test_yaml_preserves_field_order():
    doc = frontmatter.Document(
        frontmatter={"z": 1, "a": 2, "m": 3},
        body="",
    )
    rendered = doc.render()
    # Field order must be preserved (template order matters for the UI).
    z_pos = rendered.index("z:")
    a_pos = rendered.index("a:")
    m_pos = rendered.index("m:")
    assert z_pos < a_pos < m_pos


def test_malformed_frontmatter_falls_back_to_body():
    text = "---\nthis is: not: valid: yaml: at: all\n---\nBody\n"
    parsed = frontmatter.parse(text)
    # Either a graceful parse or an empty fm with content preserved.
    assert "Body" in parsed.body or "Body" in str(parsed.frontmatter)
