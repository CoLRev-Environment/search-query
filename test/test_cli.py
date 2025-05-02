#!/usr/bin/env python
"""Tests for search query cli"""
import subprocess
from pathlib import Path

from search_query import load_search_file


def test_translate_cli() -> None:
    test_data_dir = Path(__file__).parent
    input_file = test_data_dir / "search_history_file_1.json"
    output_file = test_data_dir / "output.json"

    result = subprocess.run(
        [
            "search-query-translate",
            "--from=wos",
            f"--input={input_file}",
            "--to=ebscohost",
            f"--output={output_file}",
        ],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    print(result.stderr)
    assert result.returncode == 0
    assert "Converting from wos to ebscohost" in result.stdout
    assert "Writing converted query to" in result.stdout
    assert output_file.exists()

    result_file = load_search_file(output_file)
    assert result_file.search_string == "TP (quantum AND dot AND spin)"


def test_linter_cli() -> None:
    test_data_dir = Path(__file__).parent
    input_file = test_data_dir / "search_history_file_2_linter.json"

    result = subprocess.run(
        ["search-query-lint", f"{input_file}"],
        capture_output=True,
        text=True,
    )

    assert "Lint: search_history_file_2_linter.json (wos)" in result.stdout
    assert "Unbalanced closing parenthesis" in result.stdout
    assert "Operator changed at the same level" in result.stdout
