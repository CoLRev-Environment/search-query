#!/usr/bin/env python3
"""Web-of-Science query parser."""
from __future__ import annotations

import typing
import re

from search_query.constants import PLATFORM
from search_query.constants import PLATFORM_FIELD_TRANSLATION_MAP
from search_query.constants import Fields
from search_query.parser_base import QueryListParser
from search_query.parser_base import QueryStringParser
from search_query.query import Query
from search_query.query import SearchField


class WOSParser(QueryStringParser):
    """Parser for Web-of-Science queries."""

    FIELD_TRANSLATION_MAP = PLATFORM_FIELD_TRANSLATION_MAP[PLATFORM.WOS]

    #REGEX hier unvollständig 
    TERM_REGEX = r'[\w\*]+(?:\*[\w]*)*|"[^"]+"'         # Matches quoted text or standalone words
    OPERATOR_REGEX = r'\b(AND|OR|NOT)\b'                # Matches operators as standalone words only
    SEARCH_FIELD_REGEX = r'\b\w{2}='                    # Matches (\[\w+\] [ab]) or ab= style search field
    PARENTHESIS_REGEX = r'[\(\)]'                       # Matches parentheses
    SEARCH_FIELDS_REGEX = r'\b(?!and\b)[a-zA-Z]+(?:\s(?!and\b)[a-zA-Z]+)*'    # Matches text add terms depending on search fields in data["content"]["Search Fields"]
    # ...

    pattern = "|".join(
        [
            SEARCH_FIELD_REGEX,
            OPERATOR_REGEX,
            PARENTHESIS_REGEX,
            TERM_REGEX,
            # ...
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
        return bool(re.match(r"^(AND|OR|NOT)$", token, re.IGNORECASE))
    
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
        search_field: typing.Optional[SearchField] = None,
    ) -> Query:
        """Parse a query from a list of tokens."""
        
        # Parse a query tree from tokens recursively
        def parse_expression(
                tokens, 
                index, 
                search_field: typing.Optional[SearchField] = None
        ):
            """Parse tokens starting at the given index, handling parentheses and operators recursively."""
            children = []
            current_operator = None

            # Iff there is the Search Fields point in data["content"]
            # we need to get all search fields, if there are more than one, we need to 
            # do a for loop to add the term with all search fields
            # vielleicht sollte man hier funktion rausziehen
            # dann kann man sie vorlagern und pro search field ausführen
            search_fields_list = re.findall(self.SEARCH_FIELDS_REGEX, search_field)

            while index < len(tokens):
                token, span = tokens[index]

                # Handle nested expressions within parentheses
                if token == '(':
                    # Parse the expression inside the parentheses
                    sub_expr, index = parse_expression(
                        tokens, 
                        index + 1, 
                        search_field
                    )

                    if None: # current_operator:
                        if children:
                            children = [
                                Query(
                                    value=current_operator,
                                    operator=True,
                                    children=[*children, sub_expr],
                                    position=span
                                )
                            ]
                        else:
                            children.append(sub_expr)
                        current_operator = None
                    else:
                        if isinstance(sub_expr, list):
                            for child in sub_expr:
                                if children:
                                    if current_operator == child.value or (self.is_term(child.value) and self.is_operator(children[0].value)):
                                        children[-1].children.append(child)
                                else:
                                    children.append(child)
                        else:
                            if children:
                                if current_operator == sub_expr.value or (self.is_term(sub_expr.value) and self.is_operator(children[0].value)):
                                    children[-1].children.append(sub_expr)
                                else:
                                    children.append(sub_expr)
                            else:
                                children.append(sub_expr)

                elif token == ')':
                    # if current_operator and children:
                    #     return (
                    #         Query(
                    #             value=current_operator, 
                    #             operator=True, 
                    #             children=children, 
                    #             position=span
                    #         ), 
                    #         index
                    #     )

                    if len(children) == 1:
                        return (children[0],
                                index
                        )
                    
                    if current_operator:
                        return (
                            Query(
                                value=current_operator, 
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

                else:
                    if self.is_search_field(token):
                        search_field = SearchField(
                            value=token, 
                            position=span
                        )
                    else:
                        if index:
                            previousToken, preciousSpan = tokens[index-1]
                            if self.is_term(previousToken):
                                children[-1].value = children[-1].value + " " + token
                                index += 1
                                continue
                            
                        term_node = Query(
                            value=token,
                            operator=False,
                            search_field=search_field,
                            position=span
                        )

                        if current_operator:
                            if not children or isinstance(children[-1], Query) and children[-1].value != current_operator:
                                
                                children = [
                                    Query(
                                        value=current_operator, 
                                        operator=True, 
                                        children=[*children, term_node]
                                    )
                                ]
                            else:
                                children[-1].children.append(term_node)
                            current_operator = None
                        else:
                            children.append(term_node)
                        #   search_field = None
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
            # see line 221
            # we should combine all children with their operators (should only be one)
            return (
                    Query(
                    value="Fehler hier2",
                    children=children), 
                    index
                )

        root_query, _ = parse_expression(tokens, 0, self.search_fields)
        return root_query
        
        # Add messages to self.linter_messages

    def translate_search_fields(self, query: Query) -> None:
        """Translate search fields."""

        # Translate search fields to standard names using self.FIELD_TRANSLATION_MAP


        # Add messages to self.linter_messages if needed

    def parse(self) -> Query:
        """Parse a query string."""
        self.tokenize()
        query = self.parse_query_tree(self.tokens, search_field=self.search_fields)
        self.translate_search_fields(query)

        # If self.mode == "strict", raise exception if self.linter_messages is not empty

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