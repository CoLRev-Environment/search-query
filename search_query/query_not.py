#!/usr/bin/env python
"""NOT Query"""
import typing

from search_query.constants import Operators
from search_query.query import Query
from search_query.query import SearchField

# pylint: disable=duplicate-code


class NotQuery(Query):
    """NOT Query"""

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
            value=Operators.NOT,
            children=children,
            search_field=search_field
            if isinstance(search_field, SearchField)
            else SearchField(search_field)
            if search_field is not None
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
        """Set the children of NOT query, updating parent pointers."""
        # Clear existing children and reset parent links (if necessary)
        self._children.clear()
        if not isinstance(children, list):
            raise TypeError("children must be a list of Query instances or strings")

        if len(children) != 2:
            raise ValueError("A NOT query must have two children")

        # Add each new child using add_child (ensures parent is set)
        for child in children or []:
            self.add_child(child)
