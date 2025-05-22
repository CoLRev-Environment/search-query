#!/usr/bin/env python3
"""WOS query translator."""
from search_query.query import Query
from search_query.query import SearchField
from search_query.translator_base import QueryTranslator
from search_query.wos.constants import generic_search_field_to_syntax_field
from search_query.wos.constants import search_field_general_to_generic
from search_query.wos.constants import syntax_str_to_generic_search_field_set


class WOSTranslator(QueryTranslator):
    """Translator for WOS queries."""

    # pylint: disable=duplicate-code
    @classmethod
    def translate_search_fields_to_generic(cls, query: Query) -> None:
        """Translate search fields."""

        if query.search_field:
            generic_fields = syntax_str_to_generic_search_field_set(
                query.search_field.value
            )
            if len(generic_fields) == 1:
                query.search_field.value = generic_fields.pop()
            else:
                raise NotImplementedError
        if query.children:
            for child in query.children:
                cls.translate_search_fields_to_generic(child)

        # at this point it may be necessary to split (OR)
        # queries for combined search fields
        # see _expand_combined_fields() in pubmed

    @classmethod
    def apply_search_field_general(
        cls, query: Query, search_field_general: str
    ) -> None:
        """Apply the generic search field to the query."""

        if not search_field_general:
            return

        translated = search_field_general_to_generic(search_field_general)

        if len(translated) == 1:
            query.search_field = SearchField(
                value=translated.pop(),
            )
        else:
            raise NotImplementedError

    @classmethod
    def to_generic_syntax(cls, query: Query, *, search_field_general: str) -> Query:
        """Convert the query to a generic syntax."""

        query = query.copy()
        cls.translate_search_fields_to_generic(query)
        cls.apply_search_field_general(query, search_field_general)

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

        return query
