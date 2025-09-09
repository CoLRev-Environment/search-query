#!/usr/bin/env python3
"""Pre-notation serializer."""
from __future__ import annotations

import typing

from search_query.serializer_base import StringSerializer

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.query import Query

# pylint: disable=too-few-public-methods


class GenericSerializer(StringSerializer):
    """Web of Science query serializer."""

    def to_string(self, query: Query) -> str:
        """Serialize the Query tree into a generic search string."""

        if not hasattr(query, "value"):  # pragma: no cover
            return " (?) "

        result = ""
        query_content = query.value
        if hasattr(query, "distance"):  # and isinstance(query.distance, int):
            query_content += f"/{query.distance}"
        if query.field:
            query_content += f"[{query.field}]"

        result = f"{result}{query_content}"
        if query.children == []:
            return result

        result = f"{result}["
        for child in query.children:
            result = f"{result}{self.to_string(child)}"
            if child != query.children[-1]:
                result = f"{result}, "
        return f"{result}]"
