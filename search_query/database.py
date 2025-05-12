#!/usr/bin/env python3
"""Database and filters."""
import typing
from importlib import resources

from search_query.parser import parse
from search_query.search_file import load_search_file

if typing.TYPE_CHECKING:
    from search_query.query import Query

# mypy: disable-error-code=attr-defined


def load_query(name: str) -> "Query":
    """Load a query object from JSON by name."""
    try:
        name = name.replace(".json", "")
        json_path = (
            resources.files("search_query") / f"database/{name}.json"
        )  # mypy: ignore
        # print(json_path)
        search = load_search_file(json_path)
        query = parse(search.search_string, platform=search.platform)
        # print(query.to_structured_string())
        return query
    except FileNotFoundError as exc:
        raise KeyError(f"No query file named {name}.json found") from exc


# # TODO : offer an alternative load_search_file() function
# (which gives users access to more information)
