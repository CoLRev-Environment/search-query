#!/usr/bin/env python
"""Tests for search query translation"""
import pytest

from search_query.constants import Colors
from search_query.constants import Fields
from search_query.query import Query
from search_query.query import SearchField
from search_query.query_and import AndQuery
from search_query.query_near import NEARQuery
from search_query.query_not import NotQuery
from search_query.query_or import OrQuery
from search_query.query_range import RangeQuery
from search_query.utils import format_query_string_positions

# pylint: disable=line-too-long
# flake8: noqa: E501


def test_invalid_tree_structure(query_setup: dict) -> None:
    with pytest.raises(ValueError):
        AndQuery(
            ["invalid", query_setup["query_complete"], query_setup["query_ai"]],
            search_field=SearchField(Fields.TITLE),
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
        search_field=SearchField(Fields.ABSTRACT),
    )
    ai = OrQuery(
        ["AI", "Artificial Intelligence"],
        search_field=SearchField(Fields.TITLE),
    )

    root_query = AndQuery([ethics, ai], search_field=SearchField(Fields.TITLE))

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
    expected = """OR [title][
|---"health care" [title]
|---medicine [title]
| ]"""
    assert actual == expected


def test_near_query() -> None:
    n_query = NEARQuery("NEAR", distance=12, children=[], search_field=Fields.TITLE)

    assert n_query.to_generic_string() == "NEAR/12[title]"
    assert n_query.to_structured_string() == "NEAR/12 [title]"

    with pytest.raises(ValueError):
        n_query = NEARQuery("NEAR", children=[], search_field=Fields.TITLE)

    or_query = OrQuery(
        ["health", "medicine"],
        search_field=Fields.TITLE,
    )
    with pytest.raises(ValueError):
        or_query.distance = 12


def test_format_query_string_positions_merges_overlaps() -> None:
    query_str = "cancer AND treatment OR prevention"
    positions = [(0, 6), (5, 14)]  # 'cancer' and overlapping 'AND treat'

    expected = "\x1b[93mcancer AND tre\x1b[0matment OR prevention"

    result = format_query_string_positions(query_str, positions, color=Colors.ORANGE)
    assert result.startswith(expected)


def test_search_field() -> None:
    """Test search field."""

    ethics = OrQuery(
        ["ethics", "morality"],
        search_field=Fields.ABSTRACT,
    )
    assert ethics.search_field.value == Fields.ABSTRACT  # type: ignore


def test_platform_setter() -> None:
    """Test platform setter."""

    ethics = OrQuery(
        ["ethics", "morality"],
        search_field=Fields.ABSTRACT,
    )
    assert ethics.platform == "generic"
    with pytest.raises(ValueError):
        ethics.platform = "invalid_platform"

    with pytest.raises(ValueError):
        ethics.platform = "pubmeds"


def test_value_setter() -> None:
    """Test value setter."""

    ethics = Query(
        value="OR",
        operator=True,
        children=["ethics", "morality"],
        search_field=Fields.ABSTRACT,  # type: ignore
    )
    assert ethics.value == "OR"

    with pytest.raises(TypeError):
        ethics.value = {"key": "value"}  # type: ignore

    with pytest.raises(ValueError):
        ethics.value = "non_operators"

    with pytest.raises(TypeError):
        ethics.operator = "non_operators"  # type: ignore

    ethics.value = "NEAR"


def test_children_setter() -> None:
    """Test children setter."""
    # Test for OrQuery ---------------------------------------------
    or_query = OrQuery(
        ["ethics", "morality"],
        search_field="abstract",
    )
    assert or_query.children[0].value == "ethics"
    assert or_query.children[1].value == "morality"

    with pytest.raises(TypeError):
        or_query.children = "not_a_list"  # type: ignore

    with pytest.raises(TypeError):
        or_query.children = ["valid", 123]  # type: ignore

    with pytest.raises(ValueError):
        or_query.children = ["new_child"]  # type: ignore

    or_query.children = ["new_child", "another_child", "third_child"]  # type: ignore

    # Test for AndQuery ---------------------------------------------
    and_query = AndQuery(
        ["ethics", "morality"],
        search_field="abstract",
    )
    assert and_query.children[0].value == "ethics"
    assert and_query.children[1].value == "morality"

    with pytest.raises(TypeError):
        and_query.children = "not_a_list"  # type: ignore

    with pytest.raises(TypeError):
        and_query.children = ["valid", 123]  # type: ignore

    with pytest.raises(ValueError):
        and_query.children = ["new_child"]  # type: ignore

    and_query.children = ["new_child", "another_child", "third_child"]  # type: ignore

    # Test for NotQuery ---------------------------------------------
    not_query = NotQuery(
        ["ethics"],
        search_field="abstract",
    )
    assert not_query.children[0].value == "ethics"

    with pytest.raises(TypeError):
        not_query.children = "not_a_list"  # type: ignore

    with pytest.raises(TypeError):
        not_query.children = ["valid", 123]  # type: ignore

    with pytest.raises(ValueError):
        not_query.children = ["new_child", "another_child", "third_child"]  # type: ignore

    with pytest.raises(ValueError):
        not_query.children = ["new_child"]  # type: ignore

    # Test for NEARQuery ---------------------------------------------
    near_query = NEARQuery(
        "NEAR",
        distance=5,
        children=["ethics", "morality"],
        search_field="abstract",
    )
    assert near_query.children[0].value == "ethics"
    assert near_query.children[1].value == "morality"

    with pytest.raises(TypeError):
        near_query.children = "not_a_list"  # type: ignore

    with pytest.raises(TypeError):
        near_query.children = ["valid", 123]  # type: ignore

    with pytest.raises(ValueError):
        near_query.children = ["new_child"]  # type: ignore

    with pytest.raises(ValueError):
        near_query.children = ["new_child", "another_child", "third_child"]  # type: ignore

    # Test for RangeQuery ---------------------------------------------
    range_query = RangeQuery(
        children=["2010", "2020"],
        search_field="year-publication",
    )
    assert range_query.children[0].value == "2010"
    assert range_query.children[1].value == "2020"

    with pytest.raises(TypeError):
        range_query.children = "not_a_list"  # type: ignore

    with pytest.raises(TypeError):
        range_query.children = ["valid", 123]  # type: ignore

    with pytest.raises(ValueError):
        range_query.children = ["new_child"]  # type: ignore

    with pytest.raises(ValueError):
        range_query.children = ["new_child", "another_child", "third_child"]  # type: ignore
