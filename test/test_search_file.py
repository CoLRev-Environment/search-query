#!/usr/bin/env python3
"""Tests for SearchFile parser."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from search_query.search_file import load_search_file
from search_query.search_file import SearchFile


def test_search_history_file_parser() -> None:
    """Test SearchFile parser."""

    result = load_search_file("test/search_history_file_1.json")
    assert hasattr(result, "search_string")


def test_search_file_to_dict_and_save(tmp_path: Path) -> None:
    search_data = {
        "search_string": "cancer AND treatment",
        "platform": "pubmed",
        "authors": [
            {
                "name": "John Doe",
                "ORCID": "0000-0001-2345-678X",
                "email": "john@example.com",
            }
        ],
        "record_info": {"source": "manual"},
        "date": {"year": 2024},
        "extra_field": "extra_value",
    }

    sf = SearchFile(**search_data)  # type: ignore

    # Check to_dict content
    data_dict = sf.to_dict()
    assert data_dict["search_string"] == "cancer AND treatment"
    assert data_dict["authors"][0]["ORCID"] == "0000-0001-2345-678X"
    assert data_dict["extra_field"] == "extra_value"

    # Save and reload
    file_path = tmp_path / "search.json"
    sf.save(file_path)
    loaded = load_search_file(file_path)

    assert loaded.search_string == sf.search_string
    assert loaded.authors == sf.authors
    assert loaded.date == sf.date


def test_save_without_filepath_raises() -> None:
    sf = SearchFile(search_string="AI", platform="pubmed")
    with pytest.raises(
        ValueError,
        match="No search_history_path provided and no search_results_path stored.",
    ):
        sf.save()


def test_load_search_file_missing_keys(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.json"
    with open(bad_file, "w", encoding="utf-8") as f:
        json.dump({"authors": [], "date": {}}, f)

    with pytest.raises(
        ValueError, match="must contain at least 'search_string' and 'platform'"
    ):
        load_search_file(bad_file)


def test_valid_author_with_email_and_orcid() -> None:
    sf = SearchFile(
        search_string="example",
        platform="pubmed",
        authors=[
            {
                "name": "John Doe",
                "ORCID": "0000-0001-2345-678X",
                "email": "john.doe@example.com",
            }
        ],
    )
    assert sf.authors[0]["name"] == "John Doe"


def test_missing_authors_key() -> None:
    with pytest.raises(ValueError, match="Data must have an 'authors' key."):
        sf = SearchFile(search_string="example", platform="pubmed")
        sf._validate_authors({})  # force call with missing authors


def test_authors_not_a_list() -> None:
    with pytest.raises(TypeError, match="Authors must be a list."):
        SearchFile(search_string="example", platform="pubmed", authors="not a list")  # type: ignore


def test_author_not_a_dict() -> None:
    with pytest.raises(TypeError, match="Author must be a dictionary."):
        SearchFile(search_string="example", platform="pubmed", authors=["John Doe"])  # type: ignore


def test_author_missing_name_key() -> None:
    with pytest.raises(ValueError, match="Author must have a 'name' key."):
        SearchFile(
            search_string="example",
            platform="pubmed",
            authors=[{"email": "john@example.com"}],
        )


def test_author_name_not_a_string() -> None:
    with pytest.raises(TypeError, match="Author name must be a string."):
        SearchFile(search_string="example", platform="pubmed", authors=[{"name": 123}])


def test_orcid_not_a_string() -> None:
    with pytest.raises(TypeError, match="ORCID must be a string."):
        SearchFile(
            search_string="example",
            platform="pubmed",
            authors=[{"name": "Jane", "ORCID": 1234}],
        )


def test_orcid_invalid_format() -> None:
    with pytest.raises(ValueError, match="Invalid ORCID."):
        SearchFile(
            search_string="example",
            platform="pubmed",
            authors=[{"name": "Jane", "ORCID": "1234-5678-9012"}],
        )


def test_email_not_a_string() -> None:
    with pytest.raises(TypeError, match="Email must be a string."):
        SearchFile(
            search_string="example",
            platform="pubmed",
            authors=[{"name": "Jane", "email": 42}],
        )


def test_email_invalid_format() -> None:
    with pytest.raises(ValueError, match="Invalid email."):
        SearchFile(
            search_string="example",
            platform="pubmed",
            authors=[{"name": "Jane", "email": "not-an-email"}],
        )
