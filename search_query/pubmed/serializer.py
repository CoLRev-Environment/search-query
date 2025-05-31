#!/usr/bin/env python3
"""Pubmed serializer."""
from __future__ import annotations

import typing

from search_query.constants import Operators

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.query import Query


def to_string_pubmed(query: Query) -> str:
    """Serialize the Query tree into a PubMed search string."""

    # to do combine querys for PLATFORM_COMBINED_FIELDS_MAP

    result = ""
    for child in query.children:
        if not child.operator:
            # query is not an operator
            if (child == query.children[0]) & (child != query.children[-1]):
                # current element is first but not only child element
                # -->operator does not need to be appended again
                result = (
                    f"{result}({child.value}"
                    f"{child.search_field.value if child.search_field else ''}"
                )

            else:
                # current element is not first child
                result = (
                    f"{result} {query.value} {child.value}"
                    f"{child.search_field.value if child.search_field else ''}"
                )

            if child == query.children[-1]:
                # current Element is last Element -> closing parenthesis
                result = f"{result})"

        else:
            # query is operator query
            if child.value == Operators.NOT:
                if len(child.children) == 1:
                    result = f"{result}{to_string_pubmed(child)}"
                else:
                    result = f"{result}({to_string_pubmed(child)}"

            elif (child == query.children[0]) & (child != query.children[-1]):
                result = f"{result}({to_string_pubmed(child)}"
            else:
                result = f"{result} {query.value} {to_string_pubmed(child)}"

            if (child == query.children[-1]) & (child.value != Operators.NOT):
                result = f"{result})"
    return result
