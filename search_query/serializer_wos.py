#!/usr/bin/env python3
"""WOS serializer."""
from __future__ import annotations

import typing

from search_query.constants import Fields
from search_query.constants import Operators

if typing.TYPE_CHECKING:  # pragma: no
    from search_query.query import Query


def to_string_wos(node: Query) -> str:
    """actual translation logic for WOS syntax"""

    result = ""
    for child in node.children:
        if not child.operator:
            # node is not an operator
            if (child == node.children[0]) & (child != node.children[-1]):
                # current element is first but not only child element
                # -->operator does not need to be appended again
                result = (
                    f"{result}"
                    f"{_get_search_field_wos(str(child.search_field))}="
                    f"({child.value}"
                )

            else:
                # current element is not first child
                result = f"{result} {node.value} {child.value}"

            if child == node.children[-1]:
                # current Element is last Element -> closing parenthesis
                result = f"{result})"

        else:
            # node is operator node
            if child.value == Operators.NOT:
                # current element is NOT Operator -> no parenthesis in WoS
                result = f"{result}{to_string_wos(child)}"

            elif (child == node.children[0]) & (child != node.children[-1]):
                result = f"{result}({to_string_wos(child)}"
            else:
                result = f"{result} {node.value} {to_string_wos(child)}"

            if (child == node.children[-1]) & (child.value != Operators.NOT):
                result = f"{result})"
    return f"{result}"


# https://pubmed.ncbi.nlm.nih.gov/help/
# https://images.webofknowledge.com/images/help/WOS/hs_advanced_fieldtags.html
# https://images.webofknowledge.com/images/help/WOS/hs_wos_fieldtags.html
def _get_search_field_wos(search_field: str) -> str:
    """transform search field to WoS Syntax"""
    if search_field == Fields.ABSTRACT:
        result = "AB"
    elif search_field == Fields.TITLE:
        result = "TI"
    else:
        raise ValueError(f"Search field not supported ({search_field})")
    return result
