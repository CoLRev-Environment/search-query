#!/usr/bin/env python
"""Tests for search query translation"""
import pytest

from search_query.query import SearchField
from search_query.query_and import AndQuery

# pylint: disable=line-too-long
# flake8: noqa: E501


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
