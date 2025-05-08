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
