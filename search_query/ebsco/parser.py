#!/usr/bin/env python3
"""EBSCO query parser."""
from __future__ import annotations

import re
import typing

from search_query.constants import GENERAL_ERROR_POSITION
from search_query.constants import LinterMode
from search_query.constants import PLATFORM
from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.ebsco.linter import EBSCOQueryStringLinter
from search_query.linter_base import QueryListLinter
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField
from search_query.query import Term


class EBSCOParser(QueryStringParser):
    """Parser for EBSCO queries."""

    PARENTHESIS_REGEX = r"[\(\)]"
    LOGIC_OPERATOR_REGEX = r"\b(AND|and|OR|or|NOT|not)\b"
    PROXIMITY_OPERATOR_REGEX = r"(N|W)\d+"
    SEARCH_FIELD_REGEX = r"\b([A-Z]{2})\b"
    SEARCH_TERM_REGEX = r"\"[^\"]*\"|\b(?!S\d+\b)[^()\s]+[\*\+\?]?"

    OPERATOR_REGEX = "|".join([LOGIC_OPERATOR_REGEX, PROXIMITY_OPERATOR_REGEX])

    pattern = "|".join(
        [
            PARENTHESIS_REGEX,
            LOGIC_OPERATOR_REGEX,
            PROXIMITY_OPERATOR_REGEX,
            SEARCH_FIELD_REGEX,
            SEARCH_TERM_REGEX,
        ]
    )

    def __init__(
        self,
        query_str: str,
        *,
        search_field_general: str = "",
        mode: str = LinterMode.STRICT,
    ) -> None:
        """Initialize the parser."""
        super().__init__(
            query_str, search_field_general=search_field_general, mode=mode
        )
        self.linter = EBSCOQueryStringLinter()

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

    def tokenize(self) -> None:
        """Tokenize the query_str."""

        if self.query_str is None:
            raise ValueError("No string provided to parse.")

        self.tokens = []
        token_type = TokenTypes.UNKNOWN
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
                token_type = TokenTypes.UNKNOWN

            # Append token with its type and position to self.tokens
            self.tokens.append(
                Token(value=value, type=token_type, position=(start, end))
            )

        # Combine subsequent search_terms in case of no quotation marks
        self.combine_subsequent_tokens()

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
        tokens: typing.Optional[list] = None,
        search_field: typing.Optional[SearchField] = None,
        search_field_par: typing.Optional[SearchField] = None,
    ) -> Query:
        """
        Build a query tree from a list of tokens
        dynamic tree restructuring based on PRECEDENCE.
        """
        if not tokens:
            tokens = list(self.tokens)
        root: typing.Optional[Query] = None
        current_operator: typing.Optional[Query] = None

        while tokens:
            token = tokens.pop(0)

            if token.type == TokenTypes.FIELD:
                # Create new search_field used by following search_terms
                search_field = SearchField(token.value, position=token.position)

            elif token.type == TokenTypes.SEARCH_TERM:
                # Create new search_term and in case tree is empty, sets first root
                term_node = Term(
                    value=token.value,
                    position=token.position,
                    search_field=search_field or search_field_par,
                    origin_platform="deactivated",
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
                proximity_node = Query(
                    value=token.value,
                    position=token.position,
                    search_field=search_field or search_field_par,
                    distance=distance,
                    origin_platform="deactivated",
                )

                # Set proximity_operator as tree node
                root, current_operator = self.append_operator(root, proximity_node)

            elif token.type == TokenTypes.LOGIC_OPERATOR:
                # Create new operator node
                new_operator_node = Query(
                    value=token.value,
                    position=token.position,
                    search_field=search_field or search_field_par,
                    origin_platform="deactivated",
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

    def parse(self) -> Query:
        """Parse a query string."""

        self.tokenize()

        self.tokens = self.linter.validate_tokens(
            tokens=self.tokens,
            query_str=self.query_str,
            search_field_general=self.search_field_general,
        )
        self.linter.check_status()

        query = self.parse_query_tree()
        self.linter.validate_query_tree(query)
        self.linter.check_status()

        query.set_origin_platform(PLATFORM.EBSCO.value)

        return query


class EBSCOListParser(QueryListParser):
    """Parser for EBSCO (list format) queries."""

    def __init__(self, query_list: str, search_field_general: str, mode: str) -> None:
        """Initialize with a query list and use EBSCOParser for parsing each query."""
        super().__init__(
            query_list=query_list,
            parser_class=EBSCOParser,
            search_field_general=search_field_general,
            mode=mode,
        )
        self.linter = QueryListLinter(parser=self, string_parser_class=EBSCOParser)

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
        self.linter.add_linter_message(
            QueryErrorCode.INVALID_LIST_REFERENCE,
            list_position=GENERAL_ERROR_POSITION,
            position=(-1, -1),
            details="Connecting lines possibly failed. "
            "Please use this format for connection: "
            "S1 OR S2 OR S3 / #1 OR #2 OR #3",
        )
        return token_nr

    def parse(self) -> Query:
        """Parse the query in list format."""
        raise NotImplementedError("List parsing not implemented yet.")
