#!/usr/bin/env python3
"""Web-of-Science query parser."""
from __future__ import annotations

import re
import typing

from search_query.constants import PLATFORM
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.exception import QuerySyntaxError
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField
from search_query.query_near import NEARQuery
from search_query.query_not import NotQuery
from search_query.query_term import Term
from search_query.wos.constants import field_general_to_syntax
from search_query.wos.linter import WOSQueryListLinter
from search_query.wos.linter import WOSQueryStringLinter

# pylint: disable=duplicate-code


class WOSParser(QueryStringParser):
    """Parser for Web-of-Science queries."""

    # 1) structured parts
    FIELD_REGEX = re.compile(r"\b\w{2,3}=")
    LOGIC_OPERATOR_REGEX = re.compile(r"\b(AND|OR|NOT)\b", flags=re.IGNORECASE)
    PROXIMITY_OPERATOR_REGEX = re.compile(
        r"\b(NEAR/\d{1,2}|NEAR)\b", flags=re.IGNORECASE
    )
    PARENTHESIS_REGEX = re.compile(r"[\(\)]")

    # 2) quoted term — this matches only if quotes are balanced.
    QUOTED_TERM_REGEX = re.compile(r"\".*?\"")

    # 3) fallback term:
    # make this permissive enough to also swallow a stray `"`,
    # but still exclude structural WOS characters (space, parens, equals).
    PERMISSIVE_TERM_REGEX = re.compile(r"[^\s\(\)=]+")

    # build the combined pattern:
    # fields → logic/proximity → parens → quoted term → term
    pattern = re.compile(
        "|".join(
            [
                FIELD_REGEX.pattern,
                LOGIC_OPERATOR_REGEX.pattern,
                PROXIMITY_OPERATOR_REGEX.pattern,
                PARENTHESIS_REGEX.pattern,
                QUOTED_TERM_REGEX.pattern,
                PERMISSIVE_TERM_REGEX.pattern,
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
        self.linter = WOSQueryStringLinter(
            query_str=query_str,
            original_str=original_str,
            silent=silent,
            ignore_failing_linter=ignore_failing_linter,
        )

    def tokenize(self) -> None:
        """Tokenize the query_str."""

        self.tokens = []
        for match in self.pattern.finditer(self.query_str):
            value = match.group(0)
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
            elif self.FIELD_REGEX.fullmatch(value):
                token_type = TokenTypes.FIELD
            elif self.QUOTED_TERM_REGEX.fullmatch(value):
                # fully quoted term
                token_type = TokenTypes.TERM
            elif self.PERMISSIVE_TERM_REGEX.fullmatch(value):
                token_type = TokenTypes.TERM
            else:  # pragma: no cover
                token_type = TokenTypes.UNKNOWN

            self.tokens.append(Token(value=value, type=token_type, position=position))

        self.adjust_token_positions()

        self.combine_subsequent_terms()
        self.split_operators_with_missing_whitespace()

    def combine_subsequent_terms(self) -> None:
        """Combine subsequent terms in the list of tokens."""
        combined_tokens: typing.List[Token] = []
        i = 0
        j = 0

        while i < len(self.tokens):
            if len(combined_tokens) > 0:
                if (
                    self.tokens[i].type == TokenTypes.TERM
                    and combined_tokens[j - 1].type == TokenTypes.TERM
                ):
                    combined_token = Token(
                        value=combined_tokens[j - 1].value + " " + self.tokens[i].value,
                        type=TokenTypes.TERM,
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
                and self.tokens[i].type == TokenTypes.TERM
                and self.tokens[i + 1].type == TokenTypes.TERM
            ):
                combined_token = Token(
                    value=self.tokens[i].value + " " + self.tokens[i + 1].value,
                    type=TokenTypes.TERM,
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

    def parse_query_tree(self, tokens: list[Token]) -> Query:
        """Top-down predictive parser for query tree."""

        if self._is_not_query(tokens):
            return self._parse_not_query(tokens)
        if self._is_compound_query(tokens):
            return self._parse_compound_query(tokens)
        if self._is_near_query(tokens):
            return self._parse_near_query(tokens)
        if self._is_nested_query(tokens):
            return self._parse_nested_query(tokens)
        if self._is_term_query(tokens):
            return self._parse_term(tokens)

        raise ValueError(f"Unrecognized query structure: {tokens}")

    def _is_term_query(self, tokens: list[Token]) -> bool:
        return bool(tokens and len(tokens) <= 2 and tokens[-1].type == TokenTypes.TERM)

    def _is_near_query(self, tokens: list[Token]) -> bool:
        return (
            len(tokens) == 3
            and tokens[0].type == TokenTypes.TERM
            and tokens[1].type == TokenTypes.PROXIMITY_OPERATOR
            and tokens[2].type == TokenTypes.TERM
        )

    def _is_not_query(self, tokens: list[Token]) -> bool:
        return (
            len(tokens) >= 2
            and tokens[0].type == TokenTypes.LOGIC_OPERATOR
            and tokens[0].value.upper() == "NOT"
        )

    def _is_compound_query(self, tokens: list[Token]) -> bool:
        return bool(self._get_operator_indices(tokens))

    def _is_nested_query(self, tokens: list[Token]) -> bool:
        return (
            tokens[0].type == TokenTypes.PARENTHESIS_OPEN
            or (
                tokens[0].type == TokenTypes.FIELD
                and len(tokens) > 1
                and tokens[1].type == TokenTypes.PARENTHESIS_OPEN
            )
        ) and tokens[-1].type == TokenTypes.PARENTHESIS_CLOSED

    def _get_operator_type(self, token: Token) -> str:
        val = token.value.upper()
        if val in {"AND", "&"}:
            return "AND"
        if val in {"OR", "|"}:
            return "OR"
        if val == "NOT":
            return "NOT"
        raise ValueError(f"Unrecognized operator: {token.value}")

    def _get_operator_indices(self, tokens: list[Token]) -> list[int]:
        indices: list[int] = []
        depth = 0
        first_op = None

        for i, token in enumerate(tokens):
            if token.type == TokenTypes.PARENTHESIS_OPEN:
                depth += 1
            elif token.type == TokenTypes.PARENTHESIS_CLOSED:
                depth -= 1
            elif depth == 0 and token.type == TokenTypes.LOGIC_OPERATOR:
                op = self._get_operator_type(token)
                if first_op is None:
                    first_op = op
                elif op != first_op:
                    raise ValueError("Mixed operators without parentheses.")
                indices.append(i)
        return indices

    def _parse_compound_query(self, tokens: list[Token]) -> Query:
        op_indices = self._get_operator_indices(tokens)
        if not op_indices:
            raise ValueError("No operator found for compound query.")

        operator_type = self._get_operator_type(tokens[op_indices[0]])
        children = []

        start = 0
        for idx in op_indices:
            sub_tokens = tokens[start:idx]
            children.append(self.parse_query_tree(sub_tokens))
            start = idx + 1

        children.append(self.parse_query_tree(tokens[start:]))

        return Query.create(
            value=operator_type,
            children=children,  # type: ignore
            position=(tokens[0].position[0], tokens[-1].position[1]),
            platform="deactivated",
        )

    def _parse_nested_query(self, tokens: list[Token]) -> Query:
        if tokens[0].type == TokenTypes.PARENTHESIS_OPEN:
            nested_query = self.parse_query_tree(tokens[1:-1])
        elif (
            tokens[0].type == TokenTypes.FIELD
            and len(tokens) > 1
            and tokens[1].type == TokenTypes.PARENTHESIS_OPEN
        ):
            nested_query = self.parse_query_tree(tokens[2:-1])
            nested_query.field = SearchField(
                value=tokens[0].value, position=tokens[0].position
            )
        else:
            raise ValueError("Invalid nested query structure.")

        return nested_query

    def _parse_near_query(self, tokens: list[Token]) -> Query:
        left_token = tokens[0]
        operator_token = tokens[1]
        right_token = tokens[2]

        distance = self._extract_proximity_distance(operator_token)

        return NEARQuery(
            value=operator_token.value.upper().split("/")[0],
            distance=distance,
            position=(left_token.position[0], right_token.position[1]),
            children=[
                Term(
                    value=left_token.value,
                    position=left_token.position,
                    field=None,
                    platform="deactivated",
                ),
                Term(
                    value=right_token.value,
                    position=right_token.position,
                    field=None,
                    platform="deactivated",
                ),
            ],
            platform="deactivated",
        )

    def _parse_not_query(self, tokens: list[Token]) -> Query:
        # NOT must be followed by a single query (term or nested)
        assert tokens[0].value.upper() == "NOT"
        child = self.parse_query_tree(tokens[1:])

        return NotQuery(
            children=[child],
            platform="deactivated",
        )

    def _parse_term(self, tokens: list[Token]) -> Query:
        # term or field + term
        if len(tokens) == 1:
            return Term(
                value=tokens[0].value,
                position=tokens[0].position,
                platform="deactivated",
            )
        assert len(tokens) == 2
        return Term(
            value=tokens[1].value,
            position=tokens[1].position,
            field=SearchField(
                value=tokens[0].value,
                position=tokens[0].position or (-1, -1),
            ),
            platform="deactivated",
        )

    def _extract_proximity_distance(self, token: Token) -> int:
        """Extract distance from proximity operator like NEAR/5."""
        match = re.search(r"/(\d+)", token.value)
        if not match:
            raise ValueError(f"Invalid proximity operator: {token.value}")
        return int(match.group(1))

    def _pre_tokenization_checks(self) -> None:
        self.linter.handle_fully_quoted_query_str(self)
        self.linter.handle_nonstandard_quotes_in_query_str(self)
        self.linter.handle_prefix_in_query_str(
            self, prefix_regex=re.compile(r"^Web of Science\:?\s*", flags=re.IGNORECASE)
        )
        self.linter.handle_suffix_in_query_str(self)

    def parse(self) -> Query:
        """Parse a query string."""

        self._pre_tokenization_checks()

        self.tokenize()

        self.tokens = self.linter.validate_tokens(
            tokens=self.tokens,
            query_str=self.query_str,
            field_general=self.field_general,
        )
        self.linter.check_status()

        query = self.parse_query_tree(self.tokens)
        self.linter.validate_query_tree(query)
        self.linter.check_status()

        if self.field_general:
            field_general = SearchField(
                value=field_general_to_syntax(self.field_general),
                position=(-1, -1),
            )
            query.field = field_general

        query.set_platform_unchecked(PLATFORM.WOS.value, silent=True)

        return query


class WOSListParser(QueryListParser):
    """Parser for Web-of-Science (list format) queries."""

    def __init__(
        self,
        query_list: str,
        field_general: str = "",
        ignore_failing_linter: bool = False,
    ) -> None:
        super().__init__(
            query_list,
            parser_class=WOSParser,
            field_general=field_general,
            ignore_failing_linter=ignore_failing_linter,
        )
        self.linter = WOSQueryListLinter(
            parser=self,
            string_parser_class=WOSParser,
            original_query_str=query_list,
            ignore_failing_linter=ignore_failing_linter,
        )

    def parse(self) -> Query:
        """Parse the list of queries."""

        self.tokenize_list()
        self.linter.validate_list_tokens()
        self.linter.check_status()

        query_str, offset = self.build_query_str()

        query_parser = WOSParser(
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

        query.set_platform_unchecked(PLATFORM.WOS.value, silent=True)

        return query
