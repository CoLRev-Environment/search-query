#!/usr/bin/env python
"""Tests for search query translation"""
from search_query.constants import PLATFORM
from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.linter_base import QueryStringLinter
from search_query.query_and import AndQuery
from search_query.query_term import Term

# ruff: noqa: E501
# flake8: noqa: E501


def test_check_missing_tokens() -> None:
    linter = QueryStringLinter("digitalization 2 AND work")  # type: ignore
    linter.tokens = [
        Token(
            type=TokenTypes.TERM,
            value="digitalization",
            position=(0, 15),
        ),
        Token(
            type=TokenTypes.LOGIC_OPERATOR,
            value="AND",
            position=(18, 21),
        ),
        Token(
            type=TokenTypes.TERM,
            value="work",
            position=(25, 29),
        ),
    ]
    linter.check_missing_tokens()
    assert linter.messages == [
        {
            "code": "PARSE_0001",
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
            type=TokenTypes.TERM,
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
            type=TokenTypes.TERM,
            value="work",
            position=(25, 29),
        ),
    ]
    linter.check_unknown_token_types()

    assert linter.messages == [
        {
            "code": "PARSE_0001",
            "label": "tokenizing-failed",
            "message": "Fatal error during tokenization",
            "is_fatal": True,
            "position": [(16, 17)],
            "details": "Unknown token: '2'",
        }
    ]


def test_check_invalid_characters_in_term() -> None:
    linter = QueryStringLinter("digitalization 2 AND work")  # type: ignore
    linter.tokens = [
        Token(
            type=TokenTypes.TERM,
            value="digital#ization",
            position=(0, 15),
        ),
        Token(
            type=TokenTypes.LOGIC_OPERATOR,
            value="AND",
            position=(18, 21),
        ),
        Token(
            type=TokenTypes.TERM,
            value="work",
            position=(25, 29),
        ),
    ]
    linter.check_invalid_characters_in_term("#%&", QueryErrorCode.WOS_INVALID_CHARACTER)
    print(linter.messages)
    assert linter.messages == [
        {
            "code": "WOS_0012",
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
            type=TokenTypes.TERM,
            value="digitalization",
            position=(0, 15),
        ),
        Token(
            type=TokenTypes.LOGIC_OPERATOR,
            value="&",
            position=(16, 17),
        ),
        Token(
            type=TokenTypes.TERM,
            value="work",
            position=(18, 22),
        ),
    ]
    linter.check_boolean_operator_readability()
    print(linter.messages)
    assert linter.messages == [
        {
            "code": "STRUCT_0003",
            "label": "boolean-operator-readability",
            "message": "Boolean operator readability",
            "is_fatal": False,
            "position": [(16, 17)],
            "details": "Use AND, OR, NOT instead of |&",
        }
    ]


def test_check_invalid_characters_in_term_query() -> None:
    linter = QueryStringLinter("digitalizat#ion AND work")  # type: ignore
    query = AndQuery(
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
    linter.check_invalid_characters_in_term_query(
        query, "#%&", QueryErrorCode.WOS_INVALID_CHARACTER
    )
    print(linter.messages)
    assert linter.messages == [
        {
            "code": "WOS_0012",
            "label": "invalid-character",
            "message": "Search term contains invalid character",
            "is_fatal": False,
            "position": [(0, 16)],
            "details": "Invalid character '#' in search term 'digitalizat#ion'",
        }
    ]
