#!/usr/bin/env python3
"""Web-of-Science query linter."""

import re

from search_query.constants import WOSRegex
# vielleichtr regex in constants.py packen und dann jeweil importieren?

class QueryLinter:
    """Linter for wos query"""
    def __init__(self, search_str: str, linter_messages: dict):
        self.search_str = search_str
        self.linter_messages = linter_messages

    def pre_linting(self, tokens: list) -> bool:
        """Performs a pre-linting"""
        return (self._check_unmatched_parentheses() or
                self._check_order_of_tokens(tokens))

    def _check_unmatched_parentheses(self) -> bool:
        """Check for unmatched parentheses in the query."""
        unmatched_parentheses  = False
        stack = []
        for i, char in enumerate(self.search_str):
            if char == "(":
                stack.append(i)
            elif char == ")":
                if stack:
                    stack.pop()
                else:
                    unmatched_parentheses = True
                    self.linter_messages.append({
                        "rule": "UnmatchedParenthesis",
                        "message": "Unmatched closing parenthesis ')'.",
                        "position": (i, i+1)
                    })

        for unmatched_index in stack:
            unmatched_parentheses = True
            self.linter_messages.append({
                "rule": "UnmatchedParenthesis",
                "message": "Unmatched opening parenthesis '('.",
                "position": (unmatched_index, unmatched_index+1)
            })

        return unmatched_parentheses

    def _check_order_of_tokens(self, tokens: list) -> bool:
        missplaced_order = False
        index = 0
        while index < len(tokens) - 1:
            token, span = tokens[index]
            # Check for two operators in a row
            if (
                re.match(WOSRegex.OPERATOR_REGEX, token) and
                re.match(WOSRegex.OPERATOR_REGEX, tokens[index+1][0])
            ):
                self.linter_messages.append({
                    "rule": "TwoOperatorInRow",
                    "message": "Two operators in a row.",
                    "position": tokens[index+1][1]
                })
                missplaced_order = True

            #Check for two search fields in a row
            if (
                re.match(WOSRegex.SEARCH_FIELD_REGEX, token) and
                re.match(WOSRegex.SEARCH_FIELD_REGEX, tokens[index+1][0])
            ):
                self.linter_messages.append({
                    "rule": "TwoSearchFieldsInRow",
                    "message": "Two Search Fields in a row.",
                    "position": tokens[index+1][1]
                })
                missplaced_order = True

            # Check for opening parenthesis after term
            if (
                (
                    not re.match(WOSRegex.SEARCH_FIELD_REGEX, token) and
                    not re.match(WOSRegex.OPERATOR_REGEX, token) and
                    not re.match(WOSRegex.PARENTHESIS_REGEX, token) and
                    re.match(WOSRegex.TERM_REGEX, token)
                ) and
                    (tokens[index+1][0] == "(")
            ):
                self.linter_messages.append({
                    "rule": "ParenthesisAfterTerm",
                    "message": "Missing Operator between term and parenthesis.",
                    "position": span
                })
                missplaced_order = True

            # Check for closing parenthesis after term
            if (
                (token == ")") and
                    (
                        not re.match(WOSRegex.SEARCH_FIELD_REGEX, tokens[index+1][0]) and
                        not re.match(WOSRegex.OPERATOR_REGEX, tokens[index+1][0]) and
                        not re.match(WOSRegex.PARENTHESIS_REGEX, tokens[index+1][0]) and
                        re.match(WOSRegex.TERM_REGEX, tokens[index+1][0])
                    )
                ):
                self.linter_messages.append({
                    "rule": "ParenthesisBeforeTerm",
                    "message": "Missing Operator between term and parenthesis.",
                    "position": tokens[index+1][1]
                })
                missplaced_order = True
            index += 1

        return missplaced_order

    def _check_near_operator_format(self, query):
        """Check for NEAR without a specified distance."""
        # if "NEAR" in query and not any(x in query for x in ["NEAR/", "NEAR /"]):
        #     self.linter_messages.append({
        #         "rule": "MissingDistance",
        #         "message": "NEAR operator is missing a specified distance (e.g., NEAR/5).",
        #         "position": query.find("NEAR")
        #     })
