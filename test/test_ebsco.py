#!/usr/bin/env python
"""Tests for search query translation."""
from typing import List
from typing import Tuple

import pytest

from search_query.constants import LinterMode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.parser_base import QueryStringParser
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
        # Add more test cases as needed
    ],
)
def test_tokenization(
    query_string: str, expected_tokens: List[Tuple[str, str, Tuple[int, int]]]
) -> None:
    """Test EBSCO parser tokenization."""
    ebsco_parser = EBSCOParser(query_string, "")
    ebsco_parser.tokenize()

    # Assert equality with error message on failure
    actual_tokens = ebsco_parser.tokens
    assert actual_tokens == expected_tokens, print_debug_tokens(
        ebsco_parser, expected_tokens, query_string
    )


# TODO : move to parser_base?
def print_debug_tokens(
    ebsco_parser: QueryStringParser,
    expected_tokens: List[Tuple[str, str, Tuple[int, int]]],
    query_string: str,
) -> str:
    """Debugging utility for tokenization mismatches."""
    debug_message = (
        f"Query String: {query_string}\n\n"
        f"Expected Tokens: {expected_tokens}\n\n"
        f"Actual Tokens: {ebsco_parser.tokens}\n\n"
    )
    return debug_message


@pytest.mark.parametrize(
    "query_string, messages",
    [
        # 1. Boolean operator not capitalized
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
        # 2. Unbalanced parentheses
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
        # 3. Invalid token sequence (FIELD followed directly by LOGIC_OPERATOR)
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
        # 4. Correct query (no linter messages expected)
        ("TI Artificial Intelligence AND AB Future", []),
        # 1. Ambiguous token
        (
            "AI governance OR AB Future",
            [
                {
                    "code": "W0008",
                    "label": "token-ambiguity",
                    "message": "Token ambiguity",
                    "is_fatal": False,
                    "position": (0, 2),
                    "details": "The token 'AI governance' (at (0, 13)) is ambiguous. The AI could be a search field or a search term. To avoid confusion, please add parentheses.",
                }
            ],
        ),
        # Resolved ambiguity
        (
            '"AI governance" OR AB Future',
            [],
        ),
        # Unknown search field (TODO)
        # (
        #     'AI "governance" OR AB Future',
        #     [],
        # ),
    ],
)
def test_linter(query_string: str, messages: list) -> None:
    ebsco_parser = EBSCOParser(query_string, "")
    try:
        ebsco_parser.parse()
    except Exception:
        pass
    assert ebsco_parser.linter.messages == messages


@pytest.mark.parametrize(
    "query_string, messages",
    [
        # 1. Invalid token sequence (FIELD followed directly by LOGIC_OPERATOR)
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
    ebsco_parser = EBSCOParser(query_string, "AB", mode=LinterMode.STRICT)
    try:
        ebsco_parser.parse()
    except Exception:
        pass
    assert ebsco_parser.linter.messages == messages


@pytest.mark.parametrize(
    "query_str, expected_translation",
    [
        (
            'TI example AND (AU "John Doe" OR AU "John Wayne")',
            'AND[example[ti], OR["John Doe"[au], "John Wayne"[au]]]',
        ),
        # Artificial parentheses
        # TODO : check NOT (should be unary!?)
        (
            'TI "Artificial Intelligence" AND AB Future NOT AB Past',
            'AND["Artificial Intelligence"[ti], NOT[Future[ab], Past[ab]]]'
            # 'TI "Artificial Intelligence" AND ( ( AB Future NOT AB Past ) ) ',
        ),
        # TODO : check NOT (should be unary!?)
        (
            'TI "Artificial Intelligence" NOT AB Future AND AB Past',
            'AND[NOT["Artificial Intelligence"[ti], Future[ab]], Past[ab]]'
            # '( TI "Artificial Intelligence" NOT AB Future ) AND AB Past ',
        ),
        (
            'TI "AI" OR AB Robots AND AB Ethics',
            'OR["AI"[ti], AND[Robots[ab], Ethics[ab]]]'
            # 'TI "AI" OR ( AB Robots AND AB Ethics ) ',
        ),
        (
            'TI "AI" AND AB Robots OR AB Ethics',
            'OR[AND["AI"[ti], Robots[ab]], Ethics[ab]]'
            # '( TI "AI" AND AB Robots ) OR AB Ethics ',
        ),
        # TODO : check NOT (should be unary!?)
        (
            'TI "AI" NOT AB Robots OR AB Ethics',
            'OR[NOT["AI"[ti], Robots[ab]], Ethics[ab]]'
            # '( TI "AI" NOT AB Robots ) OR AB Ethics ',
        ),
        # TODO : check NOT (should be unary!?)
        (
            'TI "AI" AND (AB Robots OR AB Ethics NOT AB Bias) OR SU "Technology"',
            'OR[AND["AI"[ti], OR[Robots[ab], NOT[Ethics[ab], Bias[ab]]]], "Technology"[st]]'
            # '( TI "AI" AND ( AB Robots OR ( AB Ethics NOT AB Bias ) ) ) OR SU "Technology" ',
        ),
        # TODO : check NOT (should be unary!?)
        (
            'TI "Robo*" OR AB Robots AND AB Ethics NOT AB Bias OR SU "Technology"',
            'OR["Robo*"[ti], AND[Robots[ab], NOT[Ethics[ab], Bias[ab]]], "Technology"[st]]'
            # 'TI "Robo*" OR ( AB Robots AND ( AB Ethics NOT AB Bias ) ) OR SU "Technology" ',
        ),
    ],
)
def test_parser(query_str: str, expected_translation: str) -> None:
    parser = EBSCOParser(
        query_str=query_str,
        search_field_general="",
        mode="",
    )
    query_tree = parser.parse()

    parser.print_tokens()

    assert expected_translation == query_tree.to_string(), print(query_tree.to_string())
