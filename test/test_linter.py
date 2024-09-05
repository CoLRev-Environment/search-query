#!/usr/bin/env python
"""Tests for query linter"""
import search_query.linter

# flake8: noqa: E501


def test_alphabetical_order() -> None:
    # synonym_query = parse("TS=(digital OR virtual OR online)")
    messages = search_query.linter.run_linter(
        "TS=(digital OR virtual OR online)", syntax="wos"
    )
    print(messages)
    assert messages == []
