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
    result = ""
    first_child = node.children[0] if node.children else None
    last_child = node.children[-1] if node.children else None

    for child in node.children:
        print(f"string so far: {result}\nCurrent Value: {child.value}")

        if not child.operator:
            # Node is a search term (not an operator)
            field = get_search_field_ebsco(str(child.search_field))

            if child == first_child and child != last_child:
                # First but not only child (open parenthesis)
                result = f"{result} {field}{child.value}".strip()
            else:
                # Other children (prepend operator before term)
                result = f"{result} {node.value} {field}{child.value}".strip()

            if child == last_child:
                # Last child, close parentheses
                result = f"{result})".strip()

        else:
            if child.value in ("NEAR", "WITHIN"):
                # Handle proximity operators correctly
                child.value = handle_proximity_operator(child)
                if child == first_child and child != last_child:
                    # First but not only child (open parenthesis)
                    result = f"({result}{to_string_ebsco(child)}"
                else:
                    result = f"{result} {child.value} {to_string_ebsco(child)}"

            else:
                if child == first_child and child != last_child:
                    # First but not only child (open parenthesis)
                    result = f"({result}{to_string_ebsco(child)}"
                else:
                    # Other children (prepend operator before term)
                    result = f"{result} {node.value} {to_string_ebsco(child)}"

    return f"{result}"


EBSCO_FIELD_MAP = PLATFORM_FIELD_MAP[PLATFORM.EBSCO]


def handle_proximity_operator(node: Query) -> str:
    """Transform proximity operator to EBSCO Syntax"""
    if node.distance is None:
        raise ValueError(
            "Proximity operator without distance is not supported by EBSCO"
        )
    proximity_operator = ""
    if node.value == "NEAR":
        proximity_operator = f"N{node.distance}"
    else:
        proximity_operator = f"W{node.distance}"
    return proximity_operator


def get_search_field_ebsco(search_field: str) -> str:
    """Transform search field to EBSCO Syntax."""
    if search_field is None or search_field == "None":
        return ""  # Return empty string if no search field is provided
    if search_field in EBSCO_FIELD_MAP:
        return f"{EBSCO_FIELD_MAP[search_field]} "
    raise ValueError(f"Field {search_field} not supported by EBSCO")
