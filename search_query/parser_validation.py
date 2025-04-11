#!/usr/bin/env python3
"""Validator for search queries."""
from __future__ import annotations

import re

import search_query.parser_base
from search_query.constants import QueryErrorCode


# Could indeed be a general Validator class
class QueryStringValidator:
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

    def check_operator(self) -> None:
        """Check for operators written in not all capital letters."""

        for match in re.finditer(
            self.FAULTY_OPERATOR_REGEX, self.query_str, flags=re.IGNORECASE
        ):
            operator = match.group()
            start, end = match.span()
            if operator != operator.upper():
                self.query_str = (
                    self.query_str[:start] + operator.upper() + self.query_str[end:]
                )

                self.parser.add_linter_message(
                    QueryErrorCode.OPERATOR_CAPITALIZATION,
                    (start, end),
                )

    def check_parenthesis(self) -> None:
        """Check if the string has the same amount of '(' as well as ')'."""

        open_count = 0
        close_count = 0

        for match in re.finditer(self.PARENTHESIS_REGEX, self.query_str):
            parenthesis = match.group()

            if parenthesis == "(":
                open_count += 1

            if parenthesis == ")":
                close_count += 1

        if open_count != close_count:
            self.parser.add_linter_message(QueryErrorCode.UNBALANCED_PARENTHESES, ())


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
