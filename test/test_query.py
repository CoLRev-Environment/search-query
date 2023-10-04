#!/usr/bin/env python
"""Tests for the Query"""
import search_query.query


def test_parse() -> None:
    query = search_query.query.Query()
    query.parse(query_string="(digital OR online) AND work")

    actual_list = query.get_linked_list()

    expected_list = {1: "digital", 2: "online", 3: "1 OR 2", 4: "work", 5: "3 AND 4"}
    assert actual_list == expected_list
