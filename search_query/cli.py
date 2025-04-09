#!/usr/bin/env python3
"""CLI for search-query."""
import argparse
from pathlib import Path
import search_query.parser
from search_query import SearchFile
from search_query import load_search_file


def main():
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
        query = search_query.parser.parse(search_file.search_string, syntax=args.source, search_field_general="")
        converted_query = query.to_string(syntax=args.target)
        search_file.search_string = converted_query
        search_file.save()

    else:
        raise NotImplemented



if __name__ == "__main__":
    main()
