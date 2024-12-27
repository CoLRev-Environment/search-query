#!/usr/bin/env python3
"""Pubmed serializer."""
from __future__ import annotations

import typing

from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_MAP
from search_query.constants import Operators
if typing.TYPE_CHECKING:  # pragma: no
    from search_query.query import Query


def to_string_pubmed(node: Query) -> str:
    """actual translation logic for PubMed"""

    # to do combine nodes for SYNTAX_COMBINED_FIELDS_MAP

    result = ""
    for child in node.children:
        if not child.operator:
            # node is not an operator
            if (child == node.children[0]) & (child != node.children[-1]):
                # current element is first but not only child element
                # -->operator does not need to be appended again
                result = (
                    f"{result}({child.value}"
                    f"{get_search_field_pubmed(str(child.search_field))}"
                )

            else:
                # current element is not first child
                result = (
                    f"{result} {node.value} {child.value}"
                    f"{get_search_field_pubmed(str(child.search_field))}"
                )

            if child == node.children[-1]:
                # current Element is last Element -> closing parenthesis
                result = f"{result})"

        else:
            # node is operator node
            if child.value == Operators.NOT:
                # current element is NOT Operator -> no parenthesis in PubMed
                result = f"{result}{to_string_pubmed(child)}"

            elif (child == node.children[0]) & (child != node.children[-1]):
                result = f"{result}({to_string_pubmed(child)}"
            else:
                result = f"{result} {node.value} {to_string_pubmed(child)}"

            if (child == node.children[-1]) & (child.value != Operators.NOT):
                result = f"{result})"
    return f"{result}"


PUBMED_FIELD_MAP = PLATFORM_FIELD_MAP[PLATFORM.PUBMED]


def get_search_field_pubmed(search_field: str) -> str:
    """transform search field to PubMed Syntax"""

    if search_field in PUBMED_FIELD_MAP:
        return PUBMED_FIELD_MAP[search_field]
    raise ValueError(f"Field {search_field} not supported by PubMed")
