#!/usr/bin/env python
"""Tests for the constants"""
from collections import Counter

from search_query.constants import QueryErrorCode

# pylint: disable=line-too-long
# flake8: noqa: E501


# Make sure the error-codes are unique
def test_assert_unique_error_codes() -> None:
    codes = [e.code for e in QueryErrorCode]
    counter = Counter(codes)
    duplicates = [code for code, count in counter.items() if count > 1]

    assert not duplicates, f"Duplicate error code(s) found: {', '.join(duplicates)}"
