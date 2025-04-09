#!/usr/bin/env python3
"""Tests for SearchFile parser."""
from __future__ import annotations

from search_query.search_file import load_search_file


def test_search_history_file_parser() -> None:
    """Test SearchFile parser."""

    file_path = "test/search_history_file_1.json"

    result = load_search_file(file_path)

    assert hasattr(result, "parsed")
