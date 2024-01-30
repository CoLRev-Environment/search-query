from __future__ import annotations
from tree import Tree
from node import Node
from query import Query

class AND_Query(Query):
    
        
    def __init__(self,qs, nestedQueries):
        self.qs = qs
        self.nestedQueries = nestedQueries
        self.qt=Tree(Node("AND",True))
        self.parseQuery()
        
