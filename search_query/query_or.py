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
        field: typing.Optional[typing.Union[SearchField, str]] = None,
        position: typing.Optional[typing.Tuple[int, int]] = None,
        platform: str = "generic",
    ) -> None:
        """init method
        search terms: strings to include in the search query
        nested queries: queries whose roots are appended to the query
        search field: search field to which the query should be applied
        """

        super().__init__(
            value=Operators.OR,
            children=children,
            field=field
            if isinstance(field, SearchField)
            else SearchField(field)
            if field is not None
            else None,
            position=position,
            platform=platform,
        )

    @property
    def children(self) -> typing.List[Query]:
        """Children property."""
        return self._children

    @children.setter
    def children(self, children: typing.List[Query]) -> None:
        """Set the children of OR query, updating parent pointers."""
        # Clear existing children and reset parent links (if necessary)
        self._children.clear()
        if not isinstance(children, list):
            raise TypeError("children must be a list of Query instances or strings")

        if len(children) < 2:
            raise ValueError("An OR query must have two children")

        # Add each new child using add_child (ensures parent is set)
        for child in children or []:
            self.add_child(child)

    def selects_record(self, record_dict: dict) -> bool:
        return any(x.selects(record_dict=record_dict) for x in self.children)
