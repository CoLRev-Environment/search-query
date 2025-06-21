#!/usr/bin/env python3
"""Example serializer template for a custom platform."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from search_query.query import Query


def to_string_custom(query: Query) -> str:
    # Leaf node (no children)
    if not query.children:
        field = query.field.value if query.field else ""
        return f"{field}{query.value}"

    # Composite node (operator with children)
    serialized_children = [to_string_custom(child) for child in query.children]
    joined_children = f" {query.value} ".join(serialized_children)

    # Add parentheses to clarify grouping
    if len(query.children) > 1:
        joined_children = f"({joined_children})"

    # Prefix with field if applicable
    if query.field:
        return f"{query.field.value}{joined_children}"
    return joined_children
