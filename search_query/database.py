#!/usr/bin/env python3
"""Database and filters."""
import typing

try:
    from importlib.resources import files  # Python 3.9+
except ImportError:
    from importlib_resources import files  # pip install importlib_resources

from search_query.parser import parse
from search_query.search_file import load_search_file

if typing.TYPE_CHECKING:
    from search_query.query import Query

# mypy: disable-error-code=attr-defined


def load_query(name: str) -> "Query":
    """Load a query object from JSON by name."""
    try:
        name = name.replace(".json", "")
        json_path = files("search_query") / f"json_db/{name}.json"  # mypy: ignore
        # print(json_path)
        search = load_search_file(json_path)
        query = parse(search.search_string, platform=search.platform)
        # print(query.to_structured_string())
        return query
    except FileNotFoundError as exc:
        raise KeyError(f"No query file named {name}.json found") from exc


def list_queries() -> typing.List[str]:
    """List all available predefined query identifiers (without .json)."""

    # TODO : also give details (dictionary?)

    json_dir = files("search_query") / "json_db"
    return [
        file.name.replace(".json", "")
        for file in json_dir.iterdir()
        if file.suffix == ".json"
    ]


# # TODO : offer an alternative load_search_file() function
# (which gives users access to more information)
