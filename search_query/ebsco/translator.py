#!/usr/bin/env python3
"""EBSCO query translator."""
from search_query.constants import Fields
from search_query.ebsco.constants import generic_search_field_to_syntax_field
from search_query.ebsco.constants import syntax_str_to_generic_search_field_set
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
            generic_fields = syntax_str_to_generic_search_field_set(original_value)
            if len(generic_fields) == 1:
                query.search_field.value = generic_fields.pop()
            else:  # pragma: no cover
                # No multiple-field mappings for EBSCO?
                raise NotImplementedError

        # Iterate through queries
        for child in query.children:
            cls.translate_search_fields_to_generic(child)

    @classmethod
    def to_generic_syntax(cls, query: Query) -> Query:
        """Convert the query to a generic syntax."""

        query = query.copy()
        cls.translate_search_fields_to_generic(query)

        return query

    @classmethod
    def _translate_search_fields(cls, query: Query) -> None:
        if query.search_field:
            translated_field = generic_search_field_to_syntax_field(
                query.search_field.value
            )
            query.search_field.value = translated_field

        if query.operator:
            for child in query.children:
                cls._translate_search_fields(child)

    @classmethod
    def replace_non_supported_fields(cls, query: Query) -> None:
        """Replace non-supported fields with nearest supported field."""

        if query.search_field:
            if query.search_field.value == Fields.KEYWORDS_PLUS:
                print('Replacing non-supported field "KEYWORDS_PLUS" with "KEYWORDS"')
                query.search_field.value = Fields.KEYWORDS

        for child in query.children:
            cls.replace_non_supported_fields(child)

    @classmethod
    def to_specific_syntax(cls, query: Query) -> Query:
        """Convert the query to a specific syntax."""

        query = query.copy()

        cls.replace_non_supported_fields(query)
        cls._translate_search_fields(query)
        cls.move_fields_to_operator(query)
        cls._remove_redundant_terms(query)

        return query
