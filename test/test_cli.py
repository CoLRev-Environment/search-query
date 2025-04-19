#!/usr/bin/env python
"""Tests for search query cli"""
import subprocess
from pathlib import Path


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

    print(result.stderr)
    print(result.stdout)

    assert result.returncode == 0
    assert "Converting from wos to ebscohost" in result.stdout
    assert "Writing converted query to" in result.stdout
    assert output_file.exists()

    # # Optionally, validate output content
    # with open(output_file) as f:
    #     data = json.load(f)
    #     assert "search_string" in data
    #     assert isinstance(data["search_string"], str)


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
