#!/usr/bin/env python
"""Tests for search query translation."""
import json
from pathlib import Path
from typing import List
from typing import Tuple

import pytest

from search_query.constants import LinterMode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.linter_ebsco import EBSCOQueryStringLinter
from search_query.parser import parse
from search_query.parser_base import QueryStringParser
from search_query.parser_ebsco import EBSCOParser
from search_query.query import Query

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
def test_tokenization_ebsco(
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


@pytest.mark.parametrize(
    "query_string, updated_string",
    [
        (
            'TI "Artificial Intelligence" AND AB Future NOT AB Past',
            'TI "Artificial Intelligence" AND ( ( AB Future NOT AB Past ) ) ',
        ),
        (
            'TI "Artificial Intelligence" NOT AB Future AND AB Past',
            '( TI "Artificial Intelligence" NOT AB Future ) AND AB Past ',
        ),
        (
            'TI "AI" OR AB Robots AND AB Ethics',
            'TI "AI" OR ( AB Robots AND AB Ethics ) ',
        ),
        (
            'TI "AI" AND AB Robots OR AB Ethics',
            '( TI "AI" AND AB Robots ) OR AB Ethics ',
        ),
        (
            'TI "AI" NOT AB Robots OR AB Ethics',
            '( TI "AI" NOT AB Robots ) OR AB Ethics ',
        ),
        (
            'TI "AI" AND (AB Robots OR AB Ethics NOT AB Bias) OR SU "Technology"',
            '( TI "AI" AND ( AB Robots OR ( AB Ethics NOT AB Bias ) ) ) OR SU "Technology" ',
        ),
        (
            'TI "Robo*" OR AB Robots AND AB Ethics NOT AB Bias OR SU "Technology"',
            'TI "Robo*" OR ( AB Robots AND ( AB Ethics NOT AB Bias ) ) OR SU "Technology" ',
        ),
    ],
)
def test_add_artificial_parentheses_for_operator_precedence(
    query_string: str, updated_string: List[Tuple[str, str, Tuple[int, int]]]
) -> None:
    """Test EBSCO parser tokenization."""
    ebsco_parser = EBSCOParser(query_string, "")
    ebsco_parser.tokenize()

    linter = EBSCOQueryStringLinter(ebsco_parser)
    linter.validate_tokens()
    actual_tokens = ebsco_parser.tokens
    actual_string = "".join([f"{token.value} " for token in actual_tokens])

    # Assert equality with error message on failure
    print("actual string: " + actual_string)
    assert actual_string == updated_string, print_debug_tokens(
        ebsco_parser, updated_string, query_string
    )


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


directory_path = Path(
    "/home/ubuntu1/Thesis/example/searchRxiv_scraper/search-query/data/ebscohost"
)
file_list = list(directory_path.glob("*.json"))


# Use the list of files with pytest.mark.parametrize
@pytest.mark.parametrize("file_path", file_list)
def test_ebsco_query_parser(file_path: str) -> None:
    """Test the translation of a search query to an EBSCO query."""

    with open(file_path) as file:
        data = json.load(file)
        query_string = data["search_string"]
        expected = data["parsed"]["search"]

        query = parse(query_string, search_field_general="", syntax="ebscohost")
        query_str = query.to_string("pre_notation")

        assert query_str == expected, print_debug(  # type: ignore
            query, query_string, query_str
        )


def print_debug(query: Query, query_string: str, query_str: str) -> None:
    """Debugging utility for query parsing mismatches."""
    print(query_string)
    print()
    print(query_str)
    print(query.to_string("structured"))


@pytest.mark.parametrize(
    "query_string, linter_messages",
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
                    "details": "",
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
    ],
)
def test_linter_ebsco(query_string: str, linter_messages: list) -> None:
    ebsco_parser = EBSCOParser(query_string, "")
    try:
        ebsco_parser.parse()
    except Exception:
        pass
    assert ebsco_parser.linter_messages == linter_messages


@pytest.mark.parametrize(
    "query_string, linter_messages",
    [
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
def test_linter_ebsco_non_strict(query_string: str, linter_messages: list) -> None:
    ebsco_parser = EBSCOParser(query_string, "", mode=LinterMode.NONSTRICT)
    ebsco_parser.parse()
    assert ebsco_parser.linter_messages == linter_messages


@pytest.mark.parametrize(
    "query_string, linter_messages",
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
def test_linter_ebsco_general_search_field(
    query_string: str, linter_messages: list
) -> None:
    ebsco_parser = EBSCOParser(query_string, "AB", mode=LinterMode.STRICT)
    try:
        ebsco_parser.parse()
    except Exception:
        pass
    assert ebsco_parser.linter_messages == linter_messages


def test_query_parsing_1() -> None:
    parser = EBSCOParser(
        query_str="TI example AND (AU John Doe OR AU John Wayne)",
        search_field_general="",
        mode="",
    )
    query = parser.parse()
    assert query.value == "AND"
    assert query.operator
    assert len(query.children) == 2
    assert query.children[0].value == "example"
    assert not query.children[0].operator
    assert query.children[1].value == "OR"

    assert query.children[1].children[1].value == "John Wayne"
    assert query.children[1].children[1].search_field
    assert query.children[1].children[1].search_field.value == "au"
