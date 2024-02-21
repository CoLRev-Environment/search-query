from search_query.node import Node
from search_query.query import Query
from search_query.tree import Tree


class NOT_Query(Query):
    def __init__(self, qs, nestedQueries, searchField):
        self.qs = qs
        self.nestedQueries = nestedQueries
        self.searchField = searchField
        self.qt = Tree(Node("NOT", True, searchField))
        self.buildQueryTree()
        if self.validTreeStructure(self.qt.root):
            self.qt.removeAllMarks()
            for nq in nestedQueries:
                nq.qt.removeAllMarks()
        else:
            self = None
            raise Exception("Error: Invalid Tree Structure")
