#!/usr/bin/env python3
"""WOS query translator."""
from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_MAP
from search_query.constants_wos import map_default_field
from search_query.query import Query
from search_query.translator_base import QueryTranslator


class WOSTranslator(QueryTranslator):
    """Translator for WOS queries."""

    WOS_FIELD_MAP = PLATFORM_FIELD_MAP[PLATFORM.WOS]

    @classmethod
    def translate_search_fields_to_generic(cls, query: Query) -> None:
        """Translate search fields."""

        if query.search_field:
            query.search_field.value = map_default_field(query.search_field.value)
        if query.children:
            for child in query.children:
                cls.translate_search_fields_to_generic(child)

        # at this point it may be necessary to split (OR)
        # queries for combined search fields
        # see _expand_combined_fields() in pubmed

    @classmethod
    def to_generic_syntax(cls, query: Query, *, search_field_general: str) -> Query:
        """Convert the query to a generic syntax."""

        query = query.copy()
        cls.translate_search_fields_to_generic(query)

        # TODO : translate / apply search_field_general (according to drop-down field)

        return query

    @classmethod
    def _remove_contradicting_search_fields(cls, query: Query) -> None:
        """remove search fields that contradict the operator"""

        if not query.operator:
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
    def _get_search_field_wos(cls, search_field: str) -> str:
        """transform search field to WoS Syntax"""
        if search_field in cls.WOS_FIELD_MAP:
            return cls.WOS_FIELD_MAP[search_field]
        raise ValueError(f"Search field not supported ({search_field})")

    @classmethod
    def _translate_search_fields(cls, query: Query) -> None:
        if query.search_field:
            query.search_field.value = cls._get_search_field_wos(
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
