#!/usr/bin/env python
"""Node: This module contains the node logic."""


class Node:
    """Node class."""

    def __init__(self, value: str, operator: bool, search_field: str):
        """init method"""
        self.value = value
        self.operator = operator
        # flag whether the Node is an operator
        self.children: list[Node] = []
        # list of children nodes 
        self.marked = False
        # marked flag for validation, necessary method
        self.search_field = search_field
        #search field to which the node (e.g. search term) should be applied 
        if operator:
            self.search_field = ""

    def print_node(self) -> str:
        """returns a string with all information to the node"""
        return f"value: {self.value} operator: {str(self.operator)} search field: {self.search_field}"
