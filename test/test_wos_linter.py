"""Web-of-Science linter unit tests."""
import typing
from typing import Callable

import pytest

from search_query.constants import LinterMode
from search_query.exception import SearchQueryException
from search_query.linter_wos import WOSQueryStringLinter
from search_query.parser_wos import WOSParser

# ruff: noqa: E501
# flake8: noqa: E501


@pytest.fixture(scope="module")
def linter_factory() -> Callable[[str], WOSQueryStringLinter]:
    def _build_linter(query_str: str) -> WOSQueryStringLinter:
        parser = WOSParser(query_str)
        parser.tokenize()
        return WOSQueryStringLinter(parser)

    return _build_linter


@pytest.mark.parametrize(
    "query_str, expected_messages",
    [
        (
            "test query",
            [
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": (-1, -1),
                    "details": "",
                }
            ],
        ),
        (
            "(test query)",
            [
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": (-1, -1),
                    "details": "",
                }
            ],
        ),
        (
            "(test query",
            [
                {
                    "code": "F1001",
                    "label": "unbalanced-parentheses",
                    "message": "Parentheses are unbalanced in the query",
                    "is_fatal": True,
                    "position": (0, 1),
                    "details": "Unbalanced opening parenthesis",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": (-1, -1),
                    "details": "",
                },
            ],
        ),
        (
            "test query)",
            [
                {
                    "code": "F1001",
                    "label": "unbalanced-parentheses",
                    "message": "Parentheses are unbalanced in the query",
                    "is_fatal": True,
                    "position": (10, 11),
                    "details": "Unbalanced closing parenthesis",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": (-1, -1),
                    "details": "",
                },
            ],
        ),
        (
            "(test query))",
            [
                {
                    "code": "F1001",
                    "label": "unbalanced-parentheses",
                    "message": "Parentheses are unbalanced in the query",
                    "is_fatal": True,
                    "position": (12, 13),
                    "details": "Unbalanced closing parenthesis",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": (-1, -1),
                    "details": "",
                },
            ],
        ),
        (
            "((test query)",
            [
                {
                    "code": "F1001",
                    "label": "unbalanced-parentheses",
                    "message": "Parentheses are unbalanced in the query",
                    "is_fatal": True,
                    "position": (0, 1),
                    "details": "Unbalanced opening parenthesis",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": (-1, -1),
                    "details": "",
                },
            ],
        ),
        (
            "TI=term1 AND OR",
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": (9, 15),
                    "details": "Two operators in a row are not allowed.",
                },
                {
                    "code": "W0007",
                    "label": "implicit-precedence",
                    "message": "Operator changed at the same level (explicit parentheses are recommended)",
                    "is_fatal": False,
                    "position": (13, 15),
                    "details": "",
                },
            ],
        ),
        (
            "TI=term1 au= ti=",
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": (9, 12),
                    "details": "",
                },
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": (13, 16),
                    "details": "",
                },
            ],
        ),
        (
            "TI=term1 (query)",
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": (9, 10),
                    "details": "",
                }
            ],
        ),
        (
            ") (query)",
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": (2, 3),
                    "details": "",
                },
                {
                    "code": "F1001",
                    "label": "unbalanced-parentheses",
                    "message": "Parentheses are unbalanced in the query",
                    "is_fatal": True,
                    "position": (0, 1),
                    "details": "Unbalanced closing parenthesis",
                },
                {
                    "code": "E0001",
                    "label": "search-field-missing",
                    "message": "Expected search field is missing",
                    "is_fatal": False,
                    "position": (-1, -1),
                    "details": "",
                },
            ],
        ),
        (
            "TI=term1 au=",
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": (9, 12),
                    "details": "",
                }
            ],
        ),
        (
            "TI=term1 NEAR/20 term2",
            [
                {
                    "code": "F2007",
                    "label": "near-distance-too-large",
                    "message": "NEAR distance is too large (max: 15).",
                    "is_fatal": True,
                    "position": (9, 16),
                    "details": "",
                },
            ],
        ),
        # TODO: should be implemented properly.
        # (
        #     "TI=term1 NEAR/10 term2",
        #     [],
        # ),
        # TODO : should be implemented properly.
        # (
        #     "term1 NEAR term2",
        #     [],  # Assuming implicit NEAR distance is handled
        # ),
        # TODO : should be implemented properly.
        # (
        #     "term1 NEAR term2",  # Repeats earlier but for implicit NEAR warning
        #     [
        #         {
        #             "code": "W0006",
        #             "is_fatal": False,
        #             "details": "",
        #             "label": "implicit-near-value",
        #             "message": "The value of NEAR operator is implicit",
        #             "position": (6, 10),
        #         },
        #     ],
        # ),
        (
            "TI=term1 !term2",
            [
                {
                    "code": "F2001",
                    "label": "wildcard-unsupported",
                    "message": "Unsupported wildcard in search string.",
                    "is_fatal": True,
                    "position": (9, 10),
                    "details": "",
                },
            ],
        ),
        (
            'TI=term1 AND "?"',
            [
                {
                    "code": "F2006",
                    "label": "wildcard-standalone",
                    "message": "Wildcard cannot be standalone.",
                    "is_fatal": True,
                    "position": (13, 16),
                    "details": "",
                },
            ],
        ),
        (
            "TI=(term1 te?m2)",
            [],
        ),
        (
            "TI=(term1 term2*)",
            [],
        ),
        (
            "TI=(term1 term2!*)",
            [
                # TODO : should we raise only one message?
                {
                    "code": "F2005",
                    "label": "wildcard-after-special-char",
                    "message": "Wildcard cannot be preceded by special characters.",
                    "is_fatal": True,
                    "position": (4, 17),
                    "details": "",
                },
                {
                    "code": "F2001",
                    "label": "wildcard-unsupported",
                    "message": "Unsupported wildcard in search string.",
                    "is_fatal": True,
                    "position": (15, 16),
                    "details": "",
                },
            ],
        ),
        (
            "TI=te*",
            [
                {
                    "code": "F2003",
                    "is_fatal": True,
                    "details": "",
                    "label": "wildcard-right-short-length",
                    "message": "Right-hand wildcard must preceded by at least three characters.",
                    "position": (3, 6),
                },
            ],
        ),
        (
            "TI=term1 TI=*term2",
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": (9, 12),
                    "details": "",
                }
            ],
        ),
        (
            "TI=*te",
            [
                {
                    "code": "F2004",
                    "is_fatal": True,
                    "details": "",
                    "label": "wildcard-left-short-length",
                    "message": "Left-hand wildcard must be preceded by at least three characters.",
                    "position": (3, 6),
                },
            ],
        ),
        (
            "IS=1234-5678",
            [],
        ),
        (
            "IS=1234-567",
            [
                {
                    "code": "F2008",
                    "is_fatal": True,
                    "details": "",
                    "label": "isbn-format-invalid",
                    "message": "Invalid ISBN format.",
                    "position": (3, 11),
                },
            ],
        ),
        (
            "IS=978-3-16-148410-0",
            [],
        ),
        (
            "IS=978-3-16-148410",
            [
                {
                    "code": "F2008",
                    "is_fatal": True,
                    "details": "",
                    "label": "isbn-format-invalid",
                    "message": "Invalid ISBN format.",
                    "position": (3, 18),
                },
            ],
        ),
        (
            "DO=10.1000/xyz123",
            [],
        ),
        (
            "DO=12.1000/xyz",
            [
                {
                    "code": "F2009",
                    "label": "doi-format-invalid",
                    "message": "Invalid DOI format.",
                    "is_fatal": True,
                    "position": (3, 14),
                    "details": "",
                },
            ],
        ),
        (
            "TI=term1 and TI=term2",
            [
                {
                    "code": "W0005",
                    "is_fatal": False,
                    "details": "",
                    "label": "operator-capitalization",
                    "message": "Operators should be capitalized",
                    "position": (9, 12),
                },
            ],
        ),
        (
            "TI=term1 AND PY=202*",
            [
                {
                    "code": "F2002",
                    "is_fatal": True,
                    "details": "",
                    "label": "wildcard-in-year",
                    "message": "Wildcard characters (*, ?, $) not supported in year search.",
                    "position": (16, 20),
                },
            ],
        ),
        (
            "TI=term1 AND IY=digital",
            [
                {
                    "code": "F2011",
                    "label": "search-field-unsupported",
                    "message": "Search field is not supported for this database",
                    "is_fatal": True,
                    "details": "Search field IY= at position (13, 16) is not supported.",
                    "position": (13, 16),
                },
            ],
        ),
        (
            "TI=term1 AND PY=1900-2000",
            [
                {
                    "code": "F2010",
                    "label": "year-span-violation",
                    "message": "Year span must be five or less.",
                    "is_fatal": True,
                    "position": (16, 25),
                    "details": "",
                },
            ],
        ),
    ],
)
def test_linter(
    query_str: str,
    expected_messages: typing.List[dict],
) -> None:
    print(query_str)

    parser = WOSParser(query_str)
    try:
        parser.parse()
    except SearchQueryException:
        pass
    parser.print_tokens()
    print(parser.linter.messages)
    assert parser.linter.messages == expected_messages


@pytest.mark.parametrize(
    "query_str, expected_message, expected_query",
    [
        (
            "TI=(term1 OR term2 AND term3)",
            "Operator changed at the same level (explicit parentheses are recommended)",
            "TI=(term1 OR TI=(term2 AND term3))",
        ),
        (
            "TI=term1 AND term2 OR term3",
            "Operator changed at the same level (explicit parentheses are recommended)",
            "(TI=(term1 AND term2) OR term3)",
        ),
        # TODO : proximity operators not yet handled by wos
        # (
        #     "term1 AND term2 NEAR term3",
        #     "Operator changed at the same level (explicit parentheses are recommended)",
        #     ""
        # ),
        # (
        #     "term1 NEAR/5 term2 AND term3",
        #     "Operator changed at the same level (explicit parentheses are recommended)",
        #     ""
        # ),
    ],
)
def test_implicit_precedence(
    query_str: str, expected_message: str, expected_query: str
) -> None:
    parser = WOSParser(query_str, mode=LinterMode.NONSTRICT)
    query = parser.parse()
    parser.print_tokens()

    assert expected_query == query.to_string(syntax="wos")

    assert len(parser.linter.messages) == 1
    msg = parser.linter.messages[0]

    assert msg["code"] == "W0007"
    assert msg["label"] == "implicit-precedence"
    assert msg["message"] == expected_message
    assert msg["is_fatal"] is False
    assert msg["details"] == ""
