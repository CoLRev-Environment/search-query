#!/usr/bin/env python3
"""Pubmed serializer."""
from __future__ import annotations

import typing

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.query import Query


def to_string_pubmed(query: Query) -> str:
    """Serialize the Query tree into a PubMed search string."""
    if not query.children:
        # Serialize a term query
        return (
            f"{query.value}"
            f"{query.search_field.value if query.search_field else ''}"
        )
    else:
        # Serialize a compound query
        result = ""
        for i, child in enumerate(query.children):
            # Add operator between query children
            if i > 0:
                result += f' {query.value} '
            # Recursively serialize query children
            if isinstance(child, str):
                result += child
            else:
                result += to_string_pubmed(child)

        if query.get_parent():
            # Add parentheses around nested queries
            result = '(' + result + ')'

        return result
