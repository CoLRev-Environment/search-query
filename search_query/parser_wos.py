#!/usr/bin/env python3
"""Web-of-Science query parser."""
from __future__ import annotations

import re
import typing

from search_query.constants import LinterMode
from search_query.constants import ListToken
from search_query.constants import ListTokenTypes
from search_query.constants import OperatorNodeTokenTypes
from search_query.constants import Operators
from search_query.constants import PLATFORM
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.constants_wos import YEAR_PUBLISHED_FIELD_REGEX
from search_query.linter_wos import WOSQueryListLinter
from search_query.linter_wos import WOSQueryStringLinter
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField
from search_query.query import Term

# pylint: disable=duplicate-code


class WOSParser(QueryStringParser):
    """Parser for Web-of-Science queries."""

    SEARCH_TERM_REGEX = (
        r"\*?[\w\-/\.\!\*]+(?:[\*\$\?][\w\-/\.\!\*]*)*"
        r'|"[^"]+"'
        r'|\u201c[^"^\u201d]+\u201d'
        r'|\u2018[^"]+\u2019'
    )
    LOGIC_OPERATOR_REGEX = r"\b(AND|and|OR|or|NOT|not)\b"
    PROXIMITY_OPERATOR_REGEX = r"\b(NEAR/\d{1,2}|near/\d{1,2}|NEAR|near)\b"
    SEARCH_FIELD_REGEX = r"\b\w{2}=|\b\w{3}="
    PARENTHESIS_REGEX = r"[\(\)]"
    SEARCH_FIELDS_REGEX = r"\b(?!and\b)[a-zA-Z]+(?:\s(?!and\b)[a-zA-Z]+)*"
    YEAR_REGEX = r"^\d{4}(-\d{4})?$"

    OPERATOR_REGEX = "|".join([LOGIC_OPERATOR_REGEX, PROXIMITY_OPERATOR_REGEX])

    # Combine all regex patterns into a single pattern
    pattern = "|".join(
        [
            SEARCH_FIELD_REGEX,
            LOGIC_OPERATOR_REGEX,
            PROXIMITY_OPERATOR_REGEX,
            SEARCH_TERM_REGEX,
            PARENTHESIS_REGEX,
            # self.SEARCH_FIELDS_REGEX,
        ]
    )

    OPERATOR_PRECEDENCE = {
        "NEAR": 3,
        "WITHIN": 3,
        "NOT": 2,
        "AND": 1,
        "OR": 0,
    }

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
        self.linter = WOSQueryStringLinter(parser=self)

    def tokenize(self) -> None:
        """Tokenize the query_str."""

        if self.query_str is None:
            raise ValueError("No string provided to parse.")

        # Parse tokens and positions based on regex pattern
        for match in re.finditer(self.pattern, self.query_str):
            value = match.group()
            position = match.span()

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

            self.tokens.append(Token(value=value, type=token_type, position=position))

        self.combine_subsequent_terms()

    # Parse a query tree from tokens recursively
    # pylint: disable=too-many-branches
    def parse_query_tree(
        self,
        index: int = 0,
        search_field: typing.Optional[SearchField] = None,
        current_negation: bool = False,
    ) -> typing.Tuple[Query, int]:
        """Parse tokens starting at the given index,
        handling parentheses, operators, search fields and terms recursively."""
        children: typing.List[Query] = []
        current_operator = ""

        if current_negation:
            current_operator = "NOT"
        search_field = None
        while index < len(self.tokens):
            token = self.tokens[index]

            # Handle nested expressions within parentheses
            if token.type == TokenTypes.PARENTHESIS_OPEN:
                # Parse the expression inside the parentheses
                sub_query, index = self.parse_query_tree(
                    index=index + 1,
                    search_field=search_field,
                    current_negation=current_negation,
                )
                sub_query.search_field = search_field
                search_field = None

                # Add the parsed expression to the list of children
                children.append(sub_query)
                current_negation = False

            # Handle closing parentheses
            elif token.type == TokenTypes.PARENTHESIS_CLOSED:
                return (
                    self.handle_closing_parenthesis(
                        children=children,
                        current_operator=current_operator,
                        search_field=search_field,
                    ),
                    index,
                )

            # Handle operators
            elif token.type == TokenTypes.LOGIC_OPERATOR:
                # Handle the operator
                # and update all changes within the handler
                (
                    current_operator,
                    current_negation,
                ) = self.handle_operator(
                    token=token,
                    current_operator=current_operator,
                    current_negation=current_negation,
                )

            # Handle search fields
            elif token.type == TokenTypes.FIELD:
                search_field = SearchField(value=token.value, position=token.position)

            # Handle terms
            else:
                # Check if the token is a search field which has constraints
                # Check if the token is a year
                if re.findall(self.YEAR_REGEX, token.value) and search_field:
                    if YEAR_PUBLISHED_FIELD_REGEX.match(search_field.value):
                        children = self.handle_year_search(
                            token, children, current_operator
                        )
                        index += 1
                        continue

                # Add term nodes
                children = self.add_term_node(
                    index=index,
                    value=token.value,
                    search_field=search_field,
                    position=token.position,
                    children=children,
                    current_operator=current_operator,
                    current_negation=current_negation,
                )
                search_field = None
                current_operator = ""

            index += 1

        # Return options if there are no more tokens
        # Return the children if there is only one child
        if len(children) == 1:
            return children[0], index

        # Return the operator and children if there is an operator
        if current_operator:
            if self.search_field_general:
                search_field = SearchField(
                    value=self.search_field_general, position=(-1, -1)
                )
            return (
                Query(
                    value=current_operator,
                    children=list(children),
                    search_field=search_field,
                ),
                index,
            )

        # Raise an error if the code gets here
        raise NotImplementedError("Error in parsing the query tree")

    def handle_closing_parenthesis(
        self,
        children: list,
        current_operator: str,
        search_field: typing.Optional[SearchField] = None,
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
            )

        # Multiple children without operator are not allowed
        # This should already be caught in the token validation
        raise ValueError(
            "[ERROR] Multiple children without operator are not allowed."
            + "\nFound: "
            + str(children)
        )

    def handle_operator(
        self,
        token: Token,
        current_operator: str,
        current_negation: bool,
    ) -> typing.Tuple[str, bool]:
        """Handle operators."""

        # Set the current operator to the token
        current_operator = token.value.upper()

        # Set a flag if the token is NOT and change to AND
        if current_operator == "NOT":
            current_negation = True
            current_operator = "AND"

        return current_operator, current_negation

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

    def handle_year_search(
        self, token: Token, children: list, current_operator: str
    ) -> typing.List[Query]:
        """Handle the year search field."""

        search_field = SearchField(
            value="py=",
            position=token.position,
        )

        # Add the year search field to the list of children
        return self.add_term_node(
            index=0,
            value=token.value,
            search_field=search_field,
            position=token.position,
            children=children,
            current_operator=current_operator,
        )

    # pylint: disable=too-many-arguments
    def add_term_node(
        self,
        *,
        index: int,
        value: str,
        search_field: typing.Optional[SearchField] = None,
        position: typing.Optional[tuple] = None,
        current_operator: str = "",
        children: typing.Optional[typing.List[Query]] = None,
        current_negation: bool = False,
    ) -> typing.List[Query]:
        """Adds the term node to the Query"""
        if not children:
            children = []
        # Create a new term node
        term_node = Term(value=value, search_field=search_field, position=position)

        # Append the term node to the list of children
        if current_operator:
            if (
                not children
                or ((children[-1].value != current_operator) and not current_negation)
                or "NEAR" in current_operator
            ):
                if "NEAR" in current_operator and "NEAR" in children[0].value:
                    current_operator, distance = current_operator.split("/")
                    # Get previous term to append
                    while index > 0:
                        if self.tokens[index - 1].type == TokenTypes.SEARCH_TERM:
                            near_operator = Query(
                                value=current_operator,
                                children=[
                                    Term(
                                        value=self.tokens[index - 1].value,
                                        search_field=search_field,
                                    ),
                                    term_node,
                                ],
                                distance=int(distance),
                            )
                            break
                        index -= 1

                    children = [
                        Query(
                            value=Operators.AND,
                            operator=True,
                            children=[*children, near_operator],
                            search_field=search_field,
                        )
                    ]
                else:
                    children = [
                        Query(
                            value=current_operator,
                            children=[*children, term_node],
                            search_field=search_field,
                        )
                    ]
            else:
                children[-1].children.append(term_node)
        else:
            children.append(term_node)

        return children

    def parse(self) -> Query:
        """Parse a query string."""

        self.linter.handle_fully_quoted_query_str()

        self.tokenize()
        self.linter.validate_tokens()
        self.linter.check_status()

        query, _ = self.parse_query_tree()
        self.linter.validate_query_tree(query)
        self.linter.check_status()

        query.origin_platform = PLATFORM.WOS.value

        return query


class WOSListParser(QueryListParser):
    """Parser for Web-of-Science (list format) queries."""

    LIST_ITEM_REGEX = r"^(\d+).\s+(.*)$"
    LIST_ITEM_REFERENCE = r"#\d+"
    OPERATOR_NODE_REGEX = r"#\d+|AND|OR"
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

    def get_token_str(self, token_nr: str) -> str:
        return f"#{token_nr}"

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
                elif operator != token.value:
                    raise ValueError(
                        "[ERROR] Two different operators used in the same line."
                    )

        assert operator, "[ERROR] No operator found in combining query."

        operator_query = Query(
            value=operator,
            children=children,
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
        for match in re.finditer(self.OPERATOR_NODE_REGEX, query_str):
            value = match.group()
            position = match.span()
            if re.fullmatch(self.LIST_ITEM_REFERENCE, value):
                token_type = OperatorNodeTokenTypes.LIST_ITEM_REFERENCE
            elif re.fullmatch(WOSParser.LOGIC_OPERATOR_REGEX, value):
                token_type = OperatorNodeTokenTypes.LOGIC_OPERATOR
            else:
                token_type = OperatorNodeTokenTypes.UNKNOWN
            tokens.append(
                ListToken(
                    value=value, type=token_type, level=node_nr, position=position
                )
            )

        return tokens
