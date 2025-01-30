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
