#!/usr/bin/env python3
"""WOS serializer."""
from __future__ import annotations

import typing

from search_query.constants import Operators
from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_MAP
from search_query.serializer_base import StringSerializer

if typing.TYPE_CHECKING:  # pragma: no
    from search_query.query import Query


# pylint: disable=too-few-public-methods
class WOSStringSerializer(StringSerializer):
    """WOS query serializer."""

    # https://pubmed.ncbi.nlm.nih.gov/help/
    # https://images.webofknowledge.com/images/help/WOS/hs_advanced_fieldtags.html
    # https://images.webofknowledge.com/images/help/WOS/hs_wos_fieldtags.html

    def _get_search_field_wos(self, search_field: str) -> str:
        """transform search field to WoS Syntax"""
        if search_field in PLATFORM_FIELD_MAP[PLATFORM.WOS]:
            return PLATFORM_FIELD_MAP[PLATFORM.WOS][search_field]
        raise ValueError(f"Search field not supported ({search_field})")

    def _translate_search_fields(self, query: Query) -> None:
        if query.search_field:
            query.search_field.value = self._get_search_field_wos(
                query.search_field.value
            )

        for child in query.children:
            self._translate_search_fields(child)

    def _stringify(self, query: Query) -> str:
        result = ""
        for child in query.children:
            if child.operator:
                # query is operator query
                if child.value == Operators.NOT:
                    # current element is NOT Operator -> no parenthesis in WoS
                    result = f"{result}{self._stringify(child)}"

                elif (child == query.children[0]) & (child != query.children[-1]):
                    result = (
                        f"{result}"
                        f"{query.search_field.value if query.search_field else ''}"
                        f"({self._stringify(child)}"
                    )
                else:
                    result = f"{result} {query.value} {self._stringify(child)}"

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

    def _move_fields_to_operator(self, query: Query) -> None:
        """move search fields to operator query"""

        if not query.operator:
            return

        for child in query.children:
            # recursive call
            self._move_fields_to_operator(child)

        common_term = ""
        for child in query.children:
            if not child.search_field:
                return
            if common_term == "":
                common_term = child.search_field.value
                continue
            if common_term != child.search_field.value:
                # Search fields differ
                return

        # all children have the same search field
        # move search field to operator
        query.search_field = query.children[0].search_field
        # remove search field from children
        for child in query.children:
            child.search_field = None

    def _remove_contradicting_search_fields(self, query: Query) -> None:
        """remove search fields that contradict the operator"""

        if not query.operator:
            return

        for child in query.children:
            # recursive call
            self._remove_contradicting_search_fields(child)

        child_fields = [
            child.search_field.value for child in query.children if child.search_field
        ]
        if len(child_fields) > 1:
            # all children have the same search field
            # move search field to operator
            query.search_field = None

    def to_string(self, query: Query) -> str:
        """Serialize the Query tree into a WoS search string."""

        # Important: do not modify the original query
        query = query.copy()

        self._translate_search_fields(query)
        self._move_fields_to_operator(query)
        self._remove_contradicting_search_fields(query)

        result = self._stringify(query)

        return result
