#!/usr/bin/env python3
"""EBSCO query parser."""
from __future__ import annotations

import re

from search_query.parser_base import QueryStringParser
from search_query.parser_base import QueryListParser
from search_query.query import Query


class QueryStringValidator():

    FAULTY_OPERATOR_REGEX = r"\b(?:[aA][nN][dD]|[oO][rR]|[nN][oO][tT])\b"
    PARENTHESIS_REGEX = r"[\(\)]"

    def check_operator(self) -> None:
        """Check for operators written in not all capital letter"""
        for match in re.finditer(self.FAULTY_OPERATOR_REGEX, self.query_str, flags=re.IGNORECASE):
            operator = match.group()
            start, end = match.span()
            self.query_str = (
                self.query_str[:start] +
                operator.upper() +
                self.query_str[end:]
            )

    def check_parenthesis(self) -> None:
        """Check if the string has the same amount of "(" as well as ")" """
        open = 0
        close = 0
        for match in re.finditer(self.PARENTHESIS_REGEX, self.query_str):
            parenthesis = match.group()
            if parenthesis is "(":
                open = open + 1
            else:
                close = close + 1
        
        if open > close:
            print("Number of parenthesis do not match, there are more open parenthesis than close")
        elif close > open:
            print("Number of parenthesis do not match, there are more close parenthesis than open")



    

    