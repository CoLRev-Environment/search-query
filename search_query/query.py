#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations
from tree import Tree
from node import Node



class Query:

    def __init__(self, queryString, nestedQueries):
        if self.validateInput(): 
            self.qs = queryString
            self.nestedQueries = nestedQueries
            self.buildQueryTree()
        else:
            raise Exception("Error: Invalid Input")
    
    #validate input to test if a valid tree structure can be guaranteed
    def validateInput(self) -> bool:
        if self in self.nestedQueries:
            return False
        if self.validateQueryString() == False:
            return False
        else:
            return True 
              
    
    #validate query string (qs) input 
    #TODO test ob eingabe zum Graph führt 
    def validateQueryString(self) -> bool:
        if (self.qs.startswith("!") | self.qs.startswith("&") | self.qs.startswith("$") | self.qs.startswith("%") | self.qs.startswith("*")):
            return False
        else:
            return True
        
        
    #parse the query provided, build nodes&tree structure
    def buildQueryTree(self):
        
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
