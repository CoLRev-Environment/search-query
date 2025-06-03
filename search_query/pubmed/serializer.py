#!/usr/bin/env python3
"""Pubmed serializer."""
from __future__ import annotations

import typing

from search_query.constants import Operators

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.query import Query


def to_string_pubmed(query: Query) -> str:
    """Serialize the Query tree into a PubMed search string."""
    if not query.children:
        # Serialize term query
        return (
            f"{query.value}" f"{query.search_field.value if query.search_field else ''}"
        )
    if query.value == Operators.NEAR:
        # Serialize near query
        return (
            f"{query.children[0].value}"
            f"{query.children[0].search_field.value[:-1]}"
            f":~{query.distance if hasattr(query, "distance") else 0}]"
        )
    if query.value == Operators.RANGE:
        # Serialize range query
        return (
            f"{query.children[0].value}:{query.children[1].value}"
            f"{query.children[0].search_field.value}"
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
            result += to_string_pubmed(child)

    if query.get_parent():
        # Add parentheses around nested queries
        result = "(" + result + ")"

    return result
