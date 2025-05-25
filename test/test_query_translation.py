#!/usr/bin/env python
"""Tests for search query translation"""
import pytest

import search_query.parser
from search_query.constants import PLATFORM
from search_query.pubmed.translator import PubmedTranslator
from search_query.query import Query
from search_query.query import SearchField

# pylint: disable=line-too-long
# flake8: noqa: E501


def test_to_generic_string(query_setup: dict) -> None:
    assert query_setup["test_node"].to_generic_string() == "testvalue[ti]"


def test_append_children(query_setup: dict) -> None:
    health_query = query_setup["query_health"]

    assert health_query.children[0].to_generic_string() == '"health care"[ti]'
    assert health_query.children[1].to_generic_string() == "medicine[ti]"


def test_or_query(query_setup: dict) -> None:
    query_ai = query_setup["query_ai"]
    assert (
        query_ai.to_generic_string()
        == 'OR[ti]["AI"[ti], "Artificial Intelligence"[ti], "Machine Learning"[ti], NOT[ti][robot*[ti]]]'
    )


def test_and_query(query_setup: dict) -> None:
    query_complete = query_setup["query_complete"]
    assert (
        query_complete.to_generic_string()
        == 'AND[ti][OR[ti]["AI"[ti], "Artificial Intelligence"[ti], "Machine Learning"[ti], NOT[ti][robot*[ti]]], OR[ti]["health care"[ti], medicine[ti]], OR[ab][ethic*[ab], moral*[ab]]]'
    )


def test_not_query(query_setup: dict) -> None:
    query_robot = query_setup["query_robot"]
    assert query_robot.to_generic_string() == "NOT[ti][robot*[ti]]"


def test_nested_queries(query_setup: dict) -> None:
    query_complete = query_setup["query_complete"]
    assert query_complete.children == [
        query_setup["query_ai"],
        query_setup["query_health"],
        query_setup["query_ethics"],
    ]


def test_no_translation(query_setup: dict) -> None:
    query_health = query_setup["query_health"]
    query_health.translate(PLATFORM.GENERIC.value)


def test_translation_wos_part(query_setup: dict) -> None:
    query_health = query_setup["query_health"]
    translated_query = query_health.translate(PLATFORM.WOS.value)
    assert translated_query.to_string() == 'TI=("health care" OR medicine)'


def test_translation_wos_complete(query_setup: dict) -> None:
    query_complete = query_setup["query_complete"]
    expected = '(TI=("AI" OR "Artificial Intelligence" OR "Machine Learning" NOT robot*) AND TI=("health care" OR medicine) AND AB=(ethic* OR moral*))'
    translated_query = query_complete.translate(PLATFORM.WOS.value)
    assert translated_query.to_string() == expected


def test_translation_pubmed_part(query_setup: dict) -> None:
    query_health = query_setup["query_health"]
    expected = '("health care"[ti] OR medicine[ti])'
    translated_query = query_health.translate(PLATFORM.PUBMED.value)
    assert translated_query.to_string() == expected


def test_translation_pubmed_complete(query_setup: dict) -> None:
    query_complete = query_setup["query_complete"]
    expected = '(("AI"[ti] OR "Artificial Intelligence"[ti] OR "Machine Learning"[ti] NOT robot*[ti]) AND ("health care"[ti] OR medicine[ti]) AND (ethic*[tiab] OR moral*[tiab]))'
    translated_query = query_complete.translate(PLATFORM.PUBMED.value)
    assert translated_query.to_string() == expected


def test_translation_wos_ebsco() -> None:
    query_str = "TS=(quantum AND dot AND spin)"
    print(query_str)
    query = search_query.parser.parse(
        query_str,
        platform=PLATFORM.WOS.value,
    )
    translated_query = query.translate(PLATFORM.EBSCO.value)
    converted_query = translated_query.to_string()
    print(translated_query.to_structured_string())
    expected = "((AB quantum OR KW quantum OR TI quantum) AND (AB dot OR KW dot OR TI dot) AND (AB spin OR KW spin OR TI spin))"

    assert converted_query == expected

    query_str = "TI=(quantum AND dot AND spin)"
    print(query_str)
    query = search_query.parser.parse(
        query_str,
        platform=PLATFORM.WOS.value,
    )
    translated_query = query.translate(PLATFORM.EBSCO.value)
    converted_query = translated_query.to_string()
    expected = "TI (quantum AND dot AND spin)"

    assert converted_query == expected


def test_translation_ebsco_wos() -> None:
    query_str = "TI (quantum AND dot AND spin)"
    print(query_str)
    query = search_query.parser.parse(
        query_str,
        platform=PLATFORM.EBSCO.value,
    )
    translated_query = query.translate(PLATFORM.WOS.value)
    converted_query = translated_query.to_string()
    expected = "TI=(quantum AND dot AND spin)"

    assert converted_query == expected


@pytest.mark.parametrize(
    "query, expected_flattened",
    [
        (
            # Nested OR structure
            Query(
                value="OR",
                operator=True,
                search_field=None,
                children=[
                    Query(
                        value="eHealth", operator=False, search_field=SearchField("ti")
                    ),
                    Query(
                        value="OR",
                        operator=True,
                        children=[
                            Query(
                                value="mHealth",
                                operator=False,
                                search_field=SearchField("ti"),
                            ),
                            Query(
                                value="telemedicine",
                                operator=False,
                                search_field=SearchField("ti"),
                            ),
                        ],
                    ),
                ],
            ),
            "OR[eHealth[ti], mHealth[ti], telemedicine[ti]]",
        ),
        (
            # Nested AND structure
            Query(
                value="AND",
                operator=True,
                children=[
                    Query(
                        value="cancer", operator=False, search_field=SearchField("ti")
                    ),
                    Query(
                        value="AND",
                        operator=True,
                        children=[
                            Query(
                                value="therapy",
                                operator=False,
                                search_field=SearchField("ti"),
                            ),
                            Query(
                                value="survivorship",
                                operator=False,
                                search_field=SearchField("ti"),
                            ),
                        ],
                    ),
                ],
            ),
            "AND[cancer[ti], therapy[ti], survivorship[ti]]",
        ),
    ],
)
def test_flatten_nested_operators(query: Query, expected_flattened: str) -> None:
    PubmedTranslator.flatten_nested_operators(query)
    assert query.to_generic_string() == expected_flattened


def test_translation_pubmed_to_generic() -> None:
    query_str = "quantum[ti] AND dot[ti] AND spin[ti]"
    print(query_str)
    query = search_query.parser.parse(
        query_str,
        platform=PLATFORM.PUBMED.value,
    )
    translated_query = query.translate(PLATFORM.GENERIC.value)
    converted_query = translated_query.to_generic_string()
    expected = "AND[quantum[ti], dot[ti], spin[ti]]"

    assert converted_query == expected
