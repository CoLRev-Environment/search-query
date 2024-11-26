#!/usr/bin/env python3
"""Web-of-Science query linter."""

from search_query.query import Query


class QueryLinter:
    """Linter for wos query"""
    def __init__(self, search_str: str, linter_messages: dict):
        self.search_str = search_str
        self.linter_messages = linter_messages

    def pre_linting(self) -> bool:
        """Performs a pre-linting"""
        return (self._check_unmatched_parentheses())

    def lint_query(self, search_query: Query):
        """
        Lints the given query. In strict mode, does not modify the query
        but logs issues to the linter messages list.

        :param query: The input query string to lint.
        :param strict_mode: If True, does not modify the query.
        :return: The original query (strict mode) or a modified query (non-strict mode).
        """
        if not isinstance(search_query, Query):
            raise ValueError("Search query must be a Query.")

        # Example rule: Check for missing NEAR/x distance
        self._check_near_operator_format(search_query)

        # Example rule: Check for unmatched parentheses
        self._check_unmatched_parentheses()
    
    def _check_near_operator_format(self, query):
        """Check for NEAR without a specified distance."""
        # if "NEAR" in query and not any(x in query for x in ["NEAR/", "NEAR /"]):
        #     self.linter_messages.append({
        #         "rule": "MissingDistance",
        #         "message": "NEAR operator is missing a specified distance (e.g., NEAR/5).",
        #         "position": query.find("NEAR")
        #     })

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
