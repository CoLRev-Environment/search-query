#!/usr/bin/env python3
"""Base query parser."""
from __future__ import annotations

import re
import typing
from abc import ABC
from abc import abstractmethod

from search_query.constants import LinterMode
from search_query.constants import ListTokenTypes
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

    def tokenize_list(self) -> None:
        """Tokenize the query_list."""
        query_list = self.query_list
        previous = 0
        for line in query_list.split("\n"):
            if line.strip() == "":
                continue

            match = self.LIST_ITEM_REGEX.match(line)
            if not match:  # pragma: no cover
                raise ValueError(f"line not matching format: {line}")
            node_nr, node_content = match.groups()
            pos_start, pos_end = match.span(2)
            pos_start += previous
            pos_end += previous
            self.query_dict[str(node_nr)] = {
                "node_content": node_content,
                "content_pos": (pos_start, pos_end),
                "type": ListTokenTypes.OPERATOR_NODE
                if "#" in node_content
                else ListTokenTypes.QUERY_NODE,
            }
            previous += len(line) + 1

    @abstractmethod
    def parse(self) -> Query:
        """Parse the query in list format."""
