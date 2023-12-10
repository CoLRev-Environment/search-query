#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations
from binarytree import tree
from node import Node


# class QueryTree:
# ...


class Query:

    def __init__(
        self,
    ) -> None:
        pass

    def buildParseList(self, *, query_string):
        query_tree = tree('')
        query_list = query_string.split()
        node_list = list()
        for elem in query_list:
            newNode= Node()
            newNode.value=elem
            if(elem.equals("OR") or elem.equals("AND") or elem.equals("NOT")):
                newNode.operator=True
            else:
                newNode.operator=False
            node_list.append(newNode)
        return node_list

    def parseQuery(self, query):
        if(query.startswith("OR")):
            newNode=Node("**OR**",True, None, None)
            childrenList=query[query.find("["):]
            print(newNode.value)
            print(childrenList)

        if(query.startswith("NOT")):
            newNode=Node("**NOT**",True)
        if(query.startswith("AND")):
            newNode=Node("**AND**",True)


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
    

    
    
