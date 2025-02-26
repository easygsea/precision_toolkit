"""Formatting utilities."""

def format_percentage(x: int | float, decimals: int = 1) -> str:
    """
    Convert number to percentage string.

    Args:
        x: Number to convert
        decimals: Decimal places to show

    Returns:
        Formatted percentage string

    Raises:
        ValueError: If input invalid or decimals negative

    Examples:
        >>> format_percentage(0.456)
        '45.6%'
        >>> format_percentage(-0.001)
        '0.0%'
        >>> format_percentage(1, decimals=2)
        '100.00%'
    """
    if not isinstance(decimals, int) or decimals < 0:
        raise ValueError("Decimals must be a non-negative integer.")

    return f"{x * 100:.{decimals}f}%"
