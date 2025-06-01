#!/usr/bin/env python3
"""WOS serializer."""
from __future__ import annotations

import typing

from search_query.constants import Operators

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.query import Query


# https://pubmed.ncbi.nlm.nih.gov/help/
# https://images.webofknowledge.com/images/help/WOS/hs_advanced_fieldtags.html
# https://images.webofknowledge.com/images/help/WOS/hs_wos_fieldtags.html


def to_string_wos(query: Query, wrap: bool = False) -> str:
    """Serialize the Query tree into a Web of Science (WoS) search string."""

    # Leaf node
    if not query.children:
        field = query.search_field.value if query.search_field else ""
        return f"{field}{query.value}"

    parts = []
    for child in query.children:
        if child.operator and child.value == Operators.NOT:
            # Special handling: inject "NOT ..." directly
            not_child = child.children[0]
            not_str = to_string_wos(not_child, wrap=True)
            parts.append(f"NOT {not_str}")
        else:
            parts.append(to_string_wos(child, wrap=True))

    joined = f" {query.value} ".join(parts)

    if wrap:
        field = query.search_field.value if query.search_field else ""
        return f"{field}({joined})"

    # Top-level: wrap=False
    if query.search_field and all(not c.search_field for c in query.children):
        return f"{query.search_field.value}({joined})"

    return joined
