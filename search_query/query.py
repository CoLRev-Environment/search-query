#!/usr/bin/env python3
"""Query class."""
from __future__ import annotations


# class QueryTree:
# ...


class Query:
    query_tree = ""

    def __init__(
        self,
    ) -> None:
        pass

    def parse(self, *, query_string) -> None:
        # ast library to create query_tree structure
        pass

    def generate(self) -> str:
        # parameter: database/syntax?
        query_str = ""
        return query_str

    def get_linked_list(self) -> dict:
        # generate linked_list from query_tree
        linked_list = {}
        return linked_list
