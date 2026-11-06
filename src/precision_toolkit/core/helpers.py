"""Helper functions."""

from typing import TypeVar

import pandas as pd

ValueType = TypeVar("ValueType")


def convert_to_list_if_single_instance(
    value: ValueType | list[ValueType],
) -> list[ValueType]:
    """Convert single instances to lists while preserving existing lists.

    Ensures consistent handling of inputs that can be either single values or lists
    by converting single instances of the expected type to single-item lists.

    Args:
        value: The input value to process (must be single value or list)

    Returns:
        Single-item list if input is not a list, or the original list.
    """
    if isinstance(value, list):
        return value
    return [value]


def assemble_exports(
    dfs: list[pd.DataFrame] | pd.DataFrame,
    headings: list[str] | str | None,
    summaries: list[str] | str | None,
) -> tuple[
    list[pd.DataFrame] | pd.DataFrame,
    list[str] | str | None,
    list[str] | str | None,
]:
    """Assemble and validate inputs for export functions across different modules.

    Args:
        dfs: Single DataFrame or list of DataFrames to export
        headings: Optional heading(s) to add to the file
        summaries: Optional summary(s) to add before the table(s)

    Returns:
        Tuple of (processed DataFrames, processed headings, processed summaries)

    Raises:
        ValueError: If number of headings or summaries doesn't match number of
        DataFrames
    """
    dfs = convert_to_list_if_single_instance(dfs)
    if headings is not None:
        headings = convert_to_list_if_single_instance(headings)
    if summaries is not None:
        summaries = convert_to_list_if_single_instance(summaries)

    if headings is not None and len(headings) != len(dfs):
        raise ValueError("Number of headings must match number of DataFrames")
    if summaries is not None and len(summaries) != len(dfs):
        raise ValueError("Number of summaries must match number of DataFrames")

    return dfs, headings, summaries
