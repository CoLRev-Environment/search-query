#!/usr/bin/env python3
"""Structured serializer."""
from __future__ import annotations

import textwrap
import typing


if typing.TYPE_CHECKING:  # pragma: no
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


def to_string_structured(node: Query, *, level: int = 0) -> str:
    """actual translation logic for structured syntax"""

    indent = "   "
    result = ""

    if not hasattr(node, "value"):
        return f"{indent} (?)"

    search_field = ""
    if not node.operator:
        search_field = f"[{node.search_field}]"

    node_value = node.value
    if hasattr(node, "near_param"):
        node_value += f"/{node.near_param}"
    result = _reindent(f"{node_value} {search_field}", level)

    if node.children == []:
        return result

    result = f"{result}[\n"
    for child in node.children:
        result = f"{result}{to_string_structured(child, level=level + 1)}\n"
    result = f"{result}{'|' + ' ' * level * 3 + ' '}]"

    return result
