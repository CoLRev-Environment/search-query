#!/usr/bin/env python
"""NOT Query"""
from __future__ import annotations

import typing
from typing import cast
from typing import List
from typing import Union

from search_query.constants import Operators
from search_query.constants import PLATFORM
from search_query.query import Query
from search_query.query import SearchField
from search_query.query_term import Term

# pylint: disable=duplicate-code


class NotQuery(Query):
    """NOT Query"""

    def __init__(
        self,
        children: typing.List[typing.Union[str, Query]],
        *,
        field: typing.Optional[typing.Union[SearchField, str]] = None,
        position: typing.Optional[typing.Tuple[int, int]] = None,
        platform: str = "generic",
    ) -> None:
        """init method
        search terms: strings to include in the search query
        nested queries: queries whose roots are appended to the query
        search field: search field to which the query should be applied
        """

        query_children = (
            [c if isinstance(c, Query) else Term(value=c) for c in children]
            if children
            else None
        )

        super().__init__(
            value=Operators.NOT,
            children=cast(List[Union[str, Query]], query_children),
            field=field
            if isinstance(field, SearchField)
            else SearchField(field)
            if field is not None
            else None,
            position=position,
            platform=platform,
        )

        self.children = query_children  # type: ignore

    @property
    def children(self) -> typing.List[Query]:
        """Children property."""
        return self._children

    @children.setter
    def children(self, children: typing.List[Query]) -> None:
        """Set the children of NOT query, updating parent pointers."""
        # Clear existing children and reset parent links (if necessary)
        self._children.clear()
        if self.platform != "deactivated" and not isinstance(children, list):
            raise TypeError("children must be a list of Query instances or strings")

        if self.platform not in {"deactivated", PLATFORM.WOS} and len(children) != 2:
            raise ValueError("A NOT query must have two children")

        # Add each new child using add_child (ensures parent is set)
        for child in children or []:
            self.add_child(child)

    def selects_record(self, record_dict: dict) -> bool:
        return self.children[0].selects(record_dict=record_dict) and not self.children[
            1
        ].selects(record_dict=record_dict)
