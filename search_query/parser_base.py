#!/usr/bin/env python3
"""Base query parser."""
from __future__ import annotations

import re
import typing

import search_query.exception as search_query_exception
from search_query.constants import Colors
from search_query.query import Query


class QueryStringParser:
    """QueryStringParser"""

    tokens: list
    linter_messages: typing.List[dict] = []

    def __init__(self, query_str: str, mode: str = "strict") -> None:
        self.query_str = query_str
        self.tokens = []
        self.mode = mode

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

    def is_search_field(self, token: str) -> bool:
        """Token is search field"""
        raise NotImplementedError(
            "is_search_field method must be implemented by inheriting classes"
        )

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

    def parse(self) -> Query:
        """Parse the query."""
        raise NotImplementedError(
            "parse method must be implemented by inheriting classes"
        )


class QueryListParser:
    """QueryListParser"""

    LIST_ITEM_REGEX = r"^(\d+).\s+(.*)$"

    def __init__(self, query_list: str, parser_class: type[QueryStringParser]) -> None:
        self.query_list = query_list
        self.parser_class = parser_class

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

        try:
            query = self.parser_class(query_string).parse()

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
