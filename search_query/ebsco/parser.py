#!/usr/bin/env python3
"""EBSCO query parser."""
from __future__ import annotations

import re
import typing

from search_query.constants import GENERAL_ERROR_POSITION
from search_query.constants import LinterMode
from search_query.constants import ListToken
from search_query.constants import ListTokenTypes
from search_query.constants import OperatorNodeTokenTypes
from search_query.constants import PLATFORM
from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.ebsco.linter import EBSCOListLinter
from search_query.ebsco.linter import EBSCOQueryStringLinter
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField
from search_query.query_term import Term


class EBSCOParser(QueryStringParser):
    """Parser for EBSCO queries."""

    PARENTHESIS_REGEX = re.compile(r"[\(\)]")
    LOGIC_OPERATOR_REGEX = re.compile(r"\b(AND|OR|NOT)\b", flags=re.IGNORECASE)
    PROXIMITY_OPERATOR_REGEX = re.compile(
        r"(N|W)\d+|(NEAR|WITHIN)/\d+", flags=re.IGNORECASE
    )
    SEARCH_FIELD_REGEX = re.compile(r"\b([A-Z]{2})\b")
    SEARCH_TERM_REGEX = re.compile(r"\"[^\"]*\"|\*?\b[^()\s]+")

    OPERATOR_REGEX = re.compile(
        "|".join([LOGIC_OPERATOR_REGEX.pattern, PROXIMITY_OPERATOR_REGEX.pattern])
    )

    pattern = re.compile(
        "|".join(
            [
                PARENTHESIS_REGEX.pattern,
                LOGIC_OPERATOR_REGEX.pattern,
                PROXIMITY_OPERATOR_REGEX.pattern,
                SEARCH_FIELD_REGEX.pattern,
                SEARCH_TERM_REGEX.pattern,
            ]
        )
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
        self.linter = EBSCOQueryStringLinter(query_str=query_str)

    def combine_subsequent_tokens(self) -> None:
        """Combine subsequent tokens based on specific conditions."""

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

    def _extract_proximity_distance(self, token: Token) -> int:
        """Convert proximity operator token into operator and distance components"""

        # Extract the operator (first character) and distance (rest of the string)
        operator = token.value[:1]
        distance_string = token.value[1:]

        # Change value of operator to fit construction of operator query
        if operator == "N":
            operator = "NEAR"
        else:
            operator = "WITHIN"

        # distance_string.is_digit() is always True afeer PROXIMITY_OPERATOR_REGEX match
        distance = int(distance_string)
        token.value = operator
        return distance

    def fix_ambiguous_tokens(self) -> None:
        """Fix ambiguous tokens that could be misinterpreted as a search field."""

        def is_potential_term(token_str: str) -> bool:
            return bool(re.fullmatch(r"[A-Z]{2,}", token_str))

        # Field token followed by term which is misclassified as a field token
        for i in range(len(self.tokens) - 1):
            current = self.tokens[i]
            next_token = self.tokens[i + 1]

            if (
                current.type == TokenTypes.FIELD
                and next_token.type == TokenTypes.FIELD
                and is_potential_term(next_token.value)
            ):
                # Reclassify the second FIELD token as a SEARCH_TERM
                next_token.type = TokenTypes.SEARCH_TERM

    def tokenize(self) -> None:
        """Tokenize the query_str."""

        self.tokens = []
        token_type = TokenTypes.UNKNOWN
        for match in self.pattern.finditer(self.query_str):
            value = match.group()
            value = value.strip()
            start, end = match.span()

            # Determine token type
            if self.PARENTHESIS_REGEX.fullmatch(value):
                if value == "(":
                    token_type = TokenTypes.PARENTHESIS_OPEN
                else:
                    token_type = TokenTypes.PARENTHESIS_CLOSED
            elif self.LOGIC_OPERATOR_REGEX.fullmatch(value):
                token_type = TokenTypes.LOGIC_OPERATOR
            elif self.PROXIMITY_OPERATOR_REGEX.fullmatch(value):
                token_type = TokenTypes.PROXIMITY_OPERATOR
            elif self.SEARCH_FIELD_REGEX.fullmatch(value):
                token_type = TokenTypes.FIELD
            elif self.SEARCH_TERM_REGEX.fullmatch(value):
                token_type = TokenTypes.SEARCH_TERM
            else:  # pragma: no cover
                token_type = TokenTypes.UNKNOWN

            # Append token with its type and position to self.tokens
            self.tokens.append(
                Token(value=value, type=token_type, position=(start, end))
            )

        # Combine subsequent search_terms in case of no quotation marks
        self.combine_subsequent_tokens()
        self.fix_ambiguous_tokens()

    def append_node(
        self,
        parent: typing.Optional[Query],
        current_operator: typing.Optional[Query],
        node: Query,
    ) -> tuple[typing.Optional[Query], typing.Optional[Query]]:
        """Append new Query node"""

        assert current_operator or parent is None

        if current_operator:
            current_operator.children.append(node)
        elif parent is None:
            parent = node

        return parent, current_operator

    def append_operator(
        self,
        parent: typing.Optional[Query],
        operator_node: Query,
    ) -> tuple[Query, Query]:
        """Append new Operator node"""
        if parent:
            operator_node.children.append(parent)
        return operator_node, operator_node

    def _check_for_none(self, parent: typing.Optional[Query]) -> Query:
        """Check if parent is none"""
        if parent is None:  # pragma: no cover
            raise ValueError("Failed to construct a valid query tree.")
        return parent

    def parse_query_tree(
        self,
        tokens: typing.Optional[list] = None,
        field_context: typing.Optional[SearchField] = None,
    ) -> Query:
        """
        Build a query tree from a list of tokens
        with dynamic restructuring based on PRECEDENCE.
        """
        if not tokens:
            tokens = list(self.tokens)

        parent: typing.Optional[Query] = None
        current_operator: typing.Optional[Query] = None
        search_field: typing.Optional[SearchField] = None

        while tokens:
            token = tokens.pop(0)

            if token.type == TokenTypes.FIELD:
                search_field = SearchField(token.value, position=token.position)

            elif token.type == TokenTypes.SEARCH_TERM:
                term_node = Term(
                    value=token.value,
                    position=token.position,
                    search_field=search_field or field_context,
                    platform="deactivated",
                )
                parent, current_operator = self.append_node(
                    parent, current_operator, term_node
                )
                search_field = None

            elif token.type == TokenTypes.PROXIMITY_OPERATOR:
                distance = self._extract_proximity_distance(token)
                proximity_node = Query(
                    value=token.value,
                    position=token.position,
                    search_field=search_field or field_context,
                    distance=distance,
                    platform="deactivated",
                )
                parent, current_operator = self.append_operator(parent, proximity_node)

            elif token.type == TokenTypes.LOGIC_OPERATOR:
                new_operator_node = Query(
                    value=token.value.upper(),
                    position=token.position,
                    search_field=search_field or field_context,
                    platform="deactivated",
                )

                if not current_operator:
                    parent, current_operator = self.append_operator(
                        parent, new_operator_node
                    )

            elif token.type == TokenTypes.PARENTHESIS_OPEN:
                # Recursively parse subexpression with same effective field
                subtree = self.parse_query_tree(tokens, search_field or field_context)
                parent, current_operator = self.append_node(
                    parent, current_operator, subtree
                )

            elif token.type == TokenTypes.PARENTHESIS_CLOSED:
                return self._check_for_none(parent)

        return self._check_for_none(parent)

    def parse(self) -> Query:
        """Parse a query string."""

        self.query_str = self.linter.handle_nonstandard_quotes_in_query_str(
            self.query_str
        )
        self.query_str = self.query_str = self.linter.handle_suffix_in_query_str(
            self.query_str
        )

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

        query.set_platform_unchecked(PLATFORM.EBSCO.value, silent=True)

        return query


class EBSCOListParser(QueryListParser):
    """Parser for EBSCO (list format) queries."""

    LIST_ITEM_REGEX = re.compile(r"^(\d+).\s+(.*)$")
    LIST_ITEM_REF = re.compile(r"[#S]\d+")
    OPERATOR_NODE_REGEX = re.compile(r"[#S]\d+|AND|OR|NOT")

    def __init__(
        self,
        query_list: str,
        search_field_general: str,
        mode: str = LinterMode.NONSTRICT,
    ) -> None:
        super().__init__(
            query_list=query_list,
            parser_class=EBSCOParser,
            search_field_general=search_field_general,
            mode=mode,
        )
        self.linter = EBSCOListLinter(parser=self, string_parser_class=EBSCOParser)

    def get_token_str(self, token_nr: str) -> str:
        pattern = rf"(S|#){token_nr}"
        match = re.search(pattern, self.query_list)
        if match:
            return f"{match.group(1)}{token_nr}"
        details = (
            "Connecting lines possibly failed. "
            "Use format: S1 OR S2 OR S3 / #1 OR #2 OR #3"
        )
        self.linter.add_linter_message(
            QueryErrorCode.INVALID_LIST_REFERENCE,
            list_position=GENERAL_ERROR_POSITION,
            positions=[(-1, -1)],
            details=details,
        )
        return token_nr

    def get_operator_node_tokens(self, token_nr: int) -> list:
        """Get tokens from an operator node."""
        node_content = self.query_dict[token_nr]["node_content"]
        tokens = []
        for match in self.OPERATOR_NODE_REGEX.finditer(node_content):
            value = match.group()
            start, end = match.span()
            if value.upper() in {"AND", "OR", "NOT"}:
                token_type = OperatorNodeTokenTypes.LOGIC_OPERATOR
            elif self.LIST_ITEM_REF.match(value):
                token_type = OperatorNodeTokenTypes.LIST_ITEM_REFERENCE
            else:
                token_type = OperatorNodeTokenTypes.UNKNOWN
            tokens.append(
                ListToken(
                    value=value, type=token_type, level=token_nr, position=(start, end)
                )
            )
        return tokens

    def _parse_operator_node(self, token_nr: int) -> Query:
        tokens = self.get_operator_node_tokens(token_nr)
        operator = ""
        children = []
        for token in tokens:
            if token.type == OperatorNodeTokenTypes.LIST_ITEM_REFERENCE:
                ref = token.value.lstrip("#S")
                children.append(self.query_dict[ref]["query"])
            elif token.type == OperatorNodeTokenTypes.LOGIC_OPERATOR:
                operator = token.value.upper()

        return Query(
            value=operator, search_field=None, children=children, platform="deactivated"
        )

    def parse(self) -> Query:
        self.tokenize_list()
        self.linter.validate_tokens()
        self.linter.check_status()

        for token_nr, query_element in self.query_dict.items():
            if query_element["type"] == ListTokenTypes.QUERY_NODE:
                parser = self.parser_class(
                    query_element["node_content"],
                    search_field_general=self.search_field_general,
                )
                query_element["query"] = parser.parse()
            elif query_element["type"] == ListTokenTypes.OPERATOR_NODE:
                query_element["query"] = self._parse_operator_node(token_nr)

        return list(self.query_dict.values())[-1]["query"]
