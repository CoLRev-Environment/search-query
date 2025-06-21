#!/usr/bin/env python3
"""CLI for search-query."""
import argparse
import sys
from pathlib import Path

import search_query.linter
import search_query.parser
from search_query import load_search_file


def translate() -> None:
    """Main entrypoint for the query translation CLI"""

    parser = argparse.ArgumentParser(
        description="Convert search queries between formats"
    )
    parser.add_argument(
        "--from",
        dest="source",
        required=True,
        help="Source query format (e.g., colrev_web_of_science)",
    )
    parser.add_argument(
        "--input",
        dest="input_file",
        required=True,
        help="Input file containing the query",
    )
    parser.add_argument(
        "--to",
        dest="target",
        required=True,
        help="Target query format (e.g., colrev_pubmed)",
    )
    parser.add_argument(
        "--output",
        dest="output_file",
        required=True,
        help="Output file for the converted query",
    )

    args = parser.parse_args()

    # Placeholder: Print what would happen
    print(f"Converting from {args.source} to {args.target}")
    print(f"Reading query from {args.input_file}")
    print(f"Writing converted query to {args.output_file}")
    print(f"Convert from {args.source} to {args.target}")

    if Path(args.input_file).suffix == ".json":
        search_file = load_search_file(args.input_file)
        query = search_query.parser.parse(
            search_file.search_string,
            platform=args.source,
            field_general=search_file.field,
        )

        translated_query = query.translate(args.target)
        converted_query = translated_query.to_string()
        search_file.search_string = converted_query
        search_file.save(args.output_file)

    else:
        raise NotImplementedError


def lint() -> None:
    """Main entrypoint for the query linter hook"""

    file_path = sys.argv[1]

    raise SystemExit(search_query.linter.pre_commit_hook(file_path))
