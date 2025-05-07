#!/usr/bin/env python3
"""Pre-notation serializer."""
from __future__ import annotations

import typing

from search_query.serializer_base import StringSerializer

if typing.TYPE_CHECKING:  # pragma: no
    from search_query.query import Query


# pylint: disable=too-few-public-methods
class GenericStringSerializer(StringSerializer):
    """Generic format query serializer."""

    def _stringify(self, node: Query) -> str:
        """actual translation logic for pre-notation"""

        if not hasattr(node, "value"):
            return " (?) "

        result = ""
        node_content = node.value
        if node.search_field:
            node_content += f"[{node.search_field}]"

        if hasattr(node, "near_param"):
            node_content += f"({node.near_param})"
        result = f"{result}{node_content}"
        if node.children == []:
            return result

        result = f"{result}["
        for child in node.children:
            result = f"{result}{self._stringify(child)}"
            if child != node.children[-1]:
                result = f"{result}, "
        return f"{result}]"

    def to_string(self, query: Query) -> str:
        """Convert the query to a string."""
        return self._stringify(query)
