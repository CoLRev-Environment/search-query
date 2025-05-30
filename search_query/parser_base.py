#!/usr/bin/env python3
"""Base query parser."""
from __future__ import annotations

import re
import typing
from abc import ABC
from abc import abstractmethod

from search_query.constants import LinterMode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.query import Query

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.linter_base import QueryStringLinter


class QueryStringParser(ABC):
    """Abstract base class for query string parsers"""

    # Note: override the following:
    OPERATOR_REGEX: re.Pattern = re.compile(r"^(AND|OR|NOT)$", flags=re.IGNORECASE)

    linter: QueryStringLinter

    def __init__(
        self,
        query_str: str,
        *,
        search_field_general: str = "",
        mode: str = LinterMode.STRICT,
    ) -> None:
        self.query_str = query_str
        self.tokens: list = []
        self.mode = mode
        # The external search_fields (in the JSON file: "search_field")
        self.search_field_general = search_field_general

    def print_tokens(self) -> None:
        """Print the tokens in a formatted table."""
        for token in self.tokens:
            # UNKNOWN could be color-coded
            print(f"{token.value:<30} {token.type:<40} {str(token.position):<10}")

    def combine_subsequent_terms(self) -> None:
        """Combine all consecutive SEARCH_TERM tokens into one."""
        combined_tokens = []
        i = 0
        while i < len(self.tokens):
            if self.tokens[i].type == TokenTypes.SEARCH_TERM:
                start = self.tokens[i].position[0]
                value_parts = [self.tokens[i].value]
                end = self.tokens[i].position[1]
                i += 1
                while (
                    i < len(self.tokens)
                    and self.tokens[i].type == TokenTypes.SEARCH_TERM
                ):
                    value_parts.append(self.tokens[i].value)
                    end = self.tokens[i].position[1]
                    i += 1
                combined_token = Token(
                    value=" ".join(value_parts),
                    type=TokenTypes.SEARCH_TERM,
                    position=(start, end),
                )
                combined_tokens.append(combined_token)
            else:
                combined_tokens.append(self.tokens[i])
                i += 1

        self.tokens = combined_tokens

    def split_operators_with_missing_whitespace(self) -> None:
        """Split operators that are not separated by whitespace."""
        # This is a workaround for the fact that some platforms do not support
        # operators without whitespace, e.g. "AND" or "OR"
        # This is not a problem for the parser, but for the linter
        # which expects whitespace between operators and search terms

        i = 0
        while i < len(self.tokens) - 1:
            token = self.tokens[i]
            next_token = self.tokens[i + 1]

            appended_operator_match = re.search(r"(AND|OR|NOT)$", token.value)

            # if the end of a search term (value) is a capitalized operator
            # without a whitespace, split the tokens
            if (
                token.type == TokenTypes.SEARCH_TERM
                and next_token.type != TokenTypes.LOGIC_OPERATOR
                and appended_operator_match
            ):
                # Split the operator from the search term

                appended_operator = appended_operator_match.group(0)
                token.value = token.value[: -len(appended_operator)]
                token.position = (
                    token.position[0],
                    token.position[1] - len(appended_operator),
                )
                # insert operator token afterwards
                operator_token = Token(
                    value=appended_operator,
                    type=TokenTypes.LOGIC_OPERATOR,
                    position=(
                        token.position[1],
                        token.position[1] + len(appended_operator),
                    ),
                )
                self.tokens.insert(i + 1, operator_token)

                i += 2  # Skip over the newly inserted operator token
            else:
                i += 1

    @abstractmethod
    def parse(self) -> Query:
        """Parse the query."""


class QueryListParser:
    """QueryListParser"""

    LIST_ITEM_REGEX: re.Pattern = re.compile(r"^(\d+).\s+(.*)$")

    def __init__(
        self,
        query_list: str,
        *,
        parser_class: type[QueryStringParser],
        search_field_general: str,
        mode: str = LinterMode.STRICT,
    ) -> None:
        self.query_list = query_list
        self.parser_class = parser_class
        self.search_field_general = search_field_general
        self.mode = mode
        self.query_dict: dict = {}

    @abstractmethod
    def tokenize_list(self) -> None:
        """Tokenize the query_list."""

    @abstractmethod
    def parse(self) -> Query:
        """Parse the query in list format."""
