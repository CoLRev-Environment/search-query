"""Linter for Crossref API queries."""
from __future__ import annotations

from search_query.constants import PLATFORM
from search_query.generic.linter import GenericLinter


class CrossrefLinter(GenericLinter):
    """Use generic query-tree validation for Crossref queries."""

    PLATFORM = PLATFORM.CROSSREF

    def __init__(
        self,
        query_str: str = "",
        *,
        silent: bool = False,
        ignore_failing_linter: bool = False,
    ) -> None:
        super().__init__(
            query_str=query_str,
            ignore_failing_linter=ignore_failing_linter,
        )
        self.silent = silent
