#!/usr/bin/env python
"""Tests for search query cli"""
import subprocess
from pathlib import Path

from search_query import load_search_file

# pylint: disable=line-too-long
# flake8: noqa: E501


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
    assert (
        result_file.search_string
        == "(AB quantum OR KW quantum OR TI quantum) AND (AB dot OR KW dot OR TI dot) AND (AB spin OR KW spin OR TI spin)"
    )


def test_linter_cli() -> None:
    test_data_dir = Path(__file__).parent
    input_file = test_data_dir / "search_history_file_2_linter.json"

    result = subprocess.run(
        ["search-query-lint", f"{input_file}"],
        capture_output=True,
        text=True,
    )

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("RETURN CODE:", result.returncode)

    assert "Lint: search_history_file_2_linter.json (wos)" in result.stdout
    assert "Unbalanced closing parenthesis" in result.stdout
    assert (
        "The query uses multiple operators with different precedence levels"
        in result.stdout
    )
