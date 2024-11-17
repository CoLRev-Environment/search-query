#!/usr/bin/env python
"""NEAR Query"""
import typing

from search_query.constants import Operators
from search_query.query import Query
from search_query.query import SearchField


class NEARQuery(Query):
    """NEAR Query"""

    def __init__(
        self,
        nearDistance: int,
        children: typing.List[typing.Union[str, Query]],
        *,
        search_field: typing.Union[SearchField, str],
        position: typing.Optional[tuple] = None
    ) -> None:
        """init method
        search terms: strings which you want to include in the search query
        nested queries: queries whose roots are appended to the query
        nearDistance: distance of operator e.g. NEAR/2 --> nearDistance = 2
        search field: search field to which the query should be applied
        """

        super().__init__(
            value=Operators.NEAR,
            nearDistance=nearDistance,
            operator=True,
            children=children,
            search_field=search_field
            if isinstance(search_field, SearchField)
            else SearchField(search_field),
            position=position,
        )
