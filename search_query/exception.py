#! /usr/bin/env python
"""Exceptions of SearchQuery."""
from __future__ import annotations

import search_query.utils
from search_query.utils import Colors


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


class WOSError(SearchQueryException):
    """WOS Exception"""


class WOSInvalidFieldTag(WOSError, QuerySyntaxError):
    """WOSInvalidFieldTag Exception"""

    # def __init__(self, msg: str, query_string: str, pos: tuple) -> None:
    #     # print("Error position marked in orange")
    #     query_string_highlighted = \
    # search_query.utils.format_query_string_pos(query_string, pos)
    #     self.message = (
    #         f"QuerySyntaxError: {msg}\n{query_string_highlighted}"
    #     )
    #     super().__init__(self.message)


class WOSSyntaxMissingSearchField(WOSError, QuerySyntaxError):
    """WOSSyntaxMissingSearchField Exception"""

    def __init__(self, *, query_string: str, pos: tuple) -> None:
        # print("Error position marked in orange")
        # self.message = f"\n{query_string_highlighted}"
        self.message = (
            "Missing search field in WOS query "
            + f"({Colors.RED}TODO: ADD ERROR CODE/EXPLAIN IN DOCS{Colors.END}):"
        )
        super().__init__(self.message, query_string, pos)


class CrossrefError(SearchQueryException):
    """Crossref Exception"""


class CrossrefSyntaxMissingSearchField(CrossrefError, QuerySyntaxError):
    """CrossrefSyntaxMissingSearchField Exception"""

    def __init__(self, *, query_string: str, pos: tuple) -> None:
        # print("Error position marked in orange")
        # self.message = f"\n{query_string_highlighted}"
        self.message = (
            "Missing search field in Crossref query "
            + f"({Colors.RED}TODO: ADD ERROR CODE/EXPLAIN IN DOCS{Colors.END}):"
        )
        super().__init__(self.message, query_string, pos)
