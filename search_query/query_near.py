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
        position: typing.Optional[typing.Tuple[int, int]] = None,
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

    @property
    def children(self) -> typing.List[Query]:
        """Children property."""
        return self._children

    @children.setter
    def children(self, children: typing.List[Query]) -> None:
        """Set the children of NEAR query, updating parent pointers."""
        # Clear existing children and reset parent links (if necessary)
        self._children.clear()
        if not isinstance(children, list):
            raise TypeError("children must be a list of Query instances or strings")

        if len(children) != 2:
            raise ValueError("A NEAR query must have two children")

        # Add each new child using add_child (ensures parent is set)
        for child in children or []:
            self.add_child(child)
