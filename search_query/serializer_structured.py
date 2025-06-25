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

    if not hasattr(query, "value"):  # pragma: no cover
        return f"{indent} (?)"

    field = ""
    if query.field:
        field = f"[{query.field}]"

    query_value = query.value
    if hasattr(query, "distance"):  # and isinstance(query.distance, int):
        query_value += f"/{query.distance}"
    result = _reindent(f"{query_value} {field}", level)

    if query.children == []:
        return result

    result = f"{result}[\n"
    for child in query.children:
        result = f"{result}{to_string_structured(child, level=level + 1)}\n"
    result = f"{result}{'|' + ' ' * level * 3 + ' '}]"

    return result


def to_string_structured_2(query: Query, level: int = 0) -> str:
    """Convert the query into a multiline, indented Boolean-style expression."""
    indent = "  " * level
    next_indent = "  " * (level + 1)
    next_indent = ""
    indent = ""

    # Leaf node
    if not query.operator:
        field = f"[{query.field}]" if query.field else ""
        return f"{indent}{query.value}{field}"

    operator = f" {query.value} "
    child_strs = [
        to_string_structured_2(child, level + 1).strip() for child in query.children
    ]

    if len(child_strs) == 1:
        inner = child_strs[0]
        return f"{indent}({inner})" if query.get_parent() else f"{indent}{inner}"

    joined = (f"{operator}{next_indent}").join(child_strs)
    wrapped = f"{indent}({next_indent}{joined}{indent})"

    return wrapped if query.get_parent() else f"{joined}"
