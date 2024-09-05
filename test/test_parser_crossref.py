#!/usr/bin/env python
"""Tests for search query translation"""
import json
from pathlib import Path

import pytest

from search_query.parser import CrossrefParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query

# flake8: noqa: E501


@pytest.mark.parametrize(
    "query_string, tokens",
    [
        (
            "https://api.crossref.org/works?query=renear+ontologies",
            [
                ("works?", (0, 6)),
                ("query", (6, 11)),
                ("=", (11, 12)),
                ("renear+ontologies", (12, 29)),
            ],
        ),
        (
            "https://api.crossref.org/works?query.title=room+at+the+bottom&query.author=richard+feynman",
            [
                ("works?", (0, 6)),
                ("query.title", (6, 17)),
                ("=", (17, 18)),
                ("room+at+the+bottom", (18, 36)),
                ("query.author", (37, 49)),
                ("=", (49, 50)),
                ("richard+feynman", (50, 65)),
            ],
        ),
        (
            "https://api.crossref.org/works?query=josiah+carberry&sort=published&order=asc",
            [
                ("works?", (0, 6)),
                ("query", (6, 11)),
                ("=", (11, 12)),
                ("josiah+carberry", (12, 27)),
                ("sort", (28, 32)),
                ("=", (32, 33)),
                ("published", (33, 42)),
                ("order", (43, 48)),
                ("=", (48, 49)),
                ("asc", (49, 52)),
            ],
        ),
    ],
)
def test_tokenization_wos(query_string: str, tokens: tuple) -> None:
    print(query_string)
    print()
    wos_parser = CrossrefParser(query_string)
    wos_parser.tokenize()
    print(wos_parser.tokens)
    print(wos_parser.get_token_types(wos_parser.tokens, legend=True))
    print(tokens)
    assert wos_parser.tokens == tokens


directory_path = Path("data/crossref")
file_list = list(directory_path.glob("*.json"))


# Use the list of files with pytest.mark.parametrize
@pytest.mark.parametrize("file_path", file_list)
def test_wos_query_parser(file_path: str) -> None:
    """Test the translation of a search query to a Crossref query"""

    with open(file_path) as file:
        data = json.load(file)
        # TODO : use SearchHistoryFile to validate
        query_string = data["search_string"]
        expected = data["parsed"]["search"]

        parser = CrossrefParser(query_string)
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
