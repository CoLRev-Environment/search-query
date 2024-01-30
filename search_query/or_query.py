from __future__ import annotations
from tree import Tree
from node import Node
from query import Query

class OR_Query(Query):
    
    
    def __init__(self, queryString, nestedQueries):
        self.qs = queryString
        self.nestedQueries = nestedQueries
        self.qt=Tree(Node("OR",True))
        self.parseQuery()
        
    
