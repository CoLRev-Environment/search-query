#!/usr/bin/env python3
"""EBSCO query parser."""
from __future__ import annotations

import re
import typing

from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_TRANSLATION_MAP
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField


class EBSCOParser(QueryStringParser):
    """Parser for EBSCO queries."""

    FIELD_TRANSLATION_MAP = PLATFORM_FIELD_TRANSLATION_MAP[PLATFORM.EBSCO]

    SEARCH_FIELD_REGEX = r"\b(TI|AU|TX|AB)"
    OPERATOR_REGEX = r"^(AND|OR|NOT)$"
    PARENTHESIS_REGEX = r"[\(\)]"
    SEARCH_TERM_REGEX = r"\"[^\"]+\"|\b\S+\*?\b"

    pattern = "|".join(
        [SEARCH_FIELD_REGEX, OPERATOR_REGEX, PARENTHESIS_REGEX, SEARCH_TERM_REGEX]
    )

    def tokenize(self) -> None:
        """Tokenize the query_str."""
        self.tokens = []

        for match in re.finditer(self.pattern, self.query_str):
            token = match.group()
            start, end = match.span()

            # Determine token type
            if re.fullmatch(self.SEARCH_FIELD_REGEX, token):
                token_type = "FIELD"
            elif re.fullmatch(self.OPERATOR_REGEX, token):
                token_type = "OPERATOR"
            elif re.fullmatch(self.PARENTHESIS_REGEX, token):
                token_type = "PARENTHESIS"
            elif re.fullmatch(self.SEARCH_TERM_REGEX, token):
                token_type = "SEARCH_TERM"
            else:
                continue

            # Append token with its type and position to self.tokens
            self.tokens.append((token, token_type, (start, end)))
            print(
               f"Tokenized: {token} as {token_type} at position {start}-{end}"
            )   # ->   Debug line

    def parse_query_tree(
        self,
        tokens: list,
        search_field: typing.Optional[SearchField] = None,
    ) -> Query:
        """Build a query tree from a list of tokens recursively."""
        if not tokens:
            raise ValueError("No tokens provided to parse.")

        root = None

        while tokens:
            token, token_type, position = tokens.pop(0)

            if token_type == "FIELD":
                search_field = SearchField(token, position=position)

            elif token_type == "SEARCH_TERM":
                term_node = Query(
                    value=token, operator=False, search_field=search_field
                )

                if root is None:
                    root = term_node
                else:
                    root.children.append(term_node)

            elif token_type == "OPERATOR":
                operator_node = Query(value=token, operator=True, position=position)

                if root:
                    operator_node.children.append(root)
                root = operator_node

            elif token_type == "PARENTHESIS":
                if token == "(":
                    # Recursively parse the group inside parentheses
                    subtree = self.parse_query_tree(tokens, search_field)
                    if root:
                        root.children.append(subtree)
                    else:
                        root = subtree
                elif token == ")" and root:
                    return root

        # check if root is None to always return Query
        if root is None:
            raise ValueError("Failed to construct a valid query tree.")

        return root

    def translate_search_fields(self, query: Query) -> None:
        """Translate search fields to standard names using self.FIELD_TRANSLATION_MAP"""

        if query.search_field:
            original_value = query.search_field.value
            translated_value = self.FIELD_TRANSLATION_MAP.get(
                original_value, original_value
            )
            query.search_field.value = translated_value

        for child in query.children:
            self.translate_search_fields(child)

    def parse(self) -> Query:
        """Parse a query string."""
        self.tokenize()
        query = self.parse_query_tree(self.tokens)
        self.translate_search_fields(query)

        # Check for strict mode and handle linter messages if any
        # if self.mode == "strict" and self.linter_messages:
        #     raise ValueError("Linter messages indicate issues with query structure.")

        return query


class EBSCOListParser(QueryListParser):
    """Parser for EBSCO (list format) queries."""

    LIST_ITEM_REGEX = r"\d+\.\s|\n"

    def __init__(self, query_list: str) -> None:
        """Initialize with a query list and use EBSCOParser for parsing each query."""
        super().__init__(query_list, EBSCOParser)

    def parse(self) -> list[Query]:
        """Parse the list of queries and return a list of parsed Query objects."""
        queries = re.split(self.LIST_ITEM_REGEX, self.query_list)

        # Parse each individual query and collect the results
        parsed_queries = []
        for i, query_str in enumerate(queries):
            if query_str.strip():
                parser = EBSCOParser(query_str.strip())
                parsed_query = parser.parse()
                parsed_queries.append(parsed_query)

        return parsed_queries

    def get_token_str(self, token_nr: str) -> str:
        """Format the token string for output or processing."""
        return f"#{token_nr}"

    # override and implement methods of parent class (as needed)

    # the parse() method of QueryListParser is called to parse the list of queries


# Add exceptions to exception.py (e.g., XYInvalidFieldTag, XYSyntaxMissingSearchField)
