#! /usr/bin/env python
"""Exceptions of SearchQuery."""
from __future__ import annotations

import search_query.utils


class SearchQueryException(Exception):
    """
    Base class for all exceptions raised by this package
    """


class QuerySyntaxError(SearchQueryException):
    """QuerySyntaxError Exception"""

    def __init__(self, msg: str, query_string: str, pos: tuple) -> None:
        # Error position marked in orange
        query_string_highlighted = search_query.utils.format_query_string_pos(
            query_string, pos
        )
        self.message = f"{msg}\n{query_string_highlighted}"
        self.pos = pos
        self.query_string = query_string
        super().__init__(self.message)
