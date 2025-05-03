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

if typing.TYPE_CHECKING:
    from search_query.linter_base import QueryStringLinter


class QueryStringParser(ABC):
    """Abstract base class for query string parsers"""

    # Higher number=higher precedence
    PRECEDENCE = {"NOT": 2, "AND": 1, "OR": 0}
    # Note: override the following:
    OPERATOR_REGEX = r"^(AND|and|OR|or|NOT|not)$"

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

    @classmethod
    @abstractmethod
    def to_generic_syntax(cls, query: Query, *, search_field_general: str) -> Query:
        """Convert the query to a generic syntax.

        Typical steps:

        # standard_key and variation_regex
        PREPROCESSING_MAP = {
            "TI=": r"TI=|Title=",
        }


        # Map standard_syntax_str to set of generic_search_field_set
        SYNTAX_GENERIC_MAP = {
            "TIAB=": {"TI=", "AB="},
            "TI=": {"TI="},
            "AB=": {"AB="},
            "TP=": {"TP="},
            "ATP=": {"TP="},
            "WOSTP=": {"TP="},
        }

        def map_to_standard(syntax_str: str) -> set:
            for standard_key, variation_regex in PREPROCESSING_MAP.items():
                if re.match(variation_regex, syntax_str, flags=re.IGNORECASE):
                    return standard_key
            return "default"

        def syntax_str_to_generic_search_field_set(syntax_str: str) -> set:
            standard_syntax_str = map_to_standard(syntax_str)
            generic_search_field_set = SYNTAX_GENERIC_MAP[standard_syntax_str]
            return generic_search_field_set

        def convert_search_fields(cls, query: Query) -> Qeury:

            if query.search_field:
                # Convert the search field to a generic syntax
                search_field = query.search_field.value
                generic_search_field_set =
                    syntax_str_to_generic_search_field_set(search_field)
                query.search_field = SearchField(
                    value=generic_search_field_set,
                    position=query.search_field.position,
                )
            # Convert the children recursively
            for child in query.children:
                if isinstance(child, Query):
                    query.children = cls.convert_search_fields(child)

            return query

        def to_generic_syntax(cls, query: Query, *, search_field_general: str) -> Query:

            # Handle special cases (such as [ti:~5])

            # Recursively convert the query
            # by using syntax_str_to_generic_search_field_set



        """

    @classmethod
    @abstractmethod
    def to_specific_syntax(cls, query: Query) -> Query:
        """Convert the query to a specific syntax."""

    def combine_subsequent_terms(self) -> None:
        """Combine subsequent terms in the list of tokens."""
        # Combine subsequent terms (without quotes)
        # This would be more challenging in the regex
        combined_tokens = []
        i = 0
        while i < len(self.tokens):
            if (
                i + 1 < len(self.tokens)
                and self.tokens[i].type == TokenTypes.SEARCH_TERM
                and self.tokens[i + 1].type == TokenTypes.SEARCH_TERM
            ):
                combined_token = Token(
                    value=self.tokens[i].value + " " + self.tokens[i + 1].value,
                    type=TokenTypes.SEARCH_TERM,
                    position=(
                        self.tokens[i].position[0],
                        self.tokens[i + 1].position[1],
                    ),
                )
                combined_tokens.append(combined_token)
                i += 2
            else:
                combined_tokens.append(self.tokens[i])
                i += 1

        self.tokens = combined_tokens

    def get_precedence(self, token: str) -> int:
        """Returns operator precedence for logical and proximity operators."""

        if token in self.PRECEDENCE:
            return self.PRECEDENCE[token]
        return -1  # Not an operator

    @abstractmethod
    def parse(self) -> Query:
        """Parse the query."""


class QueryListParser:
    """QueryListParser"""

    LIST_ITEM_REGEX = r"^(\d+).\s+(.*)$"

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

            match = re.match(self.LIST_ITEM_REGEX, line)
            if not match:
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

    def get_token_str(self, token_nr: str) -> str:
        """Get the token string."""
        raise NotImplementedError(
            "get_token_str method must be implemented by inheriting classes"
        )

    def _replace_token_nr_by_query(
        self, query_list: list, token_nr: str, token_content: dict
    ) -> None:
        for i, (content, pos) in enumerate(query_list):
            token_str = self.get_token_str(token_nr)
            if token_str in content:
                query_list.pop(i)

                content_before = content[: content.find(token_str)]
                content_before_pos = (pos[0], pos[0] + len(content_before))
                content_after = content[content.find(token_str) + len(token_str) :]
                content_after_pos = (
                    content_before_pos[1] + len(token_str),
                    content_before_pos[1] + len(content_after) + len(token_str),
                )

                new_content = token_content["node_content"]
                new_pos = token_content["content_pos"]

                if content_after:
                    query_list.insert(i, (content_after, content_after_pos))

                # Insert the sub-query from the list with "artificial parentheses"
                # (positions with length 0)
                query_list.insert(i, (")", (-1, -1)))
                query_list.insert(i, (new_content, new_pos))
                query_list.insert(i, ("(", (-1, -1)))

                if content_before:
                    query_list.insert(i, (content_before, content_before_pos))

                break

    def dict_to_positioned_list(self) -> list:
        """Convert a node to a positioned list."""

        root_node = list(self.query_dict.values())[-1]
        query_list = [(root_node["node_content"], root_node["content_pos"])]

        for token_nr, token_content in reversed(self.query_dict.items()):
            # iterate over query_list if token_nr is in the content,
            # split the content and insert the token_content, updating the content_pos
            self._replace_token_nr_by_query(query_list, token_nr, token_content)

        return query_list

    @abstractmethod
    def parse(self) -> Query:
        """Parse the query in list format."""
