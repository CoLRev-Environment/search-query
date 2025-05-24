#!/usr/bin/env python3
"""WOS query translator."""
from search_query.constants import Fields
from search_query.constants import Operators
from search_query.query import Query
from search_query.query import SearchField
from search_query.translator_base import QueryTranslator
from search_query.wos.constants import generic_search_field_to_syntax_field
from search_query.wos.constants import syntax_str_to_generic_search_field_set


class WOSTranslator(QueryTranslator):
    """Translator for WOS queries."""

    # pylint: disable=duplicate-code
    @classmethod
    def translate_search_fields_to_generic(cls, query: Query) -> None:
        """Translate search fields."""

        if query.search_field and query.search_field.value not in Fields.all():
            generic_fields = syntax_str_to_generic_search_field_set(
                query.search_field.value
            )
            if len(generic_fields) == 1:
                query.search_field.value = generic_fields.pop()
            else:
                cls._expand_combined_fields(query, generic_fields)

        if query.children:
            for child in query.children:
                cls.translate_search_fields_to_generic(child)

        # at this point it may be necessary to split (OR)
        # queries for combined search fields
        # see _expand_combined_fields() in pubmed

    @classmethod
    def _expand_combined_fields(cls, query: Query, search_fields: set) -> None:
        """Expand queries with combined search fields into an OR query"""
        query_children = []

        # Note: sorted list for deterministic order of fields
        for search_field in sorted(list(search_fields)):
            query_children.append(
                Query(
                    value=query.value,
                    operator=False,
                    search_field=SearchField(value=search_field),
                    children=None,
                )
            )

        query.value = Operators.OR
        query.operator = True
        query.search_field = None
        query.children = query_children  # type: ignore

    @classmethod
    def combine_equal_search_fields(cls, query: Query) -> None:
        """Combine queries with the same search field into an OR query."""

        if query.is_term():
            return

        # recursive call
        for child in query.children:
            cls.combine_equal_search_fields(child)

        # check if all children have the same search field
        child_fields = [
            child.search_field.value for child in query.children if child.search_field
        ]
        if len(set(child_fields)) == 1:
            # all children have the same search field
            # move search field to operator
            query.search_field = SearchField(value=child_fields[0])
            for child in query.children:
                child.search_field = None

    @classmethod
    def to_generic_syntax(cls, query: Query) -> Query:
        """Convert the query to a generic syntax."""

        query = query.copy()
        cls.move_fields_to_terms(query)
        cls.translate_search_fields_to_generic(query)
        cls.combine_equal_search_fields(query)
        return query

    @classmethod
    def _remove_contradicting_search_fields(cls, query: Query) -> None:
        """remove search fields that contradict the operator"""

        if query.is_term():
            return

        for child in query.children:
            # recursive call
            cls._remove_contradicting_search_fields(child)

        child_fields = [
            child.search_field.value for child in query.children if child.search_field
        ]
        if len(child_fields) > 1:
            # all children have the same search field
            # move search field to operator
            query.search_field = None

    @classmethod
    def _translate_search_fields(cls, query: Query) -> None:
        if query.search_field:
            query.search_field.value = generic_search_field_to_syntax_field(
                query.search_field.value
            )

        for child in query.children:
            cls._translate_search_fields(child)

    @classmethod
    def to_specific_syntax(cls, query: Query) -> Query:
        """Convert the query to a specific syntax."""

        query = query.copy()

        cls._translate_search_fields(query)
        cls.move_fields_to_operator(query)
        cls._remove_contradicting_search_fields(query)
        cls._remove_redundant_terms(query)

        return query
