#!/usr/bin/env python
"""OR Query"""
from __future__ import annotations

import typing

from search_query.constants import Operators
from search_query.query import Query
from search_query.query import SearchField


# pylint: disable=duplicate-code
class OrQuery(Query):
    """OR Query Class"""

    def __init__(
        self,
        children: typing.List[typing.Union[str, Query]],
        *,
        search_field: typing.Optional[typing.Union[SearchField, str]] = None,
        position: typing.Optional[typing.Tuple[int, int]] = None,
        platform: str = "generic",
    ) -> None:
        """init method
        search terms: strings which you want to include in the search query
        nested queries: queries whose roots are appended to the query
        search field: search field to which the query should be applied
        """

        super().__init__(
            value=Operators.OR,
            children=children,
            search_field=search_field
            if isinstance(search_field, SearchField)
            else SearchField(search_field)
            if search_field is not None
            else None,
            position=position,
            platform=platform,
        )
