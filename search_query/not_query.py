#!/usr/bin/env python
"""NOT Query"""
from search_query.node import Node
from search_query.query import Query
from search_query.tree import Tree


class NotQuery(Query):
    """NOT Query"""

    def __init__(self, query_string, nested_queries, search_field):
        """init method"""
        self.query_string = query_string
        self.nested_queries = nested_queries
        self.search_field = search_field
        self.query_tree = Tree(Node("NOT", True, search_field))
        self.build_query_tree()
        if self.valid_tree_structure(self.query_tree.root):
            self.query_tree.remove_all_marks()
            for query in nested_queries:
                query.query_tree.remove_all_marks()
        else:
            raise ValueError("Error: Invalid Tree Structure")
