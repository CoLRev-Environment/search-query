#!/usr/bin/env python
"""Tests for search query translation"""
import json
from pathlib import Path

import pytest

from search_query.parser_base import QueryStringParser
from search_query.parser_xy import XYParser
from search_query.query import Query

# flake8: noqa: E501

# to run (from top-level dir): pytest tests/test_parser_xy.py


@pytest.mark.parametrize(
    "query_string, tokens",
    [
        (
            "AB=(Health)",
            [("AB=", (0, 3)), ("(", (3, 4)), ("Health", (4, 10)), (")", (10, 11))],
        ),
    ],
)
def test_tokenization_xy(query_string: str, tokens: tuple) -> None:
    xyparser = XYParser(query_string)
    xyparser.tokenize()
    assert xyparser.tokens == tokens, print_debug_tokens(xyparser, tokens, query_string)


def print_debug_tokens(
    xyparser: QueryStringParser, tokens: tuple, query_string
) -> None:
    print(query_string)
    print()
    print(xyparser.tokens)
    print(xyparser.get_token_types(xyparser.tokens, legend=True))
    print(tokens)


directory_path = Path("data/xy")
file_list = list(directory_path.glob("*.json"))


# Use the list of files with pytest.mark.parametrize
@pytest.mark.parametrize("file_path", file_list)
def test_xy_query_parser(file_path: str) -> None:
    """Test the translation of a search query to a xy query"""

    with open(file_path) as file:
        data = json.load(file)
        query_string = data["search_string"]
        expected = data["parsed"]["search"]

        parser = XYParser(query_string)
        query = parser.parse()
        query_str = query.to_string()
        assert query_str == expected, print_debug(  # type: ignore
            parser, query, query_string, query_str
        )


def print_debug(
    parser: QueryStringParser, query: Query, query_string: str, query_str: str
) -> None:
    print(query_string)
    print()
    print(parser.get_token_types(parser.tokens))
    print(query_str)
    print(query.to_string("structured"))


@pytest.mark.parametrize(
    "query_string, linter_messages",
    [
        (
            "AB-(Health)",
            [],
        ),
    ],
)
def test_linter_xy(query_string: str, linter_messages: tuple) -> None:
    xyparser = XYParser(query_string)
    try:
        xyparser.parse()
    except Exception:
        pass
    assert xyparser.linter_messages == linter_messages
