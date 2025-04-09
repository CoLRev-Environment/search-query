#!/usr/bin/env python3
"""EBSCO serializer"""
from __future__ import annotations

import typing

from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_MAP

if typing.TYPE_CHECKING:  # pragma: no
    from search_query.query import Query


def to_string_ebsco(node: Query) -> str:
    """Serialize the Query tree into an EBSCO search string."""

    if not node.children:
        # Leaf node (single search term)
        field = get_search_field_ebsco(str(node.search_field))
        return f"{field}{node.value}"

    result = []
    needs_parentheses = len(node.children) > 1  # Parentheses needed for grouping

    for i, child in enumerate(node.children):
        child_str = to_string_ebsco(child)

        if node.value in {"NEAR", "WITHIN"}:
            # Convert proximity operator to EBSCO format
            proximity_operator = handle_proximity_operator(node)

            # Ensure correct order of proximity terms
            if i == 0:
                result.append(child_str)
            else:
                result.append(f"{proximity_operator} {child_str}")
        else:
            if i > 0:  # Add the operator between terms
                result.append(node.value)

            result.append(child_str)

    query_str = " ".join(result)

    if needs_parentheses:
        query_str = f"({query_str})"

    return query_str


EBSCO_FIELD_MAP = PLATFORM_FIELD_MAP[PLATFORM.EBSCO]


def handle_proximity_operator(node: Query) -> str:
    """Transform proximity operator to EBSCO Syntax."""

    if node.distance is None:
        raise ValueError(
            "Proximity operator without distance is not supported by EBSCO"
        )

    if node.value not in {"NEAR", "WITHIN"}:
        raise ValueError(f"Invalid proximity operator: {node.value}")

    return f"{'N' if node.value == 'NEAR' else 'W'}{node.distance}"


def get_search_field_ebsco(search_field: str) -> str:
    """Transform search field to EBSCO Syntax."""

    if search_field is None or search_field == "None":
        return ""  # Return empty string if no search field is provided

    if search_field in EBSCO_FIELD_MAP:
        return f"{EBSCO_FIELD_MAP[search_field]} "

    raise ValueError(f"Field {search_field} not supported by EBSCO")
