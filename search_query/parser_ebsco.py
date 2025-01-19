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

    SEARCH_FIELD_REGEX = r"\b(TI|AU|TX|AB|SO|SU|IS|IB)\b"
    OPERATOR_REGEX = r"\b(AND|OR|NOT)\b"
    PARENTHESIS_REGEX = r"[\(\)]"
    SEARCH_TERM_REGEX = r"\"[^\"]*\"|\b(?!S\d\b)\S+\*?\b"

    pattern = "|".join(
        [PARENTHESIS_REGEX, OPERATOR_REGEX, SEARCH_FIELD_REGEX, SEARCH_TERM_REGEX]
    )

    def combine_subsequent_tokens(self) -> None:
        """Combine subsequent tokens based on specific conditions."""
        if not self.tokens:
            return

        combined_tokens = []
        i = 0

        while i < len(self.tokens):
            current_token, current_token_type, position = self.tokens[i]

            if current_token_type == "SEARCH_TERM":
                start_pos = position[0]
                end_position = position[1]
                combined_value = current_token

                while (
                    i + 1 < len(self.tokens) and self.tokens[i + 1][1] == "SEARCH_TERM"
                ):
                    next_token, _, next_position = self.tokens[i + 1]
                    combined_value += f" {next_token}"
                    print("This is the combined value: " + combined_value)
                    end_position = next_position[1]
                    i += 1

                combined_tokens.append(
                    (combined_value, current_token_type, (start_pos, end_position))
                )

            else:
                combined_tokens.append((current_token, current_token_type, position))

            i += 1

        self.tokens = combined_tokens

    def tokenize(self) -> None:
        """Tokenize the query_str."""
        self.tokens = []

        validator = EBSCOQueryStringValidator(self.query_str, self.linter_messages)
        validator.filter_search_field(
            strict=False
        )  # strict should be changed to strict.mode
        self.query_str = validator.query_str

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
            token = token.strip()
            # print("This token is being processed: " + token)   # -> Debug line
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

            validator.validate_token_position(
                token_type, previous_token_type, (start, end)
            )
            previous_token_type = token_type

            # Append token with its type and position to self.tokens
            self.tokens.append((token, token_type, (start, end)))
            # print(
            #    f"Tokenized: {token} as {token_type} at position {start}-{end}"
            # )   # ->   Debug line
        self.combine_subsequent_tokens()

    def create_operator_node(
        self,
        token: str,
        operator: bool,
        position: tuple[int, int],
        search_field: typing.Optional[SearchField],
    ) -> Query:
        return Query(
            value=token, operator=operator, position=position, search_field=search_field
        )

    def parse_query_tree(
        self,
        tokens: list,
        search_field: typing.Optional[SearchField] = None,
    ) -> Query:
        """Build a query tree from a list of tokens with dynamic tree restructuring for precedence."""
        if not tokens:
            self.linter_messages.append(
                {
                    "level": "Fatal",
                    "msg": "parsing-failed: empty tokens",
                    "pos": None,
                }
            )
            raise ValueError("Parsing failed: No tokens provided to parse.")

        precedence = {"NOT": 3, "AND": 2, "OR": 1}  # Higher number = higher precedence
        root = None
        current_operator = None

        while tokens:
            token, token_type, position = tokens.pop(0)
            # print(f"Processing token: {token} (Type: {token_type}, Position: {position})")  # Debug line

            if token_type == "FIELD":
                search_field = SearchField(token, position=position)

            elif token_type == "SEARCH_TERM":
                term_node = self.create_operator_node(
                    token, False, position, search_field
                )
                if current_operator:
                    current_operator.children.append(term_node)
                elif root is None:
                    root = term_node
                else:
                    root.children.append(term_node)

            elif token_type == "OPERATOR":
                if current_operator and current_operator.value == token:
                    # Same operator: Append subsequent operands directly
                    continue

                new_operator_node = self.create_operator_node(
                    token, True, position, search_field
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
                    # Lower precedence: if operator is same as token, sets tree depth back one layer
                    # ensures correct logical nesting
                    if root.value == token:
                        current_operator = root
                    else:
                        # if not same, still sets back one layer, however, creates new node element
                        root.children.append(new_operator_node)
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

        # for message in self.linter_messages:
        #     print(f"Level: {message['level']}")
        #     print(f"Message: {message['msg']}")
        #     if message['pos'] is not None:
        #         print(f"Position: {message['pos']}")
        #     else:
        #         print("Position: Not specified")
        #     print("-" * 50)  # Separator for readability

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
