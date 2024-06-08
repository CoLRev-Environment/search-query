#!/usr/bin/env python3
"""Query parser."""
from __future__ import annotations

from search_query.query import Query


# pylint: disable=too-few-public-methods
class QueryRefiner:
    """Query refiner."""

    def simplify_tree(self, node: Query) -> None:
        """Simplify the tree."""
        # Simplify based on associativity
        if not node.children or not node.operator:
            return  # Base case: if the node is a leaf or has no operator, return

        children_to_move = []
        children_to_append = []

        for i, child in enumerate(node.children):
            self.simplify_tree(child)  # Recursively simplify the child first
            if child.operator and node.operator and child.value == node.value:
                children_to_move.append(i)
                children_to_append.extend(child.children)

        node.children = [
            child for i, child in enumerate(node.children) if i not in children_to_move
        ]
        node.children = children_to_append + node.children
        # Note: search queries often have parentheses at the beginning.
        # otherwise, node.children.extend(children_to_append) would be better
