#!/usr/bin/env python3
"""Query parser."""
from __future__ import annotations

import re
import typing

from search_query.constants import Colors
from search_query.constants import Operators
from search_query.query import Query


# pylint: disable=too-few-public-methods
class QueryParser:
    """QueryParser class"""

    def __init__(self, query_str: str) -> None:
        self.query_str = query_str


class QueryStringParser(QueryParser):
    """QueryStringParser"""

    tokens: list

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


class WOSParser(QueryStringParser):
    """Parser for Web of Science queries."""

    # https://images.webofknowledge.com/images/help/WOS/hs_advanced_fieldtags.html
    search_field_regex = r"[A-Z]+="
    boolean_operators_regex = r"\b(AND|OR|NOT)\b"
    proximity_search_regex = r"\bNEAR\/\d+"
    parentheses_regex = r"\(|\)"
    quoted_string_regex = r"\"[^\"]*\""
    string_regex = (
        r"\b(?!(?:AND|OR|NOT|NEAR)\b)[\w\?\$-]+"
        + r"(?:\s+(?!(?:AND|OR|NOT|NEAR)\b)[\w\?\$-]+)*\*?"
    )

    pattern = "|".join(
        [
            search_field_regex,
            boolean_operators_regex,
            proximity_search_regex,
            parentheses_regex,
            quoted_string_regex,
            string_regex,
        ]
    )

    def tokenize(self) -> None:
        """Tokenize the query_str."""
        query_str = self.query_str.replace("”", '"').replace("“", '"')

        tokens = [
            (m.group(0), (m.start(), m.end()))
            for m in re.finditer(self.pattern, query_str, re.IGNORECASE)
        ]
        self.tokens = [(token.strip(), pos) for token, pos in tokens if token.strip()]

    def is_search_field(self, token: str) -> bool:
        return bool(re.search(r"^[A-Z]+=$", token))

    def is_operator(self, token: str) -> bool:
        """Token is operator"""
        return bool(re.match(r"^(AND|OR|NOT|NEAR/\d+)$", token, re.IGNORECASE))

    def parse_node(
        self, tokens: list, search_field: str = "", unary_not: bool = False
    ) -> Query:
        """Parse a node from a list of tokens."""

        node = self._initialize_node(search_field, unary_not)
        current_operator = ""
        expecting_operator = False

        while tokens:
            if unary_not and len(node.children) > 0:
                break
            next_item, pos = self._get_next_item(tokens)
            if self.is_search_field(next_item):
                search_field = next_item
                next_item, pos = self._get_next_item(tokens)
            if next_item == ")":
                # Make sure we dont' read "()" (empty parentheses)
                assert len(node.children) > 0
                break

            if self.is_term(next_item):
                node = self._handle_term(node, next_item, search_field, pos)
                expecting_operator = True
                continue

            if next_item.upper().startswith("NEAR"):
                assert expecting_operator
                node, current_operator = self._handle_near(
                    node, next_item, pos, current_operator
                )
                continue

            if next_item.upper() in [Operators.AND, Operators.OR]:
                assert expecting_operator
                node, current_operator = self._handle_and_or(
                    node, next_item, pos, current_operator
                )
                continue

            if next_item.upper() == Operators.NOT:
                assert expecting_operator
                node = self._handle_not(node, tokens, search_field, current_operator)
                continue

            if next_item == "(":
                node.children.append(self.parse_node(tokens, search_field))
                expecting_operator = True

        # Single-element parenthesis
        if node.value == "NOT_INITIALIZED" and len(node.children) == 1:
            node = node.children[0]

        # Could add the tokens from which the node
        # was created to the node (for debugging)
        return node

    def _initialize_node(self, search_field: str, unary_not: bool) -> Query:
        """Initialize a node."""
        node = Query(search_field=search_field, operator=True)
        if unary_not:
            node.value = Operators.NOT
        return node

    def _get_next_item(self, tokens: list) -> typing.Tuple[str, typing.Tuple[int, int]]:
        """Get the next item from the tokens."""
        return tokens.pop(0)

    def _handle_term(
        self,
        node: Query,
        next_item: str,
        search_field: str,
        pos: typing.Tuple[int, int],
    ) -> Query:
        """Handle term."""
        value = next_item.lstrip('"').rstrip('"')
        term_node = Query(
            value=value,
            operator=False,
            search_field=search_field,
            position=pos,
        )
        node.children.append(term_node)
        return node

    def _handle_near(
        self,
        node: Query,
        next_item: str,
        pos: typing.Tuple[int, int],
        current_operator: str,
    ) -> typing.Tuple[Query, str]:
        """Handle NEAR operator."""
        _, near_param = next_item.upper().split("/")
        node.near_param = int(near_param)  # type: ignore
        node.operator = True
        node.value = "NEAR"
        node.position = pos
        current_operator = "NEAR"
        return node, current_operator

    def _handle_and_or(
        self,
        node: Query,
        next_item: str,
        pos: typing.Tuple[int, int],
        current_operator: str,
    ) -> typing.Tuple[Query, str]:
        """Handle AND or OR operator."""
        if current_operator.upper() not in [next_item.upper(), ""]:
            raise ValueError(
                f"Invalid Syntax (combining {current_operator} with {next_item})"
            )
        node.operator = True
        node.value = next_item.upper()
        node.position = pos
        current_operator = next_item.upper()
        return node, current_operator

    def _handle_not(
        self,
        node: Query,
        tokens: list,
        search_field: str,
        current_operator: str,
    ) -> Query:
        """Handle NOT operator."""
        if current_operator.upper() not in [Operators.AND, ""]:
            raise ValueError(f"Invalid Syntax (combining {current_operator} with NOT)")
        node.children.append(self.parse_node(tokens, search_field, unary_not=True))
        return node

    def translate_search_fields(self, node: Query) -> None:
        """Translate search fields."""
        if not node.children:
            node.search_field = node.search_field.replace("AB=", "Abstract")
            return

        for child in node.children:
            self.translate_search_fields(child)

    def parse(self) -> Query:
        """Parse a query string."""
        self.tokenize()
        node = self.parse_node(self.tokens)
        # self.translate_search_fields(node)
        return node


class PubmedParser(QueryStringParser):
    """Parser for Pubmed queries."""

    def tokenize(self) -> None:
        """Tokenize the query_str."""
        query_str = self.query_str.replace("”", '"').replace("“", '"')
        # query_str = f"({query_str})"
        pattern = (
            r"\[[A-Za-z:]+\]|\"[^\"]*\"|\bAND\b|\bOR\b|\bNOT\b|\(|\)|\b[\w-]+\b\*?"
        )
        tokens = [
            (m.group(0), (m.start(), m.end())) for m in re.finditer(pattern, query_str)
        ]
        self.tokens = [(token.strip(), pos) for token, pos in tokens if token.strip()]

    def is_search_field(self, token: str) -> bool:
        """Token is search field"""
        return bool(re.search(r"\[[A-Za-z:]+\]", token))

    def get_type(self, token: str) -> str:
        """Get the token type"""
        if self.is_search_field(token):
            return "search_field"
        if self.is_parenthesis(token):
            return "parenthesis"
        if self.is_operator(token):
            return "operator"
        if self.is_term(token):
            return "term"
        return "NOT_MATCHED"

    def parse_node(
        self, tokens: list, search_field: str = "", unary_not: bool = False
    ) -> Query:
        """Parse a node from a list of tokens."""
        # Assume that expressions start with "("
        # (we can always add surrounding parentheses)

        node = Query(search_field=search_field, operator=True)
        if unary_not:
            node.value = "NOT"

        current_operator = ""
        expecting_operator = False
        while tokens:
            if unary_not and len(node.children) > 0:
                break
            next_item, pos = tokens.pop(0)
            if next_item == ")":
                # Make sure we dont' read "()"
                assert len(node.children) > 0
                break

            if self.is_term(next_item):
                value = next_item.lstrip('"').rstrip('"')
                term_node = Query(
                    value=value, operator=False, search_field=search_field, position=pos
                )

                # print(next_item)
                next_token, _ = tokens[0]
                if self.is_search_field(next_token):
                    search_field = next_item
                    next_item, pos = tokens.pop(0)
                    term_node.search_field = search_field

                node.children.append(term_node)
                expecting_operator = True
                continue

            if next_item in [Operators.AND, Operators.OR]:
                assert expecting_operator, tokens
                if current_operator not in [next_item, ""]:
                    raise ValueError(
                        f"Invalid Syntax (combining {current_operator} "
                        f"with {next_item})"
                    )
                node.operator = True
                node.value = next_item
                node.position = pos
                expecting_operator = False
                current_operator = next_item
                continue

            if next_item == Operators.NOT:
                assert expecting_operator, tokens
                if current_operator not in [Operators.AND, ""]:
                    raise ValueError(
                        f"Invalid Syntax (combining {current_operator} with NOT)"
                    )
                node.children.append(
                    self.parse_node(tokens, search_field, unary_not=True)
                )
                continue

            if next_item == "(":
                node.children.append(self.parse_node(tokens, search_field))
                # if tokens:
                #     assert tokens.pop(0) == ')', tokens
                expecting_operator = True

        # Single-element parenthesis
        if node.value == "NOT_INITIALIZED" and len(node.children) == 1:
            node = node.children[0]

        # Could add the tokens from which the node
        # was created to the node (for debugging)
        return node

    # def translate_search_fields(self, node: Query) -> None:
    #     """Translate search fields."""
    #     if not node.children:
    #         node.search_field = node.search_field.replace("AB=", "Abstract")
    #         return

    #     for child in node.children:
    #         self.translate_search_fields(child)

    def parse(self) -> Query:
        """Parse a query string."""
        self.tokenize()
        node = self.parse_node(self.tokens)
        # self.translate_search_fields(node)
        return node


# pylint: disable=too-few-public-methods
class QueryListParser(QueryParser):
    """QueryListParser"""

    tokens: typing.Dict[str, str] = {}

    def is_or_node(self, node_content: str) -> bool:
        """Node content is OR node"""
        raise NotImplementedError

    def is_and_node(self, node_content: str) -> bool:
        """Node content is AND node"""
        raise NotImplementedError

    def parse_list(self) -> None:
        """Tokenize the query_str."""
        raise NotImplementedError

    def get_children(self, node_content: str) -> list:
        """Get the children of a node."""
        raise NotImplementedError

    def parse_term_node(self, term_str: str) -> Query:
        """Parse a term node."""
        raise NotImplementedError

    def is_term(self, token: str) -> bool:
        """Check if a token is a term."""
        return not self.is_or_node(token) and not self.is_and_node(token)

    def print_term_token_types(self, token_content: str) -> str:
        """Override with method to parse and print term node types."""
        return token_content

    def get_token_types(self, tokens: dict) -> str:
        """Print the token types"""

        output = ""
        for token_nr, token_content in tokens.items():
            output += f"{token_nr}: "
            if self.is_term(token_content):
                output += self.print_term_token_types(token_content)
            # elif self.is_search_field(token_content):
            #     output += f"{Colors.GREEN}{token_content}{Colors.END}"
            elif self.is_or_node(token_content) or self.is_and_node(token_content):
                output += f" {Colors.ORANGE}{token_content}{Colors.END} "
            # elif self.is_parenthesis(token_content):
            #     output += f"{Colors.BLUE}{token_content}{Colors.END}"
            else:
                output += f"{Colors.RED}{token_content}{Colors.END}"
            output += "\n"

        output += f"\n Term\n {Colors.BLUE}Parenthesis{Colors.END}"
        output += f"\n {Colors.GREEN}Search field{Colors.END}"
        output += f"\n {Colors.ORANGE}Operator {Colors.END}"
        output += f"\n {Colors.RED}NOT-MATCHED{Colors.END}"
        return output

    def parse_node(self, node_nr: str) -> Query:
        """Parse a node from the node list."""

        if self.is_or_node(self.tokens[node_nr]):
            node = Query(value="OR", operator=True)
            for child in self.get_children(self.tokens[node_nr]):
                node.children.append(self.parse_node(child))
            return node

        if self.is_and_node(self.tokens[node_nr]):
            node = Query(value="AND", operator=True)
            for child in self.get_children(self.tokens[node_nr]):
                node.children.append(self.parse_node(child))
            return node

        return self.parse_term_node(self.tokens[node_nr])

    def parse(self) -> Query:
        """Parse a query string."""

        self.parse_list()
        node = self.parse_node(list(self.tokens.keys())[-1])
        return node


class WOSListParser(QueryListParser):
    """Parser for Web-of-Science (list format) queries."""

    def is_or_node(self, node_content: str) -> bool:
        """Node content is OR node"""
        return bool(re.match(r"^\(?#\d+( OR #\d+)+\)?$", node_content, re.IGNORECASE))

    def is_and_node(self, node_content: str) -> bool:
        """Node content is AND node"""
        return bool(re.match(r"^\(?#\d+( AND #\d+)+\)?$", node_content, re.IGNORECASE))

    def get_children(self, node_content: str) -> list:
        """Get the children of a node."""
        return re.findall(r"#\d+", node_content)

    def parse_list(self) -> None:
        """Tokenize the query_str."""
        query_str = self.query_str
        for line in query_str.split("\n"):
            match = re.match(r"^(\d+).\s+(.*)$", line)
            if not match:
                raise ValueError(f"line not matching format: {line}")
            node_nr, node_content = match.groups()
            self.tokens[f"#{node_nr}"] = node_content

    def parse_term_node(self, term_str: str) -> Query:
        """Parse a term node."""
        node_parser = WOSParser(term_str)
        node_parser.tokenize()
        return node_parser.parse_node(node_parser.tokens)

    def print_term_token_types(self, token_content: str) -> str:
        """Override with method to parse and print term node types."""

        node_parser = WOSParser(token_content)
        node_parser.tokenize()
        return node_parser.get_token_types(node_parser.tokens)


class CINAHLParser(QueryListParser):
    """Parser for CINAHL queries."""

    def is_or_node(self, node_content: str) -> bool:
        """Node content is OR node"""
        return bool(re.match(r"^\(?S\d+( OR S\d+)+\)?$", node_content))

    def is_and_node(self, node_content: str) -> bool:
        """Node content is AND node"""
        return bool(re.match(r"^\(?S\d+( AND S\d+)+\)?$", node_content))

    def parse_list(self) -> None:
        """Tokenize the query_str."""
        query_str = self.query_str
        for line in query_str.split("\n"):
            match = re.match(r"^(\d+).\s+(.*)$", line)
            if not match:
                raise ValueError(f"line not matching format: {line}")
            node_nr, node_content = match.groups()
            self.tokens[f"S{node_nr}"] = node_content

    def parse_term_node(self, term_str: str) -> Query:
        """Parse a term node."""

        return Query(value=term_str, operator=False)

    def get_children(self, node_content: str) -> list:
        """Get the children of a node."""
        return re.findall(r"S\d+", node_content)


def parse(query_str: str, query_type: str = "wos") -> Query:
    """Parse a query string."""
    if query_type == "wos":
        return WOSParser(query_str).parse()

    if query_type == "pubmed":
        return PubmedParser(query_str).parse()

    if query_type == "cinahl":
        return CINAHLParser(query_str).parse()

    if query_type == "wos_list":
        return WOSListParser(query_str).parse()

    raise ValueError(f"Invalid query type: {query_type}")
