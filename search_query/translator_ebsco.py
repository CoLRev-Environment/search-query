#!/usr/bin/env python3
"""EBSCO query translator."""
from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_MAP
from search_query.constants import PLATFORM_FIELD_TRANSLATION_MAP
from search_query.query import Query
from search_query.translator_base import QueryTranslator


class EBSCOTranslator(QueryTranslator):
    """Translator for EBSCO queries."""

    FIELD_TRANSLATION_MAP = PLATFORM_FIELD_TRANSLATION_MAP[PLATFORM.EBSCO]
    EBSCO_FIELD_MAP = PLATFORM_FIELD_MAP[PLATFORM.EBSCO]

    EBSCO_FIELD_MAP = PLATFORM_FIELD_MAP[PLATFORM.EBSCO]

    @classmethod
    def translate_search_fields_to_generic(cls, query: Query) -> None:
        """
        Translate search fields to standard names using self.FIELD_TRANSLATION_MAP
        """

        # Error not included in linting, mainly for programming purposes
        if not hasattr(cls, "FIELD_TRANSLATION_MAP") or not isinstance(
            cls.FIELD_TRANSLATION_MAP, dict
        ):
            raise AttributeError(
                "FIELD_TRANSLATION_MAP is not defined or is not a dictionary."
            )

        # Filter out search_fields and translate based on FIELD_TRANSLATION_MAP
        if query.search_field:
            original_value = query.search_field.value
            translated_value = cls.FIELD_TRANSLATION_MAP.get(
                original_value, original_value
            )
            query.search_field.value = translated_value

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
    def _get_search_field_ebsco(cls, search_field: str) -> str:
        """Transform search field to EBSCO Syntax."""

        if search_field in cls.EBSCO_FIELD_MAP:
            return f"{cls.EBSCO_FIELD_MAP[search_field]} "

        raise ValueError(f"Field {search_field} not supported by EBSCO")

    @classmethod
    def _translate_search_fields(cls, query: Query) -> None:
        if query.search_field:
            query.search_field.value = cls._get_search_field_ebsco(
                query.search_field.value
            )
        if query.operator:
            for child in query.children:
                cls._translate_search_fields(child)

    @classmethod
    def to_specific_syntax(cls, query: Query) -> Query:
        """Convert the query to a specific syntax."""

        query = query.copy()
        cls._translate_search_fields(query)

        return query
