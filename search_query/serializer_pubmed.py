#!/usr/bin/env python3
"""Pubmed serializer."""
from __future__ import annotations

import typing

from search_query.constants import Operators
from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_MAP
from search_query.serializer_base import StringSerializer

if typing.TYPE_CHECKING:  # pragma: no
    from search_query.query import Query


class PubmedStringSerializer(StringSerializer):
    """Pubmed query serializer."""

    PUBMED_FIELD_MAP = PLATFORM_FIELD_MAP[PLATFORM.PUBMED]

    def _stringify(self, query: Query) -> str:
        """actual translation logic for PubMed"""

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
                    # current element is NOT Operator -> no parenthesis in PubMed
                    result = f"{result}{self._stringify(child)}"

                elif (child == query.children[0]) & (child != query.children[-1]):
                    result = f"{result}({self._stringify(child)}"
                else:
                    result = f"{result} {query.value} {self._stringify(child)}"

                if (child == query.children[-1]) & (child.value != Operators.NOT):
                    result = f"{result})"
        return f"{result}"

    def _get_search_field_pubmed(self, search_field: str) -> str:
        """transform search field to PubMed Syntax"""
        if search_field == "[tiab]":
            return "[tiab]"
        if search_field in self.PUBMED_FIELD_MAP:
            return self.PUBMED_FIELD_MAP[search_field]
        raise ValueError(f"Field {search_field} not supported by PubMed")

    def _translate_search_fields(self, query: Query) -> None:
        if query.operator:
            for child in query.children:
                self._translate_search_fields(child)

        else:
            if query.search_field:
                query.search_field.value = self._get_search_field_pubmed(
                    query.search_field.value
                )

    def _move_field_from_operator_to_terms(self, query: Query) -> None:
        if query.operator and query.search_field:
            # move search field from operator to terms
            for child in query.children:
                if not child.search_field:
                    child.search_field = query.search_field.copy()
            query.search_field = None

        for child in query.children:
            # Recursively call the function on the child querys
            self._move_field_from_operator_to_terms(child)

    def _combine_tiab(self, query: Query) -> None:
        """Recursively combine identical terms from TI and AB into TIAB."""

        if query.operator and query.value == "OR":
            # ab does not exist: always expand to tiab
            terms = []
            for child in query.children:
                if (
                    not child.operator
                    and child.search_field
                    and child.search_field.value == "ab"
                ):
                    child.search_field.value = "[tiab]"
                    terms.append(child.value)

            if terms:
                print(f"Info: combining terms from AB OR TI to TIAB: {terms}")

            # Warn if the same terms are not available with ti
            missing_terms = []
            for term in terms:
                if not any(
                    term == child.value
                    and child.search_field
                    and child.search_field.value == "ti"
                    for child in query.children
                ):
                    missing_terms.append(term)
            if missing_terms:
                print(
                    "Info/Warning: Search field broadened for term "
                    "(AB "
                    "(without corresponding search for the same term with TI)"
                    " -> TIAB): "
                    f"{missing_terms}"
                )

            # Remove duplicates with ti
            new_children = []
            for child in query.children:
                if child.operator:
                    # unconditionally append operators
                    new_children.append(child)
                elif child.search_field and not (
                    child.search_field.value == "ti" and child.value in terms
                ):
                    new_children.append(child)
            query.children = new_children

        # Recursively apply to child querys
        for child in query.children:
            self._combine_tiab(child)

    def _flatten_nested_operators(self, query: Query) -> None:
        """Check if there are double nested operators."""

        del_children = []
        if query.operator:
            for child in query.children:
                if child.operator:
                    if child.value == query.value:
                        # Get the child one level up
                        for grandchild in child.children:
                            query.children.append(grandchild)
                        del_children.append(query.children.index(child))

            # Delete the child
            if del_children:
                del_children.reverse()
                for index in del_children:
                    query.children.pop(index)

        if query.children:
            for child in query.children:
                self._flatten_nested_operators(child)

    def to_string(self, query: Query) -> str:
        """Serialize the Query tree into a PubMed search string."""

        # Important: do not modify the original query
        query = query.copy()

        self._move_field_from_operator_to_terms(query)
        self._flatten_nested_operators(query)
        self._combine_tiab(query)
        self._translate_search_fields(query)

        result = self._stringify(query)
        return result
