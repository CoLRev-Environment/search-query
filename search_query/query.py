#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations

import typing
from abc import ABC

from search_query.constants import Operators
from search_query.constants import PLATFORM
from search_query.serializer_ebsco import to_string_ebsco
from search_query.serializer_pre_notation import to_string_pre_notation
from search_query.serializer_pubmed import to_string_pubmed
from search_query.serializer_structured import to_string_structured
from search_query.serializer_wos import to_string_wos

# pylint: disable=too-few-public-methods


class SearchField:
    """SearchField class."""

    def __init__(
        self,
        value: str,
        *,
        position: typing.Optional[tuple] = None,
    ) -> None:
        """init method"""
        self.value = value
        self.position = position

    def __str__(self) -> str:
        return self.value


class Query(ABC):
    """Query class."""

    # pylint: disable=too-many-arguments
    # @abstractmethod
    def __init__(
        self,
        value: str = "NOT_INITIALIZED",
        *,
        operator: bool = False,
        search_field: typing.Optional[SearchField] = None,
        children: typing.Optional[typing.List[typing.Union[str, Query]]] = None,
        position: typing.Optional[tuple] = None,
        distance: typing.Optional[int] = None,
    ) -> None:
        """init method - abstract"""

        self.value = value
        self.operator = operator
        self.distance = distance
        if operator:
            assert value in [
                Operators.AND,
                Operators.OR,
                Operators.NOT,
                Operators.NEAR,
                Operators.WITHIN,
                "NOT_INITIALIZED",
            ]
            if value in {Operators.NEAR, Operators.WITHIN}:
                assert distance is not None, f"{value} operator requires a distance."
            else:
                assert distance is None, f"{value} operator cannot have a distance."

        self.children: typing.List[Query] = []
        if children:
            for child in children:
                if isinstance(child, str):
                    self.children.append(
                        Query(child, operator=False, search_field=search_field)
                    )
                else:
                    self.children.append(child)

        self.marked = False
        self.search_field = search_field
        if operator:
            self.search_field = None
        self.position = position

        self._ensure_children_not_circular()

    def get_nr_leaves(self) -> int:
        """Returns the number of leaves in the query tree"""
        return self._get_nr_leaves_from_node(self)

    def _get_nr_leaves_from_node(self, node: Query) -> int:
        return sum(
            self._get_nr_leaves_from_node(n) if n.operator else 1 for n in node.children
        )

    def _ensure_children_not_circular(
        self,
    ) -> None:
        """parse the query provided, build nodes&tree structure"""

        # Mark nodes to prevent circular references
        self.mark()
        # Remove marks
        self.remove_marks()

    def mark(self) -> None:
        """marks the node"""
        if self.marked:
            raise ValueError("Building Query Tree failed")
        self.marked = True
        for child in self.children:
            child.mark()

    def remove_marks(self) -> None:
        """removes the mark from the node"""
        self.marked = False
        for child in self.children:
            child.remove_marks()

    def print_node(self) -> str:
        """returns a string with all information to the node"""
        return (
            f"value: {self.value} "
            f"operator: {str(self.operator)} "
            f"search field: {self.search_field}"
        )

    def to_string(self, syntax: str = "pre_notation") -> str:
        """prints the query in the selected syntax"""

        if syntax == PLATFORM.PRE_NOTATION.value:
            return to_string_pre_notation(self)
        if syntax == PLATFORM.STRUCTURED.value:
            return to_string_structured(self)
        if syntax == PLATFORM.WOS.value:
            return to_string_wos(self)
        if syntax == PLATFORM.PUBMED.value:
            return to_string_pubmed(self)
        if syntax == PLATFORM.EBSCO.value:
            return to_string_ebsco(self)

        raise ValueError(f"Syntax not supported ({syntax})")
