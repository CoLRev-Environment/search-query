#!/usr/bin/env python
"""Node: This module contains the node logic."""


class Node:
    """Node class."""

    def __init__(self, value, operator, search_field):
        """init method"""
        self.value = value
        self.operator = operator
        self.children = []
        self.marked = False
        self.search_field = search_field
        if operator:
            self.search_field = ""

    def print_node(self) -> str:
        """returns a string with all information to the node"""
        return f"value: {self.value} operator: {str(self.operator)} search field: {self.search_field}"
