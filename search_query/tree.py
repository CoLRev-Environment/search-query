#!/usr/bin/env python
"""Tree: This module contains the tree logic."""
from search_query.node import Node

# pylint: disable=too-few-public-methods


class Tree:
    """Tree class."""

    def __init__(self, root: Node):
        """init method"""
        self.root = root

    def remove_all_marks(self) -> None:
        """removes all marks from all nodes"""
        self.root.marked = False
        for child in self.root.children:
            child.marked = False
