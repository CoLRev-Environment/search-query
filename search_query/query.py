#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations
from tree import Tree
from node import Node



class Query:

    def __init__(
        self,
    ) -> None:
        pass
    
    #validate query string input 
    def validateQueryString(self, query):
        if (query.startswith("!") | query.startswith("&") | query.startswith("$") | query.startswith("%") | query.startswith("*")):
            return False
        else:
            return True
        

    #parse the query provided by the user, build nodes&tree structure
    def parseQuery(self, query):

        if ("=" in query):
            #nested structure
            subqueries=query.split(";")
            #TO-DO handle nested structures

        else:
            #basic structure - one operator, n children
            root= self.createOperatorNode(query)
            queryTree = Tree(root)
            childrenStr = query[query.find("["):]
            childrenList = childrenStr[1:-1].split(", ")
            self.createTermNodes(childrenList,queryTree)
            
            queryTree.root.printNode()
        return 
    
    #build operator Nodes, print Error message
    def createOperatorNode(self, query) -> Node:
        operator =""
        
        if(query.startswith("OR")):
            operator="OR"       
        elif(query.startswith("NOT")):
            operator="NOT"
        elif(query.startswith("AND")):
            operator="AND"
        else:
            print("Error: not a valid query structure")
            return
        node= Node(operator, True)
        return node
    
    #build children term nodes, append to tree
    def createTermNodes(self, childrenList, tree) -> None:
        for item in childrenList:
            termNode = Node(item, False)
            tree.root.children.append(termNode)    
        return
    
    
    def buildQueryTree (self, node_list):
        return
        


    def generate(self) -> str:
        # parameter: database/syntax?
        query_str = ""
        return query_str

    def get_linked_list(self) -> dict:
        # generate linked_list from query_tree
        linked_list = {}
        return linked_list
    

    
    
