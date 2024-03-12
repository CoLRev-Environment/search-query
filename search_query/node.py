#!/usr/bin/env python
"""Node: This module contains the node logic."""
from typing import List

# pylint: disable=too-few-public-methods


class Node:
    """Node class."""

    def __init__(self, value: str, operator: bool, search_field: str):
        """init method"""
        self.value = value
        self.operator = operator
        # flag whether the Node is an operator
        self.children: List[Node] = []
        # list of children nodes
        self.marked = False
        # marked flag for validation to prevent circular references
        self.search_field = search_field
        # search field to which the node (e.g. search term) should be applied
        if operator:
            self.search_field = ""

    def mark(self) -> None:
        """marks the node"""
        if self.marked:
            raise ValueError("Building Query Tree failed")
        self.marked = True
        for child in self.children:
            child.mark()

    def remove_marks(self) -> None:
        """removes the mark from the node"""
        self.marked = False
        for child in self.children:
            child.remove_marks()

    def print_node(self) -> str:
        """returns a string with all information to the node"""
        return (
            f"value: {self.value} "
            f"operator: {str(self.operator)} "
            f"search field: {self.search_field}"
        )
