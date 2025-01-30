import pandas as pd

def convert_to_list_if_single_instance(value, expected_type):
    """Convert single instances to lists while preserving None and existing lists.
    
    Ensures consistent handling of inputs that can be either single values or lists
    by converting single instances of the expected type to single-item lists.
    
    Args:
        value: The input value to process (can be None, single value, or list)
        expected_type: The type to check against (e.g. pd.DataFrame, str)
        
    Returns:
        None if input is None, single-item list if input matches expected type,
        or original value otherwise.
    """
    return [value] if isinstance(value, expected_type) else (value if value is not None else None)


def assemble_exports(
    dfs: list[pd.DataFrame] | pd.DataFrame,
    headings: list[str] | str | None,
    descriptions: list[str] | str | None
) -> tuple[list[pd.DataFrame], list[str] | None, list[str] | None]:
    """Assemble and validate inputs for export functions across different modules.

    Args:
        dfs: Single DataFrame or list of DataFrames to export
        headings: Optional heading(s) to add to the file
        descriptions: Optional description(s) to add before the table(s)

    Returns:
        Tuple of (processed DataFrames, processed headings, processed descriptions)

    Raises:
        ValueError: If number of headings or descriptions doesn't match number of DataFrames
    """
    
    # Convert single instances to lists for consistent processing
    dfs = convert_to_list_if_single_instance(dfs, pd.DataFrame)
    headings = convert_to_list_if_single_instance(headings, str)
    descriptions = convert_to_list_if_single_instance(descriptions, str)
    
    # Ensure headings and descriptions match the number of DataFrames
    if headings is not None and len(headings) != len(dfs):
        raise ValueError("Number of headings must match number of DataFrames")
    if descriptions is not None and len(descriptions) != len(dfs):
        raise ValueError("Number of descriptions must match number of DataFrames")
    
    return dfs, headings, descriptions
