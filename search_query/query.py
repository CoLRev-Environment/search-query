#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations

import typing
from abc import ABC
from abc import abstractmethod

from search_query.node import Node


class Query(ABC, Node):
    """Query class."""

    # pylint: disable=too-many-arguments
    @abstractmethod
    def __init__(
        self,
        *,
        operator: str,
        children: typing.List[typing.Union[str, Node, Query]],
        search_field: str = "Abstract",
        position: typing.Optional[tuple] = None,
        color: str = "",
    ) -> None:
        """init method - abstract"""

        Node.__init__(
            self,
            value=operator,
            operator=True,
            search_field=search_field,
            position=position,
            color=color,
        )
        self._build_query_node(operator, children, search_field)

    def _build_query_node(
        self,
        operator: str,
        children: typing.List[typing.Union[str, Node, Query]],
        search_field: str,
    ) -> None:
        """parse the query provided, build nodes&tree structure"""
        assert operator in ["AND", "OR", "NOT"]
        for item in children:
            if isinstance(item, str):
                term_node = Node(item, operator=False, search_field=search_field)
                self.children.append(term_node)
            elif isinstance(item, Query):
                self.children.append(item)
            elif isinstance(item, Node):
                self.children.append(item)
            else:
                raise ValueError(f"Invalid search term ({item})")

        # Mark nodes to prevent circular references
        self.mark()
        # Remove marks
        self.remove_marks()
