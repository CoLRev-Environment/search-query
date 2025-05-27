#!/usr/bin/env python
"""NEAR Query"""
import typing

from search_query.query import Query
from search_query.query import SearchField


class NEARQuery(Query):
    """NEAR Query"""

    # pylint: disable=too-many-arguments
    # pylint: disable=duplicate-code

    def __init__(
        self,
        value: str,
        children: typing.List[typing.Union[str, Query]],
        *,
        search_field: typing.Optional[typing.Union[SearchField, str]] = None,
        position: typing.Optional[tuple] = None,
        distance: typing.Optional[int] = None,
        platform: str = "generic",
    ) -> None:
        """init method
        search terms: strings which you want to include in the search query
        nested queries: queries whose roots are appended to the query
        nearDistance: distance of operator e.g. NEAR/2 --> near_distance = 2
        search field: search field to which the query should be applied
        """

        super().__init__(
            value=value,
            children=children,
            search_field=search_field
            if isinstance(search_field, SearchField)
            else SearchField(search_field)
            if search_field is not None
            else None,
            position=position,
            distance=distance,
            platform=platform,
        )
