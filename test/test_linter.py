#!/usr/bin/env python
"""Tests for query linter"""
import search_query.linter
from search_query.parser import parse


# flake8: noqa: E501


def test_alphabetical_order() -> None:
    synonym_query = parse("digital OR virtual OR online")
    query_linter = search_query.linter.QueryLinter()
    query_linter.validate_alphabetical_order(synonym_query)
    print(query_linter.msgs)


# Checker: non-alphabetical order, unnecessary nesting, redundant-terms (CHEKC search_field!), missing-AE/BE pronounciation, missing-MESH-Terms

# marked_query = mark_query_string(WOS_QUERIES[4]["query_string"], (56, 122))
# print(marked_query)

# TODO : next: expand query (add AE/BE variations or synonyms): add nodes and mark in green
