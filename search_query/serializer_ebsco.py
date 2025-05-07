#!/usr/bin/env python3
"""EBSCO serializer"""
from __future__ import annotations

import typing

from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_MAP
from search_query.serializer_base import StringSerializer

if typing.TYPE_CHECKING:  # pragma: no
    from search_query.query import Query


class EBSCOStringSerializer(StringSerializer):
    """EBSCO query serializer."""

    EBSCO_FIELD_MAP = PLATFORM_FIELD_MAP[PLATFORM.EBSCO]

    def _stringify(self, query: Query) -> str:
        """Serialize the Query tree into an EBSCO search string."""

        query = query.copy()

        if not query.children:
            # Leaf query (single search term)
            field = self._get_search_field_ebsco(str(query.search_field))
            return f"{field}{query.value}"

        result = []
        needs_parentheses = len(query.children) > 1  # Parentheses needed for grouping

        for i, child in enumerate(query.children):
            child_str = self._stringify(child)

            if query.value in {"NEAR", "WITHIN"}:
                # Convert proximity operator to EBSCO format
                proximity_operator = self._handle_proximity_operator(query)

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

        if needs_parentheses:
            query_str = f"({query_str})"

        if query.search_field:
            # Add search field if present
            query_str = (
                self._get_search_field_ebsco(str(query.search_field)) + query_str
            )
        return query_str

    def _handle_proximity_operator(self, query: Query) -> str:
        """Transform proximity operator to EBSCO Syntax."""

        if query.distance is None:
            raise ValueError(
                "Proximity operator without distance is not supported by EBSCO"
            )

        if query.value not in {"NEAR", "WITHIN"}:
            raise ValueError(f"Invalid proximity operator: {query.value}")

        return f"{'N' if query.value == 'NEAR' else 'W'}{query.distance}"

    def _get_search_field_ebsco(self, search_field: str) -> str:
        """Transform search field to EBSCO Syntax."""

        if search_field is None or search_field == "None":
            return ""  # Return empty string if no search field is provided

        if search_field in self.EBSCO_FIELD_MAP:
            return f"{self.EBSCO_FIELD_MAP[search_field]} "

        raise ValueError(f"Field {search_field} not supported by EBSCO")

    def to_string(self, query: Query) -> str:
        """Convert the query to a string representation for EBSCO."""

        # Important: do not modify the original query
        query = query.copy()

        # Serialize the query tree into an EBSCO search string
        result = self._stringify(query)
        return result
