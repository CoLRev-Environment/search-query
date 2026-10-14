"""Serialize supported query trees as Crossref API URLs."""
from __future__ import annotations

from urllib.parse import urlencode
from urllib.parse import urlunsplit

from search_query.constants import Fields
from search_query.constants import Operators
from search_query.constants import SearchField
from search_query.query import Query
from search_query.serializer_base import StringSerializer

FIELD_PARAMETERS = {
    Fields.ALL: "query",
    Fields.TITLE: "query.title",
    Fields.AUTHOR: "query.author",
}


class CrossrefSerializer(StringSerializer):
    """Serialize a simple AND of Crossref-supported terms."""

    @classmethod
    def _collect_terms(cls, query: Query) -> list[Query]:
        if not query.operator:
            return [query]
        if query.value != Operators.AND:
            raise NotImplementedError(
                f"Crossref URL serialization does not support {query.value} queries."
            )

        terms = []
        for child in query.children:
            if child.operator and child.value == Operators.AND:
                terms.extend(cls._collect_terms(child))
            elif child.operator:
                raise NotImplementedError(
                    "Crossref URL serialization does not support "
                    f"{child.value} queries."
                )
            else:
                terms.append(child)
        return terms

    @classmethod
    def validate(cls, query: Query) -> None:
        """Raise when a query cannot be represented by Crossref parameters."""

        for term in cls._collect_terms(query):
            cls._parameter_for_field(term.field)

    @staticmethod
    def _parameter_for_field(field: SearchField | None) -> str:
        field_value = field.value if field else Fields.ALL
        try:
            return FIELD_PARAMETERS[field_value]
        except KeyError as exc:
            raise NotImplementedError(
                "Crossref URL serialization does not support the "
                f"{field_value!r} field."
            ) from exc

    def to_string(self, query: Query) -> str:
        self.validate(query)
        terms = self._collect_terms(query)
        if not terms:
            raise ValueError("A Crossref URL must contain at least one search term.")

        parameters = [
            (self._parameter_for_field(term.field), term.value) for term in terms
        ]
        parameters.extend(getattr(query, "crossref_options", []))
        endpoint = getattr(query, "crossref_endpoint", "/works")
        if endpoint not in {"/works", ""}:
            raise ValueError(f"Unsupported Crossref endpoint: {endpoint}.")

        return urlunsplit(
            ("https", "api.crossref.org", "/works", urlencode(parameters), "")
        )
