"""Web of Science serializer for version 1.0.0."""

from __future__ import annotations

from search_query.wos.serializer import to_string_wos


class WOSSerializer_v1_0_0:
    SOURCE = "wos"
    VERSION = "1.0.0"

    @staticmethod
    def to_string(query_obj) -> str:  # type: ignore[override]
        return to_string_wos(query_obj)

