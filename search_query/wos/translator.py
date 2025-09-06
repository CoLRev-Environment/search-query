#!/usr/bin/env python3
"""WOS query translator."""
from __future__ import annotations

import re

from search_query.constants import Fields
from search_query.query import Query
from search_query.query import SearchField
from search_query.query_or import OrQuery
from search_query.query_term import Term
from search_query.translator_base import QueryTranslator
from search_query.wos.constants import generic_field_to_syntax_field
from search_query.wos.constants import syntax_str_to_generic_field_set


class WOSTranslator(QueryTranslator):
    """Translator for WOS queries."""

    # pylint: disable=duplicate-code
    @classmethod
    def translate_fields_to_generic(cls, query: Query) -> None:
        """Translate search fields."""

        if query.field and query.field.value not in Fields.all():
            generic_fields = syntax_str_to_generic_field_set(query.field.value)
            if len(generic_fields) == 1:
                query.field.value = generic_fields.pop()
            else:
                cls._expand_combined_fields(query, generic_fields)

        if query.children:
            for child in query.children:
                cls.translate_fields_to_generic(child)

        # at this point it may be necessary to split (OR)
        # queries for combined search fields
        # see _expand_combined_fields() in pubmed

    @classmethod
    def _expand_combined_fields(cls, query: Query, fields: set) -> None:
        """Expand queries with combined search fields into an OR query"""
        query_children = []

        # Note: sorted list for deterministic order of fields
        for field in sorted(list(fields)):
            query_children.append(
                Term(
                    value=query.value,
                    field=SearchField(value=field),
                )
            )

        query.replace(
            OrQuery(
                children=query_children,  # type: ignore
            )
        )

    @classmethod
    def combine_equal_fields(cls, query: Query) -> None:
        """Combine queries with the same search field into an OR query."""

        if query.is_term():
            return

        # recursive call
        for child in query.children:
            cls.combine_equal_fields(child)

        # check if all children have the same search field
        child_fields = [child.field.value for child in query.children if child.field]
        if len(set(child_fields)) == 1:
            # all children have the same search field
            # move search field to operator
            query.field = SearchField(value=child_fields[0])
            for child in query.children:
                child.field = None

    @classmethod
    def to_generic_syntax(cls, query: Query) -> Query:
        """Convert the query to a generic syntax."""

        query = query.copy()
        cls.move_fields_to_terms(query)
        cls.translate_fields_to_generic(query)
        cls.combine_equal_fields(query)
        return query

    @classmethod
    def _remove_contradicting_fields(cls, query: Query) -> None:
        """remove search fields that contradict the operator"""

        if query.is_term():
            return

        for child in query.children:
            # recursive call
            cls._remove_contradicting_fields(child)

        child_fields = [child.field.value for child in query.children if child.field]
        if len(child_fields) > 1:
            # all children have the same search field
            # move search field to operator
            query.field = None

    @classmethod
    def _translate_fields(cls, query: Query) -> None:
        if query.field:
            query.field.value = generic_field_to_syntax_field(query.field.value)

        for child in query.children:
            cls._translate_fields(child)

    @classmethod
    def _format_year(cls, query: Query) -> None:
        """Format year search fields to WOS syntax."""

        if query.is_term() and query.field and query.field.value == "PY=":
            if re.fullmatch(r"^\d{4}$", query.value):
                pass

            match = re.search(r"\d{4}", query.value)
            if match:
                query.value = match.group(0)
                return

            raise ValueError(f"Invalid year format: {query.value}")

        for child in query.children:
            cls._format_year(child)

    @classmethod
    def to_specific_syntax(cls, query: Query) -> Query:
        """Convert the query to a specific syntax."""

        query = query.copy()

        cls._translate_fields(query)
        cls.move_fields_to_operator(query)
        cls._remove_contradicting_fields(query)
        cls._remove_redundant_terms(query)
        cls._format_year(query)

        return query
