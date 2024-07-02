#!/usr/bin/env python
"""Tests for query linter"""
import search_query.linter
from search_query.parser import parse

# flake8: noqa: E501


def test_alphabetical_order() -> None:
    synonym_query = parse("TS=(digital OR virtual OR online)")
    query_linter = search_query.linter.QueryLinter()
    query_linter.validate_alphabetical_order(synonym_query)
    print(query_linter.msgs)
