#!/usr/bin/env python
"""NOT Query"""
from search_query.node import Node
from search_query.query import Query
from search_query.tree import Tree


class NotQuery(Query):
    """NOT Query"""

    def __init__(
        self, search_terms: list[str], nested_queries: list[Query], search_field: str
    ):
        """init method
        search terms: strings which you want to include in the search query
        nested queries: queries whose roots are appended to the query
        search field: search field to which the query should be applied
         -> possible are: Author Keywords, Abstract, Author, DOI, ISBN, Publisher or Title
        """
        self.query_tree = Tree(Node("NOT", True, search_field))
        self.build_query_tree(search_terms, nested_queries, search_field)
        try:
            self.valid_tree_structure(self.query_tree.root)
        except:
            raise ValueError("Building Query Tree failed")
        self.query_tree.remove_all_marks()
        for query in nested_queries:
            query.query_tree.remove_all_marks()
