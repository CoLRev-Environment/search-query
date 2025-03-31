#!/usr/bin/env python3
"""XY query parser."""
from __future__ import annotations

import typing

from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_TRANSLATION_MAP
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField


class XYParser(QueryStringParser):
    """Parser for XY queries."""

    FIELD_TRANSLATION_MAP = PLATFORM_FIELD_TRANSLATION_MAP[PLATFORM.XY]

    SEARCH_FIELD_REGEX = r"..."
    OPERATOR_REGEX = r"..."
    # ...

    pattern = "|".join(
        [
            SEARCH_FIELD_REGEX,
            OPERATOR_REGEX,
            # ...
        ]
    )

    OPERATOR_PRECEDENCE = {
        # ...
    }

    def get_precedence(self, token: str) -> int:
        """Returns operator precedence for logical and proximity operators."""

        # Change precedence or add operators
        # Implement and override methods of parent class (as needed)

    def tokenize(self) -> None:
        """Tokenize the query_str."""

        # Parse tokens and positions based on regex pattern

        self.tokens = [("token_1", (0, 4))]

    # Implement and override methods of parent class (as needed)

    def parse_query_tree(
        self,
        tokens: list,
        search_field: typing.Optional[SearchField] = None,
    ) -> Query:
        """Parse a query from a list of tokens."""

        # Parse a query tree from tokens recursively

        # Add messages to self.linter_messages

    def translate_search_fields(self, query: Query) -> None:
        """Translate search fields."""

        # Translate search fields to standard names using self.FIELD_TRANSLATION_MAP

        # Add messages to self.linter_messages if needed

    def parse(self) -> Query:
        """Parse a query string."""
        self.tokenize()
        _, tokens = self.add_artificial_parentheses_for_operator_precedence(
            tokens=self.tokens
        )
        query = self.parse_query_tree(self.tokens)
        self.translate_search_fields(query)

        # If self.mode == "strict", raise exception if self.linter_messages is not empty

        return query


class XYListParser(QueryListParser):
    """Parser for XY (list format) queries."""

    LIST_ITEM_REGEX = r"..."

    def __init__(self, query_list: str) -> None:
        super().__init__(query_list, XYParser)

    def get_token_str(self, token_nr: str) -> str:
        return f"#{token_nr}"

    # override and implement methods of parent class (as needed)

    # the parse() method of QueryListParser is called to parse the list of queries


# Add exceptions to exception.py (e.g., XYInvalidFieldTag, XYSyntaxMissingSearchField)
