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

import pandas as pd

from clinical_tools.core.io import detect_format, read_dataframe, sniff_delimiter
from clinical_tools.core.writers.jira_table import populate_jira_table


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
        help="Input file (CSV, TSV, Excel, JSON). If not provided, reads from stdin.",
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
    parser.add_argument(
        "--heading", required=False, help="Optional heading/title for the JIRA table"
    )
    parser.add_argument(
        "--summary",
        required=False,
        help="Optional summary/introduction for the JIRA table",
    )

    args = parser.parse_args()

    # Determine format
    format_type = args.format or detect_format(args.input_file)

    # Determine delimiter
    delimiter = args.delimiter
    if not delimiter:
        # Try to sniff delimiter if not provided
        delimiter = sniff_delimiter(args.input_file)
        # If still not found, use default for format
        if not delimiter:
            delimiter = "\t" if format_type == "tsv" else ","

    # Read data
    df = read_dataframe(args.input_file, format_type, delimiter)

    if df is None:
        raise ValueError("Failed to read input file")

    # Handle headers option
    if args.no_headers:
        df.columns = pd.Index([f"Column_{i + 1}" for i in range(len(df.columns))])

    # Convert to JIRA table, with optional heading and summary
    jira_table = populate_jira_table(
        df,
        heading=args.heading if args.heading else None,
        summary=args.summary if args.summary else None,
    )

    # Output
    print(jira_table)


if __name__ == "__main__":
    main()
