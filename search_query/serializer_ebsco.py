#!/usr/bin/env python3
"""EBSCO serializer"""
from __future__ import annotations

import typing

from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_MAP

if typing.TYPE_CHECKING:  # pragma: no
    from search_query.query import Query


def _stringify(query: Query) -> str:
    """Serialize the Query tree into an EBSCO search string."""

    query = query.copy()

    if not query.children:
        # Leaf query (single search term)
        field = get_search_field_ebsco(str(query.search_field))
        return f"{field}{query.value}"

    result = []
    needs_parentheses = len(query.children) > 1  # Parentheses needed for grouping

    for i, child in enumerate(query.children):
        child_str = _stringify(child)

        if query.value in {"NEAR", "WITHIN"}:
            # Convert proximity operator to EBSCO format
            proximity_operator = handle_proximity_operator(query)

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
        query_str = get_search_field_ebsco(str(query.search_field)) + query_str
    return query_str


EBSCO_FIELD_MAP = PLATFORM_FIELD_MAP[PLATFORM.EBSCO]


def handle_proximity_operator(query: Query) -> str:
    """Transform proximity operator to EBSCO Syntax."""

    if query.distance is None:
        raise ValueError(
            "Proximity operator without distance is not supported by EBSCO"
        )

    if query.value not in {"NEAR", "WITHIN"}:
        raise ValueError(f"Invalid proximity operator: {query.value}")

    return f"{'N' if query.value == 'NEAR' else 'W'}{query.distance}"


def get_search_field_ebsco(search_field: str) -> str:
    """Transform search field to EBSCO Syntax."""

    if search_field is None or search_field == "None":
        return ""  # Return empty string if no search field is provided

    if search_field in EBSCO_FIELD_MAP:
        return f"{EBSCO_FIELD_MAP[search_field]} "

    raise ValueError(f"Field {search_field} not supported by EBSCO")


def to_string_ebsco(query: Query) -> str:
    """Convert the query to a string representation for EBSCO."""

    # Important: do not modify the original query
    query = query.copy()

    # Serialize the query tree into an EBSCO search string
    result = _stringify(query)
    return result
