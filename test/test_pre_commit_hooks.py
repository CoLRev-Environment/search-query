#!/usr/bin/env python
"""Tests for lint-related pre-commit hook behavior."""
from __future__ import annotations

import json
from pathlib import Path

from search_query.constants import ExitCodes
from search_query.linter import pre_commit_hook


def _write_search_file(
    tmp_path: Path,
    *,
    search_string: str,
    platform: str = "wos",
    filename: str = "search.json",
) -> Path:
    file_path = tmp_path / filename
    payload = {
        "record_info": {},
        "authors": [{"name": "Wagner, G.", "ORCID": "0000-0000-0000-1111"}],
        "date": {"data_entry": "2019.07.01", "search_conducted": "2019.07.01"},
        "platform": platform,
        "database": ["SCI-EXPANDED", "SSCI", "A&HCI"],
        "search_string": search_string,
    }
    file_path.write_text(json.dumps(payload), encoding="utf-8")
    return file_path


def test_pre_commit_hook_passes_valid_query_file(
    tmp_path: Path, capsys
) -> None:  # type: ignore
    file_path = _write_search_file(
        tmp_path, search_string='TS=("digital health" AND privacy)'
    )

    result = pre_commit_hook(str(file_path))
    captured = capsys.readouterr()

    assert result == ExitCodes.SUCCESS
    assert "Lint: search.json (wos)" in captured.out
    assert "No errors detected" in captured.out


def test_pre_commit_hook_fails_for_unbalanced_parentheses(
    tmp_path: Path, capsys
) -> None:  # type: ignore
    file_path = _write_search_file(
        tmp_path,
        search_string='TS=("digital health"[Title/Abstract]) AND ("privacy"[Title/Abstract]',
    )

    result = pre_commit_hook(str(file_path))
    captured = capsys.readouterr()

    assert result == ExitCodes.FAIL
    assert "Lint: search.json (wos)" in captured.out
    assert "unbalanced-parentheses" in captured.out


def test_pre_commit_hook_fails_for_unsupported_field(tmp_path: Path, capsys) -> None:  # type: ignore
    file_path = _write_search_file(
        tmp_path,
        search_string="TI=term1 AND IY=2020",
    )

    result = pre_commit_hook(str(file_path))
    captured = capsys.readouterr()

    assert result == ExitCodes.FAIL
    assert "Lint: search.json (wos)" in captured.out
    assert "field-unsupported" in captured.out
