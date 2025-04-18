#! /usr/bin/env python
"""Exceptions of SearchQuery."""
from __future__ import annotations

import typing

import search_query.utils
from search_query.constants import Colors


class SearchQueryException(Exception):
    """
    Base class for all exceptions raised by this package
    """


class QuerySyntaxError(SearchQueryException):
    """QuerySyntaxError Exception"""

    def __init__(self, msg: str, query_string: str, position: tuple) -> None:
        # Error position marked in orange
        query_string_highlighted = search_query.utils.format_query_string_pos(
            query_string, position
        )
        self.message = f"{msg}\n{query_string_highlighted}"
        self.position = position
        self.query_string = query_string
        super().__init__(self.message)


class FatalLintingException(SearchQueryException):
    """FatalLintingException Exception"""

    def __init__(
        self, message: str, query_string: str, messages: typing.List[dict]
    ) -> None:
        # Error positions marked in orange
        query_string_highlighted = query_string

        # need to sort the messages
        sorted_messages = sorted(messages, key=lambda x: x["position"][0], reverse=True)

        for msg in sorted_messages:
            query_string_highlighted = search_query.utils.format_query_string_pos(
                query_string_highlighted, msg["position"], color=Colors.RED
            )
        self.message = f"{message}\n{query_string_highlighted}"
        self.query_string = query_string
        super().__init__(self.message)
