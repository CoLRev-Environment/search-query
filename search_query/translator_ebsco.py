#!/usr/bin/env python3
"""EBSCO query translator."""
from search_query.constants_ebsco import generic_search_field_set_to_syntax_set
from search_query.constants_ebsco import syntax_str_to_generic_search_field_set
from search_query.query import Query
from search_query.translator_base import QueryTranslator


class EBSCOTranslator(QueryTranslator):
    """Translator for EBSCO queries."""

    @classmethod
    def translate_search_fields_to_generic(cls, query: Query) -> None:
        """
        Translate search fields to standard names using self.FIELD_TRANSLATION_MAP
        """

        # Filter out search_fields and translate based on FIELD_TRANSLATION_MAP
        if query.search_field:
            original_value = query.search_field.value
            translated_fields = syntax_str_to_generic_search_field_set(original_value)
            if len(translated_fields) == 1:
                query.search_field.value = translated_fields.pop()
            else:
                raise NotImplementedError

        # Iterate through queries
        for child in query.children:
            cls.translate_search_fields_to_generic(child)

    @classmethod
    def to_generic_syntax(cls, query: Query, *, search_field_general: str) -> Query:
        """Convert the query to a generic syntax."""

        query = query.copy()
        cls.translate_search_fields_to_generic(query)

        return query

    @classmethod
    def _translate_search_fields(cls, query: Query) -> None:
        if query.search_field:
            search_fields = generic_search_field_set_to_syntax_set(
                {query.search_field.value}
            )
            if len(search_fields) == 1:
                query.search_field.value = f"{search_fields.pop()} "
            else:
                raise NotImplementedError

        if query.operator:
            for child in query.children:
                cls._translate_search_fields(child)

    @classmethod
    def to_specific_syntax(cls, query: Query) -> Query:
        """Convert the query to a specific syntax."""

        query = query.copy()
        cls._translate_search_fields(query)

        return query
