#!/usr/bin/env python3
"""EBSCO query parser."""
from __future__ import annotations

import re
import typing

from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_TRANSLATION_MAP
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.parser_validation import QueryStringValidator
from search_query.query import Query
from search_query.query import SearchField


class EBSCOParser(QueryStringParser):
    """Parser for EBSCO queries."""

    FIELD_TRANSLATION_MAP = PLATFORM_FIELD_TRANSLATION_MAP[PLATFORM.EBSCO]

    SEARCH_FIELD_REGEX = r"\b(TI|AU|TX|AB|SO|SU|IS|IB)"
    UNSUPPORTED_SEARCH_FIELD_REGEX = (
        r"\b(?!OR\b)\b(?!S\d+\b)[A-Z]{2}\b|\b(?!OR\b)\b(?!S\d+\b)[A-Z]{1}\d+\b"
    )
    OPERATOR_REGEX = r"^(AND|OR|NOT)$"
    PARENTHESIS_REGEX = r"[\(\)]"
    SEARCH_TERM_REGEX = r"\"[^\"]+\"|\b(?!S\d\b)\S+\*?\b"

    pattern = "|".join(
        [SEARCH_FIELD_REGEX, OPERATOR_REGEX, PARENTHESIS_REGEX, SEARCH_TERM_REGEX]
    )

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

    # def validate_token_sequence(self, tokens: list) -> None:
    #     """Perform forward parsing to validate the token sequence."""
    #     stack = []  # To validate parentheses pairing
    #     previous_token_type = None

    #     for token, token_type, position in tokens:
    #         # Validate transitions
    #         self.validate_token_position(token_type, previous_token_type, position)

    #         # Handle parentheses pairing
    #         if token_type == "PARENTHESIS_OPEN":
    #             stack.append(position)  # Track the position of the opening parenthesis
    #         elif token_type == "PARENTHESIS_CLOSED":
    #             if not stack:
    #                 self.linter_messages.append({
    #                     "level": "Error",
    #                     "msg": f"Unmatched closing parenthesis at position {position}.",
    #                     "pos": position,
    #                 })
    #                 raise ValueError(f"Unmatched closing parenthesis at position {position}.")
    #             stack.pop()  # Remove the matching opening parenthesis

    #         # Update the previous token type
    #         previous_token_type = token_type

    #     # Check for unmatched opening parentheses
    #     if stack:
    #         self.linter_messages.append({
    #             "level": "Error",
    #             "msg": f"Unmatched opening parenthesis at positions {stack}",
    #             "pos": None,
    #         })
    #         raise ValueError(f"Unmatched opening parenthesis at positions {stack}.")

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

    def tokenize(self) -> None:
        """Tokenize the query_str."""
        self.tokens = []

        if self.query_str is None:
            self.linter_messages.append(
                {
                    "level": "Fatal",
                    "msg": "tokenizing-failed: empty string",
                    "pos": None,
                }
            )
            raise ValueError("No string provided to parse.")

        previous_token_type = None
        token_type = None

        for match in re.finditer(self.pattern, self.query_str):
            token = match.group()
            start, end = match.span()

            # Determine token type
            if re.fullmatch(self.SEARCH_FIELD_REGEX, token):
                token_type = "FIELD"
            elif re.fullmatch(self.OPERATOR_REGEX, token):
                token_type = "OPERATOR"
            elif re.fullmatch(self.PARENTHESIS_REGEX, token):
                if token == "(":
                    token_type = "PARENTHESIS_OPEN"
                else:
                    token_type = "PARENTHESIS_CLOSED"
            elif re.fullmatch(self.SEARCH_TERM_REGEX, token):
                token_type = "SEARCH_TERM"
            else:
                self.linter_messages.append(
                    {
                        "level": "Fatal",
                        "msg": f"tokenizing-failed: '{token}' not supported",
                        "pos": (start, end),
                    }
                )
                continue

            self.validate_token_position(token_type, previous_token_type, (start, end))
            previous_token_type = token_type

            # Append token with its type and position to self.tokens
            self.tokens.append((token, token_type, (start, end)))
            # print(
            #    f"Tokenized: {token} as {token_type} at position {start}-{end}"
            # )   # ->   Debug line

    def parse_query_tree(
        self,
        tokens: list,
        search_field: typing.Optional[SearchField] = None,
    ) -> Query:
        """Build a query tree from a list of tokens recursively."""

        if not tokens:
            self.linter_messages.append(
                {
                    "level": "Fatal",
                    "msg": "parsing-failed: empty tokens",
                    "pos": None,
                }
            )
            # Build exception for this case
            raise ValueError("Parsing failed: No tokens provided to parse.")

        root = None
        current_operator = None

        while tokens:
            token, token_type, position = tokens.pop(0)
            # print(f"Processing token: {token} (Type: {token_type}, Position: {position})")  # Debug line

            if token_type == "FIELD":
                search_field = SearchField(token, position=position)

            elif token_type == "SEARCH_TERM":
                term_node = Query(
                    value=token, operator=False, search_field=search_field
                )
                if current_operator:
                    current_operator.children.append(term_node)
                elif root is None:
                    root = term_node
                else:
                    root.children.append(term_node)

            elif token_type == "OPERATOR":
                if current_operator and current_operator.value == token:
                    pass
                else:
                    new_operator_node = Query(
                        value=token, operator=True, position=position
                    )
                    if root:
                        new_operator_node.children.append(root)
                    root = new_operator_node
                    current_operator = new_operator_node

            elif token_type == "PARENTHESIS_OPEN":
                # Recursively parse the group inside parentheses
                subtree = self.parse_query_tree(tokens, search_field)
                if current_operator:
                    current_operator.children.append(subtree)
                elif root:
                    root.children.append(subtree)
                else:
                    root = subtree

            elif token_type == "PARENTHESIS_CLOSED" and root:
                return root

        # check if root is None to always return Query
        if root is None:
            # Build exception for this case
            raise ValueError("Failed to construct a valid query tree.")

        return root

    def translate_search_fields(self, query: Query) -> None:
        """Translate search fields to standard names using self.FIELD_TRANSLATION_MAP"""

        # Error not included in linting, mainly for programming purposes
        if not hasattr(self, "FIELD_TRANSLATION_MAP") or not isinstance(
            self.FIELD_TRANSLATION_MAP, dict
        ):
            raise AttributeError(
                "FIELD_TRANSLATION_MAP is not defined or is not a dictionary."
            )

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

        self.linter_messages.clear()

        strict = False

        self.filter_search_field(strict)

        # Create an instance of QueryStringValidator
        validator = QueryStringValidator(self.query_str, self.linter_messages)

        # Call validation methods
        validator.check_operator()
        validator.check_parenthesis()

        # Update the query string and messages after validation
        self.query_str = validator.query_str
        self.linter_messages.extend(validator.linter_messages)

        # Tokenize the search string
        self.tokenize()
        # Parse query on basis of tokens and recursively build a query-tree
        query = self.parse_query_tree(self.tokens)
        # Translate EBSCO host search_fields into standardized search_fields
        self.translate_search_fields(query)

        return query


class EBSCOListParser(QueryListParser):
    """Parser for EBSCO (list format) queries."""

    def __init__(self, query_list: str) -> None:
        """Initialize with a query list and use EBSCOParser for parsing each query."""
        super().__init__(query_list, EBSCOParser)

    def get_token_str(self, token_nr: str) -> str:
        """Format the token string for output or processing."""

        pattern = rf"(S|#){token_nr}"

        match = re.search(pattern, self.query_list)

        if match:
            # Return the preceding character if found
            return f"{match.group(1)}{token_nr}"

        # Log a linter message and return the token number
        self.linter_messages.append(
            {
                "level": "Warning",
                "msg": "Connecting lines possibly failed. Please use this format for connection: S1 OR S2 OR S3 / #1 OR #2 OR #3",
                "pos": None,
            }
        )
        return token_nr

    # override and implement methods of parent class (as needed)

    # the parse() method of QueryListParser is called to parse the list of queries


# Add exceptions to exception.py (e.g., XYInvalidFieldTag, XYSyntaxMissingSearchField)
