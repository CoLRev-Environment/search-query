#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations
from tree import Tree
from node import Node



class Query:

    def __init__(self, queryString, nestedQueries):
        self.qs = queryString
        self.nestedQueries = nestedQueries
        self.parseQuery()
        
    
    #validate query string (qs) input 
    def validateQueryString(self, qs):
        if (qs.startswith("!") | qs.startswith("&") | qs.startswith("$") | qs.startswith("%") | qs.startswith("*")):
            return False
        else:
            return True
        
        
    #parse the query provided, build nodes&tree structure
    def parseQuery(self):
        
        #append Strings provided in Query Strings (qs) as children to current Query
        if(self.qs!=""):
            childrenString = self.qs[self.qs.find("["):]
            childrenList = childrenString[1:-1].split(", ")
            self.createTermNodes(childrenList)
        
        #append root of every Query in nestedQueries as a child to the current Query
        if(self.nestedQueries!=[]):
            for q in self.nestedQueries:
                self.qt.root.children.append(q.qt.root)
        
        return
    
    #build children term nodes, append to tree
    def createTermNodes(self, childrenList) -> None:
        for item in childrenList:
            termNode = Node(item, False)
            self.qt.root.children.append(termNode)    
        return
        
    #TODO implement translating logic
    def translateDB1(self) -> str:
        # parameter: database/syntax?
        query_str = ""
        return query_str
    
    #TODO implement translating logic    
    def translateDB2(self) -> str:
        # parameter: database/syntax?
        query_str = ""
        return query_str

    def get_linked_list(self) -> dict:
        # generate linked_list from query_tree
        linked_list = {}
        return linked_list
