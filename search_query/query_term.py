#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations

import typing

from search_query.constants import SearchField
from search_query.query import Query


class Term(Query):
    """Term"""

    def __init__(
        self,
        value: str,
        *,
        search_field: typing.Optional[SearchField] = None,
        position: typing.Optional[typing.Tuple[int, int]] = None,
        platform: str = "generic",
    ) -> None:
        super().__init__(
            value=value,
            operator=False,
            children=None,
            search_field=search_field,
            position=position,
            platform=platform,
        )
