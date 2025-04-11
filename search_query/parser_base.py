#!/usr/bin/env python3
"""Base query parser."""
from __future__ import annotations

import re
import typing
from abc import ABC
from abc import abstractmethod

import search_query.exception as search_query_exception
from search_query.constants import Colors
from search_query.constants import QueryErrorCode
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.query import Query


class QueryStringParser(ABC):
    """Abstract base class for query string parsers"""

    # Higher number=higher precedence
    PRECEDENCE = {"NOT": 2, "AND": 1, "OR": 0}

    def __init__(
        self, query_str: str, search_field_general: str, mode: str = "strict"
    ) -> None:
        self.query_str = query_str
        self.tokens: list = []
        self.mode = mode
        self.search_field_general = search_field_general
        self.linter_messages: typing.List[dict] = []

    def add_linter_message(
        self, error: QueryErrorCode, pos: tuple, details: str = ""
    ) -> None:
        """Add a linter message."""
        self.linter_messages.append(
            {
                "code": error.code,
                "label": error.label,
                "message": error.message,
                "is_fatal": error.is_fatal(),
                "pos": pos,
                "details": details,
            }
        )

    def get_token_types(self, tokens: list, *, legend: bool = False) -> str:
        """Print the token types"""

        mismatch = False

        for i in range(len(tokens) - 1):
            _, (_, current_end) = tokens[i]
            _, (next_start, _) = tokens[i + 1]
            if current_end + 1 != next_start:
                if re.match(r"\s*", self.query_str[current_end:next_start]):
                    continue
                # Position mismatch means: not tokenized
                print(
                    "NOT-TOKENIZED: "
                    f"{Colors.RED}{self.query_str[current_end:next_start]}{Colors.END} "
                    f"(positions {current_end}-{next_start} in query_str)"
                )
                mismatch = True

        output = ""
        for token, _ in tokens:
            if self.is_term(token):
                output += token
            elif self.is_search_field(token):
                output += f"{Colors.GREEN}{token}{Colors.END}"
            elif self.is_operator(token):
                output += f" {Colors.ORANGE}{token}{Colors.END} "
            elif self.is_parenthesis(token):
                output += f"{Colors.BLUE}{token}{Colors.END}"
            else:
                output += f"{Colors.RED}{token}{Colors.END}"

        if legend:
            output += f"\n Term\n {Colors.BLUE}Parenthesis{Colors.END}"
            output += f"\n {Colors.GREEN}Search field{Colors.END}"
            output += f"\n {Colors.ORANGE}Operator {Colors.END}"
            output += f"\n {Colors.RED}NOT-MATCHED{Colors.END}"
        if mismatch:
            raise ValueError
        return output

    @abstractmethod
    def is_search_field(self, token: str) -> bool:
        """Token is search field"""

    # TODO: should be attributes of Token  # pylint: disable=fixme
    def is_parenthesis(self, token: str) -> bool:
        """Token is parenthesis"""
        return token in ["(", ")"]

    def is_operator(self, token: str) -> bool:
        """Token is operator"""
        return bool(re.match(r"^(AND|OR|NOT)$", token, re.IGNORECASE))

    def is_term(self, token: str) -> bool:
        """Check if a token is a term."""
        return (
            not self.is_operator(token)
            and not self.is_parenthesis(token)
            and not self.is_search_field(token)
        )

    def combine_subsequent_terms(self) -> None:
        """Combine subsequent terms in the list of tokens."""
        # Combine subsequent terms (without quotes)
        # This would be more challenging in the regex
        combined_tokens = []
        i = 0
        while i < len(self.tokens):
            if (
                i + 1 < len(self.tokens)
                and self.is_term(self.tokens[i][0])
                and self.is_term(self.tokens[i + 1][0])
            ):
                combined_token = (
                    self.tokens[i][0] + " " + self.tokens[i + 1][0],
                    (self.tokens[i][1][0], self.tokens[i + 1][1][1]),
                )
                combined_tokens.append(combined_token)
                i += 2
            else:
                combined_tokens.append(self.tokens[i])
                i += 1

        self.tokens = combined_tokens

    def get_precedence(self, token: str) -> int:
        """Returns operator precedence for logical and proximity operators."""

        if token in self.PRECEDENCE:
            return self.PRECEDENCE[token]
        return -1  # Not an operator

    def add_higher_value(
        self,
        output: list[Token],
        current_value: int,
        value: int,
        art_par: int,
    ) -> tuple[list[Token], int]:
        """Adds open parenthesis to higher value operators"""
        temp: list[Token] = []
        depth_lvl = 0  # Counter for actual parenthesis

        while output:
            # Get previous tokens until right operator has been reached
            token = output.pop()

            # Track already existing and correct query blocks
            if token.type == TokenTypes.PARENTHESIS_CLOSED:
                depth_lvl += 1
            elif token.type == TokenTypes.PARENTHESIS_OPEN:
                depth_lvl -= 1

            temp.insert(0, token)

            if (
                token.type in [TokenTypes.LOGIC_OPERATOR, TokenTypes.PROXIMITY_OPERATOR]
                and depth_lvl == 0
            ):
                # Insert open parenthesis
                # depth_lvl ensures that already existing blocks are ignored

                # Insert open parenthesis after operator
                while current_value < value:
                    # Insert open parenthesis after operator
                    temp.insert(
                        1,
                        Token(
                            value="(",
                            type=TokenTypes.PARENTHESIS_OPEN,
                            position=(-1, -1),
                        ),
                    )
                    current_value += 1
                    art_par += 1
                break

        return temp, art_par

    # pylint: disable=too-many-branches
    def add_artificial_parentheses_for_operator_precedence(
        self,
        index: int = 0,
        output: typing.Optional[list] = None,
    ) -> tuple[int, list[Token]]:
        """
        Adds artificial parentheses with position (-1, -1)
        to enforce operator precedence.
        """
        if output is None:
            output = []
        # Value of operator
        value = 0
        # Value of previous operator
        current_value = -1
        # Added artificial parentheses
        art_par = 0

        while index < len(self.tokens):
            # Forward iteration through tokens

            if self.tokens[index].type == TokenTypes.PARENTHESIS_OPEN:
                output.append(self.tokens[index])
                index += 1
                index, output = self.add_artificial_parentheses_for_operator_precedence(
                    index, output
                )
                continue

            if self.tokens[index].type == TokenTypes.PARENTHESIS_CLOSED:
                output.append(self.tokens[index])
                index += 1
                # Add closed parenthesis in case there are still open ones
                while art_par > 0:
                    output.append(
                        Token(
                            value=")",
                            type=TokenTypes.PARENTHESIS_CLOSED,
                            position=(-1, -1),
                        )
                    )
                    art_par -= 1
                return index, output

            if self.tokens[index].type in [
                TokenTypes.LOGIC_OPERATOR,
                TokenTypes.PROXIMITY_OPERATOR,
            ]:
                value = self.get_precedence(self.tokens[index].value)

                if current_value in (value, -1):
                    # Same precedence → just add to output
                    output.append(self.tokens[index])
                    current_value = value

                elif value > current_value:
                    # Higher precedence → wrap previous part in parentheses
                    temp, art_par = self.add_higher_value(
                        output, current_value, value, art_par
                    )

                    output.extend(temp)
                    output.append(self.tokens[index])
                    current_value = value

                elif value < current_value:
                    # Insert close parenthesis for each point in value difference
                    while current_value > value:
                        # Lower precedence → close parenthesis
                        output.append(
                            Token(
                                value=")",
                                type=TokenTypes.PARENTHESIS_CLOSED,
                                position=(-1, -1),
                            )
                        )
                        current_value -= 1
                        art_par -= 1
                    output.append(self.tokens[index])
                    current_value = value

                index += 1
                continue

            # Default: search terms, fields, etc.
            output.append(self.tokens[index])
            index += 1

        # Add parenthesis in case there are missing ones
        if art_par > 0:
            while art_par > 0:
                output.append(
                    Token(
                        value=")", type=TokenTypes.PARENTHESIS_CLOSED, position=(-1, -1)
                    )
                )
                art_par -= 1
        if art_par < 0:
            while art_par < 0:
                output.insert(
                    0,
                    Token(
                        value="(", type=TokenTypes.PARENTHESIS_OPEN, position=(-1, -1)
                    ),
                )
                art_par += 1

        if index == len(self.tokens):
            output = self.flatten_redundant_artificial_nesting(output)
            self.tokens = output

        return index, output

    def flatten_redundant_artificial_nesting(self, tokens: list[Token]) -> list[Token]:
        """
        Flattens redundant artificial nesting:
        If two artificial open parens are followed eventually by
        two artificial close parens at the same level, removes the outer ones.
        """

        while True:
            len_initial = len(tokens)

            output = []
            i = 0
            while i < len(tokens):
                # Look ahead for double artificial opening
                if (
                    i + 1 < len(tokens)
                    and tokens[i].type == TokenTypes.PARENTHESIS_OPEN
                    and tokens[i + 1].type == TokenTypes.PARENTHESIS_OPEN
                    and tokens[i].position == (-1, -1)
                    and tokens[i + 1].position == (-1, -1)
                ):
                    # Look for matching double closing
                    inner_start = i + 2
                    depth = 2
                    j = inner_start
                    while j < len(tokens) and depth > 0:
                        if tokens[j].type == TokenTypes.PARENTHESIS_OPEN and tokens[
                            j
                        ].position == (-1, -1):
                            depth += 1
                        elif tokens[j].type == TokenTypes.PARENTHESIS_CLOSED and tokens[
                            j
                        ].position == (-1, -1):
                            depth -= 1
                        j += 1

                    # Check for double artificial closing
                    if (
                        j < len(tokens)
                        and tokens[j - 1].type == TokenTypes.PARENTHESIS_CLOSED
                        and tokens[j - 2].type == TokenTypes.PARENTHESIS_CLOSED
                        and tokens[j - 1].position == (-1, -1)
                        and tokens[j - 2].position == (-1, -1)
                    ):
                        # Skip outer pair
                        output.extend(tokens[i + 1 : j - 1])
                        i = j

                        continue

                output.append(tokens[i])
                i += 1

            # Repeat for multiple nestings
            if len_initial == len(output):
                break
            tokens = output

        return output

    @abstractmethod
    def parse(self) -> Query:
        """Parse the query."""


class QueryListParser:
    """QueryListParser"""

    LIST_ITEM_REGEX = r"^(\d+).\s+(.*)$"
    linter_messages: typing.List[dict] = []

    def __init__(
        self,
        query_list: str,
        search_field_general: str,
        parser_class: type[QueryStringParser],
    ) -> None:
        self.query_list = query_list
        self.parser_class = parser_class
        self.search_field_general = search_field_general

    def parse_dict(self) -> dict:
        """Tokenize the query_list."""
        query_list = self.query_list
        tokens = {}
        previous = 0
        for line in query_list.split("\n"):
            if line.strip() == "":
                continue

            match = re.match(self.LIST_ITEM_REGEX, line)
            if not match:
                raise ValueError(f"line not matching format: {line}")
            node_nr, node_content = match.groups()
            pos_start, pos_end = match.span(2)
            pos_start += previous
            pos_end += previous
            len_node_nr = match.span(1)[1] - match.span(1)[0]
            tokens[str(node_nr)] = {
                "node_content": node_content,
                "content_pos": (pos_start, pos_end),
                "node_nr_len": len_node_nr,
            }
            previous += len(line) + 1
        return tokens

    def get_token_str(self, token_nr: str) -> str:
        """Get the token string."""
        raise NotImplementedError(
            "get_token_str method must be implemented by inheriting classes"
        )

    def _replace_token_nr_by_query(
        self, query_list: list, token_nr: str, token_content: dict
    ) -> None:
        for i, (content, pos) in enumerate(query_list):
            token_str = self.get_token_str(token_nr)
            if token_str in content:
                query_list.pop(i)

                content_before = content[: content.find(token_str)]
                content_before_pos = (pos[0], pos[0] + len(content_before))
                content_after = content[content.find(token_str) + len(token_str) :]
                content_after_pos = (
                    content_before_pos[1] + len(token_str),
                    content_before_pos[1] + len(content_after) + len(token_str),
                )

                new_content = token_content["node_content"]
                new_pos = token_content["content_pos"]

                if content_after:
                    query_list.insert(i, (content_after, content_after_pos))

                # Insert the sub-query from the list with "artificial parentheses"
                # (positions with length 0)
                query_list.insert(i, (")", (-1, -1)))
                query_list.insert(i, (new_content, new_pos))
                query_list.insert(i, ("(", (-1, -1)))

                if content_before:
                    query_list.insert(i, (content_before, content_before_pos))

                break

    def dict_to_positioned_list(self, tokens: dict) -> list:
        """Convert a node to a positioned list."""

        root_node = list(tokens.values())[-1]
        query_list = [(root_node["node_content"], root_node["content_pos"])]

        for token_nr, token_content in reversed(tokens.items()):
            # iterate over query_list if token_nr is in the content,
            # split the content and insert the token_content, updating the content_pos
            self._replace_token_nr_by_query(query_list, token_nr, token_content)

        return query_list

    def parse(self) -> Query:
        """Parse the query in list format."""

        tokens = self.parse_dict()

        query_list = self.dict_to_positioned_list(tokens)
        query_string = "".join([query[0] for query in query_list])
        search_field_general = self.search_field_general

        try:
            query = self.parser_class(query_string, search_field_general).parse()

        except search_query_exception.QuerySyntaxError as exc:
            # Correct positions and query string
            # to display the error for the original (list) query
            new_pos = exc.pos
            for content, pos in query_list:
                # Note: artificial parentheses cannot be ignored here
                # because they were counted in teh query_string
                segment_length = len(content)

                if new_pos[0] - segment_length >= 0:
                    new_pos = (new_pos[0] - segment_length, new_pos[1] - segment_length)
                    continue
                segment_beginning = pos[0]
                new_pos = (
                    new_pos[0] + segment_beginning,
                    new_pos[1] + segment_beginning,
                )
                exc.pos = new_pos
                break

            exc.query_string = self.query_list
            raise search_query_exception.QuerySyntaxError(
                msg="", query_string=self.query_list, pos=exc.pos
            )

        return query
