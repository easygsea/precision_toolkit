"""Input/Output utilities for reading data from various file formats."""

import csv
import logging
import sys
from io import StringIO
from pathlib import Path
from typing import TextIO

import pandas as pd

# Setup logging:
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def detect_format(file_path: str | TextIO) -> str:
    """
    Detect file format based on extension.

    Args:
        file_path: Path to the file, or TextIO for stdin

    Returns:
        Detected format: 'csv', 'tsv', or 'json'

    Examples:
        >>> detect_format("data.csv")
        'csv'
        >>> detect_format("file.tsv")
        'tsv'
        >>> detect_format("data.json")
        'json'
    """
    if hasattr(file_path, "read"):
        return "csv"

    suffix = Path(file_path).suffix.lower()
    if suffix == ".tsv":
        return "tsv"
    elif suffix == ".json":
        return "json"
    else:
        return "csv"


def read_dataframe(
    input_file: str | TextIO,
    format_type: str | None = None,
    delimiter: str | None = None,
) -> pd.DataFrame | None:
    """
    Read DataFrame from file or stdin with automatic format detection.

    Supports CSV, TSV, and JSON formats. Automatically detects file format
    from extension if not specified, and can sniff delimiters for text files.

    Args:
        input_file: Path to input file, or TextIO to read from stdin
        format_type: Explicit format ('csv', 'tsv', 'json'), or None for auto-detection
        delimiter: Custom delimiter character, or None for auto-detection

    Returns:
        pandas DataFrame containing the file data, or None if read fails


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
            delimiter, buffer = sniff_delimiter(input_file)
            # Use default delimiter if sniffing fails
            if delimiter is None:
                delimiter = "\t" if format_type == "tsv" else ","
            if buffer is not None:
                input_file = StringIO(buffer)
        # Read file based on format
        if format_type == "tsv":
            return pd.read_csv(input_file, sep=delimiter)
        elif format_type == "json":
            return pd.read_json(input_file)
        else:
            return pd.read_csv(input_file, sep=delimiter)

    except Exception as e:
        logging.exception("Error reading data:")
        print(f"Exception details: {e}")
        return None


def sniff_delimiter(file_path: str | TextIO) -> tuple[str | None, str | None]:
    """
    Try to sniff delimiter from file content using CSV sniffer.

    This is useful for files that don't have standard extensions or
    use non-standard delimiters.

    Args:
        file_path: Path to the file, or TextIO for stdin

    Returns:
        Detected delimiter character, or None if detection fails

    Examples:
        >>> sniff_delimiter("data.txt")  # Could return ';', '|', etc.
        ';'
    """
    try:
        if hasattr(file_path, "read"):
            buffer = sys.stdin.read()
            keep_buffer = True
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                buffer = f.read(4096)
                keep_buffer = False

        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(buffer)

        return dialect.delimiter, buffer if keep_buffer else None
    except Exception:
        return None, None
