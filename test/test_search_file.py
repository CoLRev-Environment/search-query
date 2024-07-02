#!/usr/bin/env python3
"""Tests for SearchHistoryFile parser."""
from __future__ import annotations

import json

from search_query.search_file import SearchHistoryFile


def test_search_history_file_parser() -> None:
    """Test SearchHistoryFile parser."""

    file_path = "test/search_history_file_1.json"

    with open(file_path) as file:
        data = json.load(file)

    result = SearchHistoryFile(**data)

    assert hasattr(result, "parsed")
