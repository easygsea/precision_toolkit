"""JIRA table writer."""

import logging

import pandas as pd
from tabulate import tabulate

# Setup logging:
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def pandas_to_jira_table(df: pd.DataFrame) -> str:
    """
    Convert DataFrame to JIRA table format using tabulate.

    Args:
        df: DataFrame to convert

    Returns:
        JIRA table formatted string
    """
    if df.empty:
        return "||No data available||"

    df.columns = pd.Index([str(col).replace("|", "\\|") for col in df.columns])
    for index in df.index:
        for col in df.columns:
            if "|" in str(df.at[index, col]):
                logging.info(
                    f"Detected '|' in row {index}, column '{col}'. "
                    f"Replacing with '\\|' for better formatting."
                )
                df.at[index, col] = str(df.at[index, col]).replace("|", "\\|")

    jira_table = tabulate(
        df.to_dict(orient="list"),
        headers="keys",
        tablefmt="jira",
        showindex=False,
    )

    return jira_table


def populate_jira_table(
    df: pd.DataFrame, heading: str | None, summary: str | None
) -> str:
    """
    Generate a complete JIRA table document from DataFrame.

    Args:
        df: DataFrame to convert
        heading: Optional heading to add (h1 format)
        summary: Optional summary before table

    Returns:
        Generated JIRA content
    """
    jira_content = ""

    if heading:
        jira_content += f"h1. {heading}\n\n"
    if summary:
        jira_content += f"{summary}\n\n"

    jira_table = pandas_to_jira_table(df)
    jira_content += jira_table

    return jira_content
