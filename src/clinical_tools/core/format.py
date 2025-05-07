"""Formatting utilities."""

from clinical_tools.core.constants import DEFAULT_DECIMALS


def format_percentage(x: int | float, decimals: int = DEFAULT_DECIMALS) -> str:
    """
    Convert number to percentage string.

    Args:
        x: Number to convert
        decimals: Decimal places to show (default: DEFAULT_DECIMALS)

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


def parse_percentage_and_float(x: str | float) -> float:
    """
    Convert a string percentage or float-like value to float.

    Args:
        x: String with optional '%' or a float.

    Returns:
        Float value (e.g., '45%' -> 0.45, 0.45 -> 0.45).

    Raises:
        ValueError: If input cannot be converted to float.
    """
    if isinstance(x, str) and x.endswith("%"):
        stripped = x.strip("%")
        if stripped == "." or stripped == "":
            return 0.0
        return float(stripped) / 100
    elif isinstance(x, float):
        return x
    else:
        try:
            return float(x)
        except ValueError as e:
            raise ValueError(f"Cannot convert '{x}' to float") from e
