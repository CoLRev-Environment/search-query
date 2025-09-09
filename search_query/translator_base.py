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
        if query.operator and query.field:
            # move search field from operator to terms
            for child in query.children:
                if not child.field:
                    child.field = query.field.copy()
            query.field = None

        for child in query.children:
            # Recursively call the function on the child queries
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
            if not child.field:  # pragma: no cover
                return
            if common_term == "":
                common_term = child.field.value
                continue
            if common_term != child.field.value:
                # Search fields differ
                return

        # all children have the same search field
        # move search field to operator
        query.field = query.children[0].field
        # remove search field from children
        for child in query.children:
            child.field = None

    @classmethod
    def _remove_redundant_terms(cls, query: Query) -> None:
        """Remove redundant terms from the query (same term, same field)."""

        if query.is_term():
            return

        # Check for redundant terms in children
        seen_terms = set()
        for child in query.children:
            if child.is_term():
                if not child.field:
                    continue
                term_key = (child.field.value, child.value)
                if term_key in seen_terms:
                    query.children.remove(child)
                    print(
                        f"Removed redundant term: {child.value}"
                        f"[{child.field.value}]"
                    )
                else:
                    seen_terms.add(term_key)

        # Recursively check children
        for child in query.children:
            cls._remove_redundant_terms(child)
