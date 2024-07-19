#!/usr/bin/env python
"""Tests for search query translation"""
import pytest

from search_query.parser_base import QueryStringParser
from search_query.parser_ebsco import EBSCOListParser
from search_query.parser_ebsco import EBSCOParser
from search_query.query import Query

# flake8: noqa: E501


@pytest.mark.parametrize(
    "query_string, expected",
    [
        (
            """TI (anesthesia OR anaesthesia OR analgesia OR narcosis)""",
            """OR[anesthesia[TI], anaesthesia[TI], analgesia[TI], narcosis[TI]]""",
        )
    ],
)
def test_ebsco_query_parser(query_string: str, expected: str) -> None:
    """Test the translation of a search query to a Pubmed query"""

    parser = EBSCOParser(query_string)
    query = parser.parse()
    query_str = query.to_string()

    assert query_str == expected, print_debug(  # type: ignore
        parser, query, query_string, query_str
    )


@pytest.mark.parametrize(
    "source, query_string, expected",
    [
        (
            # Note: the search was adapted and does not correspond to the one reported at the source (searchRxiv)
            "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2023.00155",
            """1.	Clinical competence
2.	Professional practice
3.	Cultural competence
4.	Accreditation
5.	Interprofessional relations
6.	Professional education
7.	Professional licenses
8.	Standards
9.	(S1 OR S2 OR S3)
10.	(S4 OR S5 OR S6 OR S7 OR S8)
11.	(S9 AND S10)""",
            """AND[OR[Clinical competence[EBSCO_UNQUALIFIED], Professional practice[EBSCO_UNQUALIFIED], Cultural competence[EBSCO_UNQUALIFIED]], OR[Accreditation[EBSCO_UNQUALIFIED], Interprofessional relations[EBSCO_UNQUALIFIED], Professional education[EBSCO_UNQUALIFIED], Professional licenses[EBSCO_UNQUALIFIED], Standards[EBSCO_UNQUALIFIED]]]""",
        )
    ],
)
def test_ebsco_list_query_parser(source: str, query_string: str, expected: str) -> None:
    """Test the translation of a search query to a EBSCO query"""

    parser = EBSCOListParser(query_string)
    query = parser.parse()
    query_str = query.to_string()

    assert query_str == expected, print_debug_list(  # type: ignore
        parser, query, query_string, query_str
    )


def print_debug(
    parser: QueryStringParser, query: Query, query_string: str, query_str: str
) -> None:
    print(query_string)
    print()
    print(parser.tokens)
    print(parser.get_token_types(parser.tokens))
    print(query_str)
    print(query.to_string("structured"))


def print_debug_list(
    parser: EBSCOListParser, query: Query, query_string: str, query_str: str
) -> None:
    print(query_string)
    print()
    # parser.parse_list()
    print()
    # print(parser.get_token_types(parser.tokens))
    print(query_str)
    print(query.to_string("structured"))
