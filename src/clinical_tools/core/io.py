"""Input/Output utilities for reading data from various file formats."""

import csv
import sys
from pathlib import Path

import pandas as pd


def detect_format(file_path: str | None) -> str:
    """
    Detect file format based on extension.

    Args:
        file_path: Path to the file, or None for stdin

    Returns:
        Detected format: 'csv', 'tsv', or 'json'

    Examples:
        >>> detect_format("data.csv")
        'csv'
        >>> detect_format("file.tsv")
        'tsv'
        >>> detect_format("data.json")
        'json'
        >>> detect_format(None)
        'csv'
    """
    if not file_path:
        return "csv"

    suffix = Path(file_path).suffix.lower()
    if suffix == ".tsv":
        return "tsv"
    elif suffix == ".json":
        return "json"
    else:
        return "csv"


def read_dataframe(
    input_file: str | None,
    format_type: str | None = None,
    delimiter: str | None = None
) -> pd.DataFrame:
    """
    Read DataFrame from file or stdin with automatic format detection.

    Supports CSV, TSV, and JSON formats. Automatically detects file format
    from extension if not specified, and can sniff delimiters for text files.

    Args:
        input_file: Path to input file, or None to read from stdin
        format_type: Explicit format ('csv', 'tsv', 'json'), or None for auto-detection
        delimiter: Custom delimiter character, or None for auto-detection

    Returns:
        pandas DataFrame containing the file data

    Raises:
        SystemExit: If file cannot be read or parsed

    Examples:
        >>> df = read_dataframe("data.csv")
        >>> df = read_dataframe("data.tsv", delimiter="|")
        >>> df = read_dataframe(None, format_type="csv")  # Read from stdin
    """
    try:
        # Auto-detect format if not specified
        if format_type is None:
            format_type = detect_format(input_file)

        # Auto-detect delimiter if not specified
        if delimiter is None:
            delimiter = sniff_delimiter(input_file)
            # Use default delimiter if sniffing fails
            if delimiter is None:
                delimiter = "\t" if format_type == "tsv" else ","

        # Read file based on format
        if input_file:
            if format_type == "tsv":
                return pd.read_csv(input_file, sep=delimiter)
            elif format_type == "json":
                return pd.read_json(input_file)
            elif format_type == "csv":
                return pd.read_csv(input_file, sep=delimiter)
            else:
                # Fallback: try CSV with detected delimiter
                return pd.read_csv(input_file, sep=delimiter)
        else:
            # Read from stdin
            if format_type == "tsv":
                return pd.read_csv(sys.stdin, sep=delimiter)
            elif format_type == "json":
                return pd.read_json(sys.stdin)
            elif format_type == "csv":
                return pd.read_csv(sys.stdin, sep=delimiter)
            else:
                return pd.read_csv(sys.stdin, sep=delimiter)

    except Exception as e:
        print(f"Error reading data: {e}", file=sys.stderr)
        sys.exit(1)


def sniff_delimiter(file_path: str | None) -> str | None:
    """
    Try to sniff delimiter from file content using CSV sniffer.
    
    This is useful for files that don't have standard extensions or
    use non-standard delimiters.

    Args:
        file_path: Path to the file, or None for stdin

    Returns:
        Detected delimiter character, or None if detection fails

    Examples:
        >>> sniff_delimiter("data.txt")  # Could return ';', '|', etc.
        ';'
        >>> sniff_delimiter(None)
        None
    """
    try:
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                sample = f.read(4096)
        else:
            # For stdin, read a small sample and reset pointer
            sample = sys.stdin.read(4096)
            sys.stdin = sys.__stdin__  # Reset stdin for pandas

        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample)
        return dialect.delimiter
    except Exception:
        return None
