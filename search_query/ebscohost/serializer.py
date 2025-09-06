#!/usr/bin/env python3
"""EBSCO serializer"""
from __future__ import annotations

import typing

from search_query.serializer_base import StringSerializer


if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.query import Query

# pylint: disable=too-few-public-methods


class EBSCOQuerySerializer(StringSerializer):
    """EBSCO query serializer."""

    def to_string(self, query: Query) -> str:
        """Convert the query to a string representation for EBSCO."""
        # pylint: disable=import-outside-toplevel
        from search_query.query_near import NEARQuery

        if not query.children:
            # Leaf query (single search term)
            field = f"{query.field.value} " if query.field else ""
            return f"{field}{query.value}"

        result = []

        for i, child in enumerate(query.children):
            child_str = self.to_string(child)

            if isinstance(query, NEARQuery):
                # Convert proximity operator to EBSCO format
                proximity_operator = (
                    f"{'N' if query.value == 'NEAR' else 'W'}{query.distance}"
                )

                # Ensure correct order of proximity terms
                if i == 0:
                    result.append(child_str)
                else:
                    result.append(f"{proximity_operator} {child_str}")
            else:
                if i > 0:  # Add the operator between terms
                    result.append(query.value)

                result.append(child_str)

        query_str = " ".join(result)

        if query.get_parent() or query.field:
            query_str = f"({query_str})"

        if query.field:
            # Add search field if present
            query_str = f"{query.field.value} {query_str}"
        return query_str
