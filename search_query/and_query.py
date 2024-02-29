#!/usr/bin/env python
"""AND Query"""
from __future__ import annotations

from search_query.node import Node
from search_query.query import Query
from search_query.tree import Tree


class AndQuery(Query):
    """AND Query"""

    def __init__(
        self, search_terms: list[str], nested_queries: list[Query], search_field: str
    ):
        """init method"""
        self.search_terms = search_terms
        self.nested_queries = nested_queries
        self.search_field = search_field
        self.query_tree = Tree(Node("AND", True, search_field))
        self.build_query_tree()
        try:
            self.valid_tree_structure(self.query_tree.root)
        except:
            raise ValueError("Building Query Tree failed")
        else:
            self.query_tree.remove_all_marks()
            for query in nested_queries:
                query.query_tree.remove_all_marks()