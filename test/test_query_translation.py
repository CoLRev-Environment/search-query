#!/usr/bin/env python
"""Tests for search query translation"""


import search_query.parser

# pylint: disable=line-too-long
# flake8: noqa: E501


def test_print_node(query_setup: dict) -> None:
    assert (
        query_setup["test_node"].print_node()
        == "value: testvalue operator: False search field: ti"
    )


def test_append_children(query_setup: dict) -> None:
    health_query = query_setup["query_health"]
    expected_values = ['"health care"', "medicine"]

    for child, expected in zip(health_query.children, expected_values):
        assert child.print_node().startswith(f"value: {expected}")


def test_or_query(query_setup: dict) -> None:
    query_ai = query_setup["query_ai"]
    assert query_ai.print_node().startswith("value: OR")


def test_and_query(query_setup: dict) -> None:
    query_complete = query_setup["query_complete"]
    assert query_complete.print_node().startswith("value: AND")


def test_not_query(query_setup: dict) -> None:
    query_robot = query_setup["query_robot"]
    assert query_robot.print_node().startswith("value: NOT")


def test_nested_queries(query_setup: dict) -> None:
    query_complete = query_setup["query_complete"]
    assert query_complete.children == [
        query_setup["query_ai"],
        query_setup["query_health"],
        query_setup["query_ethics"],
    ]


def test_translation_wos_part(query_setup: dict) -> None:
    query_health = query_setup["query_health"]
    translated_query = query_health.translate("wos")
    assert translated_query.to_string() == 'TI=("health care" OR medicine)'


def test_translation_wos_complete(query_setup: dict) -> None:
    query_complete = query_setup["query_complete"]
    expected = '(TI=("AI" OR "Artificial Intelligence" OR "Machine Learning" NOT robot*) AND TI=("health care" OR medicine) AND AB=(ethic* OR moral*))'
    translated_query = query_complete.translate("wos")
    assert translated_query.to_string() == expected


def test_translation_pubmed_part(query_setup: dict) -> None:
    query_health = query_setup["query_health"]
    expected = '("health care"[ti] OR medicine[ti])'
    translated_query = query_health.translate("pubmed")
    assert translated_query.to_string() == expected


def test_translation_pubmed_complete(query_setup: dict) -> None:
    query_complete = query_setup["query_complete"]
    expected = '(("AI"[ti] OR "Artificial Intelligence"[ti] OR "Machine Learning"[ti] NOT robot*[ti]) AND ("health care"[ti] OR medicine[ti]) AND (ethic*[tiab] OR moral*[tiab]))'
    translated_query = query_complete.translate("pubmed")
    assert translated_query.to_string() == expected


def test_translation_wos_ebsco() -> None:
    query_str = "TS=(quantum AND dot AND spin)"
    print(query_str)
    query = search_query.parser.parse(
        query_str,
        platform="wos",
    )
    translated_query = query.translate("ebscohost")
    converted_query = translated_query.to_string()
    expected = "TP (quantum AND dot AND spin)"

    assert converted_query == expected
