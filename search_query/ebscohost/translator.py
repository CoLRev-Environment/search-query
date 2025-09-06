#!/usr/bin/env python3
"""EBSCO query translator."""
from __future__ import annotations

from search_query.constants import Fields
from search_query.ebscohost.constants import generic_field_to_syntax_field
from search_query.ebscohost.constants import syntax_str_to_generic_field_set
from search_query.query import Query
from search_query.translator_base import QueryTranslator


class EBSCOTranslator(QueryTranslator):
    """Translator for EBSCO queries."""

    @classmethod
    def translate_fields_to_generic(cls, query: Query) -> None:
        """
        Translate search fields to standard names using self.field_TRANSLATION_MAP
        """

        # Filter out fields and translate based on field_TRANSLATION_MAP
        if query.field:
            original_value = query.field.value
            generic_fields = syntax_str_to_generic_field_set(original_value)
            if len(generic_fields) == 1:
                query.field.value = generic_fields.pop()
            else:  # pragma: no cover
                # No multiple-field mappings for EBSCO?
                raise NotImplementedError

        # Iterate through queries
        for child in query.children:
            cls.translate_fields_to_generic(child)

    @classmethod
    def to_generic_syntax(cls, query: Query) -> Query:
        """Convert the query to a generic syntax."""

        query = query.copy()
        cls.translate_fields_to_generic(query)

        return query

    @classmethod
    def _translate_fields(cls, query: Query) -> None:
        if query.field:
            translated_field = generic_field_to_syntax_field(query.field.value)
            query.field.value = translated_field

        if query.operator:
            for child in query.children:
                cls._translate_fields(child)

    @classmethod
    def replace_non_supported_fields(cls, query: Query) -> None:
        """Replace non-supported fields with nearest supported field."""

        if query.field:
            if query.field.value == Fields.KEYWORDS_PLUS:
                print('Replacing non-supported field "KEYWORDS_PLUS" with "KEYWORDS"')
                query.field.value = Fields.KEYWORDS

        for child in query.children:
            cls.replace_non_supported_fields(child)

    @classmethod
    def to_specific_syntax(cls, query: Query) -> Query:
        """Convert the query to a specific syntax."""

        query = query.copy()

        cls.replace_non_supported_fields(query)
        cls._translate_fields(query)
        cls.move_fields_to_operator(query)
        cls._remove_redundant_terms(query)

        return query
