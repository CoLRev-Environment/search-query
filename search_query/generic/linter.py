#!/usr/bin/env python3
"""Linter for generic queries."""
from __future__ import annotations

import re
import typing

from search_query.constants import Fields
from search_query.constants import PLATFORM
from search_query.constants import Token
from search_query.linter_base import QueryStringLinter

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.query import Query


class GenericLinter(QueryStringLinter):
    """Linter for Generic Query Strings"""

    PLATFORM: PLATFORM = PLATFORM.GENERIC

    # Extract unique string values
    field_codes = {
        v
        for k, v in vars(Fields).items()
        if not k.startswith("__") and isinstance(v, str)
    }

    VALID_fieldS_REGEX = re.compile(r"\b(?:" + "|".join(sorted(field_codes)) + r")\b")

    def __init__(
        self,
        query_str: str = "",
        *,
        ignore_failing_linter: bool = False,
    ) -> None:
        super().__init__(
            query_str=query_str, ignore_failing_linter=ignore_failing_linter
        )

    def syntax_str_to_generic_field_set(self, field_value: str) -> set:
        """Translate a search field"""
        # Note: generic-to-generic translation is not needed
        return set()  # pragma: no cover

    def validate_tokens(
        self,
        *,
        tokens: typing.List[Token],
        query_str: str,
        field_general: str = "",
    ) -> typing.List[Token]:
        """Performs a pre-linting"""

        # Note: not needed

        return []  # pragma: no cover

    def validate_query_tree(self, query: Query) -> None:
        """
        Validate the query tree.
        This method is called after the query tree has been built.
        """

        self.check_unsupported_fields_in_query(query)
