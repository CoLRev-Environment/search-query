#!/usr/bin/env python3
"""EBSCO query parser."""
from __future__ import annotations

import re
import typing

from search_query.constants import PLATFORM
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.ebscohost.linter import EBSCOListLinter
from search_query.ebscohost.linter import EBSCOQueryStringLinter
from search_query.exception import QuerySyntaxError
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField
from search_query.query_term import Term

# pylint: disable=duplicate-code


class EBSCOParser(QueryStringParser):
    """Parser for EBSCO queries."""

    PARENTHESIS_REGEX = re.compile(r"[()]")
    LOGIC_OPERATOR_REGEX = re.compile(r"(?i:\b(AND|OR|NOT)\b)")
    PROXIMITY_OPERATOR_REGEX = re.compile(
        r"(?i:[NW]\d+|(NEAR|WITHIN)/\d+)"
    )
    FIELD_REGEX = re.compile(r"\b([A-Z]{2})\b")

    STOP = r'(?:[()]|\b(?:AND|OR|NOT)\b|(?:[NW]\d+|(?:NEAR|WITHIN)/\d+))'
    QUOTED_TERM_REGEX = re.compile(
        rf'"(?:(?!{STOP}|").)*"?'
    )
    # QUOTED_TERM_REGEX = re.compile(f'".*?"')
    TERM_REGEX = re.compile(r'[^\s()"]+')

    OPERATOR_REGEX = re.compile(
        "|".join([LOGIC_OPERATOR_REGEX.pattern, PROXIMITY_OPERATOR_REGEX.pattern])
    )

    pattern = re.compile(
        "|".join(
            [
                PARENTHESIS_REGEX.pattern,
                LOGIC_OPERATOR_REGEX.pattern,
                PROXIMITY_OPERATOR_REGEX.pattern,
                FIELD_REGEX.pattern,
                QUOTED_TERM_REGEX.pattern,
                TERM_REGEX.pattern,
            ]
        )
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
            query_str,
            field_general=field_general,
            offset=offset,
            original_str=original_str,
            silent=silent,
            ignore_failing_linter=ignore_failing_linter,
        )
        self.linter = EBSCOQueryStringLinter(
            query_str=query_str,
            original_str=original_str,
            silent=silent,
            ignore_failing_linter=ignore_failing_linter,
        )

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
                # Reclassify the second field token as a TERM
                next_token.type = TokenTypes.TERM

        # Term followed by operator is misclassified as a field token
        for i in range(len(self.tokens) - 1):
            current = self.tokens[i]
            next_token = self.tokens[i + 1]

            if (
                current.type == TokenTypes.FIELD
                and next_token.type in [TokenTypes.LOGIC_OPERATOR, TokenTypes.PROXIMITY_OPERATOR]
                and is_potential_term(current.value)
            ):
                # Reclassify the second field token as a TERM
                current.type = TokenTypes.TERM

        # Operator followed by a field token followed by a closing parenthesis
        for i in range(len(self.tokens) - 2):
            current = self.tokens[i]
            next_token = self.tokens[i + 1]
            next_next_token = self.tokens[i + 2]

            if (
                current.type
                in [TokenTypes.LOGIC_OPERATOR, TokenTypes.PROXIMITY_OPERATOR]
                and next_token.type == TokenTypes.FIELD
                and next_next_token.type == TokenTypes.PARENTHESIS_CLOSED
            ):
                # Reclassify the field token as a TERM
                next_token.type = TokenTypes.TERM

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
            elif self.FIELD_REGEX.fullmatch(value):
                token_type = TokenTypes.FIELD
            elif self.QUOTED_TERM_REGEX.fullmatch(value):
                token_type = TokenTypes.TERM
            elif self.TERM_REGEX.fullmatch(value):
                token_type = TokenTypes.TERM
            else:  # pragma: no cover
                token_type = TokenTypes.UNKNOWN

            # Append token with its type and position to self.tokens
            self.tokens.append(
                Token(value=value, type=token_type, position=(start, end))
            )

        self.adjust_token_positions()

        # Combine subsequent terms in case of no quotation marks
        self.fix_ambiguous_tokens()
        self.combine_subsequent_terms()

    def parse_query_tree(
        self, tokens: list[Token], field_context: SearchField | None = None
    ) -> Query:
        """Top-down predictive parser for query tree."""

        # Look ahead to see if field is followed by something valid
        if (
            tokens
            and tokens[0].type == TokenTypes.FIELD
            and len(tokens) > 1
            and tokens[1].type == TokenTypes.PARENTHESIS_OPEN
        ):
            field_token = tokens.pop(0)
            field_context = SearchField(
                value=field_token.value, position=field_token.position
            )

        if self._is_compound_query(tokens):
            return self._parse_compound_query(tokens, field_context)
        if self._is_nested_query(tokens):
            return self._parse_nested_query(tokens, field_context)
        if self._is_term_query(tokens):
            return self._parse_term(tokens, field_context)
        raise ValueError(
            f"Unrecognized query structure: \n{' '.join(t.value for t in tokens)}\n"
            "Expected a term, nested query, or compound query."
        )

    def _is_term_query(self, tokens: list[Token]) -> bool:
        return bool(tokens and len(tokens) <= 2 and tokens[-1].type == TokenTypes.TERM)

    def _is_compound_query(self, tokens: list[Token]) -> bool:
        return bool(self._get_operator_indices(tokens))

    def _is_nested_query(self, tokens: list[Token]) -> bool:
        return (
            tokens[0].type == TokenTypes.PARENTHESIS_OPEN
            and tokens[-1].type == TokenTypes.PARENTHESIS_CLOSED
        )

    def _get_operator_type(self, token: Token) -> str:
        val = token.value.upper()
        if val in {"AND"}:
            return "AND"
        if val in {"OR"}:
            return "OR"
        if val == "NOT":
            return "NOT"
        if val.startswith("N") or val.startswith("W"):
            return "NEAR" if val.startswith("N") else "WITHIN"
        raise ValueError(f"Unrecognized operator: {token.value}")

    def _get_operator_indices(self, tokens: list[Token]) -> list[int]:
        """Get indices of top-level operators with the lowest precedence value."""
        indices: list[int] = []
        depth = 0
        prev_op = None

        for i, token in enumerate(tokens):
            if token.type == TokenTypes.PARENTHESIS_OPEN:
                depth += 1
            elif token.type == TokenTypes.PARENTHESIS_CLOSED:
                depth -= 1
            elif depth == 0 and token.type in [TokenTypes.LOGIC_OPERATOR, TokenTypes.PROXIMITY_OPERATOR]:
                op = self._get_operator_type(token)
                if prev_op is None:
                    prev_op = op
                    indices.append(i)
                elif op == prev_op:
                    indices.append(i)
                elif self.linter.get_precedence(op) < self.linter.get_precedence(prev_op):
                    indices = [i]
        return indices

    def _parse_compound_query(
        self, tokens: list[Token], field_context: SearchField | None
    ) -> Query:
        op_indices = self._get_operator_indices(tokens)
        if not op_indices:
            raise ValueError("No operator found for compound query.")

        operator_type = self._get_operator_type(tokens[op_indices[0]])
        distance = 0
        if operator_type in {"NEAR", "WITHIN"}:
            distance = self._extract_proximity_distance(tokens[op_indices[0]])
        children = []

        start = 0
        for idx in op_indices:
            sub_tokens = tokens[start:idx]
            children.append(
                self.parse_query_tree(sub_tokens, field_context=field_context)
            )
            start = idx + 1

        children.append(
            self.parse_query_tree(tokens[start:], field_context=field_context)
        )

        return Query.create(
            value=operator_type,
            field=field_context,
            children=children,  # type: ignore
            position=(tokens[0].position[0], tokens[-1].position[1]),
            platform="deactivated",
            distance=distance,
        )

    def _parse_nested_query(
        self, tokens: list[Token], field_context: SearchField | None
    ) -> Query:
        return self.parse_query_tree(tokens[1:-1], field_context=field_context)

    def _parse_term(
        self, tokens: list[Token], field_context: SearchField | None
    ) -> Query:
        if len(tokens) == 1:
            return Term(
                value=tokens[0].value,
                position=tokens[0].position,
                field=field_context or None,
                platform="deactivated",
            )
        assert len(tokens) == 2, "Expected exactly one search term token."

        token = tokens[1]

        return Term(
            value=token.value,
            position=token.position,
            field=SearchField(
                value=tokens[0].value, position=tokens[0].position or (-1, -1)
            ),
            platform="deactivated",
        )

    def _pre_tokenization_checks(self) -> None:
        self.linter.handle_fully_quoted_query_str(self)
        self.linter.handle_nonstandard_quotes_in_query_str(self)
        self.linter.handle_suffix_in_query_str(self)
        self.linter.handle_prefix_in_query_str(
            self,
            prefix_regex=re.compile(
                r"^EBSCOHost.*\:\s*|PsycInfo|ERIC|CINAHL with Full Text",
                flags=re.IGNORECASE,
            ),
        )

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

        query.set_platform_unchecked(PLATFORM.EBSCO.value, silent=True)

        return query


class EBSCOListParser(QueryListParser):
    """Parser for EBSCO (list format) queries."""

    LIST_ITEM_REFERENCE = re.compile(r"S\d+|\#\d+")

    def __init__(
        self,
        query_list: str,
        field_general: str = "",
        ignore_failing_linter: bool = False,
    ) -> None:
        super().__init__(
            query_list=query_list,
            parser_class=EBSCOParser,
            field_general=field_general,
            ignore_failing_linter=ignore_failing_linter,
        )
        self.linter = EBSCOListLinter(
            parser=self,
            string_parser_class=EBSCOParser,
            ignore_failing_linter=ignore_failing_linter,
        )

    def parse(self) -> Query:
        """Parse EBSCO list query."""

        self.tokenize_list()
        self.linter.validate_tokens()
        self.linter.check_status()

        query_str, offset = self.build_query_str()

        query_parser = EBSCOParser(
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

        query.set_platform_unchecked(PLATFORM.EBSCO.value, silent=True)

        return query
