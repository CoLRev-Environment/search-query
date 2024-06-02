#!/usr/bin/env python3
"""Query linter."""
from __future__ import annotations

import typing

from search_query.constants import Colors
from search_query.query import Query


class QueryLinter:
    """Query linter class"""

    def __init__(self) -> None:
        self.msgs: typing.List[str] = []

    def get_position_range(self, query: Query) -> tuple:
        """Get the position range of the query."""
        if not query.children:
            if query.position:
                return query.position
            return 0, 0

        left_range = query.children[0]
        while left_range.children:
            left_range = left_range.children[0]
        right_range = query.children[-1]
        while right_range.children:
            right_range = right_range.children[-1]
        start, end = 0, 0
        if left_range.position:
            start, _ = left_range.position
        if right_range.position:
            _, end = right_range.position

        return start, end

    def _validate_alphabetical_order_children(self, query: Query) -> None:
        for index in range(len(query.children) - 1):
            if query.children[index].operator or query.children[index + 1].operator:
                continue
            if query.children[index].value > query.children[index + 1].value:
                position_range = self.get_position_range(query)
                self.msgs.append(
                    "Alphabetical order is not maintained for the query: "
                    f"{query.to_string()} (position: {position_range})"
                )
                for i, child in enumerate(query.children):
                    if (
                        i < len(query.children) - 1
                        and child.value.lower()
                        > query.children[index + 1].value.lower()
                    ):
                        query.children[index].color = Colors.ORANGE
                        query.children[index + 1].color = Colors.ORANGE

    def validate_alphabetical_order(self, query: Query) -> None:
        """Validate the alphabetical order of the query."""
        if not query.children:
            return

        if query.value in ["AND", "OR"]:
            self._validate_alphabetical_order_children(query)
        for child in query.children:
            self.validate_alphabetical_order(child)

    def mark_query_string(self, query: str, position: tuple) -> str:
        """Mark the query string."""
        start, end = position
        query = query[: end - 1] + Colors.END + query[end - 1 :]
        query = query[: start - 1] + Colors.ORANGE + query[start - 1 :]
        return query
