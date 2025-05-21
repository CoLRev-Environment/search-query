#!/usr/bin/env python3
"""Structured serializer."""
from __future__ import annotations

import textwrap
import typing


if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.query import Query


def _reindent(input_str: str, num_spaces: int) -> str:
    """_reindents the input string by num_spaces spaces."""
    lines = textwrap.wrap(input_str, 100, break_long_words=False)
    prefix = num_spaces * 3 * " "
    if num_spaces >= 1:
        prefix = "|" + num_spaces * 3 * " "
    lines = [prefix + line for line in lines]
    if num_spaces == 1:
        lines[0] = lines[0].replace(prefix, "|---")
    return "\n".join(lines)


def to_string_structured(query: Query, *, level: int = 0) -> str:
    """Convert the query to a string."""

    indent = "   "
    result = ""

    if not hasattr(query, "value"):
        return f"{indent} (?)"

    if query.search_field:
        search_field = f"[{query.search_field}]"
    else:
        search_field = "[None]"

    query_value = query.value
    if hasattr(query, "near_param"):
        query_value += f"/{query.near_param}"
    result = _reindent(f"{query_value} {search_field}", level)

    if query.children == []:
        return result

    result = f"{result}[\n"
    for child in query.children:
        result = f"{result}{to_string_structured(child, level=level + 1)}\n"
    result = f"{result}{'|' + ' ' * level * 3 + ' '}]"

    return result
