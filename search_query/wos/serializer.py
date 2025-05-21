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


def to_string_wos(query: Query) -> str:
    """Serialize the Query tree into a WoS search string."""

    result = ""
    for child in query.children:
        if child.operator:
            # query is operator query
            if child.value == Operators.NOT:
                # current element is NOT Operator -> no parenthesis in WoS
                result = f"{result}{to_string_wos(child)}"

            elif (child == query.children[0]) & (child != query.children[-1]):
                result = (
                    f"{result}"
                    f"{query.search_field.value if query.search_field else ''}"
                    f"({to_string_wos(child)}"
                )
            else:
                result = f"{result} {query.value} {to_string_wos(child)}"

            if (child == query.children[-1]) & (child.value != Operators.NOT):
                result = f"{result})"
        else:
            # query is not an operator
            if (child == query.children[0]) & (child != query.children[-1]):
                # current element is first but not only child element
                # -->operator does not need to be appended again
                result = (
                    f"{result}"
                    f"{query.search_field.value if query.search_field else ''}"
                    f"({child.search_field.value if child.search_field else ''}"
                    f"{child.value}"
                )

            else:
                # current element is not first child
                result = (
                    f"{result} {query.value} "
                    f"{child.search_field.value if child.search_field else ''}"
                    f"{child.value}"
                )

            if child == query.children[-1]:
                # current Element is last Element -> closing parenthesis
                result = f"{result})"

    return result
