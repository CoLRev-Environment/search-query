#!/usr/bin/env python3
"""EBSCO query parser."""
from __future__ import annotations

import re

class QueryStringValidator():
    """Class for Query String Validation"""

    FAULTY_OPERATOR_REGEX = r"\b(?:[aA][nN][dD]|[oO][rR]|[nN][oO][tT])\b"
    # FAULTY_OPERATOR_REGEX = r"(?<=\s)\b(?!(AND|OR|NOT)\b)\b(?:[aA][nN][dD]|[oO][rR]|[nN][oO][tT])\b(?=\s)"
    PARENTHESIS_REGEX = r"[\(\)]"

    def __init__(self, query_str: str, linter_messages: list):
        self.query_str = query_str
        self.linter_messages = linter_messages

    def check_operator(self) -> None:
        """Check for operators written in not all capital letters."""
        for match in re.finditer(self.FAULTY_OPERATOR_REGEX, self.query_str, flags=re.IGNORECASE):
            operator = match.group()
            start, end = match.span()
            operator_changed = False
            if operator != operator.upper():
                self.query_str = (
                    self.query_str[:start] +
                    operator.upper() +
                    self.query_str[end:]
                )
                operator_changed = True
            
            if operator_changed == True:
                self.linter_messages.append({
                    "level": "Warning",
                    "msg": f"Operator '{operator}' automatically capitalized",
                    "pos": (start, end),
                })

    def check_parenthesis(self) -> None:
        """Check if the string has the same amount of "(" as well as ")"."""
        open_count = 0
        close_count = 0
        for match in re.finditer(self.PARENTHESIS_REGEX, self.query_str):
            parenthesis = match.group()
            if parenthesis == "(":
                open_count += 1
            if parenthesis == ")":
                close_count += 1
        
        if open_count != close_count:
            print("Unbalanced parenthesis")
            self.linter_messages.append({
                "level": "Fatal",
                "msg": f"Unbalanced parentheses: open = {open_count}, close = {close_count}",
                "pos": "",
            })

    def check_operator_position(self) -> None:
        """Check string if operator is in wrong position"""
        raise NotImplementedError(
            "parse method must be implemented by inheriting classes"
        )
 

class QueryListValidator():
    """Class for Query List Validation"""

    def __init__(self, query_list: str, linter_messages: list):
        self.query_list = query_list
        self.linter_messages = linter_messages

    def check_string_connector(self) -> None:
        """Check string combination, e.g., replace #1 OR #2 -> S1 OR S2."""
        raise NotImplementedError(
            "parse method must be implemented by inheriting classes"
        )

    def check_comments(self) -> None:
        """Check last string for possible commentary -> add to file commentary"""
        raise NotImplementedError(
            "parse method must be implemented by inheriting classes"
        )






    

    