#!/usr/bin/env python3
"""Validator for search queries."""
from __future__ import annotations

import re

import search_query.parser_base
from search_query.constants import QueryErrorCode
from search_query.constants import TokenTypes


# Could indeed be a general Validator class
class QueryStringLinter:
    """Class for Query String Validation"""

    FAULTY_OPERATOR_REGEX = r"\b(?:[aA][nN][dD]|[oO][rR]|[nN][oO][tT])\b"
    PARENTHESIS_REGEX = r"[\(\)]"

    def __init__(
        self,
        parser: search_query.parser_base.QueryStringParser,
    ):
        self.query_str = parser.query_str
        self.search_field_general = parser.search_field_general
        self.parser = parser

    def check_operator_capitalization(self) -> None:
        """Check if operators are capitalized."""
        for token in self.parser.tokens:
            if re.match(self.parser.OPERATOR_REGEX, token.value):
                if token.value != token.value.upper():
                    self.parser.add_linter_message(
                        QueryErrorCode.OPERATOR_CAPITALIZATION,
                        position=token.position,
                    )
                    token.value = token.value.upper()

    def check_unbalanced_parentheses(self) -> None:
        """Check query for unbalanced parentheses."""
        i = 0
        for token in self.parser.tokens:
            if token.type == TokenTypes.PARENTHESIS_OPEN:
                i += 1
            if token.type == TokenTypes.PARENTHESIS_CLOSED:
                if i == 0:
                    self.parser.add_linter_message(
                        QueryErrorCode.UNBALANCED_PARENTHESES,
                        position=token.position,
                    )
                else:
                    i -= 1
        if i > 0:
            # Query contains unbalanced opening parentheses
            i = 0
            for token in reversed(self.parser.tokens):
                if token.type == TokenTypes.PARENTHESIS_CLOSED:
                    i += 1
                if token.type == TokenTypes.PARENTHESIS_OPEN:
                    if i == 0:
                        self.parser.add_linter_message(
                            QueryErrorCode.UNBALANCED_PARENTHESES,
                            position=token.position,
                        )
                    else:
                        i -= 1


class QueryListValidator:
    """Class for Query List Validation"""

    def __init__(self, query_list: str, search_field_general: str):
        self.query_list = query_list
        self.search_field_general = search_field_general

    # Possible validations to be implemented in the future
    def check_string_connector(self) -> None:
        """Check string combination, e.g., replace #1 OR #2 -> S1 OR S2."""
        raise NotImplementedError("not yet implemented")

    def check_comments(self) -> None:
        """Check string for comments -> add to file comments"""
        raise NotImplementedError("not yet implemented")
