#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations

from search_query.node import Node


class Query:
    def __init__(self, queryString, nestedQueries):
        if self.validateInput(queryString, nestedQueries) is True:
            self.qs = queryString
            self.nestedQueries = nestedQueries
            self.buildQueryTree()
        else:
            raise Exception("Invalid Input")

    # validate input to test if a valid tree structure can be guaranteed
    def validateInput(self, qs, nestedQueries) -> bool:
        if self in nestedQueries:
            return False
        if self.validateQueryString(qs) is False:
            return False

        return True

    # validate query string (qs) input
    # TODO test ob eingabe zum Graph führt
    def validateQueryString(self, qs) -> bool:
        if (
            qs.startswith("!")
            | qs.startswith("&")
            | qs.startswith("$")
            | qs.startswith("%")
            | qs.startswith("*")
        ):
            return False
        else:
            return True

    # parse the query provided, build nodes&tree structure
    def buildQueryTree(self):
        # append Strings provided in Query Strings (qs) as children to current Query
        if self.qs != "":
            childrenString = self.qs[self.qs.find("[") :]
            childrenList = childrenString[1:-1].split(", ")
            self.createTermNodes(childrenList)

        # append root of every Query in nestedQueries as a child to the current Query
        if self.nestedQueries != []:
            for q in self.nestedQueries:
                self.qt.root.children.append(q.qt.root)

        return

    # build children term nodes, append to tree
    def createTermNodes(self, childrenList) -> None:
        for item in childrenList:
            termNode = Node(item, False)
            self.qt.root.children.append(termNode)
        return

    def printQuery(self, startNode) -> str:
        result = ""
        result = f"{result}{startNode.value}"
        if startNode.children == []:
            return result
        else:
            result = f"{result}["
            for child in startNode.children:
                result = f"{result}{self.printQuery(child)}"
                if child != startNode.children[-1]:
                    result = f"{result}, "
        return f"{result}]"

    # TODO implement translating logic
    def translateDB1(self) -> str:
        # parameter: database/syntax?
        query_str = ""
        return query_str

    # TODO implement translating logic
    def translateDB2(self) -> str:
        # parameter: database/syntax?
        query_str = ""
        return query_str

    def get_linked_list(self) -> dict:
        # generate linked_list from query_tree
        linked_list = {}
        return linked_list
