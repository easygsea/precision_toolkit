"""Input/Output utilities for reading data from various file formats."""

import csv
import json
import logging
import sys
from io import BytesIO, StringIO
from pathlib import Path
from typing import TextIO

import pandas as pd

_SNIFF_READ_SIZE = 4096

# Setup logging:
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def detect_format(file_path: str | TextIO) -> str:
    """Detect file format based on extension.

    Args:
        file_path: Path to the file, or TextIO for stdin

    Returns:
        Detected format: 'csv', 'tsv', 'excel', or 'json'
    """
    if hasattr(file_path, "read"):
        return "csv"

    suffix = Path(file_path).suffix.lower()
    if suffix == ".tsv":
        return "tsv"
    elif suffix == ".xlsx":
        return "excel"
    elif suffix == ".json":
        return "json"
    else:
        return "csv"


def read_dataframe(
    input_file: str | TextIO,
    convert_to_string: bool,
    format_type: str | None = None,
    delimiter: str | None = None,
) -> pd.DataFrame | None:
    """Read DataFrame from file or stdin with automatic format detection.

    Args:
        input_file: Path to input file, or TextIO to read from stdin
        format_type: File format ('csv', 'tsv', 'excel', 'json') or None to auto-detect
        convert_to_string: Whether to read all data as strings
        delimiter: Custom delimiter character, or None for auto-detection

    Returns:
        DataFrame or None if reading fails.
    """
    try:
        # Auto-detect format if not specified
        if format_type is None:
            format_type = detect_format(input_file)

        # Auto-detect delimiter if not specified
        if delimiter is None and format_type in {"csv", "tsv"}:
            delimiter, buffer = sniff_delimiter(input_file)
            # Use default delimiter if sniffing fails
            if delimiter is None:
                delimiter = "\t" if format_type == "tsv" else ","
            if buffer is not None:
                input_file = StringIO(buffer)

        # Read file based on format
        read_arg: dict[str, type[str]] = {"dtype": str} if convert_to_string else {}
        if format_type == "tsv":
            return pd.read_csv(
                input_file,
                sep=delimiter,
                **read_arg,  # type: ignore[call-overload]
            )
        elif format_type == "excel":
            if hasattr(input_file, "buffer"):
                data = input_file.buffer.read()
                return pd.read_excel(
                    BytesIO(data),
                    engine="openpyxl",
                    **read_arg,  # type: ignore[call-overload]
                )
            else:
                return pd.read_excel(
                    input_file,
                    engine="openpyxl",
                    **read_arg,  # type: ignore[call-overload]
                )
        elif format_type == "json":
            if convert_to_string:
                if hasattr(input_file, "read"):
                    text = input_file.read()
                else:
                    with open(input_file, "r", encoding="utf-8") as f:
                        text = f.read()
                raw_data = json.loads(text, parse_float=str, parse_int=str)
                df = pd.json_normalize(raw_data)
                df = df.astype(str)
            else:
                df = pd.read_json(input_file)
            return df
        else:
            return pd.read_csv(
                input_file,
                sep=delimiter,
                **read_arg,  # type: ignore[call-overload]
            )

    except Exception as e:
        logging.exception("Error reading data:")
        print(f"Exception details: {e}")
        return None


def sniff_delimiter(file_path: str | TextIO) -> tuple[str | None, str | None]:
    """Detect delimiter from file using CSV sniffer.

    Args:
        file_path: Path to the file, or TextIO for stdin

    Returns:
        Tuple containing the detected delimiter character and the read buffer.
        If detection fails, returns None.
    """
    try:
        if hasattr(file_path, "read"):
            buffer = sys.stdin.read()
            keep_buffer = True
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                buffer = f.read(_SNIFF_READ_SIZE)
                keep_buffer = False

        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(buffer)

        return dialect.delimiter, buffer if keep_buffer else None
    except Exception:
        return None, None
