#!/usr/bin/env python3
"""CLI for search-query."""
import argparse

import search_query.parser


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

    # Example stub (replace with actual logic)
    with open(args.input_file, encoding="utf-8") as infile:
        query_str = infile.read()
        query = search_query.parser.parse(query_str, syntax=args.source)
        converted_query = query.to_string(syntax=args.target)

    with open(args.output_file, "w", encoding="utf-8") as outfile:
        outfile.write(converted_query)

    print("Conversion complete.")


if __name__ == "__main__":
    main()
