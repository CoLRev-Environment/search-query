#! /usr/bin/env python
"""Exceptions of SearchQuery."""
from __future__ import annotations

import typing


if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.linter_base import QueryStringLinter, QueryListLinter


class SearchQueryException(Exception):
    """
    Base class for all exceptions raised by this package
    """


class QuerySyntaxError(SearchQueryException):
    """QuerySyntaxError Exception"""

    def __init__(self, linter: QueryStringLinter) -> None:
        self.linter = linter
        super().__init__()


class ListQuerySyntaxError(SearchQueryException):
    """ListQuerySyntaxError Exception"""

    def __init__(self, linter: QueryListLinter) -> None:
        self.linter = linter
        super().__init__()
