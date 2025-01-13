import logging
import typing
import pandas as pd
from tabulate import tabulate


def populate_markdown(
    df: pd.DataFrame, heading: str = None, summary: str = None
) -> str:
    """
    Generate a Markdown string from a pandas DataFrame.

    Args:
        df (pd.DataFrame): The pandas DataFrame to convert.
        heading (str, optional): A heading to add to the Markdown content. Defaults to None.
        summary (str, optional): A summary to add before the table. Defaults to None.

    Returns:
        str: The generated Markdown content.
    """
    markdown_content = ""

    if heading:
        markdown_content += f"# {heading}\n\n"
    if summary:
        markdown_content += f"{summary}\n\n"

    markdown_table = tabulate(df, headers="keys", tablefmt="github", showindex=False)
    markdown_content += markdown_table

    return markdown_content


def save_markdown(content: str, output_file: typing.Union[str, bytes]) -> None:
    """
    Save a Markdown string to a file.

    Args:
        content (str): The Markdown content to save.
        output_file (Union[str, bytes]): The path to save the Markdown file.

    Returns:
        None
    """
    with open(output_file, "w") as f:
        f.write(content)
    logging.info(f"Markdown content saved to {output_file}")
