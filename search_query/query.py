#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations

import re
import typing

from search_query.constants import Fields
from search_query.constants import Operators
from search_query.constants import PLATFORM
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
    ) -> None:
        """init method - abstract"""

        self.value = value
        self.operator = operator
        if operator:
            assert value in [
                Operators.AND,
                Operators.OR,
                Operators.NOT,
                "NOT_INITIALIZED",
            ]

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

        raise ValueError(f"Syntax not supported ({syntax})")
