#!/usr/bin/env python3
"""EBSCO serializer."""
from __future__ import annotations

import typing

from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_MAP

if typing.TYPE_CHECKING:  # pragma: no
    from search_query.query import Query


def to_string_ebsco(node: Query) -> str:
    """actual translation logic for EBSCO"""

    # to do combine nodes for SYNTAX_COMBINED_FIELDS_MAP

    result = ""
    for child in node.children:
        if not child.operator:
            # node is not an operator
            if (child == node.children[0]) & (child != node.children[-1]):
                # current element is first but not only child element
                # -->operator does not need to be appended again
                result = (
                    f"{result}("
                    f"{get_search_field_ebsco(str(child.search_field))} "
                    f"{child.value}"
                )

            else:
                # current element is not first child
                result = (
                    f"{result} {node.value} "
                    f"{get_search_field_ebsco(str(child.search_field))} "
                    f"{child.value}"
                )

            if child == node.children[-1]:
                # current Element is last Element -> closing parenthesis
                result = f"{result})"

        else:
            # node is operator node
            if child.value == "NOT":
                # current element is NOT Operator -> no parenthesis in EBSCO
                result = f"{result}{to_string_ebsco(child)}"

            elif (child == node.children[0]) & (child != node.children[-1]):
                result = f"{result}({to_string_ebsco(child)}"
            else:
                result = f"{result} {node.value} {to_string_ebsco(child)}"

            if (child == node.children[-1]) & (child.value != "NOT"):
                result = f"{result})"
    return f"{result}"


EBSCO_FIELD_MAP = PLATFORM_FIELD_MAP[PLATFORM.EBSCO]


def get_search_field_ebsco(search_field: str) -> str:
    """transform search field to EBSCO Syntax"""

    if search_field in EBSCO_FIELD_MAP:
        return EBSCO_FIELD_MAP[search_field]
    raise ValueError(f"Field {search_field} not supported by EBSCO")
