#!/usr/bin/env python3
"""Tests for SearchFile parser."""
from __future__ import annotations

from search_query.search_file import SearchFile


def test_search_history_file_parser() -> None:
    """Test SearchFile parser."""

    file_path = "test/search_history_file_1.json"

    result = SearchFile(file_path)

    assert hasattr(result, "parsed")
