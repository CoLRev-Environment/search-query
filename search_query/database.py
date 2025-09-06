#!/usr/bin/env python3
"""Database and filters."""
from __future__ import annotations

import typing

try:
    from importlib.resources import files  # Python 3.9+
except ImportError:  # pragma: no cover
    from importlib_resources import files  # pip install importlib_resources

from search_query.parser import parse
from search_query.search_file import load_search_file

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.query import Query

# mypy: disable-error-code=attr-defined

# Note: the query data will be included in the package for now.
# - File sizes are small (less than 100kB)
# - Recommending filters requires queries (filters) to be available
# This decision may change in the future if the number of queries increases.


def load_query(name: str) -> Query:
    """Load a query object from JSON by name."""
    try:
        name = name.replace(".json", "")
        json_path = files("search_query") / f"json_db/{name}.json"  # mypy: ignore

        search = load_search_file(json_path)
        query = parse(search.search_string, platform=search.platform)

        return query

    except FileNotFoundError as exc:
        raise KeyError(f"No query file named {name}.json found") from exc


def list_queries() -> typing.List[str]:
    """List all available predefined query identifiers (without .json)."""

    json_dir = files("search_query") / "json_db"
    return [
        file.name.replace(".json", "")
        for file in json_dir.iterdir()
        if file.suffix == ".json"
    ]


def list_queries_with_details() -> dict:
    """List all available queries."""

    json_dir = files("search_query") / "json_db"

    details = {}
    for file in json_dir.iterdir():
        if file.suffix == ".json":
            search = load_search_file(file)
            details[file.name.replace(".json", "")] = {
                "description": search.description,  # pylint: disable=no-member
                "platform": search.platform,
                "search_string": search.search_string,
            }
    return details
