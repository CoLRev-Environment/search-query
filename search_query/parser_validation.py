#!/usr/bin/env python3
"""EBSCO query parser."""
from __future__ import annotations

import re
import typing


class QueryStringValidator:
    """Class for Query String Validation"""

    FAULTY_OPERATOR_REGEX = r"\b(?:[aA][nN][dD]|[oO][rR]|[nN][oO][tT])\b"
    PARENTHESIS_REGEX = r"[\(\)]"

    def __init__(self, query_str: str, linter_messages: typing.List[dict] = []):
        self.query_str = query_str
        self.linter_messages = linter_messages

    def check_operator(self) -> None:
        """Check for operators written in not all capital letters."""
        for match in re.finditer(
            self.FAULTY_OPERATOR_REGEX, self.query_str, flags=re.IGNORECASE
        ):
            operator = match.group()
            start, end = match.span()
            operator_changed = False
            if operator != operator.upper():
                self.query_str = (
                    self.query_str[:start] + operator.upper() + self.query_str[end:]
                )
                operator_changed = True

            if operator_changed is True:
                self.linter_messages.append(
                    {
                        "level": "Warning",
                        "msg": f"Operator '{operator}' automatically capitalized",
                        "pos": (start, end),
                    }
                )

    def check_parenthesis(self) -> None:
        """Check if the string has the same amount of "(" as well as ")"."""
        # stack = []  # To validate parentheses pairing
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
            self.linter_messages.append(
                {
                    "level": "Fatal",
                    "msg": f"Unbalanced parentheses: open = {open_count}, close = {close_count}",
                    "pos": "",
                }
            )


class EBSCOQueryStringValidator:
    """Class for EBSCO Query String Validation"""

    UNSUPPORTED_SEARCH_FIELD_REGEX = (
        r"\b(?!OR\b)\b(?!S\d+\b)[A-Z]{2}\b|\b(?!OR\b)\b(?!S\d+\b)[A-Z]{1}\d+\b"
    )

    def __init__(self, query_str: str, linter_messages: typing.List[dict] = []):
        self.query_str = query_str
        self.linter_messages = linter_messages

    def filter_search_field(self, strict: bool) -> None:
        """
        Filter out unsupported search_fields.
        Depending on strictness, automatically change or ask user
        """
        supported_fields = {"TI", "AU", "TX", "AB", "SO", "SU", "IS", "IB"}
        modified_query_list = list(
            self.query_str
        )  # Convert to list for direct modification
        unsupported_fields = []

        for match in re.finditer(self.UNSUPPORTED_SEARCH_FIELD_REGEX, self.query_str):
            field = match.group()
            start, end = match.span()

            if field not in supported_fields:
                unsupported_fields.append(field)
                if strict:
                    while True:
                        # Prompt the user to enter a replacement field
                        replacement = input(
                            f"Unsupported field '{field}' found. Please enter a replacement (e.g., 'AB'): "
                        ).strip()
                        if replacement in supported_fields:
                            # Replace directly in the modified query list
                            modified_query_list[start:end] = list(replacement)
                            print(f"Field '{field}' replaced with '{replacement}'.")
                            break
                        print(
                            f"'{replacement}' is not a supported field. Please try again."
                        )
                else:
                    # Replace the unsupported field with 'AB' directly
                    modified_query_list[start:end] = list("AB")
                    self.linter_messages.append(
                        {
                            "level": "Error",
                            "msg": f"search-field-unsupported: '{unsupported_fields}' automatically changed to Abstract AB.",
                            "pos": (start, end),
                        }
                    )

        # Convert the modified list back to a string
        self.query_str = "".join(modified_query_list)

        # Print the modified query string for verification
        # print("Modified query string:", self.query_str)

    def validate_token_position(
        self,
        token_type: str,
        previous_token_type: typing.Optional[str],
        position: typing.Optional[tuple[int, int]],
    ) -> None:
        """Validate the position of the current token based on its type and the previous token type."""

        if previous_token_type is None:
            # First token, no validation required
            return

        valid_transitions = {
            "FIELD": [
                "OPERATOR",
                "PARENTHESIS_OPEN",
            ],  # FIELD can follow an operator or open parenthesis
            "SEARCH_TERM": [
                "FIELD",
                "OPERATOR",
                "PARENTHESIS_OPEN",
            ],  # SEARCH_TERM can follow FIELD or OPERATOR
            "OPERATOR": [
                "SEARCH_TERM",
                "PARENTHESIS_CLOSED",
            ],  # OPERATOR must follow SEARCH_TERM or closing parenthesis
            "PARENTHESIS_OPEN": [
                "FIELD",
                "OPERATOR",
                "PARENTHESIS_OPEN",
            ],  # Handles open/close parentheses
            "PARENTHESIS_CLOSED": [
                "SEARCH_TERM",
                "PARENTHESIS_CLOSED",
            ],  # Handles open/close parentheses
        }

        if previous_token_type not in valid_transitions.get(token_type, []):
            print(
                f"\nInvalid token sequence: '{previous_token_type}' followed by '{token_type}' at position '{position}'"
            )
            self.linter_messages.append(
                {
                    "level": "Error",
                    "msg": f"Invalid token sequence: '{previous_token_type}' followed by '{token_type}'",
                    "pos": position,
                }
            )


class QueryListValidator:
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
