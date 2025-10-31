#!/usr/bin/env python3
"""
Standalone JIRA table converter for command line usage.

Usage:
    jira-table file.csv
        # Convert file to JIRA table based on extension and auto-detected delimiter
    cat file.csv | jira-table
        # Convert from stdin
    jira-table -h
        # Show help
    jira-table --format tsv file.tsv
        # Specify input format
    jira-table --delimiter ';' file.txt
        # Specify custom delimiter
    jira-table --heading "My Table" --summary "This is a summary" data.csv
        # Add heading and summary
"""

import argparse
import sys

import pandas as pd

from clinical_tools.core.io import read_dataframe
from clinical_tools.core.writers.jira_table import (
    populate_jira_table,
)


def main() -> None:
    """Convert input files or stdin into JIRA tables."""
    parser = argparse.ArgumentParser(
        description="Convert tabular data to JIRA table format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  jira-table data.csv
    # Convert file to JIRA table based on extension and auto-detected delimiter
  cat data.csv | jira-table
    # Convert from stdin
  jira-table --format tsv data.tsv
    # Convert TSV file
  jira-table --delimiter ';' data.txt
    # Use custom delimiter
  jira-table --heading "My Table" --summary "This is a summary" data.csv
    # Add heading and summary
        """,
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        default=sys.stdin,
        help="Input file (CSV, TSV, EXCEL, JSON). If not provided, reads from stdin.",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["csv", "tsv", "excel", "json"],
        help="Input format (auto-detected from file extension if not specified)",
    )
    parser.add_argument(
        "-d",
        "--delimiter",
        help="Specify a custom delimiter for CSV/TSV files (e.g. ';' or '|').",
    )
    parser.add_argument(
        "--no-headers",
        action="store_true",
        help="Treat first row as data instead of headers",
    )
    parser.add_argument("--heading", help="Optional heading/title for the JIRA table")
    parser.add_argument(
        "--summary",
        help="Optional summary/introduction for the JIRA table",
    )
    parser.add_argument(
        "--float-format",
        type=int,
        help="Customize the output format for float values",
    )

    args = parser.parse_args()

    # Exit if no file provided
    if args.input_file is sys.stdin and sys.stdin.isatty():
        raise IOError("No input file or stdin provided.")

    # Read data
    if args.float_format is None:
        convert_to_string = True
    else:
        convert_to_string = False
    df = read_dataframe(args.input_file, convert_to_string, args.format, args.delimiter)

    # Exit if unable to read file
    if df is None:
        raise ValueError("Failed to read input file")

    # Handle headers option
    if args.no_headers:
        current_header = df.columns
        df.columns = pd.Index([f"Column_{i + 1}" for i in range(len(df.columns))])
        first_row = pd.DataFrame([current_header], columns=df.columns)
        df = pd.concat([first_row, df], ignore_index=True)

    # Convert to JIRA table, with optional heading and summary
    jira_table = populate_jira_table(
        df,
        heading=args.heading if args.heading else None,
        summary=args.summary if args.summary else None,
        float_format=args.float_format,
    )

    # Output
    print(jira_table)


if __name__ == "__main__":
    main()
