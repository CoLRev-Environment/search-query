#!/usr/bin/env python
"""NEAR Query"""
import typing

from search_query.query import Query
from search_query.query import SearchField


class NEARQuery(Query):
    """NEAR Query"""

    # pylint: disable=too-many-arguments

    def __init__(
        self,
        value: str,
        children: typing.List[typing.Union[str, Query]],
        *,
        search_field: typing.Union[SearchField, str],
        position: typing.Optional[tuple] = None,
        distance: typing.Optional[int] = None,
    ) -> None:
        """init method
        search terms: strings which you want to include in the search query
        nested queries: queries whose roots are appended to the query
        nearDistance: distance of operator e.g. NEAR/2 --> near_distance = 2
        search field: search field to which the query should be applied
        """

        super().__init__(
            value=value,
            operator=True,
            children=children,
            search_field=search_field
            if isinstance(search_field, SearchField)
            else SearchField(search_field),
            position=position,
            distance=distance,
        )
