#!/usr/bin/env python
"""Tests for search query translation"""
import copy

import pytest

from search_query.constants import Fields
from search_query.query import SearchField
from search_query.query import Term
from search_query.query_and import AndQuery
from search_query.query_not import NotQuery
from search_query.query_or import OrQuery

# pylint: disable=line-too-long
# flake8: noqa: E501


@pytest.fixture
def query_setup() -> dict:
    test_node = Term(
        "testvalue", position=(1, 10), search_field=SearchField(Fields.TITLE)
    )
    query_robot = NotQuery(["robot*"], search_field=SearchField(Fields.TITLE))
    query_ai = OrQuery(
        ['"AI"', '"Artificial Intelligence"', '"Machine Learning"', query_robot],
        search_field=SearchField(Fields.TITLE),
    )
    query_health = OrQuery(
        ['"health care"', "medicine"],
        search_field=SearchField(Fields.TITLE),
    )
    query_ethics = OrQuery(
        ["ethic*", "moral*"],
        search_field=SearchField(Fields.ABSTRACT),
    )
    query_complete = AndQuery(
        [query_ai, query_health, query_ethics],
        search_field=SearchField(Fields.TITLE),
    )
    query_complete.origin_platform = "generic"
    query_health.origin_platform = "generic"
    query_ai.origin_platform = "generic"
    query_robot.origin_platform = "generic"
    query_ethics.origin_platform = "generic"

    return copy.deepcopy(
        {
            "test_node": test_node,
            "query_robot": query_robot,
            "query_ai": query_ai,
            "query_health": query_health,
            "query_ethics": query_ethics,
            "query_complete": query_complete,
        }
    )


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
    assert query_health.to_string(platform="wos") == 'TI=("health care" OR medicine)'


def test_translation_wos_complete(query_setup: dict) -> None:
    query_complete = query_setup["query_complete"]
    expected = '(TI=("AI" OR "Artificial Intelligence" OR "Machine Learning" NOT robot*) AND TI=("health care" OR medicine) AND AB=(ethic* OR moral*))'
    assert query_complete.to_string(platform="wos") == expected


def test_translation_pubmed_part(query_setup: dict) -> None:
    query_health = query_setup["query_health"]
    expected = '("health care"[ti] OR medicine[ti])'
    assert query_health.to_string(platform="pubmed") == expected


def test_translation_pubmed_complete(query_setup: dict) -> None:
    query_complete = query_setup["query_complete"]
    expected = '(("AI"[ti] OR "Artificial Intelligence"[ti] OR "Machine Learning"[ti] NOT robot*[ti]) AND ("health care"[ti] OR medicine[ti]) AND (ethic*[tiab] OR moral*[tiab]))'
    assert query_complete.to_string(platform="pubmed") == expected


def test_invalid_tree_structure(query_setup: dict) -> None:
    with pytest.raises(ValueError):
        AndQuery(
            ["invalid", query_setup["query_complete"], query_setup["query_ai"]],
            search_field=SearchField("Author Keywords"),
        )


def test_selects(query_setup: dict) -> None:
    query_ai = query_setup["query_ai"]
    query_health = query_setup["query_health"]
    query_complete = query_setup["query_complete"]

    record_1 = {
        "title": "Artificial Intelligence in Health Care",
        "abstract": "This study explores the role of AI and machine learning in improving health outcomes.",
    }

    record_2 = {
        "title": "Moral Implications of Artificial Intelligence",
        "abstract": "Examines ethical concerns in AI development.",
    }

    record_3 = {
        "title": "Unrelated Title",
        "abstract": "This abstract is about something else entirely.",
    }

    record_4 = {
        "title": "Title with AI and medicine",
        "abstract": "abstract containing ethics.",
    }

    assert query_ai.selects(record_dict=record_1)
    assert not query_health.selects(record_dict=record_2)
    assert not query_health.selects(record_dict=record_3)
    assert query_complete.selects(record_dict=record_4)
    assert not query_complete.selects(record_dict=record_3)
