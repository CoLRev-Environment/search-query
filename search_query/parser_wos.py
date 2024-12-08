#!/usr/bin/env python3
"""Web-of-Science query parser."""
from __future__ import annotations

import typing
import re

from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_TRANSLATION_MAP
from search_query.constants import Fields
from search_query.constants import LinterMode
from search_query.constants import WOSRegex
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField
from search_query.exception import FatalLintingException


class WOSParser(QueryStringParser):
    """Parser for Web-of-Science queries."""

    FIELD_TRANSLATION_MAP = PLATFORM_FIELD_TRANSLATION_MAP[PLATFORM.WOS]

    # Lists for different spelling of the search fields
    title_list = ["TI=", "Title", "ti=", "title=", "ti", "title", "TI", "TITLE"]
    abstract_list = ["AB=", "Abstract", "ab=", "abstract=", "ab", "abstract", "AB", "ABSTRACT"]
    author_list = ["AU=", "Author", "au=", "author=", "au", "author", "AU", "AUTHOR"]
    topic_list = ["TS=", "Topic", "ts=", "topic=", "ts", "topic", "TS", "TOPIC", "Topic Search","Topic TS"]
    language_list = ["LA=", "Languages", "la=", "language=", "la", "language", "LA", "LANGUAGE"]
    year_list = ["PY=", "Publication Year", "py=", "publication year=", "py", "publication year", "PY", "PUBLICATION YEAR"]

    # Combine all regex patterns into a single pattern
    pattern = "|".join(
        [
            WOSRegex.SEARCH_FIELD_REGEX,
            WOSRegex.OPERATOR_REGEX,
            WOSRegex.TERM_REGEX,
            WOSRegex.PARENTHESIS_REGEX,
            # WOSRegex.SEARCH_FIELDS_REGEX,
        ]
    )

    def tokenize(self) -> None:
        """Tokenize the query_str."""

        # Parse tokens and positions based on regex pattern
        compile_pattern = re.compile(pattern=self.pattern)
        matches = compile_pattern.finditer(self.query_str)

        for match in matches:
            self.tokens.append((match.group(), match.span()))

        self.combine_subsequent_terms()

        token_types = self.get_token_types(tokens=self.tokens, legend=False)

        print(token_types)

    # Implement and override methods of parent class (as needed)
    def is_search_field(self, token: str) -> bool:
        """Token is search field"""
        return bool(re.match(WOSRegex.SEARCH_FIELD_REGEX, token)) or token in self.language_list

    def is_operator(self, token: str) -> bool:
        """Token is operator"""
        return (
                bool(re.match(WOSRegex.OPERATOR_REGEX, token, re.IGNORECASE))
            )

    def is_term(self, token: str) -> bool:
        """Check if a token is a term."""
        return (
            not self.is_parenthesis(token)
            and not self.is_search_field(token)
            and not self.is_operator(token)
        )

    def parse_query_tree(
        self,
        tokens: list,
    ) -> Query:
        """Parse a query from a list of tokens."""

        # Search fields are given in the search_fields string
        if self.search_fields:
            matches = re.findall(WOSRegex.SEARCH_FIELDS_REGEX, self.search_fields)

            for match in matches:
                self.search_fields_list.append(
                    SearchField(
                            value=match,
                            position=None
                        )
                )
                print('[Info] Search Field given: ' + match)
                # TODO: Check if one search field occurs multiple times or more than one ar not recognized
                # TODO: List for Search Fields from Prof. Dr. G. Wagner

        # Parse a query tree from tokens recursively
        def parse_expression(
                tokens,
                index,
                search_field: typing.Optional[SearchField] = None,
                superior_search_field: typing.Optional[SearchField] = None,
                current_negation: bool = None,
        ):
            """Parse tokens starting at the given index, 
            handling parentheses, operators, search fields and terms recursively."""
            children = []
            current_operator = None
            default_near_distance = False
            if current_negation:
                current_operator = 'NOT'

            while index < len(tokens):
                token, span = tokens[index]

                # Handle nested expressions within parentheses
                if token == '(':
                    if self.is_search_field(tokens[index-1][0]):
                        superior_search_field = tokens[index-1][0]

                    # Parse the expression inside the parentheses
                    sub_expr, index = parse_expression(
                        tokens=tokens,
                        index=index + 1,
                        search_field=search_field,
                        superior_search_field=superior_search_field,
                        current_negation=current_negation,
                    )

                    if isinstance(sub_expr, list):
                        # Add all children from the parsed expression to the list of children
                        for child in sub_expr:
                            children = self.append_children(
                                children=children,
                                sub_expr=child,
                                current_operator=current_operator,
                            )
                    else:
                        # Add the parsed expression to the list of children
                        children = self.append_children(
                            children=children,
                            sub_expr=sub_expr,
                            current_operator=current_operator,
                        )
                    current_negation = False

                # Handle closing parentheses
                elif token == ')':
                    superior_search_field = None
                    return (
                        self.handle_closing_parenthesis(
                            children=children,
                            current_operator=current_operator,
                        ),
                        index
                    )

                # Handle operators
                elif self.is_operator(token):

                    # Safe the children if there is a change
                    # of operator within the current parentheses
                    if current_operator and current_operator != token.upper():
                        children = (self.safe_children(
                            children=children,
                            current_operator=current_operator,
                            )
                        )

                    # Handle the operator and update all changes within the handler
                    current_operator, current_negation, default_near_distance = (
                        self.handle_operator(
                            token=token,
                            span=span,
                            current_operator=current_operator,
                            current_negation=current_negation,
                            default_near_distance=default_near_distance,
                        )
                    )

                    # Parse the expression after the operator
                    # parse_expression(
                    #     tokens=tokens,
                    #     index=index+1,
                    #     search_field=search_field,
                    #     superior_search_field=superior_search_field,
                    #     current_negation=current_negation,
                    # )

                # Handle search fields
                elif (
                        (self.is_search_field(token)) or
                        (token in self.language_list)
                ):
                    # Create a new search field with the token as value
                    search_field = SearchField(
                        value=token,
                        position=span
                    )

                    #TODO: Handle the year search field. 
                    # Check year format
                    # Check if year 1990-2021 is max 5 years (from wos)
                    # is added with an and to the query but that is already fine

                # Handle terms
                else:
                    # Check if search fields are given from JSON and search field is not set
                    if self.search_fields_list and not search_field:

                        # Set unsetted operator
                        if not current_operator and len(self.search_fields_list) > 1:
                            current_operator= 'OR'

                        # Add term nodes for all search fields
                        for search_field_elem in self.search_fields_list:
                            children = self.add_term_node(
                                value=token,
                                operator=False,
                                search_field=search_field_elem,
                                position=span,
                                children=children,
                                current_operator=current_operator,
                                current_negation=current_negation,
                            )

                    else:
                        # Set search field to superior search field if no search field is given
                        if not search_field and superior_search_field:
                            search_field = superior_search_field

                        # Set search field to ALL if no search field is given
                        if not search_field:
                            search_field = Fields.ALL

                        # Add term nodes
                        children = self.add_term_node(
                            value=token,
                            operator=False,
                            search_field=search_field,
                            position=span,
                            children=children,
                            current_operator=current_operator,
                            current_negation=current_negation,
                        )

                    current_operator = None
                    search_field_for_check = None

                    if isinstance(search_field, SearchField):
                        search_field_for_check = search_field.value
                    else:
                        search_field_for_check = search_field

                    if not(
                        superior_search_field and
                        superior_search_field == search_field_for_check
                    ):
                        search_field = None

                index += 1

            # Return options if there are no more tokens

            # Return the children if there is only one child
            if len(children) == 1:
                return children[0], index

            # Return the operator and children if there is an operator
            if current_operator:
                return (
                    Query(
                        value=current_operator,
                        operator=True,
                        children=children
                    ),
                    index
                )

            # Return the children if there are multiple children
            if self.is_operator(children[0].value):
                # Check if the operator of the first child is not the same as the second child
                if children[0].value != children[1].value:
                    for child in children:
                        if not children[0].value == children[children.index(child)].value:
                            # Check if the search field is in the language list
                            if (
                                children[children.index(child)].search_field.value
                                and children[children.index(child)].search_field.value in
                                self.language_list
                            ):
                                children[0].children.append(child)
                                children.pop(children.index(child))
                    return children[0], index

                # Check if the operator of the first child is the same as the second child
                if children[0].value == children[1].value:
                    operator_children = []
                    for child in children:
                        for grandchild in child.children:
                            operator_children.append(grandchild)

                    return (
                        Query(
                            value=children[0].value,
                            operator=True,
                            children=operator_children
                        ),
                        index
                    )

            # Raise an error if the code gets here
            raise NotImplementedError(
                "Error in parsing the query tree"
            )

        root_query, _ = parse_expression(
                            tokens=tokens,
                            index=0,
                            search_field=None
                        )
        return root_query

    def handle_closing_parenthesis(
            self,
            children: list,
            current_operator: str,
    ):
        """Handle closing parentheses."""
        # Return the children if there is only one child
        if len(children) == 1:
            return children[0]

        # Return the operator and children if there is an operator
        elif current_operator:
            return (
                Query(
                    value=current_operator,
                    operator=True,
                    children=children,
                )
            )
        else:

            # Return the children if there are multiple children
            return children

    def handle_operator(
            self,
            token: str,
            span: tuple,
            current_operator: str,
            current_negation: bool,
            default_near_distance: bool,
    ):
        """Handle operators."""
        # Set the current operator to the token
        current_operator = token.upper()

        # Add linter messages for operators that are not uppercase
        if token.islower():
            self.add_linter_message(rule='UppercaseOperator',
                                    msg='Operators must be uppercase.',
                                    position=span
            )

        # Set default near_distance if not set in the search string
        if current_operator == 'NEAR':
            # Add linter message for NEAR operator without distance
            self.add_linter_message(rule='NearWithoutDistance',
                                    msg='Default distance is 15.',
                                    position=span
            )
            default_near_distance = True
            current_operator = 'NEAR/15'

        # Set a flag if the token is NOT and change to AND
        if current_operator =='NOT':
            current_negation = True
            current_operator = 'AND'

        return current_operator, current_negation, default_near_distance

    def combine_subsequent_terms(self) -> None:
        """Combine subsequent terms in the list of tokens."""
        # Combine subsequent terms (without quotes)
        # This would be more challenging in the regex
        # Changed the implementation to combine multiple terms
        combined_tokens = []
        i = 0
        j = 0
        while i < len(self.tokens):
            if len(combined_tokens) > 1:
                if (
                    i + 1 < len(self.tokens)
                    and self.is_term(self.tokens[i][0])
                    and self.is_term(combined_tokens[j-1][0])
                ):
                    combined_token = (
                        combined_tokens[j-1][0] + " " + self.tokens[i][0],
                        (combined_tokens[j-1][1][0], self.tokens[i][1][1]),
                )
                    combined_tokens.pop()
                    combined_tokens.append(combined_token)
                    i += 1
                    continue

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
                j += 1
            else:
                combined_tokens.append(self.tokens[i])
                i += 1
                j += 1

        self.tokens = combined_tokens

    def append_children(
        self,
        children: list,
        sub_expr,
        current_operator: str,
    ) -> list:
        """Check where to append the sub expression."""
        if children:

            # Check if the current operator is the same as the last child
            # and if the last child is the same as the last child of the sub expression
            if (
                current_operator == sub_expr.value and
                sub_expr.value == children[-1].value
            ):
                # Append the children of the sub expression to the last child
                for child in sub_expr.children:
                    children[-1].children.append(child)

            # Check if the last child is an operator and the sub expression is a term
            # and the current operator is the same as the last child
            elif ((
                current_operator == sub_expr.value
                    or self.is_term(sub_expr.value)
                    and self.is_operator(children[0].value)
                    and sub_expr.children)
            ):
                # Append the sub expression to the last child
                for child in sub_expr.children:
                    children.append(child)
            # Check if the sub_expr is an operator or the sub expression is a term
            # and the current operator is the same as the last child
            elif ((
                self.is_operator(sub_expr.value)
                    or self.is_term(sub_expr.value))
                    and current_operator == children[0].value
            ):
                # Append the sub expression to the last child
                children[-1].children.append(sub_expr)
            else:
                # Append the sub expression to the list of children
                children.append(sub_expr)
        else:
            # Append the sub expression to the list of children
            children.append(sub_expr)

        return children

    def add_linter_message(self,
                           rule: str,
                           msg: str,
                           position: typing.Optional[tuple] = None,
    ):
        """Adds a message to the self.linter_messages list"""
        
        # check if linter message is already in the list
        for message in self.linter_messages:
            if (message['rule'] == rule 
                and message['message'] == msg 
                and message['position'] == position):
                return
        
        self.linter_messages.append({
            "rule": rule,
            "message": msg,
            "position": position,
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
    ) -> typing.Optional[typing.List[typing.Union[str, Query]]]:
        """Adds the term node to the Query"""

        # Create a new term node
        term_node = Query(
            value=value,
            operator=operator,
            search_field=search_field,
            position=position
        )

        # Check if the current operator is NEAR and the distance is not set
        check_near_operator = False
        if current_operator == 'NEAR':
            check_near_operator = children[-1].value == current_operator

        # Append the term node to the list of children
        if current_operator:
            if (
                not children
                or ((isinstance(children[-1], Query)
                and (children[-1].value != current_operator))
                and not current_negation)
                and not check_near_operator
            ):
                children = [
                    Query(
                        value=current_operator,
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
                                        position=query.position
                )

        if not query.search_field and not translated_field and not query.operator:
            query.search_field = Fields.ALL
            # Add messages to self.linter_messages
            self.add_linter_message(rule='AllSearchField',
                                    msg='Search Field must be set. Set to "ALL=".',
                                    position=query.position
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
            "LA=" if search_field in self.language_list else \
            "PY=" if search_field in self.year_list else \
            "ALL="

    def safe_children(
            self,
            children: list,
            current_operator: str
        ) -> list:
        """Safe children, when there is a change of 
        operator within the current parentheses."""
        safe_children = []
        safe_children.append(
            Query(
                value=current_operator,
                operator=True,
                children=children,
            )
        )

        return safe_children

    def pre_linting(self):
        """Pre-linting of the query string."""
        # Check if there is an unsolvable error in the query string
        self.fatal_linter_err = self.query_linter.pre_linting(self.tokens)

    def parse(self) -> Query:
        """Parse a query string."""
        # Remove all previous linter messages
        self.linter_messages.clear()

        # Tokenize the query string
        self.tokenize()

        # Pre-linting of the query string
        self.pre_linting()

        if not self.fatal_linter_err:
            # Parse the query string, build the query tree and translate search fields
            query = self.parse_query_tree(self.tokens)
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

            # Raise an exception if the linter is in strict mode or if a fatal error has occurred
            if (self.mode == "strict" or self.fatal_linter_err) and self.linter_messages:
                print("\nSearch Field format accaptable: 'xx=' or 'xxx='\n")
                # raise FatalLintingException(message='LinterDetected',
                #                             query_string=self.query_str,
                #                             linter_messages=self.linter_messages
                # )

        return query


class WOSListParser(QueryListParser):
    """Parser for Web-of-Science (list format) queries."""

    LIST_ITEM_REGEX = r"^(\d+).\s+(.*)$"
    LIST_COMBINE_REGEX = r"#\d+|AND|OR"

    def __init__(self, query_list: str, search_fields: str, linter_mode: LinterMode) -> None:
        super().__init__(query_list, WOSParser, search_fields, linter_mode)

    def get_token_str(self, token_nr: str) -> str:
        return f"#{token_nr}"

    def parse(self) -> Query:
        """Parse the list of queries."""
        query_dict = self.parse_dict()
        queries = []
        combine_queries = {}

        for node_nr, node_content in query_dict.items():
            if node_nr == '14':
                print(node_content["node_content"])

            if '#' in node_content["node_content"]:
                combine_queries[node_nr] = node_content["node_content"]
                queries.append("Filler for combine queries")
            else:
                query_parser = self.parser_class(
                    query_str=node_content["node_content"],
                    search_fields=self.search_fields,
                    mode=self.linter_mode
                )
                query = query_parser.parse()
                queries.append(query)

        # If there is no combining list item, raise a linter exception
        # Individual list items can not be connected
        if not combine_queries:
            raise FatalLintingException(
                message='NoCombiningListItem',
                query_string=self.query_list,
                linter_messages=[{
                    "rule": "NoCombiningListItem",
                    "message": "[Linter] No combining list item found.",
                    "position": None
                }]
            )
        
        if not (combine_queries[len(combine_queries)-1] 
                == query_dict[len(query_dict)]["node_content"]):
            raise FatalLintingException(
                message='LastListItemMustBeCombiningString',
                query_string=self.query_list,
                linter_messages=[{
                    "rule": "LastListItemMustBeCombiningString",
                    "message": "[Linter] The last item of the list must be a combining string.",
                    "position": None
                }]
            )

        for index, query in combine_queries.items():
            children = []
            res_children = []
            operator = None
            tokens = self.tokenize_combining_list_elem(query)

            # Check if the last token is a number
            if not "#" in tokens[len(tokens)-1]:
                raise ValueError(
                    "[ERROR] The last token of a combining list item must be a number."
                    )

            for token in tokens:
                if "#" in token:
                    token = token.replace("#", "")
                    children.append(queries[int(token) - 1])
                else:
                    if not operator or operator == token:
                        operator = token
                    else:
                        raise ValueError(
                            "[ERROR] Two different operators are used in one line."
                            )

            for child in children:
                if child.value == operator:
                    for grandchild in child.children:
                        res_children.append(grandchild)
                else:
                    res_children.append(child)

            queries[int(index) - 1] = Query(
                    value=operator,
                    operator=True,
                    children=res_children
                )

        return queries[len(queries) - 1]

    def tokenize_combining_list_elem(self, query_str: str) -> list:
        """Tokenize the query_list."""
        matches = re.findall(self.LIST_COMBINE_REGEX, query_str)
        return matches

    # override and implement methods of parent class (as needed)

    # the parse() method of QueryListParser is called to parse the list of queries

    # Add exceptions to exception.py (e.g., XYInvalidFieldTag, XYSyntaxMissingSearchField)
