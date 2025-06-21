#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations

import re
import typing

from search_query.constants import Fields
from search_query.constants import SearchField
from search_query.query import Query


class Term(Query):
    """Term"""

    def __init__(
        self,
        value: str,
        *,
        field: typing.Optional[SearchField] = None,
        position: typing.Optional[typing.Tuple[int, int]] = None,
        platform: str = "generic",
    ) -> None:
        super().__init__(
            value=value,
            operator=False,
            children=None,
            field=field,
            position=position,
            platform=platform,
        )

    def selects_record(self, record_dict: dict) -> bool:
        assert self.field is not None, "Search field must be set for terms"
        if self.field.value == Fields.TITLE:
            field_value = record_dict.get("title", "").lower()
        elif self.field.value == Fields.ABSTRACT:
            field_value = record_dict.get("abstract", "").lower()
        else:
            raise ValueError(f"Unsupported search field: {self.field}")

        value = self.value.lower().lstrip('"').rstrip('"')

        # Handle wildcards
        if "*" in value:
            pattern = re.compile(value.replace("*", ".*").lower())
            match = pattern.search(field_value)
            return match is not None

        # Match exact word
        return value.lower() in field_value
