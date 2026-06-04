import pytest

from familyvault import templates


def test_by_type_known():
    assert templates.by_type("Person").type_name == "Person"
    assert templates.by_type("person").type_name == "Person"


def test_by_type_unknown_raises():
    with pytest.raises(KeyError):
        templates.by_type("Banana")


def test_empty_frontmatter_includes_all_fields():
    fm = templates.PERSON.empty_frontmatter()
    for f in templates.PERSON.fields:
        assert f.key in fm


def test_empty_frontmatter_has_correct_blanks():
    fm = templates.PERSON.empty_frontmatter()
    assert fm["name"] == ""
    assert fm["parents"] == []
    assert fm["lives_in"] == ""  # single link → empty string, not list


def test_field_lookup():
    f = templates.PERSON.field("name")
    assert f is not None and f.label == "Name"
    assert templates.PERSON.field("nonexistent") is None


def test_field_ordering_most_important_first():
    # Per the brief, name comes first and least-important fields are last.
    keys = [f.key for f in templates.PERSON.fields]
    assert keys[0] == "name"
    assert keys[-1] == "employers"


def test_place_has_maps_link():
    assert templates.PLACE.field("maps_link") is not None


def test_type_in_empty_frontmatter():
    assert templates.PERSON.empty_frontmatter()["type"] == "person"
