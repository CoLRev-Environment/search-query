"""Parser for AIS eLibrary query syntax."""
from __future__ import annotations

import re
import typing

from search_query.constants import Fields
from search_query.constants import Operators
from search_query.constants import PLATFORM
from search_query.constants import QueryErrorCode
from search_query.constants import SearchField
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.generic.linter import GenericLinter
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query_and import AndQuery
from search_query.query_near import NEARQuery
from search_query.query_not import NotQuery
from search_query.query_or import OrQuery
from search_query.query_term import Term

_FIELD_MAP = {
    "abstract": Fields.ABSTRACT,
    "subject": Fields.TOPIC,
    "author": Fields.AUTHOR,
    "institution": Fields.AFFILIATION,
    "title": Fields.TITLE,
    "document_type": Fields.PUBLICATION_TYPE,
    "publication_title": Fields.PUBLICATION_NAME,
    "configured_field_t_issn": Fields.ISSN,
}
_FIELD_REGEX = re.compile(
    r"(?:abstract|subject|author|institution|title|document_type|"
    r"publication_title|configured_field_t_issn):",
    re.IGNORECASE,
)
_BOOLEAN_REGEX = re.compile(r"\b(?:AND|OR|NOT)\b", re.IGNORECASE)
_PROXIMITY_REGEX = re.compile(r"\bNEAR/\d+\b", re.IGNORECASE)
_PARENTHESIS_REGEX = re.compile(r"[()]")
_QUOTED_TERM_REGEX = re.compile(r'"[^"]*"')
_TERM_REGEX = re.compile(
    r"\b(?!(?:AND|OR|NOT)\b)(?!NEAR/\d+\b)[\w?$-]+"
    r"(?:\s+(?!(?:AND|OR|NOT)\b)(?!NEAR/\d+\b)[\w?$-]+)*\*?",
    re.IGNORECASE,
)
_TOKEN_REGEX = re.compile(
    "|".join(
        [
            _FIELD_REGEX.pattern,
            _PROXIMITY_REGEX.pattern,
            _BOOLEAN_REGEX.pattern,
            _PARENTHESIS_REGEX.pattern,
            _QUOTED_TERM_REGEX.pattern,
            _TERM_REGEX.pattern,
        ]
    ),
    re.IGNORECASE,
)


class AISParser(QueryStringParser):
    """Parse Boolean, proximity, and fielded AIS eLibrary queries."""

    VERSION = "1"
    OPERATOR_PRECEDENCE = {
        Operators.OR: 0,
        Operators.AND: 1,
        Operators.NOT: 2,
        Operators.NEAR: 3,
    }

    # pylint: disable=too-many-arguments, duplicate-code
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
        super().__init__(
            query_str=query_str,
            field_general=field_general,
            offset=offset,
            original_str=original_str,
            silent=silent,
            ignore_failing_linter=ignore_failing_linter,
        )
        self.linter = GenericLinter(
            query_str=query_str,
            ignore_failing_linter=ignore_failing_linter,
        )
        self._index = 0
        self._current_field: typing.Optional[SearchField] = None

    def _syntax_error(
        self,
        details: str,
        position: typing.Optional[typing.Tuple[int, int]] = None,
    ) -> typing.NoReturn:
        if position is None:
            position = (0, len(self.query_str))
        self.linter.add_message(
            QueryErrorCode.INVALID_SYNTAX,
            positions=[position],
            details=details,
            fatal=True,
        )
        self.linter.check_status()
        raise ValueError(details)

    def tokenize(self) -> None:
        """Tokenize AIS fields, operators, parentheses, and search terms."""
        self.tokens = []
        previous_end = 0
        for match in _TOKEN_REGEX.finditer(self.query_str):
            gap = self.query_str[previous_end : match.start()]
            if gap.strip():
                self._syntax_error(
                    f"Unrecognized AIS query syntax: {gap.strip()}",
                    (previous_end, match.start()),
                )

            value = match.group(0)
            if _FIELD_REGEX.fullmatch(value):
                token_type = TokenTypes.FIELD
            elif _PROXIMITY_REGEX.fullmatch(value):
                token_type = TokenTypes.PROXIMITY_OPERATOR
            elif _BOOLEAN_REGEX.fullmatch(value):
                token_type = TokenTypes.LOGIC_OPERATOR
            elif value == "(":
                token_type = TokenTypes.PARENTHESIS_OPEN
            elif value == ")":
                token_type = TokenTypes.PARENTHESIS_CLOSED
            else:
                token_type = TokenTypes.TERM

            self.tokens.append(
                Token(value=value, type=token_type, position=match.span())
            )
            previous_end = match.end()

        tail = self.query_str[previous_end:]
        if tail.strip():
            self._syntax_error(
                f"Unrecognized AIS query syntax: {tail.strip()}",
                (previous_end, len(self.query_str)),
            )

    def _parse_primary(self) -> Query:
        while (
            self._index < len(self.tokens)
            and self.tokens[self._index].type == TokenTypes.FIELD
        ):
            field_token = self.tokens[self._index]
            field_name = field_token.value[:-1].lower()
            self._current_field = SearchField(
                _FIELD_MAP[field_name], position=field_token.position
            )
            self._index += 1

        if self._index >= len(self.tokens):
            self._syntax_error("Expected a search term.")

        token = self.tokens[self._index]
        if token.type == TokenTypes.PARENTHESIS_OPEN:
            self._index += 1
            field_before_group = self._current_field
            query = self._parse_expression()
            if (
                self._index >= len(self.tokens)
                or self.tokens[self._index].type != TokenTypes.PARENTHESIS_CLOSED
            ):
                self._syntax_error("Unbalanced opening parenthesis", token.position)
            self._index += 1
            self._current_field = field_before_group
            return query

        if token.type == TokenTypes.PARENTHESIS_CLOSED:
            self._syntax_error("Unexpected closing parenthesis", token.position)

        if token.type == TokenTypes.LOGIC_OPERATOR:
            if token.value.upper() != Operators.NOT:
                self._syntax_error(
                    f"Unexpected operator {token.value!r}", token.position
                )
            self._index += 1
            child = self._parse_primary()
            return NotQuery(
                [child],
                position=child.position,
                platform="deactivated",
            )

        if token.type != TokenTypes.TERM:
            self._syntax_error("Expected a search term.", token.position)

        self._index += 1
        value = token.value
        if value.startswith('"') and value.endswith('"') and len(value) >= 2:
            value = value[1:-1]
        return Term(
            value=value,
            field=self._current_field,
            position=token.position,
            platform="deactivated",
        )

    @staticmethod
    def _combined_position(
        left: Query, right: Query
    ) -> typing.Optional[tuple[int, int]]:
        if left.position is None or right.position is None:
            return None
        return left.position[0], right.position[1]

    def _combine(self, operator: str, left: Query, right: Query) -> Query:
        position = self._combined_position(left, right)
        children: typing.List[typing.Union[str, Query]]
        if operator == Operators.AND:
            children = (
                [*left.children, right]
                if left.operator and left.value == Operators.AND
                else [left, right]
            )
            return AndQuery(children, position=position, platform="deactivated")
        if operator == Operators.OR:
            children = (
                [*left.children, right]
                if left.operator and left.value == Operators.OR
                else [left, right]
            )
            return OrQuery(children, position=position, platform="deactivated")
        raise ValueError(f"Unsupported AIS Boolean operator: {operator}")

    def _parse_expression(self, min_precedence: int = 0) -> Query:
        left = self._parse_primary()
        while self._index < len(self.tokens):
            token = self.tokens[self._index]
            if token.type not in {
                TokenTypes.LOGIC_OPERATOR,
                TokenTypes.PROXIMITY_OPERATOR,
            }:
                break

            operator = token.value.upper()
            if operator.startswith("NEAR/"):
                operator = Operators.NEAR
                distance_match = re.fullmatch(r"NEAR/(\d+)", token.value, re.IGNORECASE)
                if not distance_match:
                    self._syntax_error("Invalid AIS proximity distance", token.position)
                distance = int(distance_match.group(1))
            else:
                distance = None

            precedence = self.OPERATOR_PRECEDENCE.get(operator)
            if precedence is None or precedence < min_precedence:
                break

            self._index += 1
            right = self._parse_expression(precedence + 1)
            if operator == Operators.NEAR:
                left = NEARQuery(
                    value=Operators.NEAR,
                    children=[left, right],
                    distance=typing.cast(int, distance),
                    position=self._combined_position(left, right),
                    platform="deactivated",
                )
            elif operator == Operators.NOT:
                negative = NotQuery(
                    [right], position=right.position, platform="deactivated"
                )
                left = self._combine(Operators.AND, left, negative)
            else:
                left = self._combine(operator, left, right)
        return left

    def parse(self) -> Query:
        """Parse an AIS eLibrary query into the current query tree model."""
        self.tokenize()
        self._index = 0
        self._current_field = None
        query = self._parse_expression()
        if self._index != len(self.tokens):
            token = self.tokens[self._index]
            self._syntax_error(f"Unexpected token {token.value!r}", token.position)

        query.set_platform_unchecked(PLATFORM.AISEL.value, silent=True)
        self.linter.validate_query_tree(query)
        self.linter.check_status()
        return query


class AISListParser(QueryListParser):
    """Reject numbered list input, which AIS eLibrary does not support."""

    VERSION = "1"

    def __init__(
        self,
        query_list: str,
        *,
        field_general: str = "",
        ignore_failing_linter: bool = False,
    ) -> None:
        super().__init__(
            query_list=query_list,
            parser_class=AISParser,
            field_general=field_general,
            ignore_failing_linter=ignore_failing_linter,
        )

    def parse(self) -> Query:
        raise ValueError("AIS eLibrary does not support numbered list queries.")
