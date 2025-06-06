#!/usr/bin/env python3
"""Pubmed query parser."""
import re

from search_query.constants import LinterMode
from search_query.constants import ListToken
from search_query.constants import ListTokenTypes
from search_query.constants import OperatorNodeTokenTypes
from search_query.constants import Operators
from search_query.constants import PLATFORM
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.exception import QuerySyntaxError
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.pubmed.linter import PubmedQueryListLinter
from search_query.pubmed.linter import PubmedQueryStringLinter
from search_query.query import Query
from search_query.query import SearchField
from search_query.query_term import Term


class PubmedParser(QueryStringParser):
    """Parser for Pubmed queries."""

    SEARCH_FIELD_REGEX = re.compile(r"\[[^\[]*?\]")
    OPERATOR_REGEX = re.compile(r"(\||&|\b(?:AND|OR|NOT|:)\b)(?!\s?\[[^\[]*?\])")
    PARENTHESIS_REGEX = re.compile(r"[\(\)]")
    SEARCH_PHRASE_REGEX = re.compile(r"\".*?\"")
    SEARCH_TERM_REGEX = re.compile(r"[^\s\[\]()\|&]+")
    PROXIMITY_REGEX = re.compile(r"^\[(.+):~(.*)\]$")

    pattern = re.compile(
        "|".join(
            [
                SEARCH_FIELD_REGEX.pattern,
                OPERATOR_REGEX.pattern,
                PARENTHESIS_REGEX.pattern,
                SEARCH_PHRASE_REGEX.pattern,
                SEARCH_TERM_REGEX.pattern,
            ]
        ),
        flags=re.IGNORECASE,
    )

    def __init__(
        self,
        query_str: str,
        search_field_general: str = "",
        mode: str = LinterMode.NONSTRICT,
    ) -> None:
        """Initialize the parser."""
        super().__init__(
            query_str=query_str, search_field_general=search_field_general, mode=mode
        )
        self.linter = PubmedQueryStringLinter(query_str=query_str)

    def tokenize(self) -> None:
        """Tokenize the query_str"""

        # Parse tokens and positions based on regex patterns.
        for match in self.pattern.finditer(self.query_str):
            value = match.group(0)

            if value.upper() in {"AND", "OR", "NOT", "|", "&"}:
                token_type = TokenTypes.LOGIC_OPERATOR
            elif value == ":":
                token_type = TokenTypes.RANGE_OPERATOR
            elif value == "(":
                token_type = TokenTypes.PARENTHESIS_OPEN
            elif value == ")":
                token_type = TokenTypes.PARENTHESIS_CLOSED
            elif value.startswith("[") and value.endswith("]"):
                token_type = TokenTypes.FIELD
            else:
                token_type = TokenTypes.SEARCH_TERM

            self.tokens.append(
                Token(value=value, type=token_type, position=match.span())
            )

        self.combine_subsequent_terms()

    def parse_query_tree(self, tokens: list) -> Query:
        """Parse a query from a list of tokens"""

        if self._is_compound_query(tokens):
            query = self._parse_compound_query(tokens)

        elif self._is_nested_query(tokens):
            query = self._parse_nested_query(tokens)

        elif self._is_term_query(tokens):
            query = self._parse_search_term(tokens)

        else:  # pragma: no cover
            raise ValueError()

        return query

    def _is_term_query(self, tokens: list) -> bool:
        """Check if the query is a search term"""
        return tokens[0].type == TokenTypes.SEARCH_TERM and len(tokens) <= 2

    def _is_compound_query(self, tokens: list) -> bool:
        """Check if the query is a compound query"""
        return bool(self._get_operator_indices(tokens))

    def _is_nested_query(self, tokens: list) -> bool:
        """Check if the query is nested in parentheses"""
        return (
            tokens[0].type == TokenTypes.PARENTHESIS_OPEN
            and tokens[-1].type == TokenTypes.PARENTHESIS_CLOSED
        )

    def _get_operator_type(self, token: Token) -> str:
        """Get operator type"""
        if token.value.upper() in {"&", "AND"}:
            return Operators.AND
        if token.value.upper() in {"|", "OR"}:
            return Operators.OR
        if token.value.upper() == "NOT":
            return Operators.NOT
        if token.value == ":":
            return Operators.RANGE
        raise ValueError()  # pragma: no cover

    def _get_operator_indices(self, tokens: list) -> list:
        """Get indices of top-level operators in the token list"""
        operator_indices = []

        i = 0
        first_operator_found = False
        first_operator = ""
        # Iterate over tokens in reverse
        # to find and save positions of consecutive top-level operators
        # matching the first encountered until a different type is found.
        for token in reversed(tokens):
            token_index = tokens.index(token)

            if token.type == TokenTypes.PARENTHESIS_OPEN:
                i = i + 1
            elif token.type == TokenTypes.PARENTHESIS_CLOSED:
                i = i - 1

            if i == 0 and token.type in [
                TokenTypes.LOGIC_OPERATOR,
                TokenTypes.RANGE_OPERATOR,
            ]:
                operator = self._get_operator_type(token)
                if not first_operator_found:
                    first_operator = operator
                    first_operator_found = True
                if operator == first_operator:
                    operator_indices.append(token_index)
                else:  # pragma: no cover
                    # Note: this should not happen because the linter calls
                    # add_artificial_parentheses_for_operator_precedence()
                    raise ValueError

        return operator_indices

    def _parse_compound_query(self, tokens: list) -> Query:
        """Parse a compound query
        consisting of two or more subqueries connected by a boolean operator"""

        operator_indices = self._get_operator_indices(tokens)

        # Divide tokens into separate lists based on top-level operator positions.
        token_lists = []
        i = 0
        for position in reversed(operator_indices):
            token_lists.append(tokens[i:position])
            i = position + 1
        token_lists.append(tokens[i:])

        # The token lists represent the subqueries (children
        # of the compound query and are parsed individually.
        children = []
        for token_list in token_lists:
            query = self.parse_query_tree(token_list)
            children.append(query)

        operator_type = self._get_operator_type(tokens[operator_indices[0]])

        query_start_pos = tokens[0].position[0]
        query_end_pos = tokens[-1].position[1]

        return Query(
            value=operator_type,
            search_field=None,
            children=list(children),
            position=(query_start_pos, query_end_pos),
            platform="deactivated",
        )

    def _parse_nested_query(self, tokens: list) -> Query:
        """Parse a query nested inside a pair of parentheses"""
        inner_query = self.parse_query_tree(tokens[1:-1])
        return inner_query

    def _parse_search_term(self, tokens: list) -> Query:
        """Parse a search term"""
        search_term_token = tokens[0]

        # Determine the search field of the search term.
        if len(tokens) > 1 and tokens[1].type == TokenTypes.FIELD:
            search_field = SearchField(
                value=tokens[1].value, position=tokens[1].position
            )
        else:
            # Select default field "all" if no search field is found.
            search_field = SearchField(value="[all]", position=(-1, -1))

        return Term(
            value=search_term_token.value,
            search_field=search_field,
            position=tokens[0].position,
            platform="deactivated",
        )

    def parse(self) -> Query:
        """Parse a query string"""

        self.query_str = self.linter.handle_nonstandard_quotes_in_query_str(
            self.query_str
        )
        self.query_str = self.query_str = self.linter.handle_prefix_in_query_str(
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

        # Parsing
        query = self.parse_query_tree(self.tokens)
        self.linter.validate_query_tree(query)
        self.linter.check_status()

        query.set_platform_unchecked(PLATFORM.PUBMED.value, silent=True)

        return query


class PubmedListParser(QueryListParser):
    """Parser for Pubmed (list format) queries."""

    LIST_ITEM_REGEX = re.compile(r"^(\d+).\s+(.*)$")
    LIST_ITEM_REF = re.compile(r"#?\d+")
    OPERATOR_NODE_ELEMENTS_REGEX = re.compile(r"#?\d+|AND|OR|NOT")
    OPERATOR_NODE_REGEX = re.compile(
        r"^\{?(?:#?\d+\s*(?:OR|AND)?\s*)+#?\d+\}?$", re.IGNORECASE
    )

    def __init__(
        self,
        query_list: str,
        *,
        search_field_general: str = "",
        mode: str = LinterMode.NONSTRICT,
    ) -> None:
        super().__init__(
            query_list,
            parser_class=PubmedParser,
            search_field_general=search_field_general,
            mode=mode,
        )
        self.linter = PubmedQueryListLinter(self, PubmedParser)

    def get_operator_node_tokens(self, token_nr: int) -> list:
        """Get operator node tokens"""
        node_content = self.query_dict[token_nr]["node_content"]
        operator_node_tokens = []
        for match in self.OPERATOR_NODE_ELEMENTS_REGEX.finditer(node_content):
            value = match.group(0)
            start, end = match.span()
            if value.upper() in {"AND", "OR", "NOT"}:
                token_type = OperatorNodeTokenTypes.LOGIC_OPERATOR
            elif self.LIST_ITEM_REF.match(value):
                token_type = OperatorNodeTokenTypes.LIST_ITEM_REFERENCE
            else:  # pragma: no cover
                token_type = OperatorNodeTokenTypes.UNKNOWN
            operator_node_tokens.append(
                ListToken(
                    value=value, type=token_type, level=token_nr, position=(start, end)
                )
            )
        return operator_node_tokens

    def _parse_operator_node(self, token_nr: int) -> Query:
        """Parse an operator node."""

        operator_node_tokens = self.get_operator_node_tokens(token_nr)

        children_tokens = [
            t.value.replace("#", "")
            for t in operator_node_tokens
            if t.type == OperatorNodeTokenTypes.LIST_ITEM_REFERENCE
        ]
        children = [self.query_dict[token_nr]["query"] for token_nr in children_tokens]
        operator = operator_node_tokens[1].value
        if operator.upper() in {"&", "AND"}:
            operator = Operators.AND
        if operator.upper() in {"|", "OR"}:
            operator = Operators.OR

        return Query(
            value=operator,
            search_field=None,
            children=children,
            position=(1, 1),
            platform="deactivated",
        )

    def parse(self) -> Query:
        """Parse the query in list format."""

        self.tokenize_list()
        self.linter.validate_tokens()
        self.linter.check_status()

        for token_nr, query_element in self.query_dict.items():
            print(f"*** Query list element: #{token_nr} *************************")
            if query_element["type"] == ListTokenTypes.QUERY_NODE:
                parser = self.parser_class(
                    query_element["node_content"],
                    search_field_general=self.search_field_general,
                )
                try:
                    query_element["query"] = parser.parse()
                except QuerySyntaxError:  # pragma: no cover
                    pass

                self.linter.messages[token_nr] = parser.linter.messages

            if query_element["type"] == ListTokenTypes.OPERATOR_NODE:
                query_element["query"] = self._parse_operator_node(
                    token_nr
                    # query_element["node_content"]
                )

        query = list(self.query_dict.values())[-1]["query"]

        # linter.check_status() ?
        query.set_platform_unchecked(PLATFORM.PUBMED.value)

        return query
