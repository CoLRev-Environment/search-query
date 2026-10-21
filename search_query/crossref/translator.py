"""Translate supported generic query trees to and from Crossref queries."""
from __future__ import annotations

from search_query.constants import PLATFORM
from search_query.crossref.serializer import CrossrefSerializer
from search_query.query import Query
from search_query.translator_base import QueryTranslator


class CrossrefTranslator(QueryTranslator):
    """Translator for Crossref API query URLs."""

    @classmethod
    def to_generic_syntax(cls, query: Query) -> Query:
        generic_query = query.copy()
        generic_query.set_platform_unchecked(PLATFORM.GENERIC.value, silent=True)
        return generic_query

    @classmethod
    def to_specific_syntax(cls, query: Query) -> Query:
        # Validate representability before changing the platform. Crossref's API
        # search parameters can express terms joined with AND, but not arbitrary
        # Boolean query trees.
        CrossrefSerializer.validate(query)

        crossref_query = query.copy()
        crossref_query.set_platform_unchecked(PLATFORM.CROSSREF.value, silent=True)
        return crossref_query
