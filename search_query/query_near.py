#!/usr/bin/env python
"""NEAR Query"""
from __future__ import annotations

import typing
from typing import cast
from typing import List
from typing import Union

from search_query.constants import Operators
from search_query.query import Query
from search_query.query import SearchField
from search_query.query_term import Term


class NEARQuery(Query):
    """NEAR Query"""

    # pylint: disable=too-many-arguments
    # pylint: disable=duplicate-code

    def __init__(
        self,
        value: str,
        children: typing.List[typing.Union[str, Query]],
        *,
        field: typing.Optional[typing.Union[SearchField, str]] = None,
        position: typing.Optional[typing.Tuple[int, int]] = None,
        distance: int,
        platform: str = "generic",
    ) -> None:
        """init method
        search terms: strings to include in the search query
        nested queries: queries whose roots are appended to the query
        nearDistance: distance of operator e.g. NEAR/2 --> near_distance = 2
        search field: search field to which the query should be applied
        """

        query_children = [
            c if isinstance(c, Query) else Term(value=c) for c in children
        ]

        super().__init__(
            value=value,
            children=cast(List[Union[str, Query]], query_children),
            field=field
            if isinstance(field, SearchField)
            else SearchField(field)
            if field is not None
            else None,
            position=position,
            platform=platform,
        )
        self.children = query_children
        # assert isinstance(distance, int) and distance >= 0, (
        #     "distance must be a non-negative integer"
        # )
        self.distance: int = distance

    @property
    def distance(self) -> typing.Optional[int]:
        """Distance property."""
        return self._distance

    @distance.setter
    def distance(self, dist: typing.Optional[int]) -> None:
        """Set distance property."""

        if self.operator and self.value in {Operators.NEAR, Operators.WITHIN}:
            if dist is None:
                raise ValueError(f"{self.value} operator requires a distance")
        else:
            if dist is not None:
                raise ValueError(f"{self.value} operator cannot have a distance")

        self._distance = dist

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

        if self.platform not in {
            "deactivated",
            "pubmed",
        }:  # Note: temporary for EBSCO parser
            if len(children) != 2:
                raise ValueError("A NEAR query must have two children")

        # Add each new child using add_child (ensures parent is set)
        for child in children or []:
            self.add_child(child)

    def selects_record(self, record_dict: dict) -> bool:
        """Check if the record matches the NEAR query."""
        assert len(self.children) == 2, "NEAR query must have two children"
        assert self.children[0].field, "First child must have a search field"
        assert self.children[1].field, "Second child must have a search field"
        assert self.distance is not None, "NEAR query must have a distance"
        assert (
            self.children[0].field.value == self.children[1].field.value
        ), "Both children of NEAR query must have the same search field"

        # the self.children[0].value
        # must be in self.distance words of self.children[1].value
        field = self.children[0].field.value
        text = record_dict.get(field, "")
        if not isinstance(text, str):
            return False

        term1 = self.children[0].value.lower()
        term2 = self.children[1].value.lower()

        tokens = (
            text.split()
        )  # Simple whitespace tokenizer; can be replaced with a smarter one
        # Get all positions of term1 and term2
        positions_term1 = [
            i for i, token in enumerate(tokens) if token.lower() == term1
        ]
        positions_term2 = [
            i for i, token in enumerate(tokens) if token.lower() == term2
        ]

        # Check if any pair is within the allowed distance
        for p1 in positions_term1:
            for p2 in positions_term2:
                if abs(p1 - p2) <= self.distance:
                    return True

        return False
