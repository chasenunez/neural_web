from familyvault import parsing


def test_empty_input():
    assert parsing.split_nouns("") == []
    assert parsing.split_nouns("   ") == []


def test_single_name():
    assert parsing.split_nouns("Mary") == ["Mary"]


def test_comma_separated():
    assert parsing.split_nouns("Mary, John, Sue") == ["Mary", "John", "Sue"]


def test_and_separator():
    assert parsing.split_nouns("Mom and Dad") == ["Mom", "Dad"]


def test_ampersand_separator():
    assert parsing.split_nouns("Mary & John") == ["Mary", "John"]


def test_mixed_separators():
    assert parsing.split_nouns("Mary, John and Sue & Tim") == [
        "Mary", "John", "Sue", "Tim",
    ]


def test_dedupes_case_insensitive():
    assert parsing.split_nouns("Mary, mary, MARY") == ["Mary"]


def test_strips_whitespace():
    assert parsing.split_nouns("  Mary  ,   John  ") == ["Mary", "John"]


def test_preserves_first_seen_casing():
    assert parsing.split_nouns("mary smith, Mary Smith") == ["mary smith"]


def test_semicolon_separator():
    assert parsing.split_nouns("Mary; John") == ["Mary", "John"]
