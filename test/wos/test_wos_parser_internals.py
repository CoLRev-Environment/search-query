#!/usr/bin/env python3
"""Web-of-Science unit tests for internals of query parser."""
from search_query.constants import Fields
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.wos.constants import syntax_str_to_generic_field_set
from search_query.wos.parser import WOSParser

# ruff: noqa: E501
# pylint: disable=too-many-lines
# flake8: noqa: E501


def test_combine_subsequent_terms_single_term() -> None:
    """
    Test the `combine_subsequent_terms` method with a single term.

    This test verifies that the `combine_subsequent_terms` method correctly handles
    a list of tokens with a single term and does not combine it with anything.
    """
    parser = WOSParser(query_str="")
    parser.tokens = [Token(value="example", type=TokenTypes.TERM, position=(0, 7))]
    parser.combine_subsequent_terms()

    expected_tokens = [Token(value="example", type=TokenTypes.TERM, position=(0, 7))]

    assert parser.tokens == expected_tokens


def test_combine_subsequent_terms_multiple_terms() -> None:
    """
    Test the `combine_subsequent_terms` method with multiple terms.

    This test verifies that the `combine_subsequent_terms` method correctly combines
    subsequent terms into a single token.
    """
    parser = WOSParser(query_str="")
    parser.tokens = [
        Token(value="example", type=TokenTypes.TERM, position=(0, 7)),
        Token(value="example2", type=TokenTypes.TERM, position=(8, 16)),
    ]
    parser.combine_subsequent_terms()

    expected_tokens = [
        Token(value="example example2", type=TokenTypes.TERM, position=(0, 16))
    ]

    assert parser.tokens == expected_tokens


def test_combine_subsequent_terms_with_operators() -> None:
    """
    Test the `combine_subsequent_terms` method with terms and operators.

    This test verifies that the `combine_subsequent_terms` method correctly combines
    subsequent terms into a single token and does not combine terms with operators.
    """
    parser = WOSParser(query_str="")
    parser.tokens = [
        Token(value="example", type=TokenTypes.TERM, position=(0, 7)),
        Token(value="AND", type=TokenTypes.LOGIC_OPERATOR, position=(8, 11)),
        Token(value="example2", type=TokenTypes.TERM, position=(12, 20)),
    ]
    parser.combine_subsequent_terms()

    expected_tokens = [
        Token(value="example", type=TokenTypes.TERM, position=(0, 7)),
        Token(value="AND", type=TokenTypes.LOGIC_OPERATOR, position=(8, 11)),
        Token(value="example2", type=TokenTypes.TERM, position=(12, 20)),
    ]

    assert parser.tokens == expected_tokens


def test_combine_subsequent_terms_with_special_characters() -> None:
    """
    Test the `combine_subsequent_terms` method with terms containing special characters.

    This test verifies that the `combine_subsequent_terms` method correctly combines
    subsequent terms containing special characters into a single token.
    """
    parser = WOSParser(query_str="")
    parser.tokens = [
        Token(value="ex$mple", type=TokenTypes.TERM, position=(0, 7)),
        Token(value="example2", type=TokenTypes.TERM, position=(8, 16)),
    ]
    parser.combine_subsequent_terms()

    expected_tokens = [
        Token(value="ex$mple example2", type=TokenTypes.TERM, position=(0, 16))
    ]

    assert parser.tokens == expected_tokens


def test_combine_subsequent_terms_with_mixed_case() -> None:
    """
    Test the `combine_subsequent_terms` method with terms in mixed case.

    This test verifies that the `combine_subsequent_terms` method correctly combines
    subsequent terms in mixed case into a single token.
    """
    parser = WOSParser(query_str="")
    parser.tokens = [
        Token(value="Example", type=TokenTypes.TERM, position=(0, 7)),
        Token(value="example2", type=TokenTypes.TERM, position=(8, 16)),
    ]
    parser.combine_subsequent_terms()

    expected_tokens = [
        Token(value="Example example2", type=TokenTypes.TERM, position=(0, 16))
    ]

    assert parser.tokens == expected_tokens


def test_check_fields_title() -> None:
    """
    Test the `check_fields` method with title search fields.

    This test verifies that the `check_fields` method correctly translates
    title search fields into the base search field "TI=".
    """
    title_fields = ["TI=", "ti=", "title="]

    for field in title_fields:
        result = syntax_str_to_generic_field_set(field)
        assert result == {Fields.TITLE}


def test_check_fields_abstract() -> None:
    """
    Test the `check_fields` method with abstract search fields.

    This test verifies that the `check_fields` method correctly translates
    abstract search fields into the base search field "AB=".
    """
    abstract_fields = [
        "AB=",
        "ab=",
        "abstract=",
    ]

    for field in abstract_fields:
        result = syntax_str_to_generic_field_set(field)
        assert result == {Fields.ABSTRACT}


def test_check_fields_author() -> None:
    """
    Test the `check_fields` method with author search fields.

    This test verifies that the `check_fields` method correctly translates
    author search fields into the base search field "AU=".
    """
    author_fields = [
        "AU=",
        "au=",
        "author=",
    ]

    for field in author_fields:
        result = syntax_str_to_generic_field_set(field)
        assert result == {Fields.AUTHOR}


def test_check_fields_topic() -> None:
    """
    Test the `check_fields` method with topic search fields.

    This test verifies that the `check_fields` method correctly translates
    topic search fields into the base search field "TS=".
    """
    topic_fields = [
        "TS=",
        "ts=",
        "topic=",
    ]

    for field in topic_fields:
        result = syntax_str_to_generic_field_set(field)
        assert result == {
            Fields.TITLE,
            Fields.ABSTRACT,
            Fields.AUTHOR_KEYWORDS,
            Fields.KEYWORDS_PLUS,
        }


def test_check_fields_language() -> None:
    """
    Test the `check_fields` method with language search fields.

    This test verifies that the `check_fields` method correctly translates
    language search fields into the base search field "LA=".
    """
    language_fields = [
        "LA=",
        "la=",
        "language=",
    ]

    for field in language_fields:
        result = syntax_str_to_generic_field_set(field)
        assert result == {Fields.LANGUAGE}


def test_check_fields_year() -> None:
    """
    Test the `check_fields` method with year search fields.

    This test verifies that the `check_fields` method correctly translates
    year search fields into the base search field "PY=".
    """
    year_fields = [
        "PY=",
        "py=",
    ]

    for field in year_fields:
        result = syntax_str_to_generic_field_set(field)
        assert result == {Fields.YEAR_PUBLICATION}


def test_query_parsing_1() -> None:
    parser = WOSParser(query_str="TI=example AND AU=John Doe")
    query = parser.parse()

    # Assertions using standard assert statement
    assert query.value == "AND"
    assert query.operator is True
    assert len(query.children) == 2
    assert query.children[0].value == "example"
    assert query.children[0].operator is False
    assert query.children[1].value == "John Doe"
    assert query.children[1].field.value == "AU="  # type: ignore
    assert query.children[1].operator is False


def test_query_parsing_2() -> None:
    parser = WOSParser(
        query_str="TI=example AND (AU=John Doe OR AU=John Wayne)",
    )
    query = parser.parse()

    # Assertions using standard assert statement
    assert query.value == "AND"
    assert query.operator is True
    assert len(query.children) == 2
    assert query.children[0].value == "example"
    assert query.children[0].operator is False
    assert query.children[1].value == "OR"
    assert query.children[1].children[1].value == "John Wayne"
    assert query.children[1].children[1].field.value == "AU="  # type: ignore
