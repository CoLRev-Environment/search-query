#!/usr/bin/env python3
"""Pubmed serializer."""
from __future__ import annotations

import typing

from search_query.constants import Operators
from search_query.serializer_base import StringSerializer

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.query import Query

# pylint: disable=too-few-public-methods


class PUBMEDQuerySerializer(StringSerializer):
    """PubMed query serializer."""

    def to_string(self, query: Query) -> str:
        """Serialize the Query tree into a PubMed search string."""
        if not query.children:
            # Serialize term query
            return f"{query.value}" f"{query.field.value if query.field else ''}"
        if query.value == Operators.NEAR:
            # Serialize near query
            distance = query.distance if hasattr(query, "distance") else 0
            assert query.children[0].field
            return (
                f"{query.children[0].value}"
                f"{query.children[0].field.value[:-1]}"
                f":~{distance}]"
            )
        if query.value == Operators.RANGE:
            # Serialize range query
            assert query.children[0].field
            assert query.children[1]
            return (
                f"{query.children[0].value}:{query.children[1].value}"
                f"{query.children[0].field.value}"
            )
        # Serialize compound query
        result = ""
        for i, child in enumerate(query.children):
            if i > 0:
                # Add operator between query children
                result += f" {query.value} "
            if isinstance(child, str):
                result += child
            else:
                # Recursively serialize query children
                result += self.to_string(child)

        if query.get_parent():
            # Add parentheses around nested queries
            result = "(" + result + ")"

        return result
