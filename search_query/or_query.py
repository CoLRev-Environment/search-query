#!/usr/bin/env python
"""OR Query"""
from __future__ import annotations

from search_query.node import Node
from search_query.query import Query
from search_query.tree import Tree


class OrQuery(Query):
    """OR Query Class"""

    def __init__(
        self, search_terms: list[str], nested_queries: list[Query], search_field: str
    ):
        """init method"""
        self.search_terms = search_terms 
        # strings which you want to include in the search query
        self.nested_queries = nested_queries 
        # queries whose roots are appended to the query
        self.search_field = search_field 
        # search field to which the query should be applied 
        # possible are: Author Keywords, Abstract, Author, DOI, ISBN, Publisher or Title
        self.query_tree = Tree(Node("OR", True, search_field))
        self.build_query_tree()
        try:
            self.valid_tree_structure(self.query_tree.root)
        except:
            raise ValueError("Building Query Tree failed")
        else:
            self.query_tree.remove_all_marks()
            for query in nested_queries:
                query.query_tree.remove_all_marks()
