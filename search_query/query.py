#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations
from tree import Tree
from node import Node



class OR_Query:
    
    qt=Tree(None)
    qs=""
    nestedQueries=[]

    def __init__(self, queryString, nestedQueries):
        self.qs = queryString
        self.nestedQueries = nestedQueries
        self.qt = self.parseQuery(self.qs,self.nestedQueries)
        
    
    #validate query string (qs) input 
    def validateQueryString(self, qs):
        if (qs.startswith("!") | qs.startswith("&") | qs.startswith("$") | qs.startswith("%") | qs.startswith("*")):
            return False
        else:
            return True
        
        
    #parse the query provided, build nodes&tree structure
    def parseQuery(self, qs, queries)-> Tree:
        root = Node("OR",True)
        qt = Tree(root)
        
        if(qs!=""):
            childrenString = qs[self.qs.find("["):]
            childrenList = childrenString[1:-1].split(", ")
            self.createTermNodes(childrenList,qt)
        
        if(queries!=[]):
            for q in queries:
                qt.children.append(q.qt.root)
        
        return qt
    
    
    #build children term nodes, append to tree
    def createTermNodes(self, childrenList, tree) -> None:
        for item in childrenList:
            termNode = Node(item, False)
            tree.root.children.append(termNode)    
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
    
class AND_Query:
        
    qt=Tree(None)
    qs="QueryString"
    nestedQueries=[]
        
    def __init__(self,qs, nestedQueries):
        self.qs = qs
        self.nestedQueries = nestedQueries
        self.qt = self.parseQuery(self.qs,self.nestedQueries)
        
    def parseQuery(self, qs, queries)-> Tree:
        root = Node("AND",True)
        qt = Tree(root)
        
        if(qs!=""):
            childrenString = qs[self.qs.find("["):]
            childrenList = childrenString[1:-1].split(", ")
            self.createTermNodes(childrenList,qt)
        
        if(queries!=[]):
            for q in queries:
                qt.root.children.append(q.qt.root)
        
        return qt
     
    def createTermNodes(self, childrenList, qt) -> None:
        for item in childrenList:
            termNode = Node(item, False)
            qt.root.children.append(termNode)    
        return   
    
        
        
    

    
    
