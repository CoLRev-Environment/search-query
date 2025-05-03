#!/usr/bin/env python3
"""CLI for search-query."""
import sys

import search_query.linter


def lint() -> None:
    """Main entrypoint for the query linter hook"""

    file_path = sys.argv[1]

    raise SystemExit(search_query.linter.pre_commit_hook(file_path))
