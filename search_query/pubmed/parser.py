#!/usr/bin/env python3
"""Pubmed query parser."""
from __future__ import annotations

import re
import typing

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
from search_query.query_near import NEARQuery
from search_query.query_term import Term

# pylint: disable=duplicate-code


class PubmedParser(QueryStringParser):
    """Parser for Pubmed queries."""

    FIELD_REGEX = re.compile(r"\[[^\[]*?\]")
    LOGIC_OPERATOR_REGEX = re.compile(r"(\||&|\b(?:AND|OR|NOT|:)\b)(?!\s?\[[^\[]*?\])")
    PARENTHESIS_REGEX = re.compile(r"[\(\)]")
    SEARCH_PHRASE_REGEX = re.compile(r"\".*?\"")
    TERM_REGEX = re.compile(r"[^\s\[\]()\|&]+")
    PROXIMITY_REGEX = re.compile(r"^\[(.+):~(.*)\]$")

    pattern = re.compile(
        "|".join(
            [
                FIELD_REGEX.pattern,
                LOGIC_OPERATOR_REGEX.pattern,
                PARENTHESIS_REGEX.pattern,
                SEARCH_PHRASE_REGEX.pattern,
                TERM_REGEX.pattern,
            ]
        ),
        flags=re.IGNORECASE,
    )

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        query_str: str,
        *,
        field_general: str = "",
        offset: typing.Optional[dict] = None,
        original_str: typing.Optional[str] = None,
        silent: bool = False,
        ignore_failing_linter: bool = False,
    ) -> None:
        """Initialize the parser."""
        super().__init__(
            query_str=query_str,
            field_general=field_general,
            offset=offset,
            original_str=original_str,
            silent=silent,
            ignore_failing_linter=ignore_failing_linter,
        )
        self.linter = PubmedQueryStringLinter(
            query_str=query_str,
            original_str=original_str,
            silent=silent,
            ignore_failing_linter=ignore_failing_linter,
        )

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
                token_type = TokenTypes.TERM

            self.tokens.append(
                Token(value=value, type=token_type, position=match.span())
            )

        self.adjust_token_positions()
        self.combine_subsequent_terms()

    def parse_query_tree(self, tokens: list) -> Query:
        """Parse a query from a list of tokens"""

        if self._is_compound_query(tokens):
            query = self._parse_compound_query(tokens)

        elif self._is_nested_query(tokens):
            query = self._parse_nested_query(tokens)

        elif self._is_term_query(tokens):
            query = self._parse_term(tokens)

        else:  # pragma: no cover
            raise ValueError()

        return query

    def _is_term_query(self, tokens: list) -> bool:
        """Check if the query is a search term"""
        return tokens[0].type == TokenTypes.TERM and len(tokens) <= 2

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

        return Query.create(
            value=operator_type,
            field=None,
            children=list(children),
            position=(query_start_pos, query_end_pos),
            platform="deactivated",
        )

    def _parse_nested_query(self, tokens: list) -> Query:
        """Parse a query nested inside a pair of parentheses"""
        inner_query = self.parse_query_tree(tokens[1:-1])
        return inner_query

    def _parse_term(self, tokens: list) -> Query:
        """Parse a search term"""
        term_token = tokens[0]

        # Determine the search field of the search term.
        if len(tokens) > 1 and tokens[1].type == TokenTypes.FIELD:
            if ":~" in tokens[1].value:
                # Parse NEAR query
                field_value, distance = self.PROXIMITY_REGEX.match(
                    tokens[1].value
                ).groups()  # type: ignore
                if not distance.isdigit():
                    distance = 3
                field_value = "[" + field_value + "]"
                return NEARQuery(
                    value=Operators.NEAR,
                    field=None,
                    children=[
                        Term(
                            value=term_token.value,
                            field=SearchField(
                                value=field_value, position=tokens[1].position
                            ),
                            position=tokens[0].position,
                            platform="deactivated",
                        )
                    ],
                    position=(tokens[0].position[0], tokens[1].position[1]),
                    distance=int(distance),  # type: ignore
                    platform="deactivated",
                )

            field = SearchField(value=tokens[1].value, position=tokens[1].position)
        else:
            # Select default field "all" if no search field is found.
            field = SearchField(value="[all]", position=(-1, -1))

        return Term(
            value=term_token.value,
            field=field,
            position=tokens[0].position,
            platform="deactivated",
        )

    def _pre_tokenization_checks(self) -> None:
        self.linter.handle_fully_quoted_query_str(self)

        self.linter.handle_nonstandard_quotes_in_query_str(self)
        self.linter.handle_prefix_in_query_str(
            self, prefix_regex=re.compile(r"^Pubmed.*\:\s*", flags=re.IGNORECASE)
        )
        self.linter.handle_suffix_in_query_str(self)

    def parse(self) -> Query:
        """Parse a query string"""

        self._pre_tokenization_checks()

        self.tokenize()

        self.tokens = self.linter.validate_tokens(
            tokens=self.tokens,
            query_str=self.query_str,
            field_general=self.field_general,
        )
        self.linter.check_status()

        # Parsing
        query = self.parse_query_tree(self.tokens)
        self.linter.validate_query_tree(query)
        self.linter.check_status()

        query.set_platform_unchecked(PLATFORM.PUBMED.value, silent=True)

        self.linter.validate_platform_query(query)  # type: ignore
        self.linter.check_status()

        return query


class PubmedListParser(QueryListParser):
    """Parser for Pubmed (list format) queries."""

    def __init__(
        self,
        query_list: str,
        *,
        field_general: str = "",
        ignore_failing_linter: bool = False,
    ) -> None:
        super().__init__(
            query_list,
            parser_class=PubmedParser,
            field_general=field_general,
            ignore_failing_linter=ignore_failing_linter,
        )
        self.linter = PubmedQueryListLinter(
            self,
            PubmedParser,
            ignore_failing_linter=ignore_failing_linter,
        )

    def parse(self) -> Query:
        """Parse the query in list format."""

        self.tokenize_list()
        self.linter.validate_tokens()
        self.linter.check_status()

        query_str, offset = self.build_query_str()

        query_parser = PubmedParser(
            query_str=query_str,
            original_str=self.query_list,
            field_general=self.field_general,
            offset=offset,
            silent=True,
            ignore_failing_linter=self.ignore_failing_linter,
        )
        try:
            query = query_parser.parse()
        except QuerySyntaxError as exc:
            raise exc
        finally:
            self.assign_linter_messages(query_parser.linter.messages, self.linter)

            self.linter.check_status()

        query.set_platform_unchecked(PLATFORM.PUBMED.value, silent=True)

        return query
