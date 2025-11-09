#!/usr/bin/env python3
"""CLI for search-query."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import search_query.linter
import search_query.parser
from search_query import load_search_file
from search_query.constants import Colors
from search_query.exception import QuerySyntaxError
from search_query.upgrade import upgrade_query


def _cmd_translate(args: argparse.Namespace) -> int:
    """Translate a query file from one platform/format to another."""

    print(f"Reading query from {args.input_file}")
    input_path = Path(args.input_file)
    if input_path.suffix != ".json":
        print("Only .json search files are supported at the moment.", file=sys.stderr)
        return 2

    search_file = load_search_file(args.input_file)
    try:
        query = search_query.parser.parse(
            search_file.search_string,
            platform=search_file.platform,
            field_general=search_file.field,
        )
    except QuerySyntaxError:
        print("Fatal error parsing query.")
        return 1

    print(f"Converting from {search_file.platform} to {args.target}")
    try:
        translated_query = query.translate(args.target)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error translating query: {e}")
        return 1

    converted_query = translated_query.to_string()
    search_file.search_string = converted_query
    search_file.platform = args.target

    print(f"Writing converted query to {args.output_file}")
    search_file.save(args.output_file)
    return 0


def _lint(args: argparse.Namespace) -> int:
    """Lint files."""
    exit_code = 0
    for file_path in args.files:
        search_file = load_search_file(file_path)
        try:
            result = search_query.linter.lint_file(search_file)
            if result:
                exit_code = 1
        except QuerySyntaxError as e:
            print(f"Error linting file {file_path}: {e}")
            exit_code = 1

        if exit_code == 0:
            print(f"{Colors.GREEN}File {file_path} linted successfully.{Colors.END}")
    return exit_code


def _cmd_upgrade(args: argparse.Namespace) -> int:
    """Upgrade a search query file."""

    search_file = load_search_file(args.file)
    platform = search_query.parser.get_platform(search_file.platform)
    version_current = (
        getattr(search_file, "version", None)
        or search_query.parser.LATEST_VERSIONS[platform]
    )
    version_target = args.to or search_query.parser.LATEST_VERSIONS[platform]

    upgraded = upgrade_query(
        search_file.search_string,
        platform=platform,
        version_current=version_current,
        version_target=version_target,
    )
    print(upgraded)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="search-query",
        description="Tools for working with search queries "
        + "(linting, translation, etc.)",
    )
    subparsers = parser.add_subparsers(
        dest="command", metavar="<command>", required=True
    )

    # translate
    p_tr = subparsers.add_parser(
        "translate",
        help="Convert search queries between formats",
        description="Convert search queries between formats.",
    )
    p_tr.add_argument(
        "--input",
        dest="input_file",
        required=True,
        help="Input .json file containing the query",
    )
    p_tr.add_argument(
        "--to",
        dest="target",
        required=True,
        help="Target query format (e.g., colrev_pubmed)",
    )
    p_tr.add_argument(
        "--output",
        dest="output_file",
        required=True,
        help="Output file path for the converted query",
    )
    p_tr.set_defaults(func=_cmd_translate)

    # lint
    p_li = subparsers.add_parser(
        "lint",
        help="Lint query files",
        description="Lint one or more query files. "
        + "Intended for standalone use or pre-commit.",
    )
    p_li.add_argument(
        "files",
        nargs="+",
        help="File(s) to lint",
    )
    p_li.set_defaults(func=_lint)

    # upgrade
    p_up = subparsers.add_parser(
        "upgrade",
        help="Upgrade a search file to another parser/serializer version",
        description="Upgrade a search query file to a different syntax version.",
    )
    p_up.add_argument("file", help="Search file (.json) to upgrade")
    p_up.add_argument("--to", dest="to", required=False, help="Target version")
    p_up.set_defaults(func=_cmd_upgrade)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
