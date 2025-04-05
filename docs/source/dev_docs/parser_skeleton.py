#!/usr/bin/env python3
"""XY query parser."""
from __future__ import annotations

import re
import typing

from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_TRANSLATION_MAP
from search_query.constants import QueryErrorCode
from search_query.constants import TokenTypes
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField


class XYParser(QueryStringParser):
    """Parser for XY queries."""

    FIELD_TRANSLATION_MAP = PLATFORM_FIELD_TRANSLATION_MAP[PLATFORM.XY]

    PARENTHESIS_REGEX = r"[\(\)]"
    LOGIC_OPERATOR_REGEX = r"\b(AND|OR|NOT)\b"
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
        for match in re.finditer(self.pattern, self.query_str):
            token = match.group()
            token = token.strip()
            start, end = match.span()

            # Determine token type
            if re.fullmatch(self.PARENTHESIS_REGEX, token):
                if token == "(":
                    token_type = TokenTypes.PARENTHESIS_OPEN
                else:
                    token_type = TokenTypes.PARENTHESIS_CLOSED
            elif re.fullmatch(self.LOGIC_OPERATOR_REGEX, token):
                token_type = TokenTypes.LOGIC_OPERATOR
            # ...
            else:
                self.add_linter_message(QueryErrorCode.TOKENIZING_FAILED, (start, end))
                continue

            self.tokens.append((token, token_type, (start, end)))

    # Override methods of parent class (as needed)

    def parse_query_tree(
        self,
        tokens: list,
        search_field: typing.Optional[SearchField] = None,
    ) -> Query:
        """Parse a query from a list of tokens."""

        # Parse a query tree from tokens (bottom-up or top-down)

        # Add messages to self.linter_messages
        # self.add_linter_message(QueryErrorCode.ADD_CODE, (start, end))

    def translate_search_fields(self, query: Query) -> None:
        """Translate search fields."""

        # Translate search fields to standard names using self.FIELD_TRANSLATION_MAP

        # Add messages to self.linter_messages if needed
        # self.add_linter_message(QueryErrorCode.ADD_CODE, (start, end))

    def parse(self) -> Query:
        """Parse a query string."""

        self.tokenize()
        self.add_artificial_parentheses_for_operator_precedence()

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

    # Override methods of parent class (as needed)

    # The parse() method of QueryListParser is called to parse the list of queries
