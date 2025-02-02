#!/usr/bin/env python
"""Tests for search query translation."""
from typing import List
from typing import Tuple

import pytest  # type: ignore

from search_query.parser_base import QueryStringParser
from search_query.parser_ebsco import EBSCOParser


# to run (from top-level dir): pytest test/test_parser_ebsco.py

# flake8: noqa: E501


@pytest.mark.parametrize(
    "query_string, expected_tokens",
    [
        (
            'TI "Artificial Intelligence" AND AB Future NOT AB Past',
            [
                ("TI", "FIELD", (0, 2)),
                ('"Artificial Intelligence"', "SEARCH_TERM", (3, 28)),
                ("AND", "LOGIC_OPERATOR", (29, 32)),
                ("AB", "FIELD", (33, 35)),
                ("Future", "SEARCH_TERM", (36, 42)),
                ("NOT", "LOGIC_OPERATOR", (43, 46)),
                ("AB", "FIELD", (47, 49)),
                ("Past", "SEARCH_TERM", (50, 54)),
            ],
        ),
        (
            "Artificial N2 Intelligence",
            [
                ("Artificial", "SEARCH_TERM", (0, 10)),
                ("N2", "PROXIMITY_OPERATOR", (11, 13)),
                ("Intelligence", "SEARCH_TERM", (14, 26)),
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


# directory_path = Path(
#     "/home/ubuntu1/Thesis/sorted-examples/search-query/data/ebscohost"
# )
# file_list = list(directory_path.glob("*.json"))


# # Use the list of files with pytest.mark.parametrize
# @pytest.mark.parametrize("file_path", file_list)
# def test_ebsco_query_parser(file_path: str) -> None:
#     """Test the translation of a search query to an EBSCO query."""

#     with open(file_path) as file:
#         data = json.load(file)
#         query_string = data.get("search_string")
#         expected = data["parsed"]["search"]

#         parser = EBSCOParser(query_string, "")
#         query = parser.parse()
#         query_str = query.to_string()

#         assert query_str == expected, print_debug(  # type: ignore
#             parser, query, query_string, query_str
#         )


# def print_debug(
#     parser: QueryStringParser, query: Query, query_string: str, query_str: str
# ) -> str:
#     """Debugging utility for query parsing mismatches."""
#     return (
#         f"Query String: {query_string}\n\n"
#         f"Tokens: {parser.get_token_types(parser.tokens)}\n\n"
#         f"Generated Query String: {query_str}\n\n"
#         f"Structured Query: {query.to_string()}"
#     )


@pytest.mark.parametrize(
    "query_string, linter_messages",
    [
        # 1️. Boolean operators should be capitalized
        (
            "Artificial intelligence and Future",
            [
                {
                    "level": "Warning",
                    "msg": "Operator 'and' automatically capitalized",
                    "pos": (24, 27),
                }
            ],
        ),
        # 2️. Unbalanced parentheses
        (
            "(Artificial Intelligence AND Future",
            [
                {
                    "level": "Fatal",
                    "msg": "Unbalanced parentheses: open = 1, close = 0",
                    "pos": "",
                }
            ],
        ),
        # 3. Unsupported search fields (e.g., `XY` is unsupported)
        (
            "XY Artificial Intelligence OR AB Future",
            [
                {
                    "level": "Error",
                    "msg": "search-field-unsupported: 'XY' automatically changed to Abstract AB.",
                    "pos": (0, 2),
                }
            ],
        ),
        # 4️. Invalid token sequence (Field followed directly by Logic Operator)
        (
            "TI AND Artificial Intelligence",
            [
                {
                    "level": "Error",
                    "msg": "Invalid token sequence: 'FIELD' followed by 'LOGIC_OPERATOR'",
                    "pos": (3, 6),
                }
            ],
        ),
        # 5️. Correct query (No linter messages expected)
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
