"""Markdown writer."""

import logging
from pathlib import Path

import pandas as pd
from tabulate import tabulate


def populate_markdown(
    df: pd.DataFrame, heading: str | None = None, summary: str | None = None
) -> str:
    """
    Generate a Markdown string from DataFrame.

    Args:
        df: DataFrame to convert
        heading: Optional heading to add
        summary: Optional summary before table

    Returns:
        Generated Markdown content
    """
    markdown_content = ""

    if heading:
        markdown_content += f"# {heading}\n\n"
    if summary:
        markdown_content += f"{summary}\n\n"

    markdown_table = tabulate(df, headers="keys", tablefmt="github", showindex=False)  # type: ignore
    markdown_content += markdown_table

    return markdown_content


def save_markdown(content: str, output_file: str | Path) -> None:
    """
    Save Markdown content to file.

    Args:
        content: Markdown content to save
        output_file: Path to output file

    Raises:
        IOError: If file cannot be written
    """
    try:
        with open(output_file, "w") as f:
            f.write(content)
        logging.info(f"Markdown content saved to {output_file}")
    except IOError as e:
        logging.error(f"Failed to save markdown to {output_file}: {e}")
        raise
