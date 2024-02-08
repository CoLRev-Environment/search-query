from __future__ import annotations

from search_query.node import Node
from search_query.query import Query
from search_query.tree import Tree


class OR_Query(Query):
    def __init__(self, queryString, nestedQueries):
        if self.validateInput(queryString, nestedQueries) is True:
            self.qs = queryString
            self.nestedQueries = nestedQueries
            self.qt = Tree(Node("OR", True))
            self.buildQueryTree()
        else:
            raise Exception("Error: Invalid Input")
