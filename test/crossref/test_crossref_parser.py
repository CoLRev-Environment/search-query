"""Tests for Crossref URL parsing and translation."""
from __future__ import annotations

import pytest

from search_query.constants import Fields
from search_query.constants import PLATFORM
from search_query.constants import SearchField
from search_query.exception import ListQuerySyntaxError
from search_query.exception import QuerySyntaxError
from search_query.linter import lint_query_string
from search_query.parser import parse
from search_query.query_and import AndQuery
from search_query.query_or import OrQuery
from search_query.query_term import Term


def test_parse_crossref_url_and_serialize_round_trip() -> None:
    url = (
        "https://api.crossref.org/works?query.title=room+at+the+bottom"
        "&query.author=richard+feynman&sort=published&order=asc"
    )

    query = parse(url, platform="crossref")

    assert query.platform == PLATFORM.CROSSREF.value
    assert query.to_generic_string() == (
        "AND[room at the bottom[title], richard feynman[author]]"
    )
    assert query.to_string() == url


def test_parse_crossref_bibliographic_query() -> None:
    query = parse(
        "https://api.crossref.org/works?query=renear+ontologies",
        platform=PLATFORM.CROSSREF.value,
    )

    assert query.to_generic_string() == "renear ontologies[all-fields]"
    assert query.to_string() == (
        "https://api.crossref.org/works?query=renear+ontologies"
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://example.org/works?query=term",
        "https://api.crossref.org/members?query=term",
        "https://api.crossref.org?query=term",
        "https://api.crossref.org/works?query.issn=1234-5678",
        "https://api.crossref.org/works?sort=published",
        "https://api.crossref.org/works?query=",
    ],
)
def test_reject_unsupported_crossref_url(url: str) -> None:
    with pytest.raises(QuerySyntaxError):
        parse(url, platform="crossref")


def test_crossref_list_queries_are_rejected() -> None:
    with pytest.raises(ListQuerySyntaxError):
        parse("1. term", platform="crossref", is_list=True)


def test_crossref_url_lints_without_messages() -> None:
    messages = lint_query_string(
        "https://api.crossref.org/works?query.title=term",
        platform=PLATFORM.CROSSREF.value,
    )

    assert messages == []


def test_parse_crossref_alias() -> None:
    assert (
        parse(
            "https://api.crossref.org/works?query.title=term", platform="Crossref API"
        ).platform
        == PLATFORM.CROSSREF.value
    )


def test_generic_query_translates_to_crossref_and_back() -> None:
    generic_query = AndQuery(
        [
            Term("room at the bottom", field=SearchField(Fields.TITLE)),
            Term("A&B", field=SearchField(Fields.AUTHOR)),
        ]
    )

    crossref_query = generic_query.translate(PLATFORM.CROSSREF.value)

    assert crossref_query.platform == PLATFORM.CROSSREF.value
    assert crossref_query.to_string() == (
        "https://api.crossref.org/works?query.title=room+at+the+bottom"
        "&query.author=A%26B"
    )

    round_tripped = crossref_query.translate(PLATFORM.GENERIC.value)
    assert round_tripped.to_generic_string() == generic_query.to_generic_string()


def test_crossref_translation_rejects_or_queries() -> None:
    generic_query = OrQuery(["one", "two"], field=SearchField(Fields.TITLE))

    with pytest.raises(NotImplementedError, match="does not support OR"):
        generic_query.translate(PLATFORM.CROSSREF.value)


def test_crossref_translation_rejects_unsupported_fields() -> None:
    generic_query = Term("2020", field=SearchField(Fields.YEAR_PUBLICATION))

    with pytest.raises(
        NotImplementedError, match="does not support the 'year-publication'"
    ):
        generic_query.translate(PLATFORM.CROSSREF.value)
