"""PubMed serializer for version 1.0.0."""

from __future__ import annotations

from search_query.pubmed.serializer import to_string_pubmed


class PubMedSerializer_v1_0_0:
    SOURCE = "pubmed"
    VERSION = "1.0.0"

    @staticmethod
    def to_string(query_obj) -> str:  # type: ignore[override]
        return to_string_pubmed(query_obj)

