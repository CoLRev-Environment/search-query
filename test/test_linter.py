#!/usr/bin/env python
"""Tests for search query translation"""
import pytest

from search_query.constants import PLATFORM
from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.linter import lint_query_string
from search_query.linter_base import QueryStringLinter
from search_query.query_and import AndQuery
from search_query.query_term import Term
from search_query.utils import aggregate_linter_messages

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
            "position": [(7, 8)],
            "details": "Invalid character '#' in search term 'digital#ization' will be replaced with whitespace.",
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


def test_aggregate_linter_messages_combines_positions() -> None:
    messages = [
        {
            "code": "STRUCT_0002",
            "label": "operator-capitalization",
            "message": "Operators should be capitalized",
            "is_fatal": False,
            "position": [(10, 12)],
            "details": "",
        },
        {
            "code": "STRUCT_0002",
            "label": "operator-capitalization",
            "message": "Operators should be capitalized",
            "is_fatal": False,
            "position": [(22, 24)],
            "details": "",
        },
    ]

    aggregated_messages = aggregate_linter_messages(messages)

    assert aggregated_messages == [
        {
            "code": "STRUCT_0002",
            "label": "operator-capitalization",
            "message": "Operators should be capitalized",
            "is_fatal": False,
            "position": [(10, 12), (22, 24)],
            "details": "",
        }
    ]


def test_aggregate_linter_messages_preserves_fields_and_input() -> None:
    message = {
        "code": "STRUCT_0002",
        "label": "operator-capitalization",
        "message": "Operators should be capitalized",
        "is_fatal": False,
        "position": [(10, 12)],
        "details": "",
        "metadata": {"source": "test"},
    }

    aggregated_messages = aggregate_linter_messages([message])

    assert aggregated_messages == [message]
    assert aggregated_messages[0] is not message
    assert aggregated_messages[0]["metadata"] is message["metadata"]


def test_aggregate_linter_messages_preserves_missing_position() -> None:
    message = {
        "code": "STRUCT_0002",
        "label": "operator-capitalization",
        "message": "Operators should be capitalized",
        "is_fatal": False,
    }

    assert aggregate_linter_messages([message]) == [message]


def test_check_status_aggregates_and_prints_duplicate_messages(
    capsys: pytest.CaptureFixture[str],
) -> None:
    linter = QueryStringLinter("a AND b and c")  # type: ignore
    message = {
        "code": "STRUCT_0002",
        "label": "operator-capitalization",
        "message": "Operators should be capitalized",
        "is_fatal": False,
        "position": [(6, 9)],
        "details": "Capitalize the operator",
    }
    second_message = {**message, "position": [(12, 15)]}
    linter.messages = [message, second_message]

    linter.check_status()

    output = capsys.readouterr().out
    assert output.count("operator-capitalization (STRUCT_0002)") == 1
    assert output.count("Capitalize the operator") == 1
    assert "\x1b[93mb a\x1b[0mnd" in output
    assert "\x1b[93mc\x1b[0m" in output
    assert len(linter.messages) == 1
    assert linter.messages[0]["position"] == [(6, 9), (12, 15)]


def test_string_linter_aggregates_stored_messages_across_status_checks(
    capsys: pytest.CaptureFixture[str],
) -> None:
    linter = QueryStringLinter("a AND b and c")  # type: ignore
    linter.messages = [
        {
            "code": "STRUCT_0002",
            "label": "operator-capitalization",
            "message": "Operators should be capitalized",
            "is_fatal": False,
            "position": [(6, 9)],
            "details": "Capitalize the operator",
        }
    ]

    linter.check_status()
    capsys.readouterr()

    linter.messages.append(
        {
            "code": "STRUCT_0002",
            "label": "operator-capitalization",
            "message": "Operators should be capitalized",
            "is_fatal": False,
            "position": [(12, 15)],
            "details": "Capitalize the operator",
        }
    )
    linter.check_status()

    assert len(linter.messages) == 1
    assert linter.messages[0]["position"] == [(6, 9), (12, 15)]


def test_query_list_linter_aggregates_stored_messages_by_item() -> None:
    from search_query.linter_base import QueryListLinter

    class DummyParser:
        query_list = "a AND b and c"

    list_linter = QueryListLinter(
        parser=DummyParser(),  # type: ignore[arg-type]
        string_parser_class=object,  # type: ignore[arg-type]
    )
    list_linter.messages = {
        1: [
            {
                "code": "STRUCT_0002",
                "label": "operator-capitalization",
                "message": "Operators should be capitalized",
                "is_fatal": False,
                "position": [(6, 9)],
                "details": "Capitalize the operator",
            },
            {
                "code": "STRUCT_0002",
                "label": "operator-capitalization",
                "message": "Operators should be capitalized",
                "is_fatal": False,
                "position": [(12, 15)],
                "details": "Capitalize the operator",
            },
        ],
        2: [
            {
                "code": "STRUCT_0002",
                "label": "operator-capitalization",
                "message": "Operators should be capitalized",
                "is_fatal": False,
                "position": [(20, 23)],
                "details": "Capitalize the operator",
            }
        ],
    }

    list_linter.check_status()

    assert list_linter.messages[1][0]["position"] == [(6, 9), (12, 15)]
    assert list_linter.messages[2][0]["position"] == [(20, 23)]


def test_list_linter_stores_new_positions_in_existing_aggregate() -> None:
    from search_query.linter_base import QueryListLinter

    class DummyParser:
        query_list = "a AND b and c"

    list_linter = QueryListLinter(
        parser=DummyParser(),  # type: ignore[arg-type]
        string_parser_class=object,  # type: ignore[arg-type]
    )
    list_linter.messages = {
        1: [
            {
                "code": "STRUCT_0002",
                "label": "operator-capitalization",
                "message": "Operators should be capitalized",
                "is_fatal": False,
                "position": [(6, 9)],
                "details": "Capitalize the operator",
            }
        ]
    }

    list_linter.messages[1].append(
        {
            "code": "STRUCT_0002",
            "label": "operator-capitalization",
            "message": "Operators should be capitalized",
            "is_fatal": False,
            "position": [(12, 15)],
            "details": "Capitalize the operator",
        }
    )
    list_linter.check_status()

    assert len(list_linter.messages[1]) == 1
    assert list_linter.messages[1][0]["position"] == [(6, 9), (12, 15)]


def test_lint_query_string_returns_stored_aggregated_list_messages() -> None:
    query_list = "1. insomnia OR insomnia\n2. S1 AND S1"

    messages = lint_query_string(query_list, platform="ebscohost")

    assert isinstance(messages, dict)
    assert len(messages["1"]) == 1
    assert messages["1"][0]["position"] == [(3, 11)]
