#!/usr/bin/env python3
"""EBSCO query parser."""
from __future__ import annotations

import re
import typing

from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_TRANSLATION_MAP
from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes
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
    SEARCH_FIELD_REGEX = r"\b(TI|AU|TX|AB|SO|SU|IS|IB|DE|LA|KW)\b"
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

    OPERATOR_PRECEDENCE = {
        "NEAR": 3,
        "WITHIN": 3,
        "NOT": 2,
        "AND": 1,
        "OR": 0,
    }

    def combine_subsequent_tokens(self) -> None:
        """Combine subsequent tokens based on specific conditions."""
        if not self.tokens:
            return

        combined_tokens = []
        i = 0

        while i < len(self.tokens):
            # Iterate through token list
            # current_token, current_token_type, position = self.tokens[i]

            if self.tokens[i].type == TokenTypes.SEARCH_TERM:
                # Filter out search_term
                start_pos = self.tokens[i].position[0]
                end_position = self.tokens[i].position[1]
                combined_value = self.tokens[i].value

                while (
                    i + 1 < len(self.tokens)
                    and self.tokens[i + 1].type == TokenTypes.SEARCH_TERM
                ):
                    # Iterate over subsequent search_terms and combine
                    combined_value += f" {self.tokens[i + 1].value}"
                    end_position = self.tokens[i + 1].position[1]
                    i += 1

                combined_tokens.append(
                    Token(
                        value=combined_value,
                        type=self.tokens[i].type,
                        position=(start_pos, end_position),
                    )
                )

            else:
                combined_tokens.append(
                    Token(
                        value=self.tokens[i].value,
                        type=self.tokens[i].type,
                        position=self.tokens[i].position,
                    )
                )

            i += 1

        self.tokens = combined_tokens

    def convert_proximity_operators(
        self, token: str, token_type: str
    ) -> tuple[str, int]:
        """Convert proximity operator token into operator and distance components"""
        if token_type != TokenTypes.PROXIMITY_OPERATOR:
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

    def is_search_field(self, token: str) -> bool:
        """Check if the token is a valid search field."""
        return re.fullmatch(self.SEARCH_FIELD_REGEX, token) is not None

    def get_precedence(self, token: str) -> int:
        """Returns operator precedence for logical and proximity operators."""

        if token.startswith("N"):
            return self.OPERATOR_PRECEDENCE["NEAR"]
        if token.startswith("W"):
            return self.OPERATOR_PRECEDENCE["WITHIN"]
        if token in self.OPERATOR_PRECEDENCE:
            return self.OPERATOR_PRECEDENCE[token]
        return -1  # Not an operator

    def tokenize(self) -> None:
        """Tokenize the query_str."""

        if self.query_str is None:
            raise ValueError("No string provided to parse.")

        strict = False
        # Commented for automatic testing, after pull-request is done, please uncomment
        # if self.mode == "strict":
        #     strict = True

        self.tokens = []

        validator = EBSCOQueryStringValidator(self)
        validator.filter_search_field(strict)
        self.query_str = validator.query_str

        validator.check_search_field_general(strict=self.mode)

        previous_token_type = None
        token_type = None

        for match in re.finditer(self.pattern, self.query_str):
            value = match.group()
            value = value.strip()
            start, end = match.span()

            # Determine token type
            if re.fullmatch(self.PARENTHESIS_REGEX, value):
                if value == "(":
                    token_type = TokenTypes.PARENTHESIS_OPEN
                else:
                    token_type = TokenTypes.PARENTHESIS_CLOSED
            elif re.fullmatch(self.LOGIC_OPERATOR_REGEX, value):
                token_type = TokenTypes.LOGIC_OPERATOR
            elif re.fullmatch(self.PROXIMITY_OPERATOR_REGEX, value):
                token_type = TokenTypes.PROXIMITY_OPERATOR
            elif re.fullmatch(self.SEARCH_FIELD_REGEX, value):
                token_type = TokenTypes.FIELD
            elif re.fullmatch(self.SEARCH_TERM_REGEX, value):
                token_type = TokenTypes.SEARCH_TERM
            else:
                self.add_linter_message(QueryErrorCode.TOKENIZING_FAILED, (start, end))
                continue

            # Validate token positioning to ensure logical structure
            validator.validate_token_position(
                token_type, previous_token_type, (start, end)
            )
            # Set token_type for continoued validation
            previous_token_type = token_type

            # Append token with its type and position to self.tokens
            self.tokens.append(
                Token(value=value, type=token_type, position=(start, end))
            )

        # Combine subsequent search_terms in case of no quotation marks
        self.combine_subsequent_tokens()

    # pylint: disable=too-many-arguments
    def create_query_node(
        self,
        token: str,
        operator: bool = False,
        position: typing.Optional[tuple] = None,
        search_field: typing.Optional[SearchField] = None,
        distance: typing.Optional[int] = None,
        search_field_par: typing.Optional[SearchField] = None,
    ) -> Query:
        """Create new Query node"""

        # Handles case if search_field was created for entire parentheses
        if not search_field and search_field_par is not None:
            search_field = search_field_par

        return Query(
            value=token,
            operator=operator,
            position=position,
            search_field=search_field,
            distance=distance,
        )

    def append_node(
        self,
        root: typing.Optional[Query],
        current_operator: typing.Optional[Query],
        node: Query,
    ) -> tuple[typing.Optional[Query], typing.Optional[Query]]:
        """Append new Query node"""
        if current_operator:
            current_operator.children.append(node)
        elif root is None:
            root = node
        else:
            root.children.append(node)
        return root, current_operator

    def append_operator(
        self,
        root: typing.Optional[Query],
        operator_node: Query,
    ) -> tuple[Query, Query]:
        """Append new Operator node"""
        if root:
            operator_node.children.append(root)
        return operator_node, operator_node

    def check_for_none(self, root: typing.Optional[Query]) -> Query:
        """Check if root is none"""
        if root is None:
            raise ValueError("Failed to construct a valid query tree.")
        return root

    def parse_query_tree(
        self,
        tokens: list,
        search_field: typing.Optional[SearchField] = None,
        search_field_par: typing.Optional[SearchField] = None,
    ) -> Query:
        """
        Build a query tree from a list of tokens
        dynamic tree restructuring based on PRECEDENCE.
        """

        root: typing.Optional[Query] = None
        current_operator: typing.Optional[Query] = None

        while tokens:
            token = tokens.pop(0)

            if token.type == TokenTypes.FIELD:
                # Create new search_field used by following search_terms
                search_field = SearchField(token.value, position=token.position)

            elif token.type == TokenTypes.SEARCH_TERM:
                # Create new search_term and in case tree is empty, sets first root
                term_node = self.create_query_node(
                    token.value,
                    False,
                    token.position,
                    search_field,
                    None,
                    search_field_par,
                )

                # Append search_term to tree
                root, current_operator = self.append_node(
                    root, current_operator, term_node
                )

                search_field = None

            elif token.type == TokenTypes.PROXIMITY_OPERATOR:
                # Split token into NEAR/WITHIN and distance
                token.value, distance = self.convert_proximity_operators(
                    token.value, token.type
                )

                # Create new proximity_operator from token (N3, W1, N13, ...)
                proximity_node = self.create_query_node(
                    token.value, True, token.position, search_field, distance
                )

                # Set proximity_operator as tree node
                root, current_operator = self.append_operator(root, proximity_node)

            elif token.type == TokenTypes.LOGIC_OPERATOR:
                # Create new operator node
                new_operator_node = self.create_query_node(
                    token.value, True, token.position, search_field, None
                )

                if not current_operator:
                    # No current operator; initialize root
                    root, current_operator = self.append_operator(
                        root, new_operator_node
                    )

            elif token.type == TokenTypes.PARENTHESIS_OPEN:
                # Recursively parse the group inside parentheses
                # Set search_field_par as search field regarding the whole subtree
                # If subtree is done, reset search_field_par
                if search_field_par is not None:
                    search_field = search_field_par

                subtree = self.parse_query_tree(tokens, search_field, search_field)
                search_field_par = None

                root, current_operator = self.append_node(
                    root, current_operator, subtree
                )

            elif token.type == TokenTypes.PARENTHESIS_CLOSED:
                # Return subtree
                root = self.check_for_none(root)
                return root

        root = self.check_for_none(root)

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

    # def print_linter_messages(self, linter_messages: list[dict]) -> None:
    #     """Print linter messages in a readable format"""
    #     if not linter_messages:
    #         print("No linter messages to display.")
    #         return

    #     print("Linter Messages:")
    #     print("-" * 20)

    #     for message in linter_messages:
    #         if not isinstance(message, dict):
    #             print(f"Invalid message format: {message}")
    #             continue

    #         level = message.get("level", "Unknown Level")
    #         msg = message.get("msg", "No message provided")
    #         pos = message.get("pos", "Position not specified")

    #         print(f"Level: {level}")
    #         print(f"Message: {msg}")
    #         print(f"Position: {pos}")
    #         print("-" * 20)

    def parse(self) -> Query:
        """Parse a query string."""

        self.linter_messages.clear()

        # Create an instance of QueryStringValidator
        validator = QueryStringValidator(self)

        # Call validation methods
        validator.check_operator()

        validator.check_parenthesis()

        # Update the query string and messages after validation
        self.query_str = validator.query_str

        # Tokenize the search string
        self.tokenize()
        # Add artificial parentheses
        self.add_artificial_parentheses_for_operator_precedence()

        # Parse query on basis of tokens and recursively build a query-tree
        query = self.parse_query_tree(self.tokens)

        # Translate EBSCO host search_fields into standardized search_fields
        self.translate_search_fields(query)

        # Uncomment if linter_messages should be printed (e.g. for testing)
        # self.print_linter_messages(self.linter_messages)

        return query


class EBSCOListParser(QueryListParser):
    """Parser for EBSCO (list format) queries."""

    def __init__(self, query_list: str, search_field_general: str) -> None:
        """Initialize with a query list and use EBSCOParser for parsing each query."""
        super().__init__(query_list, search_field_general, EBSCOParser)

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
