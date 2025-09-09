#!/usr/bin/env python
"""Range Query"""
from __future__ import annotations

import typing

from search_query.constants import Operators
from search_query.query import Query
from search_query.query import SearchField

# pylint: disable=duplicate-code


class RangeQuery(Query):
    """Range Query"""

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
            value=Operators.RANGE,
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
        """Set the children of RANGE query, updating parent pointers."""
        # Clear existing children and reset parent links (if necessary)
        self._children.clear()
        if not isinstance(children, list):
            raise TypeError("children must be a list of Query instances or strings")

        if len(children) != 2:
            raise ValueError("A RANGE query must have two children")

        # Add each new child using add_child (ensures parent is set)
        for child in children or []:
            self.add_child(child)

    def selects_record(self, record_dict: dict) -> bool:
        """Check if the record matches the range query."""
        assert len(self.children) == 2, "RANGE query must have two children"
        assert self.children[0].field, "First child must have a search field"
        assert self.children[1].field, "Second child must have a search field"
        assert (
            self.children[0].field.value == self.children[1].field.value
        ), "Both children of RANGE query must have the same search field"

        term1 = self.children[0].value.lower()
        term2 = self.children[1].value.lower()
        record_field = record_dict.get(
            self.children[0].field.value, record_dict.get("year", "")
        )

        if term1.isdigit() and term2.isdigit() and record_field.isdigit():
            value1 = int(term1)
            value2 = int(term2)
            record_value = int(record_field)
            return value1 <= record_value <= value2

        # Match other cases here (e.g., dates)

        raise ValueError("Both children of RANGE query must be numeric values")
