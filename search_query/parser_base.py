#!/usr/bin/env python3
"""Base query parser."""
from __future__ import annotations

import re
import typing
from abc import ABC
from abc import abstractmethod

from search_query.constants import GENERAL_ERROR_POSITION
from search_query.constants import ListToken
from search_query.constants import ListTokenTypes
from search_query.constants import OperatorNodeTokenTypes
from search_query.constants import Token
from search_query.constants import TokenTypes
from search_query.query import Query

if typing.TYPE_CHECKING:  # pragma: no cover
    from search_query.linter_base import QueryStringLinter


class QueryStringParser(ABC):
    """Abstract base class for query string parsers"""

    # Note: override the following:
    OPERATOR_REGEX: re.Pattern = re.compile(r"^(AND|OR|NOT)$", flags=re.IGNORECASE)
    LOGIC_OPERATOR_REGEX = re.compile(r"\b(AND|OR|NOT)\b", flags=re.IGNORECASE)

    linter: QueryStringLinter

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
        self.query_str = query_str
        self.tokens: list = []
        # The external fields (in the JSON file: "field")
        self.field_general = field_general
        self.silent = silent
        self.ignore_failing_linter = ignore_failing_linter
        self.offset = offset or {}
        self.original_str = original_str or query_str

    def print_tokens(self) -> None:
        """Print the tokens in a formatted table."""
        for token in self.tokens:
            # UNKNOWN could be color-coded
            print(f"{token.value:<30} {token.type:<40} {str(token.position):<10}")

    def adjust_token_positions(self) -> None:
        """Adjust virtual positions of tokens using offset mapping."""
        if (
            not hasattr(self, "offset")
            or not isinstance(self.offset, dict)
            or not self.offset
        ):
            return  # No offsets to apply

        # print(f"Adjusting token positions with offsets: {self.offset}")
        next_offset_keys = sorted(self.offset.keys())
        current_offset = 0
        next_offset_index = 0
        virtual_position = self.offset[next_offset_keys[0]] if next_offset_keys else 0
        last_end = 0

        for token in self.tokens:
            start, end = token.position

            # Apply offset shifts if we passed new offset positions
            offset_applied = False
            while (
                next_offset_index < len(next_offset_keys)
                and start >= next_offset_keys[next_offset_index]
            ):
                current_offset = self.offset[next_offset_keys[next_offset_index]]
                virtual_position = current_offset
                offset_applied = True
                next_offset_index += 1

            # print(f"Virtual position: {virtual_position}")
            gap_length = start - last_end
            if not offset_applied and gap_length > 0:
                virtual_position += gap_length
                # print(
                #     f"Adjusted virtual position: {virtual_position} "
                #     f"(gap length {gap_length})"
                # )

            token_length = end - start
            if virtual_position == -1:
                token_length = 0  # Special case for artificial parentheses tokens

            # print("")
            # print(f"{token.value} (token value)")
            # print(
            #     self.query_str[token.position[0] : token.position[1]]
            #     + f" (query_str, original positions: {token.position})"
            # )
            token.position = (virtual_position, virtual_position + token_length)
            # print(
            #     self.original_str[token.position[0] : token.position[1]]
            #     + f" (original_str, adjusted positions: {token.position})"
            # )
            # print("---------------")
            # print(self.original_str)
            # Compare only letters (ignore case and non-letters)
            orig = "".join(
                c
                for c in self.original_str[token.position[0] : token.position[1]]
                if c.isalpha()
            ).lower()
            val = "".join(c for c in token.value if c.isalpha()).lower()
            assert orig == val, (
                f"Token value mismatch (letters only): {token.value} != "
                f"{self.original_str[token.position[0]:token.position[1]]}"
            )
            virtual_position += token_length
            assert virtual_position == token.position[1]
            last_end = end

    def combine_subsequent_terms(self) -> None:
        """Combine all consecutive TERM tokens into one."""
        combined_tokens = []
        i = 0
        while i < len(self.tokens):
            if self.tokens[i].type == TokenTypes.TERM:
                start = self.tokens[i].position[0]
                value_parts = [self.tokens[i].value]
                end = self.tokens[i].position[1]
                i += 1
                while i < len(self.tokens) and self.tokens[i].type == TokenTypes.TERM:
                    value_parts.append(self.tokens[i].value)
                    end = self.tokens[i].position[1]
                    i += 1
                combined_token = Token(
                    value=" ".join(value_parts),
                    type=TokenTypes.TERM,
                    position=(start, end),
                )
                combined_tokens.append(combined_token)
            else:
                combined_tokens.append(self.tokens[i])
                i += 1

        self.tokens = combined_tokens

    def split_operators_with_missing_whitespace(self) -> None:
        """Split operators that are not separated by whitespace."""
        # This is a workaround for the fact that some platforms do not support
        # operators without whitespace, e.g. "AND" or "OR"
        # This is not a problem for the parser, but for the linter
        # which expects whitespace between operators and search terms

        i = 0
        while i < len(self.tokens) - 1:
            token = self.tokens[i]
            next_token = self.tokens[i + 1]

            appended_operator_match = re.search(r"(AND|OR|NOT)$", token.value)

            # if the end of a search term (value) is a capitalized operator
            # without a whitespace, split the tokens
            if (
                token.type == TokenTypes.TERM
                and next_token.type != TokenTypes.LOGIC_OPERATOR
                and appended_operator_match
            ):
                # Split the operator from the search term

                appended_operator = appended_operator_match.group(0)
                token.value = token.value[: -len(appended_operator)]
                token.position = (
                    token.position[0],
                    token.position[1] - len(appended_operator),
                )
                # insert operator token afterwards
                operator_token = Token(
                    value=appended_operator,
                    type=TokenTypes.LOGIC_OPERATOR,
                    position=(
                        token.position[1],
                        token.position[1] + len(appended_operator),
                    ),
                )
                self.tokens.insert(i + 1, operator_token)

                i += 2  # Skip over the newly inserted operator token
            else:
                i += 1

    @abstractmethod
    def parse(self) -> Query:
        """Parse the query."""


class QueryListParser:
    """QueryListParser"""

    LIST_QUERY_LINE_REGEX: re.Pattern = re.compile(r"^\s*(\d+).\s+(.*)$")
    LIST_ITEM_REFERENCE = re.compile(r"#\d+")

    def __init__(
        self,
        query_list: str,
        *,
        parser_class: type[QueryStringParser],
        field_general: str,
        ignore_failing_linter: bool = False,
    ) -> None:
        # Remove leading whitespaces/newlines from the query_list
        # to ensure correct token positions
        self.query_list = query_list.lstrip()
        self.parser_class = parser_class
        self.field_general = field_general
        self.ignore_failing_linter = ignore_failing_linter
        self.query_dict: dict = {}

    def tokenize_list(self) -> None:
        """Tokenize the query_list."""
        # pylint: disable=too-many-locals
        query_list = self.query_list
        previous = 0
        for line in query_list.split("\n"):
            if line.strip() == "":
                continue

            match = self.LIST_QUERY_LINE_REGEX.match(line)
            if not match:  # pragma: no cover
                raise ValueError(f"line not matching format: {line}")
            node_nr, node_content = match.groups()
            pos_start, pos_end = match.span(2)
            pos_start += previous
            pos_end += previous
            query_type = ListTokenTypes.QUERY_NODE
            if self.LIST_ITEM_REFERENCE.search(node_content):
                query_type = ListTokenTypes.OPERATOR_NODE

            self.query_dict[str(node_nr)] = {
                "node_content": node_content,
                "content_pos": (pos_start, pos_end),
                "type": query_type,
            }
            previous += len(line) + 1

    def tokenize_operator_node(self, query_str: str, node_nr: int) -> list:
        """Tokenize the query string into list-references and logic operator tokens."""

        tokens = []
        pos = 0
        length = len(query_str)

        while pos < length:
            # Skip any whitespace
            while pos < length and query_str[pos].isspace():
                pos += 1

            if pos >= length:
                break

            match = self.LIST_ITEM_REFERENCE.match(query_str, pos)
            if match:
                start, end = match.span()
                tokens.append(
                    ListToken(
                        value=match.group(),
                        type=OperatorNodeTokenTypes.LIST_ITEM_REFERENCE,
                        level=node_nr,
                        position=(start, end),
                    )
                )
                pos = end
            else:
                # Collect non-space, non-list-ref characters
                start = pos
                while (
                    pos < length
                    and not query_str[pos].isspace()
                    and not self.LIST_ITEM_REFERENCE.match(query_str, pos)
                ):
                    pos += 1

                if start != pos:
                    value = query_str[start:pos]
                    tokens.append(
                        ListToken(
                            value=value,
                            type=OperatorNodeTokenTypes.NON_LIST_ITEM_REFERENCE,
                            level=node_nr,
                            position=(start, pos),
                        )
                    )

        return tokens

    def build_query_str(self) -> typing.Tuple[str, dict]:
        """Build the query string from the list format."""
        # The `offset` dictionary maps positions in the `query_str` back to their
        # corresponding character positions in the original (list) query string.
        #
        # Key (int): character offset in the `query_str`.
        # Value (int): character offset in the original input (e.g., from content_pos).
        #
        # This mapping enables linters to trace tokens and messages
        # back to their original location.
        #
        # Example:
        # Given `query_str`` like: "cancer OR tumor"
        # and source nodes:
        #   "1": {"node_content": "cancer", "content_pos": [100]}
        #   "2": {"node_content": "#1 OR tumor", "content_pos": [200]}
        # The offset map might include:
        #   {0: 100, 7: 203, 10: 206}
        # So position 7 ("O" in "OR") traces back to character 203 in the original.
        offset: typing.Dict[int, int] = {}

        # Helper function to recursively resolve query references
        def resolve_reference(ref_nr: str) -> typing.Tuple[str, dict]:
            # pylint: disable=too-many-locals
            assert ref_nr in self.query_dict

            node_content = self.query_dict[ref_nr]
            if node_content["type"] == ListTokenTypes.QUERY_NODE:
                query = node_content["node_content"]
                pos = node_content["content_pos"][0]
                if query[-1] != ")":
                    query = f"({query})"
                    offset = {0: -1, 1: pos, len(query) - 1: -1}
                    return query, offset
                return query, {0: pos}

            if node_content["type"] == ListTokenTypes.OPERATOR_NODE:
                tokens = self.tokenize_operator_node(
                    node_content["node_content"], int(ref_nr)
                )
                operator_base_offset = node_content["content_pos"][0]

                parts = []
                local_pos_dict = {}
                current_pos = 0

                for token in tokens:
                    if token.type.name == "LIST_ITEM_REFERENCE":
                        nested_ref_nr = token.value.lstrip("#S")
                        resolved_query, nested_pos_dict = resolve_reference(
                            nested_ref_nr
                        )
                        parts.append(resolved_query)
                        for rel_pos, orig_pos in nested_pos_dict.items():
                            local_pos_dict[current_pos + rel_pos] = orig_pos
                        current_pos += len(resolved_query)
                    else:
                        parts.append(token.value)
                        token_pos = operator_base_offset + token.position[0]
                        local_pos_dict[current_pos] = token_pos
                        current_pos += len(token.value)

                    parts.append(" ")
                    current_pos += 1

                resolved = "".join(parts).strip()
                return resolved, local_pos_dict

            return "", {}

        # Entry point: find the top-level operator node and resolve it
        for token_nr in self.query_dict:
            query_str, offset = resolve_reference(token_nr)

        return query_str, offset

    def assign_linter_messages(self, parser_messages, linter) -> None:  # type: ignore
        """Assign linter messages to the appropriate query nodes."""
        if GENERAL_ERROR_POSITION not in linter.messages:
            linter.messages[GENERAL_ERROR_POSITION] = []
        for message in parser_messages:
            assigned = False
            if message["position"] != [(-1, -1)] and message["position"] != []:
                for level, node in self.query_dict.items():
                    if (
                        node["content_pos"][0]
                        <= message["position"][0][0]
                        <= node["content_pos"][1]
                    ):
                        if level not in linter.messages:
                            linter.messages[level] = []
                        linter.messages[level].append(message)
                        assigned = True
                        break

            if not assigned:
                linter.messages[GENERAL_ERROR_POSITION].append(message)

    @abstractmethod
    def parse(self) -> Query:
        """Parse the query in list format."""
