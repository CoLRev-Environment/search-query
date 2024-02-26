#!/usr/bin/env python
"""Tree: This module contains the tree logic."""


class Tree:
    """Tree class."""

    def __init__(self, root):
        """init method"""
        self.root = root

    def remove_all_marks(self):
        """removes all marks from all nodes"""
        self.root.marked = False
        for child in self.root.children:
            child.marked = False
        return
