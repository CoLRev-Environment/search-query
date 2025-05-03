#!/usr/bin/env python
"""Tests for search query cli"""
import subprocess
from pathlib import Path

def test_linter_cli() -> None:
    test_data_dir = Path(__file__).parent
    input_file = test_data_dir / "search_history_file_2_linter.json"

    result = subprocess.run(
        ["search-query-lint", f"{input_file}"],
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    assert "Lint: search_history_file_2_linter.json (wos)" in result.stdout
    assert "Unbalanced closing parenthesis" in result.stdout
    assert "Operator changed at the same level" in result.stdout
