#!/usr/bin/env python3
"""Web-of-Science query parser."""
from __future__ import annotations

import re
import typing

from search_query.constants import LinterMode
from search_query.constants import ListToken
from search_query.constants import ListTokenTypes
from search_query.constants import OperatorNodeTokenTypes
from search_query.constants import PLATFORM
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField
from search_query.query_term import Term
from search_query.wos.constants import search_field_general_to_syntax
from search_query.wos.linter import WOSQueryListLinter
from search_query.wos.linter import WOSQueryStringLinter

# pylint: disable=duplicate-code


class WOSParser(QueryStringParser):
    """Parser for Web-of-Science queries."""

    SEARCH_TERM_REGEX = re.compile(
        r'\*?[\w\-/\.\!\*,&\\]+(?:[\*\$\?][\w\-/\.\!\*,&\\]*)*|"[^"]+"'
    )
    LOGIC_OPERATOR_REGEX = re.compile(r"\b(AND|OR|NOT)\b", flags=re.IGNORECASE)
    PROXIMITY_OPERATOR_REGEX = re.compile(
        r"\b(NEAR/\d{1,2}|NEAR)\b", flags=re.IGNORECASE
    )
    SEARCH_FIELD_REGEX = re.compile(r"\b\w{2}=|\b\w{3}=")
    PARENTHESIS_REGEX = re.compile(r"[\(\)]")
    SEARCH_FIELDS_REGEX = re.compile(r"\b(?!and\b)[a-zA-Z]+(?:\s(?!and\b)[a-zA-Z]+)*")

    OPERATOR_REGEX = re.compile(
        "|".join([LOGIC_OPERATOR_REGEX.pattern, PROXIMITY_OPERATOR_REGEX.pattern])
    )

    # Combine all regex patterns into a single pattern
    pattern = re.compile(
        r"|".join(
            [
                SEARCH_FIELD_REGEX.pattern,
                LOGIC_OPERATOR_REGEX.pattern,
                PROXIMITY_OPERATOR_REGEX.pattern,
                SEARCH_TERM_REGEX.pattern,
                PARENTHESIS_REGEX.pattern,
                # self.SEARCH_FIELDS_REGEX.pattern,
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
            query_str,
            search_field_general=search_field_general,
            mode=mode,
        )
        self.linter = WOSQueryStringLinter(query_str=query_str)

    def tokenize(self) -> None:
        """Tokenize the query_str."""

        # Parse tokens and positions based on regex pattern
        for match in self.pattern.finditer(self.query_str):
            value = match.group()
            position = match.span()

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

            self.tokens.append(Token(value=value, type=token_type, position=position))

        self.combine_subsequent_terms()
        self.split_operators_with_missing_whitespace()

    # Parse a query tree from tokens recursively
    # pylint: disable=too-many-branches
    def parse_query_tree(
        self,
        index: int = 0,
        search_field: typing.Optional[SearchField] = None,
    ) -> typing.Tuple[Query, int]:
        """Parse tokens starting at the given index,
        handling parentheses, operators, search fields and terms recursively."""

        children: typing.List[Query] = []
        current_operator = ""
        current_negation = False
        distance: typing.Optional[int] = None

        search_field = None
        while index < len(self.tokens):
            token = self.tokens[index]

            # Handle nested expressions within parentheses
            if token.type == TokenTypes.PARENTHESIS_OPEN:
                # Parse the expression inside the parentheses
                sub_query, index = self.parse_query_tree(
                    index=index + 1,
                    search_field=search_field,
                )
                sub_query.search_field = search_field
                search_field = None

                if current_negation:
                    # If the current operator is NOT, wrap the sub_query in a NOT
                    not_part = Query(
                        value="NOT",
                        operator=True,
                        children=[sub_query],
                        search_field=search_field,
                        platform="deactivated",
                    )
                    children.append(not_part)
                    current_negation = False
                    current_operator = "AND"
                else:
                    children.append(sub_query)

            # Handle closing parentheses
            elif token.type == TokenTypes.PARENTHESIS_CLOSED:
                return (
                    self._handle_closing_parenthesis(
                        children=children,
                        current_operator=current_operator,
                        search_field=search_field,
                        distance=distance,
                    ),
                    index,
                )

            # Handle operators
            elif token.type == TokenTypes.LOGIC_OPERATOR:
                current_operator = token.value.upper()

                # Set a flag if the token is NOT and change to AND
                if current_operator == "NOT":
                    current_negation = True
                    current_operator = "AND"

            elif token.type == TokenTypes.PROXIMITY_OPERATOR:
                current_operator = token.value.upper()
                if "NEAR" in current_operator:
                    assert "/" in current_operator  # fixed in linter
                    current_operator, raw_distance = current_operator.split("/")
                    distance = int(raw_distance)

            # Handle search fields
            elif token.type == TokenTypes.FIELD:
                search_field = SearchField(value=token.value, position=token.position)

            # Handle terms
            elif token.type == TokenTypes.SEARCH_TERM:
                if current_negation:
                    not_part = Query(
                        value="NOT",
                        operator=True,
                        children=[
                            Term(
                                value=token.value,
                                search_field=search_field,
                                position=token.position,
                            )
                        ],
                        search_field=search_field,
                        platform="deactivated",
                    )
                    children = children + [not_part]
                    current_negation = False
                    current_operator = "AND"
                else:
                    term_node = Term(
                        value=token.value,
                        search_field=search_field,
                        position=token.position,
                        platform="deactivated",
                    )
                    children.append(term_node)
                    search_field = None

            index += 1

        # Return options if there are no more tokens
        # Return the children if there is only one child
        if len(children) == 1:
            return children[0], index

        if not current_operator:  # pragma: no cover
            raise NotImplementedError("Error in parsing the query tree")

        # Return the operator and children if there is an operator
        return (
            Query(
                value=current_operator,
                children=list(children),
                search_field=search_field,
                platform="deactivated",
            ),
            index,
        )

    def _handle_closing_parenthesis(
        self,
        children: list,
        current_operator: str,
        search_field: typing.Optional[SearchField] = None,
        distance: typing.Optional[int] = None,
    ) -> Query:
        """Handle closing parentheses."""
        # Return the children if there is only one child
        if len(children) == 1:
            return children[0]

        # Return the operator and children if there is an operator
        if current_operator:
            return Query(
                value=current_operator,
                children=children,
                search_field=search_field,
                platform="deactivated",
                distance=distance,
            )

        # Multiple children without operator are not allowed
        # This should already be caught in the token validation
        raise ValueError(  # pragma: no cover
            "[ERROR] Multiple children without operator are not allowed."
            + "\nFound: "
            + str(children)
        )

    def combine_subsequent_terms(self) -> None:
        """Combine subsequent terms in the list of tokens."""
        # Combine subsequent terms (without quotes)
        # This would be more challenging in the regex
        # Changed the implementation to combine multiple terms
        combined_tokens: typing.List[Token] = []
        i = 0
        j = 0

        while i < len(self.tokens):
            if len(combined_tokens) > 0:
                if (
                    self.tokens[i].type == TokenTypes.SEARCH_TERM
                    and combined_tokens[j - 1].type == TokenTypes.SEARCH_TERM
                ):
                    combined_token = Token(
                        value=combined_tokens[j - 1].value + " " + self.tokens[i].value,
                        type=TokenTypes.SEARCH_TERM,
                        position=(
                            combined_tokens[j - 1].position[0],
                            self.tokens[i].position[1],
                        ),
                    )
                    combined_tokens.pop()
                    combined_tokens.append(combined_token)
                    i += 1
                    continue

            if (
                i + 1 < len(self.tokens)
                and self.tokens[i].type == TokenTypes.SEARCH_TERM
                and self.tokens[i + 1].type == TokenTypes.SEARCH_TERM
            ):
                combined_token = Token(
                    value=self.tokens[i].value + " " + self.tokens[i + 1].value,
                    type=TokenTypes.SEARCH_TERM,
                    position=(
                        self.tokens[i].position[0],
                        self.tokens[i + 1].position[1],
                    ),
                )
                combined_tokens.append(combined_token)
                i += 2
                j += 1
            else:
                combined_tokens.append(self.tokens[i])
                i += 1
                j += 1

        self.tokens = combined_tokens

    def parse(self) -> Query:
        """Parse a query string."""

        # self.linter.query_str = self.query_str

        self.query_str = self.linter.handle_fully_quoted_query_str(self.query_str)
        self.query_str = self.linter.handle_nonstandard_quotes_in_query_str(
            self.query_str
        )
        # self.query_str = self.query_str = self.linter.handle_prefix_in_query_str(
        #     self.query_str
        # )
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

        query, _ = self.parse_query_tree()
        self.linter.validate_query_tree(query)
        self.linter.check_status()

        if self.search_field_general:
            search_field_general = SearchField(
                value=search_field_general_to_syntax(self.search_field_general),
                position=(-1, -1),
            )
            query.search_field = search_field_general

        query.set_platform_unchecked(PLATFORM.WOS.value, silent=True)

        return query


class WOSListParser(QueryListParser):
    """Parser for Web-of-Science (list format) queries."""

    LIST_ITEM_REGEX = re.compile(r"^(\d+).\s+(.*)$")
    LIST_ITEM_REFERENCE = re.compile(r"#\d+")
    OPERATOR_NODE_REGEX = re.compile(r"#\d+|AND|OR")
    query_dict: dict

    def __init__(self, query_list: str, search_field_general: str, mode: str) -> None:
        super().__init__(
            query_list=query_list,
            parser_class=WOSParser,
            search_field_general=search_field_general,
            mode=mode,
        )
        self.linter = WOSQueryListLinter(
            parser=self,
            string_parser_class=WOSParser,
        )

    def tokenize_list(self) -> None:
        """Tokenize the query_list."""
        query_list = self.query_list
        previous = 0
        for line in query_list.split("\n"):
            if line.strip() == "":
                continue

            match = self.LIST_ITEM_REGEX.match(line)
            if not match:  # pragma: no cover
                raise ValueError(f"line not matching format: {line}")
            node_nr, node_content = match.groups()
            pos_start, pos_end = match.span(2)
            pos_start += previous
            pos_end += previous
            self.query_dict[str(node_nr)] = {
                "node_content": node_content,
                "content_pos": (pos_start, pos_end),
                "type": ListTokenTypes.OPERATOR_NODE
                if "#" in node_content
                else ListTokenTypes.QUERY_NODE,
            }
            previous += len(line) + 1

    def _build_query_from_operator_node(self, tokens: list) -> Query:
        operator = ""
        children = []
        for token in tokens:
            if "#" in token.value:
                idx = token.value.replace("#", "")  # - 1
                children.append(self.query_dict[idx]["query"])
            else:
                if not operator:
                    operator = token.value
                # checked in token-linter
                assert operator == token.value

        assert operator, "[ERROR] No operator found in combining query."

        operator_query = Query(
            value=operator,
            children=children,
            platform="deactivated",
        )
        return operator_query

    def _parse_list_query(self) -> Query:
        for node_nr, node_content in self.query_dict.items():
            if node_content["type"] == ListTokenTypes.QUERY_NODE:
                query_parser = WOSParser(
                    query_str=node_content["node_content"],
                    search_field_general=self.search_field_general,
                    mode=self.mode,
                )
                query = query_parser.parse()
                node_content["query"] = query

            elif node_content["type"] == ListTokenTypes.OPERATOR_NODE:
                tokens = self.tokenize_operator_node(
                    node_content["node_content"], node_nr
                )
                query = self._build_query_from_operator_node(tokens)
                self.query_dict[node_nr]["query"] = query

        return list(self.query_dict.values())[-1]["query"]

    def parse(self) -> Query:
        """Parse the list of queries."""

        self.tokenize_list()
        # note: messages printed in linter
        self.linter.validate_list_tokens()
        self.linter.check_status()

        query = self._parse_list_query()
        return query

    def tokenize_operator_node(self, query_str: str, node_nr: int) -> list:
        """Tokenize the query_list."""

        tokens = []
        for match in self.OPERATOR_NODE_REGEX.finditer(query_str):
            value = match.group()
            position = match.span()
            if self.LIST_ITEM_REFERENCE.fullmatch(value):
                token_type = OperatorNodeTokenTypes.LIST_ITEM_REFERENCE
            elif WOSParser.LOGIC_OPERATOR_REGEX.fullmatch(value):
                token_type = OperatorNodeTokenTypes.LOGIC_OPERATOR
            else:  # pragma: no cover
                token_type = OperatorNodeTokenTypes.UNKNOWN
            tokens.append(
                ListToken(
                    value=value, type=token_type, level=node_nr, position=position
                )
            )

        return tokens
