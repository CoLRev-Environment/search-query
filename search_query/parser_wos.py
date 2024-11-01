#!/usr/bin/env python3
"""Web-of-Science query parser."""
from __future__ import annotations

import typing
import re

from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_TRANSLATION_MAP
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField


class WOSParser(QueryStringParser):
    """Parser for Web-of-Science queries."""

    FIELD_TRANSLATION_MAP = PLATFORM_FIELD_TRANSLATION_MAP[PLATFORM.WOS]

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
        query = self.parse_query_tree(self.tokens)
        self.translate_search_fields(query)

        # If self.mode == "strict", raise exception if self.linter_messages is not empty

        return query


class WOSListParser(QueryListParser):
    """Parser for Web-of-Science (list format) queries."""

    LIST_ITEM_REGEX = r"..."

    def __init__(self, query_list: str) -> None:
        super().__init__(query_list, WOSParser)

    def get_token_str(self, token_nr: str) -> str:
        return f"#{token_nr}"

    # override and implement methods of parent class (as needed)

    # the parse() method of QueryListParser is called to parse the list of queries


# Add exceptions to exception.py (e.g., XYInvalidFieldTag, XYSyntaxMissingSearchField)