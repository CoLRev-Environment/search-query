#!/usr/bin/env python
"""Tests for search query translation"""
import pytest

from search_query.constants import Colors
from search_query.query import SearchField
from search_query.query_and import AndQuery
from search_query.query_near import NEARQuery
from search_query.query_or import OrQuery
from search_query.utils import format_query_string_positions


# pylint: disable=line-too-long
# flake8: noqa: E501


def test_invalid_tree_structure(query_setup: dict) -> None:
    with pytest.raises(ValueError):
        AndQuery(
            ["invalid", query_setup["query_complete"], query_setup["query_ai"]],
            search_field=SearchField("ti"),
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

    with pytest.raises(ValueError):
        query_complete.children[0].children[0].search_field.value = "au"
        print(query_complete.to_structured_string())
        query_complete.selects(record_dict=record_1)


def test_parent_and_root() -> None:
    """Test parent and root."""

    # Build a nested query structure
    ethics = OrQuery(
        ["ethics", "morality"],
        search_field=SearchField("ab"),
    )
    ai = OrQuery(
        ["AI", "Artificial Intelligence"],
        search_field=SearchField("ti"),
    )

    root_query = AndQuery([ethics, ai], search_field=SearchField("ti"))

    # Check that each subquery has root_query as its root
    assert ethics.get_parent() is root_query
    assert ai.get_parent() is root_query
    for child in ethics.children:
        assert child.get_parent() is ethics
    for child in ai.children:
        assert child.get_parent() is ai

    # And the root references itself
    assert root_query.get_parent() is None
    assert ethics.get_root() is root_query
    assert ai.get_root() is root_query
    assert ethics.get_root() is root_query
    assert ai.children[0].get_root() is root_query


def test_to_structured_string(query_setup: dict) -> None:
    health_query = query_setup["query_health"]
    actual = health_query.to_structured_string()
    expected = """OR [ti][
|---"health care" [ti]
|---medicine [ti]
| ]"""
    assert actual == expected


def test_near_query() -> None:
    n_query = NEARQuery("NEAR", distance=12, children=[], search_field="ti")

    assert n_query.to_generic_string() == "NEAR[ti](12)"
    assert n_query.to_structured_string() == "NEAR/12 [ti]"


def test_format_query_string_positions_merges_overlaps() -> None:
    query_str = "cancer AND treatment OR prevention"
    positions = [(0, 6), (5, 14)]  # 'cancer' and overlapping 'AND treat'

    expected = "\x1b[93mcancer AND tre\x1b[0matment OR prevention"

    result = format_query_string_positions(query_str, positions, color=Colors.ORANGE)
    assert result.startswith(expected)
