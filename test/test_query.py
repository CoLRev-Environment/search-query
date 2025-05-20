#!/usr/bin/env python
"""Tests for search query translation"""
import pytest

from search_query.query import SearchField
from search_query.query_and import AndQuery
from search_query.query_or import OrQuery


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
