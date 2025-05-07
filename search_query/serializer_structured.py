#!/usr/bin/env python3
"""Structured serializer."""
from __future__ import annotations

import textwrap
import typing

from search_query.serializer_base import StringSerializer

if typing.TYPE_CHECKING:  # pragma: no
    from search_query.query import Query


# pylint: disable=too-few-public-methods
class StructuredStringSerializer(StringSerializer):
    """Structured format query serializer."""

    def _reindent(self, input_str: str, num_spaces: int) -> str:
        """_reindents the input string by num_spaces spaces."""
        lines = textwrap.wrap(input_str, 100, break_long_words=False)
        prefix = num_spaces * 3 * " "
        if num_spaces >= 1:
            prefix = "|" + num_spaces * 3 * " "
        lines = [prefix + line for line in lines]
        if num_spaces == 1:
            lines[0] = lines[0].replace(prefix, "|---")
        return "\n".join(lines)

    def _stringify(self, node: Query, *, level: int = 0) -> str:
        """actual translation logic for structured syntax"""

        indent = "   "
        result = ""

        if not hasattr(node, "value"):
            return f"{indent} (?)"

        if node.search_field:
            search_field = f"[{node.search_field}]"
        else:
            search_field = "[None]"

        node_value = node.value
        if hasattr(node, "near_param"):
            node_value += f"/{node.near_param}"
        result = self._reindent(f"{node_value} {search_field}", level)

        if node.children == []:
            return result

        result = f"{result}[\n"
        for child in node.children:
            result = f"{result}{self._stringify(child, level=level + 1)}\n"
        result = f"{result}{'|' + ' ' * level * 3 + ' '}]"

        return result

    def to_string(self, query: Query) -> str:
        """Convert the query to a string."""
        return self._stringify(query)
