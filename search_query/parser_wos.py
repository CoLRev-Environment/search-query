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

    TERM_REGEX = r'"[^"]+"|[\w\*]+(?:\*[\w]*)*' # Matches quoted text or standalone words
    OPERATOR_REGEX = r'\b(AND|OR|NOT)\b'        # Matches operators as standalone words only
    SEARCH_FIELD_REGEX = r'\[\w+\]|\b\w{2}='    # Matches [ab] or ab= style search fields
    PARENTHESIS_REGEX = r'[\(\)]'               # Matches parentheses
    # ...

    pattern = "|".join(
        [
            SEARCH_FIELD_REGEX,
            OPERATOR_REGEX,
            PARENTHESIS_REGEX,
            TERM_REGEX,
            # ...
        ]
    )

    def tokenize(self) -> None:
        """Tokenize the query_str."""
        print('Start tokenize query.')
        # Parse tokens and positions based on regex pattern
        compile_pattern = re.compile(pattern=self.pattern)
        matches = compile_pattern.finditer(self.query_str)

        for match in matches:
            self.tokens.append((match.group(), match.span()))
            print(match)

        token_types = self.get_token_types(tokens=self.tokens, legend=False)

        print(token_types)

        # only to know the pattern: self.tokens = [("token_1", (0, 4))]

    # Implement and override methods of parent class (as needed)
    def is_search_field(self, token: str) -> bool:
        """Token is search field"""
        return re.match(self.SEARCH_FIELD_REGEX, token)


    def parse_query_tree(
            self,
            tokens: list,
            search_field: typing.Optional[SearchField] = None,
    ) -> Query:
        """Parse a query from a list of tokens."""
        print('Start create query tree.')
        def parse_expression(tokens, index):
            """Parse tokens starting at the given index, handling parentheses and operators recursively."""
            children = []
            search_field = None
            while index < len(tokens):
                token, span = tokens[index]
                # span = tokens[index][1]

                # Handle nested expressions within parentheses
                if token == '(':
                    sub_expr, index = parse_expression(tokens, index + 1)
                    children.append(sub_expr)
                elif token == ')':
                    return Query(type='EXPRESSION', value=None, children=children), index
                elif self.is_operator(token):

                    # Operator nodes in the query tree
                    op_type = 'AND' if token == 'AND' else 'OR' if token == 'OR' else 'NOT' if token == 'NOT' else 'MSCI'

                    # Append operator with right-hand side expression
                    right, index = parse_expression(tokens, index + 1)
                    children.append(Query(type=op_type, value=token, children=[children.pop(), right]))
                else:
                    # Regular term or search field
                    if self.is_search_field(token):
                        search_field = token
                    else:
                        # Append a term node
                        children.append(Query(value= token, operator=False, search_field=(search_field), children=[]))
                index += 1
            return Query(value=None, operator=False, search_field=(search_field), children=children), index

        # Start parsing from the first token
        root_query, _ = parse_expression(tokens, 0)
        return root_query
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