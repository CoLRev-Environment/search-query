"""Tests for the AIS eLibrary parser."""
from __future__ import annotations

import pytest

from search_query.constants import Fields
from search_query.constants import Operators
from search_query.constants import PLATFORM
from search_query.exception import QuerySyntaxError
from search_query.parser import parse
from search_query.query_near import NEARQuery


@pytest.mark.parametrize(
    ("field_name", "generic_field"),
    [
        ("title", Fields.TITLE),
        ("abstract", Fields.ABSTRACT),
        ("subject", Fields.TOPIC),
        ("author", Fields.AUTHOR),
        ("institution", Fields.AFFILIATION),
        ("document_type", Fields.PUBLICATION_TYPE),
        ("publication_title", Fields.PUBLICATION_NAME),
        ("configured_field_t_issn", Fields.ISSN),
    ],
)
def test_ais_field_mappings(field_name: str, generic_field: str) -> None:
    query = parse(f"{field_name}:microsourcing", platform=PLATFORM.AISEL.value)

    assert query.platform == PLATFORM.AISEL.value
    assert query.is_term()
    assert query.field is not None
    assert query.field.value == generic_field


def test_ais_boolean_precedence_and_field_scope() -> None:
    query = parse(
        "title:microsourcing OR abstract:service AND subject:technology",
        platform=PLATFORM.AISEL.value,
    )

    assert query.operator
    assert query.value == Operators.OR
    assert len(query.children) == 2
    assert query.children[0].field is not None
    assert query.children[0].field.value == Fields.TITLE

    conjunction = query.children[1]
    assert conjunction.value == Operators.AND
    assert [child.field.value for child in conjunction.children if child.field] == [
        Fields.ABSTRACT,
        Fields.TOPIC,
    ]


def test_ais_near_operator_and_unary_not() -> None:
    near_query = parse(
        "title:open innovation NEAR/3 title:business model",
        platform=PLATFORM.AISEL.value,
    )
    assert isinstance(near_query, NEARQuery)
    assert near_query.value == Operators.NEAR
    assert near_query.distance == 3
    assert [child.field.value for child in near_query.children if child.field] == [
        Fields.TITLE,
        Fields.TITLE,
    ]

    not_query = parse(
        "title:innovation AND NOT abstract:obsolete",
        platform=PLATFORM.AISEL.value,
    )
    assert not_query.value == Operators.AND
    assert not_query.children[1].value == Operators.NOT
    assert not_query.children[1].children[0].field is not None
    assert not_query.children[1].children[0].field.value == Fields.ABSTRACT


@pytest.mark.parametrize(
    "query_string",
    [
        "unknown:term",
        "title:",
        "term AND AND other",
        "(title:term",
        "term NEAR/nope other",
        ")",
    ],
)
def test_ais_invalid_query_syntax_is_reported(query_string: str) -> None:
    with pytest.raises(QuerySyntaxError):
        parse(query_string, platform=PLATFORM.AISEL.value)


def test_ais_list_queries_are_rejected_explicitly() -> None:
    with pytest.raises(ValueError, match="does not support numbered list queries"):
        parse("1. title:term", platform=PLATFORM.AISEL.value, is_list=True)
