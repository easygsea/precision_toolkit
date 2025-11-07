"""JIRA table writer."""

import logging

import pandas as pd
from tabulate import tabulate

# Setup logging:
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def pandas_to_jira_table(df: pd.DataFrame, float_format: int | None) -> str:
    """
    Convert DataFrame to JIRA table format using tabulate.

    Args:
        df: DataFrame to convert
        float_format: Optional float format type

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

    format_args: dict[str, bool | str] = {}
    if float_format is None:
        format_args["disable_numparse"] = True
    elif float_format == 0:
        # return as scientific
        format_args["floatfmt"] = "e"
    elif float_format >= 1:
        # return as a float with n places
        format_args["floatfmt"] = f".{float_format}f"
    else:
        raise ValueError("float_format must be None, 0, or a positive integer")

    jira_table = tabulate(
        df.to_dict(orient="list"),
        headers="keys",
        tablefmt="jira",
        showindex=False,
        **format_args,  # type: ignore[arg-type]
    )

    return jira_table


def populate_jira_table(
    df: pd.DataFrame,
    heading: str | None,
    summary: str | None,
    float_format: int | None,
) -> str:
    """
    Generate a complete JIRA table document from DataFrame.

    Args:
        df: DataFrame to convert
        heading: Optional heading to add (h1 format)
        summary: Optional summary before table
        float_format: Optional float format type
    Returns:
        Generated JIRA content
    """
    jira_content = ""

    if heading:
        jira_content += f"h1. {heading}\n\n"
    if summary:
        jira_content += f"{summary}\n\n"

    jira_table = pandas_to_jira_table(df, float_format)
    jira_content += jira_table

    return jira_content
