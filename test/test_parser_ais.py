#!/usr/bin/env python
"""Tests for search query translation"""
import pytest

from search_query.parser import parse
from search_query.parser_ais import AISParser

# flake8: noqa: E501


@pytest.mark.parametrize(
    "query_string, tokens",
    [
        (
            "title:microsourcing OR abstract:microsourcing OR subject:microsourcing",
            [
                ("title:", (0, 6)),
                ("microsourcing", (6, 19)),
                ("OR", (20, 22)),
                ("abstract:", (23, 32)),
                ("microsourcing", (32, 45)),
                ("OR", (46, 48)),
                ("subject:", (49, 57)),
                ("microsourcing", (57, 70)),
            ],
        ),
    ],
)
def test_tokenization_ais(query_string: str, tokens: tuple) -> None:
    print(query_string)
    print()
    ais_parser = AISParser(query_string)
    ais_parser.tokenize()
    print(ais_parser.tokens)
    print(ais_parser.get_token_types(ais_parser.tokens, legend=True))
    print(tokens)
    assert ais_parser.tokens == tokens


@pytest.mark.parametrize(
    "source, query_string, expected",
    [
        (
            "custom",
            """title:microsourcing OR abstract:microsourcing OR subject:microsourcing""",
            """OR[microsourcing, microsourcing, microsourcing]""",
        ),
    ],
)
def test_wos_query_parser(source: str, query_string: str, expected: str) -> None:
    """Test the translation of a search query to an AIS query"""

    # STRATEGIE
    # - Web-of-science und pubmed
    # - list format: https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2024.00492

    print("--------------------")
    print(source)
    print()
    print(query_string)
    print()
    query = parse(query_string, query_type="ais_library")
    query_str = query.to_string()
    print(query_str)

    assert query_str == expected
