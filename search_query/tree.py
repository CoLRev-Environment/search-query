#!/usr/bin/env python
"""Tree: This module contains the tree logic."""
from search_query.node import Node

# pylint: disable=too-few-public-methods


class Tree:
    """Tree class."""

    def __init__(self, root: Node):
        """init method"""
        self.root = root
