#!/usr/bin/env python3
"""Pubmed query translator."""
from __future__ import annotations

import typing
from abc import abstractmethod

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.query import Query


class QueryTranslator:
    """Translator for queries."""

    @classmethod
    @abstractmethod
    def to_generic_syntax(cls, query: Query) -> Query:
        """Convert the query to a generic syntax."""

    @classmethod
    @abstractmethod
    def to_specific_syntax(cls, query: Query) -> Query:
        """Convert the query to a specific syntax."""

    @classmethod
    def move_fields_to_terms(cls, query: Query) -> None:
        """Move the search field from the operator to the terms."""
        if query.operator and query.search_field:
            # move search field from operator to terms
            for child in query.children:
                if not child.search_field:
                    child.search_field = query.search_field.copy()
            query.search_field = None

        for child in query.children:
            # Recursively call the function on the child querys
            cls.move_fields_to_terms(child)

    @classmethod
    def flatten_nested_operators(cls, query: Query) -> None:
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
                cls.flatten_nested_operators(child)

    @classmethod
    def move_fields_to_operator(cls, query: Query) -> None:
        """move search fields to operator query"""

        if query.is_term():
            return

        for child in query.children:
            # recursive call
            cls.move_fields_to_operator(child)

        common_term = ""
        for child in query.children:
            if not child.search_field:  # pragma: no cover
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

    @classmethod
    def _remove_redundant_terms(cls, query: Query) -> None:
        """Remove redundant terms from the query (same term, same field)."""

        if query.is_term():
            return

        # Check for redundant terms in children
        seen_terms = set()
        for child in query.children:
            if child.is_term():
                if not child.search_field:
                    continue
                term_key = (child.search_field.value, child.value)
                if term_key in seen_terms:
                    query.children.remove(child)
                    print(
                        f"Removed redundant term: {child.value}"
                        f"[{child.search_field.value}]"
                    )
                else:
                    seen_terms.add(term_key)

        # Recursively check children
        for child in query.children:
            cls._remove_redundant_terms(child)
