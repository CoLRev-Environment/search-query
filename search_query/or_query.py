#!/usr/bin/env python
"""OR Query"""
from __future__ import annotations

import typing

from search_query.query import Query

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.node import Node


class OrQuery(Query):
    """OR Query Class"""

    def __init__(
        self,
        children: typing.List[typing.Union[str, Node, Query]],
        *,
        search_field: str,
        position: typing.Optional[tuple] = None,
    ) -> None:
        """init method
        search terms: strings which you want to include in the search query
        nested queries: queries whose roots are appended to the query
        search field: search field to which the query should be applied
        options: Author Keywords, Abstract, Author, DOI, ISBN, Publisher or Title
        """

        super().__init__(
            operator="OR",
            children=children,
            search_field=search_field,
            position=position,
        )
