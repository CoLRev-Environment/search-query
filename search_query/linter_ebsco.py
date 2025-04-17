#!/usr/bin/env python3
"""Validator for search queries."""
from __future__ import annotations

import re

from search_query.constants import LinterMode
from search_query.constants import QueryErrorCode
from search_query.constants import TokenTypes
from search_query.linter_base import QueryStringLinter


class EBSCOQueryStringLinter(QueryStringLinter):
    """Class for EBSCO Query String Validation"""

    UNSUPPORTED_SEARCH_FIELD_REGEX = r"\b(?!OR\b)\b(?!S\d+\b)[A-Z]{2}\b"

    VALID_TRANSITIONS = {
        TokenTypes.FIELD: [
            TokenTypes.SEARCH_TERM,
            TokenTypes.PARENTHESIS_OPEN,
        ],  # After FIELD can be SEARCH_TERM; PARENTHESIS_OPEN
        TokenTypes.SEARCH_TERM: [
            TokenTypes.SEARCH_TERM,
            TokenTypes.LOGIC_OPERATOR,
            TokenTypes.PROXIMITY_OPERATOR,
            TokenTypes.PARENTHESIS_CLOSED,
        ],  # After SEARCH_TERM can be SEARCH_TERM (will get connected anyway);
        # LOGIC_OPERATOR; PROXIMITY_OPERATOR; PARENTHESIS_CLOSED
        TokenTypes.LOGIC_OPERATOR: [
            TokenTypes.SEARCH_TERM,
            TokenTypes.FIELD,
            TokenTypes.PARENTHESIS_OPEN,
        ],  # After LOGIC_OPERATOR can be SEARCH_TERM; FIELD; PARENTHESIS_OPEN
        TokenTypes.PROXIMITY_OPERATOR: [
            TokenTypes.SEARCH_TERM,
            TokenTypes.PARENTHESIS_OPEN,
            TokenTypes.FIELD,
        ],  # After PROXIMITY_OPERATOR can be SEARCH_TERM; PARENTHESIS_OPEN; FIELD
        TokenTypes.PARENTHESIS_OPEN: [
            TokenTypes.FIELD,
            TokenTypes.SEARCH_TERM,
            TokenTypes.PARENTHESIS_OPEN,
        ],  # After PARENTHESIS_OPEN can be FIELD; SEARCH_TERM; PARENTHESIS_OPEN
        TokenTypes.PARENTHESIS_CLOSED: [
            TokenTypes.PARENTHESIS_CLOSED,
            TokenTypes.LOGIC_OPERATOR,
            TokenTypes.PROXIMITY_OPERATOR,
        ],  # After PARENTHESIS_CLOSED can be PARENTHESIS_CLOSED;
        # LOGIC_OPERATOR; PROXIMITY_OPERATOR
    }

    def check_search_field_general(self) -> None:
        """Check field 'Search Fields' in content."""

        if self.search_field_general != "" and self.parser.mode == LinterMode.STRICT:
            self.parser.add_linter_message(QueryErrorCode.SEARCH_FIELD_EXTRACTED, ())

    def filter_search_field(self) -> None:
        """
        Filter out unsupported search_fields.
        Depending on strictness, automatically change or ask user
        """

        supported_fields = {
            "TI",
            "AU",
            "TX",
            "AB",
            "SO",
            "SU",
            "IS",
            "IB",
            "DE",
            "LA",
            "KW",
        }
        modified_query_list = list(
            self.parser.query_str
        )  # Convert to list for direct modification
        unsupported_fields = []

        for match in re.finditer(
            self.UNSUPPORTED_SEARCH_FIELD_REGEX, self.parser.query_str
        ):
            field = match.group()
            field = field.strip()
            start, end = match.span()

            # if escaped by quotes: continue (e.g., search term "AI")
            if self.parser.query_str[start - 1] == '"':
                continue

            if field not in supported_fields:
                unsupported_fields.append(field)
                if self.parser.mode == LinterMode.STRICT:
                    while True:
                        # Prompt the user to enter a replacement field
                        replacement = input(
                            f"Unsupported field '{field}' found. "
                            "Please enter a replacement (e.g., 'AB'): "
                        ).strip()
                        if replacement in supported_fields:
                            # Replace directly in the modified query list
                            modified_query_list[start:end] = list(replacement)
                            print(f"Field '{field}' replaced with '{replacement}'.")
                            break
                        print(
                            f"'{replacement}' is not a supported field. "
                            "Please try again."
                        )
                else:
                    # Replace the unsupported field with 'AB' directly
                    modified_query_list[start:end] = list("AB")
                    self.parser.add_linter_message(
                        QueryErrorCode.SEARCH_FIELD_UNSUPPORTED, (start, end)
                    )

        # Convert the modified list back to a string
        self.parser.query_str = "".join(modified_query_list)

    def validate_token_positions(self) -> None:
        """
        Validate the position of the current token
        based on its type and the previous token type.
        """

        for i, token in enumerate(self.parser.tokens):
            # Check the last token
            if i == len(self.parser.tokens):
                if self.parser.tokens[i - 1].type in [
                    TokenTypes.PARENTHESIS_OPEN,
                    TokenTypes.LOGIC_OPERATOR,
                    TokenTypes.SEARCH_TERM,
                ]:
                    self.parser.add_linter_message(
                        QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                        position=self.parser.tokens[i - 1].position,
                        details=f"Cannot end with {self.parser.tokens[i-1].type}",
                    )
                break

            token_type = token.type
            # Check the first token
            if i == 0:
                if token_type not in [
                    TokenTypes.SEARCH_TERM,
                    TokenTypes.FIELD,
                    TokenTypes.PARENTHESIS_OPEN,
                ]:
                    self.parser.add_linter_message(
                        QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                        position=token.position,
                        details=f"Cannot start with {token_type}",
                    )
                continue

            prev_type = self.parser.tokens[i - 1].type

            if token_type not in self.VALID_TRANSITIONS[prev_type]:
                if token_type == TokenTypes.FIELD:
                    details = "Invalid search field position"
                    position = token.position

                elif token_type == TokenTypes.LOGIC_OPERATOR:
                    details = "Invalid operator position"
                    position = token.position

                elif (
                    prev_type == TokenTypes.PARENTHESIS_OPEN
                    and token_type == TokenTypes.PARENTHESIS_CLOSED
                ):
                    details = "Empty parenthesis"
                    position = (
                        self.parser.tokens[i - 1].position[0],
                        token.position[1],
                    )

                elif (
                    token_type and prev_type and prev_type != TokenTypes.LOGIC_OPERATOR
                ):
                    details = "Missing operator"
                    position = (
                        self.parser.tokens[i - 1].position[0],
                        token.position[1],
                    )

                else:
                    details = ""
                    position = (
                        token.position
                        if token_type
                        else self.parser.tokens[i - 1].position
                    )

                self.parser.add_linter_message(
                    QueryErrorCode.INVALID_TOKEN_SEQUENCE,
                    position=position,
                    details=details,
                )
