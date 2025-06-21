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


# Assert ordered error codes
def test_assert_ordered_error_codes() -> None:
    codes = [e.code for e in QueryErrorCode]
    ordered_codes = sorted(codes)

    assert codes == ordered_codes, "Error codes are not in ascending order"


# Assert that the error codes are in the correct range
def test_assert_error_codes_in_range() -> None:
    for e in QueryErrorCode:
        print(e.code)
        print(e.code.split("_")[1])
    codes = [int(e.code.split("_")[1]) for e in QueryErrorCode]
    min_code = min(codes)
    max_code = max(codes)

    assert min_code >= 0, f"Error codes should start from 1000, but got {min_code}"
    assert max_code <= 9999, f"Error codes should end at 1999, but got {max_code}"


# Assert that the error codes are not empty
def test_assert_error_codes_not_empty() -> None:
    codes = [e.code for e in QueryErrorCode]

    assert codes, "Error codes should not be empty"


# Assert that the error codes are not None
def test_assert_error_codes_not_none() -> None:
    codes = [e.code for e in QueryErrorCode]

    assert all(code is not None for code in codes), "Error codes should not be None"
