#!/usr/bin/env python
"""Tests for search query translation."""
from typing import List
from typing import Tuple

import pytest

from search_query.constants import Colors
from search_query.constants import LinterMode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.parser_ebsco import EBSCOParser

# flake8: noqa: E501


@pytest.mark.parametrize(
    "query_string, expected_tokens",
    [
        (
            'TI "Artificial Intelligence" AND AB Future NOT AB Past',
            [
                Token(value="TI", type=TokenTypes.FIELD, position=(0, 2)),
                Token(
                    value='"Artificial Intelligence"',
                    type=TokenTypes.SEARCH_TERM,
                    position=(3, 28),
                ),
                Token(value="AND", type=TokenTypes.LOGIC_OPERATOR, position=(29, 32)),
                Token(value="AB", type=TokenTypes.FIELD, position=(33, 35)),
                Token(value="Future", type=TokenTypes.SEARCH_TERM, position=(36, 42)),
                Token(value="NOT", type=TokenTypes.LOGIC_OPERATOR, position=(43, 46)),
                Token(value="AB", type=TokenTypes.FIELD, position=(47, 49)),
                Token(value="Past", type=TokenTypes.SEARCH_TERM, position=(50, 54)),
            ],
        ),
        (
            "Artificial N2 Intelligence",
            [
                Token(
                    value="Artificial", type=TokenTypes.SEARCH_TERM, position=(0, 10)
                ),
                Token(
                    value="N2", type=TokenTypes.PROXIMITY_OPERATOR, position=(11, 13)
                ),
                Token(
                    value="Intelligence", type=TokenTypes.SEARCH_TERM, position=(14, 26)
                ),
            ],
        ),
    ],
)
def test_tokenization(
    query_string: str, expected_tokens: List[Tuple[str, str, Tuple[int, int]]]
) -> None:
    """Test EBSCO parser tokenization."""
    parser = EBSCOParser(query_string, search_field_general="")
    parser.tokenize()

    actual_tokens = parser.tokens
    parser.print_tokens()
    assert actual_tokens == expected_tokens


@pytest.mark.parametrize(
    "query_string, messages",
    [
        (
            "Artificial intelligence and Future",
            [
                {
                    "code": "W0005",
                    "label": "operator-capitalization",
                    "message": "Operators should be capitalized",
                    "is_fatal": False,
                    "position": (24, 27),
                    "details": "",
                }
            ],
        ),
        (
            "(Artificial Intelligence AND Future",
            [
                {
                    "code": "F1001",
                    "label": "unbalanced-parentheses",
                    "message": "Parentheses are unbalanced in the query",
                    "is_fatal": True,
                    "position": (0, 1),
                    "details": "Unbalanced opening parenthesis",
                }
            ],
        ),
        (
            "TI AND Artificial Intelligence",
            [
                {
                    "code": "F1004",
                    "label": "invalid-token-sequence",
                    "message": "The sequence of tokens is invalid.",
                    "is_fatal": True,
                    "position": (3, 6),
                    "details": "Invalid operator position",
                }
            ],
        ),
        ("TI Artificial Intelligence AND AB Future", []),
        (
            "AI governance OR AB Future",
            [
                {
                    "code": "W0008",
                    "label": "token-ambiguity",
                    "message": "Token ambiguity",
                    "is_fatal": False,
                    "position": (0, 2),
                    "details": "The token 'AI governance' (at (0, 13)) is ambiguous. The AI could be a search field or a search term. To avoid confusion, please add quotes.",
                }
            ],
        ),
        (
            '"AI governance" OR AB Future',
            # Resolved ambiguity
            [],
        ),
        (
            'AI "governance" OR AB Future',
            [
                {
                    "code": "F0001",
                    "label": "tokenizing-failed",
                    "message": "Fatal error during tokenization",
                    "is_fatal": True,
                    "position": (0, 15),
                    "details": "Token 'AI \"governance\"' should be fully quoted",
                },
                {
                    "code": "W0008",
                    "label": "token-ambiguity",
                    "message": "Token ambiguity",
                    "is_fatal": False,
                    "position": (0, 2),
                    "details": "The token 'AI \"governance\"' (at (0, 15)) is ambiguous. The AI could be a search field or a search term. To avoid confusion, please add quotes.",
                },
            ],
        ),
        (
            "governance[tiab]",
            [
                {
                    "code": "F1010",
                    "label": "invalid-syntax",
                    "message": "Query contains invalid syntax",
                    "is_fatal": True,
                    "position": (10, 16),
                    "details": "EBSCOHOst fields must be before search terms and without brackets, e.g. AB robot or TI monitor. '[tiab]' is invalid.",
                },
                {
                    "code": "E0004",
                    "label": "invalid-character",
                    "message": "Search term contains invalid character",
                    "is_fatal": False,
                    "position": (0, 16),
                    "details": "",
                },
            ],
        ),
    ],
)
def test_linter(query_string: str, messages: list) -> None:
    parser = EBSCOParser(query_string, search_field_general="")
    try:
        parser.parse()
    except Exception:
        pass

    print(query_string)
    parser.tokenize()
    print(parser.tokens)
    parser.print_tokens()
    print(parser.linter.messages)

    assert parser.linter.messages == messages


@pytest.mark.parametrize(
    "query_string, messages",
    [
        (
            "TI Artificial Intelligence AND AB Future",
            [
                {
                    "code": "W0002",
                    "label": "search-field-extracted",
                    "message": "Recommend explicitly specifying the search field in the string",
                    "is_fatal": False,
                    "position": (),
                    "details": "",
                }
            ],
        ),
    ],
)
def test_linter_general_search_field(query_string: str, messages: list) -> None:
    parser = EBSCOParser(
        query_string, search_field_general="AB", mode=LinterMode.STRICT
    )
    try:
        parser.parse()
    except Exception:
        pass
    assert parser.linter.messages == messages


@pytest.mark.parametrize(
    "query_str, expected_translation",
    [
        (
            'TI example AND (AU "John Doe" OR AU "John Wayne")',
            'AND[example[TI], OR["John Doe"[AU], "John Wayne"[AU]]]',
        ),
        # Implicit precedence / artificial parentheses
        (
            'TI "Artificial Intelligence" AND AB Future NOT AB Past',
            'AND["Artificial Intelligence"[TI], NOT[Future[AB], Past[AB]]]',
        ),
        (
            'TI "Artificial Intelligence" NOT AB Future AND AB Past',
            'AND[NOT["Artificial Intelligence"[TI], Future[AB]], Past[AB]]',
        ),
        (
            'TI "AI" OR AB Robots AND AB Ethics',
            'OR["AI"[TI], AND[Robots[AB], Ethics[AB]]]',
        ),
        (
            'TI "AI" AND AB Robots OR AB Ethics',
            'OR[AND["AI"[TI], Robots[AB]], Ethics[AB]]',
        ),
        (
            'TI "AI" NOT AB Robots OR AB Ethics',
            'OR[NOT["AI"[TI], Robots[AB]], Ethics[AB]]',
        ),
        (
            'TI "AI" AND (AB Robots OR AB Ethics NOT AB Bias) OR SU "Technology"',
            'OR[AND["AI"[TI], OR[Robots[AB], NOT[Ethics[AB], Bias[AB]]]], "Technology"[SU]]',
        ),
        (
            'TI "Robo*" OR AB Robots AND AB Ethics NOT AB Bias OR SU "Technology"',
            'OR["Robo*"[TI], AND[Robots[AB], NOT[Ethics[AB], Bias[AB]]], "Technology"[SU]]',
        ),
    ],
)
def test_parser(query_str: str, expected_translation: str) -> None:
    print(
        f"Run query parser for: \n  {Colors.GREEN}{query_str}{Colors.END}\n--------------------\n"
    )

    parser = EBSCOParser(
        query_str=query_str,
        search_field_general="",
        mode="",
    )
    query_tree = parser.parse()

    # print("--------------------")
    # print("Tokens: \n")
    # parser.print_tokens()

    assert expected_translation == query_tree.to_generic_string(), print(
        query_tree.to_generic_string()
    )
