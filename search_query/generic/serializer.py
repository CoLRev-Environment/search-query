#!/usr/bin/env python3
"""Pre-notation serializer."""
from __future__ import annotations

import typing

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.query import Query


def to_string_generic(query: Query) -> str:
    """Convert the query to a string."""
    if not hasattr(query, "value"):  # pragma: no cover
        return " (?) "

    result = ""
    query_content = query.value
    if hasattr(query, "distance") and query.distance:
        query_content += f"/{query.distance}"
    if query.search_field:
        query_content += f"[{query.search_field}]"

    result = f"{result}{query_content}"
    if query.children == []:
        return result

    result = f"{result}["
    for child in query.children:
        result = f"{result}{to_string_generic(child)}"
        if child != query.children[-1]:
            result = f"{result}, "
    return f"{result}]"
