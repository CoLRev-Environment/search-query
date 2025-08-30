"""EBSCO serializer for version 1.0.0."""

from __future__ import annotations

from search_query.ebsco.serializer import to_string_ebsco


class EBCOSerializer_v1_0_0:
    SOURCE = "ebsco"
    VERSION = "1.0.0"

    @staticmethod
    def to_string(query_obj) -> str:  # type: ignore[override]
        return to_string_ebsco(query_obj)

