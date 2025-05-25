#!/usr/bin/env python
"""Tests for search query translation"""
from search_query.constants import PLATFORM
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.linter_base import QueryStringLinter
from search_query.query import Query
from search_query.query import Term

# ruff: noqa: E501
# flake8: noqa: E501


def test_check_missing_tokens() -> None:
    linter = QueryStringLinter("digitalization 2 AND work")  # type: ignore
    linter.tokens = [
        Token(
            type=TokenTypes.SEARCH_TERM,
            value="digitalization",
            position=(0, 15),
        ),
        Token(
            type=TokenTypes.LOGIC_OPERATOR,
            value="AND",
            position=(18, 21),
        ),
        Token(
            type=TokenTypes.SEARCH_TERM,
            value="work",
            position=(25, 29),
        ),
    ]
    linter.check_missing_tokens()
    assert linter.messages == [
        {
            "code": "F0001",
            "label": "tokenizing-failed",
            "message": "Fatal error during tokenization",
            "is_fatal": True,
            "position": [(14, 17)],
            "details": "Unparsed segment: '2'",
        }
    ]


def test_unknown_token_types() -> None:
    linter = QueryStringLinter("digitalization 2 AND work")  # type: ignore
    linter.tokens = [
        Token(
            type=TokenTypes.SEARCH_TERM,
            value="digitalization",
            position=(0, 15),
        ),
        Token(
            type=TokenTypes.UNKNOWN,
            value="2",
            position=(16, 17),
        ),
        Token(
            type=TokenTypes.LOGIC_OPERATOR,
            value="AND",
            position=(18, 21),
        ),
        Token(
            type=TokenTypes.SEARCH_TERM,
            value="work",
            position=(25, 29),
        ),
    ]
    linter.check_unknown_token_types()

    assert linter.messages == [
        {
            "code": "F0001",
            "label": "tokenizing-failed",
            "message": "Fatal error during tokenization",
            "is_fatal": True,
            "position": [(16, 17)],
            "details": "Unknown token: '2'",
        }
    ]


def test_check_invalid_characters_in_search_term() -> None:
    linter = QueryStringLinter("digitalization 2 AND work")  # type: ignore
    linter.tokens = [
        Token(
            type=TokenTypes.SEARCH_TERM,
            value="digital#ization",
            position=(0, 15),
        ),
        Token(
            type=TokenTypes.LOGIC_OPERATOR,
            value="AND",
            position=(18, 21),
        ),
        Token(
            type=TokenTypes.SEARCH_TERM,
            value="work",
            position=(25, 29),
        ),
    ]
    linter.check_invalid_characters_in_search_term("#%&")
    print(linter.messages)
    assert linter.messages == [
        {
            "code": "E0004",
            "label": "invalid-character",
            "message": "Search term contains invalid character",
            "is_fatal": False,
            "position": [(0, 15)],
            "details": "Invalid character '#' in search term 'digital#ization'",
        }
    ]


def test_check_boolean_operator_readability() -> None:
    linter = QueryStringLinter("digitalization & work")  # type: ignore
    linter.tokens = [
        Token(
            type=TokenTypes.SEARCH_TERM,
            value="digitalization",
            position=(0, 15),
        ),
        Token(
            type=TokenTypes.LOGIC_OPERATOR,
            value="&",
            position=(16, 17),
        ),
        Token(
            type=TokenTypes.SEARCH_TERM,
            value="work",
            position=(18, 22),
        ),
    ]
    linter.check_boolean_operator_readability()
    print(linter.messages)
    assert linter.messages == [
        {
            "code": "W0009",
            "label": "boolean-operator-readability",
            "message": "Boolean operator readability",
            "is_fatal": False,
            "position": [(16, 17)],
            "details": "Please use AND, OR, NOT instead of |&",
        }
    ]


def test_check_invalid_characters_in_search_term_query() -> None:
    linter = QueryStringLinter("digitalizat#ion AND work")  # type: ignore
    query = Query(
        value="AND",
        operator=True,
        children=[
            Term(
                value="digitalizat#ion",
                position=(0, 16),
            ),
            Term(
                value="work",
                position=(21, 25),
            ),
        ],
        platform=PLATFORM.WOS.value,
    )
    linter.check_invalid_characters_in_search_term_query(query, "#%&")
    print(linter.messages)
    assert linter.messages == [
        {
            "code": "E0004",
            "label": "invalid-character",
            "message": "Search term contains invalid character",
            "is_fatal": False,
            "position": [(0, 16)],
            "details": "Invalid character '#' in search term 'digitalizat#ion'",
        }
    ]
