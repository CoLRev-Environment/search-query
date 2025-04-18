#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations

import re
import typing

from search_query.constants import Fields
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


# pylint: disable=too-many-instance-attributes
class Query:
    """Query class."""

    # pylint: disable=too-many-arguments
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
        self._value: str = ""
        self._operator = False
        self._distance = -1
        self._children: typing.List[Query] = []
        self._search_field = None

        self.operator = operator
        self.value = value
        self.distance = distance
        self.search_field = search_field
        self.position = position
        self.marked = False

        if children:
            for child in children:
                self.add_child(child)

        self._ensure_children_not_circular()

    @property
    def value(self) -> str:
        """Value property."""
        return self._value

    @value.setter
    def value(self, v: str) -> None:
        """Set value property."""
        if not isinstance(v, str):
            raise TypeError("value must be a string")
        if self.operator and v not in [
            Operators.AND,
            Operators.OR,
            Operators.NOT,
            Operators.NEAR,
            Operators.WITHIN,
            "NOT_INITIALIZED",
        ]:
            raise ValueError(f"Invalid operator value: {v}")
        self._value = v

    @property
    def operator(self) -> bool:
        """Operator property."""
        return self._operator

    @operator.setter
    def operator(self, is_op: bool) -> None:
        """Set operator property."""
        if not isinstance(is_op, bool):
            raise TypeError("operator must be a boolean")
        self._operator = is_op

    @property
    def distance(self) -> typing.Optional[int]:
        """Distance property."""
        return self._distance

    @distance.setter
    def distance(self, dist: typing.Optional[int]) -> None:
        """Set distance property."""
        if not dist:
            return
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
        """Set children property."""
        if not isinstance(children, list):
            raise TypeError("children must be a list of Query objects")
        self._children = children

    def add_child(self, child: typing.Union[str, Query]) -> None:
        """Add child to the query."""
        if isinstance(child, str):
            self._children.append(
                Query(child, operator=False, search_field=self.search_field)
            )
        elif isinstance(child, Query):
            self._children.append(child)
        else:
            raise TypeError("Children must be Query objects or strings")

    @property
    def search_field(self) -> typing.Optional[SearchField]:
        """Search field property."""
        return self._search_field

    @search_field.setter
    def search_field(self, sf: typing.Optional[SearchField]) -> None:
        """Set search field property."""
        self._search_field = sf

    def selects(self, *, record_dict: dict) -> bool:
        """Indicates whether the query selects a given record."""

        if self.value == Operators.NOT:
            return not self.children[0].selects(record_dict=record_dict)

        if self.value == Operators.AND:
            return all(x.selects(record_dict=record_dict) for x in self.children)

        if self.value == Operators.OR:
            return any(x.selects(record_dict=record_dict) for x in self.children)

        assert not self.operator

        if self.search_field is None:
            raise ValueError("Search field not set")

        if self.search_field.value == Fields.TITLE:
            field_value = record_dict.get("title", "").lower()
        elif self.search_field.value == Fields.ABSTRACT:
            field_value = record_dict.get("abstract", "").lower()
        else:
            raise ValueError(f"Invalid search field: {self.search_field}")

        value = self.value.lower().lstrip('"').rstrip('"')

        # Handle wildcards
        if "*" in value:
            pattern = re.compile(value.replace("*", ".*").lower())
            match = pattern.search(field_value)
            return match is not None

        # Match exact word
        return value.lower() in field_value

    def is_operator(self) -> bool:
        """Check whether the SearchQuery is an operator."""
        return self.operator

    def is_term(self) -> bool:
        """Check whether the SearchQuery is a term."""
        return not self.is_operator()

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
