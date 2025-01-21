#!/usr/bin/env python3
"""EBSCO query parser."""
from __future__ import annotations

import re
import typing

from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_TRANSLATION_MAP
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.parser_validation import EBSCOQueryStringValidator
from search_query.parser_validation import QueryStringValidator
from search_query.query import Query
from search_query.query import SearchField


class EBSCOParser(QueryStringParser):
    """Parser for EBSCO queries."""

    FIELD_TRANSLATION_MAP = PLATFORM_FIELD_TRANSLATION_MAP[PLATFORM.EBSCO]

    PARENTHESIS_REGEX = r"[\(\)]"
    LOGIC_OPERATOR_REGEX = r"\b(AND|OR|NOT)\b"
    PROXIMITY_OPERATOR_REGEX = r"(N|W)\d+"
    SEARCH_FIELD_REGEX = r"\b(TI|AU|TX|AB|SO|SU|IS|IB)\b"
    SEARCH_TERM_REGEX = r"\"[^\"]*\"|\b(?!S\d+\b)[^()\s]+[\*\+\?]?"

    pattern = "|".join(
        [
            PARENTHESIS_REGEX,
            LOGIC_OPERATOR_REGEX,
            PROXIMITY_OPERATOR_REGEX,
            SEARCH_FIELD_REGEX,
            SEARCH_TERM_REGEX,
        ]
    )

    def combine_subsequent_tokens(self) -> None:
        """Combine subsequent tokens based on specific conditions."""
        if not self.tokens:
            return

        combined_tokens = []
        i = 0

        while i < len(self.tokens):
            # Iterate through token list
            current_token, current_token_type, position = self.tokens[i]

            if current_token_type == "SEARCH_TERM":
                # Filter out search_term
                start_pos = position[0]
                end_position = position[1]
                combined_value = current_token

                while (
                    i + 1 < len(self.tokens) and self.tokens[i + 1][1] == "SEARCH_TERM"
                ):
                    # Iterate over subsequent search_terms and combine
                    next_token, _, next_position = self.tokens[i + 1]
                    combined_value += f" {next_token}"
                    end_position = next_position[1]
                    i += 1

                combined_tokens.append(
                    (combined_value, current_token_type, (start_pos, end_position))
                )

            else:
                combined_tokens.append((current_token, current_token_type, position))

            i += 1

        self.tokens = combined_tokens

    def convert_proximity_operators(
        self, token: str, token_type: str
    ) -> tuple[str, int]:
        """Convert proximity operator token into operator and distance components"""
        if token_type != "PROXIMITY_OPERATOR":
            raise ValueError(
                f"Invalid token type: {token_type}. Expected 'PROXIMITY_OPERATOR'."
            )

        # Extract the operator (first character) and distance (rest of the string)
        operator = token[:1]
        distance_string = token[1:]

        # Change value of operator to fit construction of operator query
        if operator == "N":
            operator = "NEAR"
        else:
            operator = "WITHIN"

        # Validate and convert the distance
        if not distance_string.isdigit():
            raise ValueError(
                f"Invalid proximity operator format: '{token}'. "
                "Expected a number after the operator."
            )

        distance = int(distance_string)
        return operator, distance

    def tokenize(self) -> None:
        """Tokenize the query_str."""

        if self.query_str is None:
            raise ValueError("No string provided to parse.")

        self.tokens = []

        validator = EBSCOQueryStringValidator(
            self.query_str, self.search_fields_general
        )
        validator.filter_search_field(
            strict=False
        )  # strict should be changed to strict.mode
        self.query_str = validator.query_str
        self.linter_messages.extend(validator.linter_messages)

        validator.check_search_fields_general(strict=True)
        self.linter_messages.extend(validator.linter_messages)

        previous_token_type = None
        token_type = None

        for match in re.finditer(self.pattern, self.query_str):
            token = match.group()
            token = token.strip()
            # print("This token is being processed: " + token)   # -> Debug line
            start, end = match.span()

            # Determine token type
            if re.fullmatch(self.PARENTHESIS_REGEX, token):
                if token == "(":
                    token_type = "PARENTHESIS_OPEN"
                else:
                    token_type = "PARENTHESIS_CLOSED"
            elif re.fullmatch(self.LOGIC_OPERATOR_REGEX, token):
                token_type = "LOGIC_OPERATOR"
            elif re.fullmatch(self.PROXIMITY_OPERATOR_REGEX, token):
                token_type = "PROXIMITY_OPERATOR"
            elif re.fullmatch(self.SEARCH_FIELD_REGEX, token):
                token_type = "FIELD"
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

            # Validate token positioning to ensure logical structure
            validator.validate_token_position(
                token_type, previous_token_type, (start, end)
            )
            # Set token_type for continoued validation
            previous_token_type = token_type
            self.linter_messages.extend(validator.linter_messages)

            # Append token with its type and position to self.tokens
            self.tokens.append((token, token_type, (start, end)))
            # print(
            #    f"Tokenized: {token} as {token_type} at position {start}-{end}"
            # )   # ->   Debug line

        # Combine subsequent search_terms in case of no quotation marks
        self.combine_subsequent_tokens()

    def create_operator_node(
        self,
        token: str,
        operator: bool,
        position: tuple[int, int],
        search_field: typing.Optional[SearchField],
        distance: typing.Optional[int],
    ) -> Query:
        """Create new Query node"""
        return Query(
            value=token,
            operator=operator,
            position=position,
            search_field=search_field,
            distance=distance,
        )

    def parse_query_tree(
        self,
        tokens: list,
        search_field: typing.Optional[SearchField] = None,
    ) -> Query:
        """
        Build a query tree from a list of tokens
        dynamic tree restructuring for precedence (NOT -> AND -> OR).
        """
        if not tokens:
            self.linter_messages.append(
                {
                    "level": "Fatal",
                    "msg": "parsing-failed: empty tokens",
                    "pos": None,
                }
            )
            raise ValueError("Parsing failed: No tokens provided to parse.")

        precedence = {"NOT": 3, "AND": 2, "OR": 1}  # Higher number=higher precedence
        root = None
        current_operator = None

        while tokens:
            token, token_type, position = tokens.pop(0)

            if token_type == "FIELD":
                # Create new search_field used by following search_terms
                search_field = SearchField(token, position=position)

            elif token_type == "SEARCH_TERM":
                # Create new search_term and in case tree is empty, sets first root
                term_node = self.create_operator_node(
                    token, False, position, search_field, None
                )
                if current_operator:
                    current_operator.children.append(term_node)
                elif root is None:
                    root = term_node
                else:
                    root.children.append(term_node)

            elif token_type == "PROXIMITY_OPERATOR":
                # Split token into NEAR/WITHIN and distance
                operater_value = self.convert_proximity_operators(token, token_type)
                token = operater_value[0]
                distance = operater_value[1]

                # Create new proximity_operator from token (N3, W1, N13, ...)
                proximity_node = self.create_operator_node(
                    token, True, position, search_field, distance
                )

                # Set proximity_operator as tree node
                if root:
                    proximity_node.children.append(root)
                root = proximity_node
                current_operator = proximity_node

            elif token_type == "LOGIC_OPERATOR":
                # Same operator: Append subsequent operands directly
                if current_operator and current_operator.value == token:
                    continue

                # Create new operator node
                new_operator_node = self.create_operator_node(
                    token, True, position, search_field, None
                )

                if not current_operator:
                    # No current operator; initialize root
                    if root:
                        new_operator_node.children.append(root)
                    root = new_operator_node
                    current_operator = new_operator_node
                elif precedence[token] > precedence[current_operator.value]:
                    # Higher precedence:
                    #   pop child from previous operator
                    #   append to new operator and new operator takes place of child
                    #   functions then as current operator
                    new_operator_node.children.append(current_operator.children.pop())
                    current_operator.children.append(new_operator_node)
                    current_operator = new_operator_node
                else:
                    # Lower precedence:
                    # if operator is same as token, sets tree depth back one layer
                    # ensures correct logical nesting
                    if root and root.value == token:
                        current_operator = root
                    else:
                        # if not same, still sets back one layer,
                        # however, creates new node element
                        if root:
                            root.children.append(new_operator_node)
                            current_operator = new_operator_node
                        else:
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

            elif token_type == "PARENTHESIS_CLOSED":
                if root is None:
                    raise ValueError("Parsing failed: Unmatched closing parenthesis.")
                return root

        if root is None:
            raise ValueError("Failed to construct a valid query tree.")

        return root

    def translate_search_fields(self, query: Query) -> None:
        """
        Translate search fields to standard names using self.FIELD_TRANSLATION_MAP
        """

        # Error not included in linting, mainly for programming purposes
        if not hasattr(self, "FIELD_TRANSLATION_MAP") or not isinstance(
            self.FIELD_TRANSLATION_MAP, dict
        ):
            raise AttributeError(
                "FIELD_TRANSLATION_MAP is not defined or is not a dictionary."
            )

        # Filter out search_fields and translate based on FIELD_TRANSLATION_MAP
        if query.search_field:
            original_value = query.search_field.value
            translated_value = self.FIELD_TRANSLATION_MAP.get(
                original_value, original_value
            )
            query.search_field.value = translated_value

        # Iterate through queries
        for child in query.children:
            self.translate_search_fields(child)

    def print_linter_messages(self, linter_messages: list[dict]) -> None:
        """
        Print linter messages in a readable format.

        :param linter_messages: List of linter message dictionaries.
        """
        if not linter_messages:
            print("No linter messages to display.")
            return

        print("Linter Messages:")
        print("-" * 50)

        for message in linter_messages:
            if not isinstance(message, dict):
                print(f"Invalid message format: {message}")
                continue

            level = message.get("level", "Unknown Level")
            msg = message.get("msg", "No message provided")
            pos = message.get("pos", "Position not specified")

            print(f"Level: {level}")
            print(f"Message: {msg}")
            print(f"Position: {pos}")
            print("-" * 50)

    def parse(self) -> Query:
        """Parse a query string."""

        self.linter_messages.clear()

        # Create an instance of QueryStringValidator
        validator = QueryStringValidator(self.query_str, self.search_fields_general)

        # Call validation methods
        validator.check_operator()
        self.linter_messages.extend(validator.linter_messages)

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

        self.print_linter_messages(self.linter_messages)

        return query


class EBSCOListParser(QueryListParser):
    """Parser for EBSCO (list format) queries."""

    def __init__(self, query_list: str, search_fields_general: str) -> None:
        """Initialize with a query list and use EBSCOParser for parsing each query."""
        super().__init__(query_list, search_fields_general, EBSCOParser)

    def get_token_str(self, token_nr: str) -> str:
        """Format the token string for output or processing."""

        # Match string combinators such as S1 AND S2 ... ; #1 AND #2 ; ...
        pattern = rf"(S|#){token_nr}"

        match = re.search(pattern, self.query_list)

        if match:
            # Return the preceding character if found
            return f"{match.group(1)}{token_nr}"

        # Log a linter message and return the token number
        # 1 AND 2 ... are still possible,
        # however for standardization purposes it should be S/#
        self.linter_messages.append(
            {
                "level": "Warning",
                "msg": (
                    "Connecting lines possibly failed."
                    "Please use this format for connection:"
                    "S1 OR S2 OR S3 / #1 OR #2 OR #3"
                ),
                "pos": None,
            }
        )
        return token_nr

    # the parse() method of QueryListParser is called to parse the list of queries


# Add exceptions to exception.py (e.g., XYInvalidFieldTag, XYSyntaxMissingSearchField)


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
#                 raise ValueError(
#                   f"Unmatched closing parenthesis at position {position}."
# )
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
