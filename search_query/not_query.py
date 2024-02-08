from search_query.node import Node
from search_query.query import Query
from search_query.tree import Tree


class AND_Query(Query):
    def __init__(self, qs, nestedQueries):
        self.qs = qs
        self.nestedQueries = nestedQueries
        self.qt = Tree(Node("NOT", True))
        self.buildQueryTree()
