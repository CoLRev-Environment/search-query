#!/usr/bin/env python3
"""Web-of-Science query parser."""
from __future__ import annotations

import typing
import re

from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_TRANSLATION_MAP
from search_query.constants import Fields
from search_query.constants import LinterMode
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField
from search_query.exception import StrictLinterModeError


class WOSParser(QueryStringParser):
    """Parser for Web-of-Science queries."""

    FIELD_TRANSLATION_MAP = PLATFORM_FIELD_TRANSLATION_MAP[PLATFORM.WOS]

    # Lists for different spelling of the search fields
    title_list = ["TI=", "Title", "ti=", "title=", "ti", "title", "TI", "TITLE"]
    abstract_list = ["AB=", "Abstract", "ab=", "abstract=", "ab", "abstract", "AB", "ABSTRACT"]
    author_list = ["AU=", "Author", "au=", "author=", "au", "author", "AU", "AUTHOR"]
    topic_list = ["TS=", "Topic", "ts=", "topic=", "ts", "topic", "TS", "TOPIC"]

    # Matches quoted text or standalone words, including leading wildcard
    TERM_REGEX = r'\*?[\w-]+(?:\*[\w-]*)*|"[^"]+"'

    # Matches operators as standalone words only
    OPERATOR_REGEX = r'\b(AND|OR|NOT|NEAR)\b'

    # Matches search fields in the format of 'ab=' or 'abc='
    SEARCH_FIELD_REGEX = r'\b\w{2}=|\b\w{3}='

    # Matches parentheses
    PARENTHESIS_REGEX = r'[\(\)]'

    # Matches text add terms depending on search fields in data["content"]["Search Fields"]
    SEARCH_FIELDS_REGEX = r'\b(?!and\b)[a-zA-Z]+(?:\s(?!and\b)[a-zA-Z]+)*'

    # Combine all regex patterns into a single pattern
    pattern = "|".join(
        [
            SEARCH_FIELD_REGEX,
            TERM_REGEX,
            OPERATOR_REGEX,
            PARENTHESIS_REGEX,
            SEARCH_FIELDS_REGEX,
        ]
    )

    def tokenize(self) -> None:
        """Tokenize the query_str."""

        # Parse tokens and positions based on regex pattern
        compile_pattern = re.compile(pattern=self.pattern)
        matches = compile_pattern.finditer(self.query_str)

        for match in matches:
            self.tokens.append((match.group(), match.span()))

        token_types = self.get_token_types(tokens=self.tokens, legend=False)

        print(token_types)

        # only to know the pattern: self.tokens = [("token_1", (0, 4))]

    # Implement and override methods of parent class (as needed)
    def is_search_field(self, token: str) -> bool:
        """Token is search field"""
        return bool(re.match(self.SEARCH_FIELD_REGEX, token))

    def is_operator(self, token: str) -> bool:
        """Token is operator"""
        return bool(re.match(r"^(AND|OR|NOT|NEAR)$", token, re.IGNORECASE))

    def is_term(self, token: str) -> bool:
        """Check if a token is a term."""
        return (
            not self.is_parenthesis(token)
            and not self.is_search_field(token)
            and not self.is_operator(token)
        )

    # def build_query_tree(self, tokens: list[str]) -> Query:
    #     """Build the query tree from tokens."""
    #     query_tree = Query()
    #     for token in tokens:
    #         if re.match(self.SEARCH_FIELD_REGEX, token):
    #             self.handle_search_field(query_tree, token)
    #         elif re.match(self.TERM_REGEX, token):
    #             self.handle_term(query_tree, token)
    #         elif re.match(self.OPERATOR_REGEX, token):
    #             self.handle_operator(query_tree, token)
    #         elif re.match(self.PARENTHESIS_REGEX, token):
    #             self.handle_parenthesis(query_tree, token)
    #     return query_tree

    def parse_query_tree(
        self,
        tokens: list,
        search_field: typing.Optional[SearchField] = None,
    ) -> Query:
        """Parse a query from a list of tokens."""

        if search_field:
            self.search_fields_list = re.findall(self.SEARCH_FIELDS_REGEX, search_field)
            print('Search Fields given: ' + str(self.search_fields_list))

        # Parse a query tree from tokens recursively
        def parse_expression(
                tokens,
                index,
                search_field: typing.Optional[SearchField] = None,
                current_negation: bool = None,
                near_distance: int = None,
        ):
            """Parse tokens starting at the given index, 
            handling parentheses and operators recursively."""
            children = []
            current_operator = None
            if current_negation:
                current_operator = 'NOT'

            while index < len(tokens):
                token, span = tokens[index]

                # Handle nested expressions within parentheses
                if token == '(':
                    # Parse the expression inside the parentheses
                    sub_expr, index = parse_expression(
                        tokens=tokens,
                        index=index + 1,
                        search_field=search_field,
                        current_negation=current_negation,
                        near_distance=near_distance,
                    )

                    # Add the parsed expression to the list of children
                    if isinstance(sub_expr, list):
                        for child in sub_expr:
                            if children:
                                if (
                                    current_operator == child.value or
                                        (self.is_term(child.value) and
                                            self.is_operator(children[0].value))
                                    ):
                                    children[-1].children.append(child)
                                else:
                                    children.append(child)
                            else:
                                children.append(child)
                    else:
                        if children:
                            if (
                                current_operator == sub_expr.value or
                                    (self.is_term(sub_expr.value) and
                                        self.is_operator(children[0].value)
                                            and sub_expr.children)
                            ):
                                for child in sub_expr.children:
                                    children[-1].children.append(child)
                            elif ((
                                self.is_operator(sub_expr.value) or
                                    self.is_term(sub_expr.value)) and
                                        current_operator == children[0].value
                            ):
                                children[-1].children.append(sub_expr)
                            else:
                                children.append(sub_expr)
                        else:
                            children.append(sub_expr)
                    current_negation = False
                    # nearDistance = None

                elif token == ')':
                    if len(children) == 1:
                        return (children[0],
                                index
                        )

                    if current_operator:
                        return (
                            Query(
                                value=current_operator,
                                near_distance=near_distance,
                                operator=True,
                                children=children,
                                position=span
                            ),
                            index
                        )

                    return (
                        children,
                        index
                    )

                elif self.is_operator(token):
                    current_operator = token.upper()
                    if token.islower():
                        self.add_linter_message(rule='UppercaseOperator',
                                                msg='Operators must be uppercase.',
                                                posision=span
                        )

                    if current_operator == 'NEAR':
                        near_distance = str(tokens[index+1][0])
                        #current_operator = 'AND'
                        index += 1
                    if current_operator =='NOT':
                        current_negation = True
                        current_operator = 'AND'
                        parse_expression(
                            tokens=tokens,
                            index=index+1,
                            search_field=search_field,
                            current_negation=current_negation,
                            near_distance=near_distance,
                        )
                else:
                    if self.is_search_field(token):
                        search_field = SearchField(
                            value=token,
                            position=span
                        )
                    else:
                        if index:
                            if current_operator == 'NEAR':
                                # pylint: disable=unused-variable
                                previous_token, precious_span = tokens[index-2]
                            else:
                                # pylint: disable=unused-variable
                                previous_token, precious_span = tokens[index-1]

                            if self.is_term(previous_token):
                                if self.is_term(children[-1].value):
                                    children[-1].value = children[-1].value + " " + token
                                else:
                                    last_child_index = len(children[-1].children) - 1
                                    last_child = children[-1].children[last_child_index]
                                    last_child.value = last_child.value + " " + token
                                index += 1
                                continue

                        if len(self.search_fields_list) > 1 and not search_field:
                            if not current_operator:
                                current_operator= 'OR'

                            for search_field_elem in self.search_fields_list:
                                children = self.add_term_node(
                                    value=token,
                                    operator=False,
                                    search_field=search_field_elem,
                                    position=span,
                                    children=children,
                                    current_operator=current_operator,
                                    current_negation=current_negation,
                                    near_distance=near_distance,
                                )

                        else:
                            if len(self.search_fields_list) == 1 and not search_field:
                                search_field = self.search_fields_list[0]

                            children = self.add_term_node(
                                value=token,
                                operator=False,
                                search_field=search_field,
                                position=span,
                                children=children,
                                current_operator=current_operator,
                                current_negation=current_negation,
                                near_distance=near_distance,
                            )

                        if current_operator:
                            current_operator = None


                        # TODO: irgendwas muss hier gemacht werden,
                        # search field muss zu bestimmten werten none
                        # werden siehe query string 1 in test
                        # search_field = None
                index += 1

            if len(children) == 1:
                return children[0], index

            if current_operator:
                return (
                    Query(
                    value=current_operator,
                    operator=True,
                    children=children),
                    index
                )

            if self.is_operator(children[0].value):
                for child in children:
                    if not children[0].value == children[children.index(child)].value:
                        # raise error or implement linter
                        continue

                if children[0].value == children[1].value:
                    op_children = []
                    for child in children:
                        for grandchild in child.children:
                            op_children.append(grandchild)

                    return (
                        Query(
                        value=children[0].value,
                        operator=True,
                        children=op_children),
                        index
                    )

            # if we return here, we have an error in the code
            # see line 281
            # we should combine all children with their operators (should only be one)
            return (
                    Query(
                    value="Fehler hier2",
                    children=children),
                    index
                )

        root_query, _ = parse_expression(tokens=tokens, index=0, search_field=None)
        return root_query

        # Add messages to self.linter_messages

    def add_linter_message(self,
                           rule: str,
                           msg: str,
                           posision: typing.Optional[tuple] = None,
    ):
        """Adds a message to the self.linter_messages list"""
        self.linter_messages.append({
            "rule": rule,
            "message": msg,
            "position": posision,
        })

    def add_term_node(
            self,
            value,
            operator,
            search_field: typing.Optional[SearchField] = None,
            position: typing.Optional[tuple] = None,
            current_operator: str = None,
            children: typing.Optional[typing.List[typing.Union[str, Query]]] = None,
            current_negation:bool = None,
            near_distance: int = None,
    ) -> typing.Optional[typing.List[typing.Union[str, Query]]]:
        """Adds the term node to the Query"""
        term_node = Query(
            value=value,
            operator=operator,
            search_field=search_field,
            position=position
        )

        if current_operator:
            if (
                not children or
                    ((isinstance(children[-1], Query) and
                        children[-1].value != current_operator) and
                        not current_negation)
            ):

                children = [
                    Query(
                        value=current_operator,
                        near_distance=near_distance,
                        operator=True,
                        children=[*children, term_node]
                    )
                ]
            else:
                children[-1].children.append(term_node)
        else:
            children.append(term_node)
        return children

    def translate_search_fields(self, query: Query) -> None:
        """Translate search fields."""
        translated_field = None
        if query.search_field:
            original_field = self.check_search_fields(query.search_field)
            if isinstance(original_field, str):
                translated_field = self.FIELD_TRANSLATION_MAP.get(original_field, None)

            # Translate only if a mapping exists else use default search field [ALL=]
            if translated_field:
                query.search_field = translated_field

                # Add messages to self.linter_messages
                self.add_linter_message(rule='TranslatedSearchField',
                                        msg='Search Field has been updated to '
                                            + translated_field + '.',
                                        posision=query.position
                )

        if not query.search_field and not translated_field and not query.operator:
            query.search_field = Fields.ALL
            # Add messages to self.linter_messages
            self.add_linter_message(rule='AllSearchField',
                                    msg='Search Field must be set. Set to "ALL=".',
                                    posision=query.position
            )

        # Recursively translate the search fields of child nodes
        for child in query.children:
            self.translate_search_fields(child)

    def check_search_fields(self, search_field) -> str:
        """Translate a search field into base search field."""
        if isinstance(search_field, SearchField):
            search_field = search_field.value

        # Check if the given search field is in one of the lists of search fields
        return "TI=" if search_field in self.title_list else \
            "AB=" if search_field in self.abstract_list else \
            "AU=" if search_field in self.author_list else \
            "TS=" if search_field in self.topic_list else \
            search_field

    def pre_linting(self):
        """Pre-linting of the query string."""
        # Check if there is an unsolvable error in the query string
        self.fatal_linter_err = self.query_linter.pre_linting()

    def parse(self) -> Query:
        """Parse a query string."""
        # Remove all previous linter messages
        self.linter_messages.clear()

        # Pre-linting of the query string
        self.pre_linting()

        if not self.fatal_linter_err:
            # Parse the query string, build the query tree and translate search fields
            self.tokenize()
            query = self.parse_query_tree(self.tokens, search_field=self.search_fields)
            self.translate_search_fields(query)
        else:
            print('\n[FATAL] Fatal error detected in pre-linting')

        # Print linter messages
        if self.linter_messages:
            if self.mode != LinterMode.STRICT and not self.fatal_linter_err:
                print('\n[INFO] The following errors have been corrected by the linter:')

            for msg in self.linter_messages:
                print(
                    '[Linter] ' 
                        + msg['rule'] + '\t'
                        + msg['message']
                        + ' At position '
                        + str(msg['position'])
                    )

            if (self.mode == "strict" or self.fatal_linter_err) and self.linter_messages:
                print("\n")
                raise StrictLinterModeError(message='LinterDetected',
                                            query_string=self.query_str,
                                            linter_messages=self.linter_messages
                )

        return query


class WOSListParser(QueryListParser):
    """Parser for Web-of-Science (list format) queries."""

    LIST_ITEM_REGEX = r"..."

    def __init__(self, query_list: str) -> None:
        super().__init__(query_list, WOSParser)

    def get_token_str(self, token_nr: str) -> str:
        return f"#{token_nr}"

    # override and implement methods of parent class (as needed)

    # the parse() method of QueryListParser is called to parse the list of queries

    # Add exceptions to exception.py (e.g., XYInvalidFieldTag, XYSyntaxMissingSearchField)
