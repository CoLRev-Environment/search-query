"""Tests for deterministic documentation index generation."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict

REPOSITORY_ROOT = Path(__file__).parents[1]
GENERATED_DIRECTORIES = (
    REPOSITORY_ROOT / "docs/source/lint",
    REPOSITORY_ROOT / "docs/source/query_database",
)


def _generated_files() -> Dict[str, bytes]:
    """Return generated documentation files and their exact contents."""
    return {
        str(path.relative_to(REPOSITORY_ROOT)): path.read_bytes()
        for directory in GENERATED_DIRECTORIES
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def _generate_indices() -> None:
    subprocess.run(
        [sys.executable, "docs/generate_indices.py"],
        cwd=REPOSITORY_ROOT,
        check=True,
        env={**os.environ, "PYTHONPATH": str(REPOSITORY_ROOT)},
    )


def test_generate_indices_is_deterministic() -> None:
    """Repeated generation is byte-identical and uses filename ordering."""
    _generate_indices()
    first_generation = _generated_files()

    _generate_indices()
    assert _generated_files() == first_generation

    overview_path = REPOSITORY_ROOT / "docs/source/query_database/query_overview.json"
    overview = json.loads(overview_path.read_text(encoding="utf-8"))
    identifiers = [
        entry["identifier"].split(" ", maxsplit=1)[0][1:] for entry in overview
    ]
    assert identifiers == sorted(
        identifiers, key=lambda identifier: (identifier.casefold(), identifier)
    )
