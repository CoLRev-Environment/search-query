#!/usr/bin/env python
"""Tests for search query translation"""
import copy

import pytest

from search_query.constants import Fields
from search_query.query import SearchField
from search_query.query_and import AndQuery
from search_query.query_not import NotQuery
from search_query.query_or import OrQuery
from search_query.query_term import Term

# pylint: disable=line-too-long
# flake8: noqa: E501


@pytest.fixture
def query_setup() -> dict:
    test_node = Term("testvalue", position=(1, 10), field=SearchField(Fields.TITLE))
    query_robot = NotQuery(
        ['"Machine Learning"', "robot*"], field=SearchField(Fields.TITLE)
    )
    query_ai = OrQuery(
        ['"AI"', '"Artificial Intelligence"'],
        field=SearchField(Fields.TITLE),
    )
    query_health = OrQuery(
        ['"health care"', "medicine"],
        field=SearchField(Fields.TITLE),
    )
    query_ethics = OrQuery(
        ["ethic*", "moral*"],
        field=SearchField(Fields.ABSTRACT),
    )
    query_complete = AndQuery(
        [query_ai, query_health, query_ethics],
        field=SearchField(Fields.TITLE),
    )
    query_complete.platform = "generic"
    query_health.platform = "generic"
    query_ai.platform = "generic"
    query_robot.platform = "generic"
    query_ethics.platform = "generic"

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
