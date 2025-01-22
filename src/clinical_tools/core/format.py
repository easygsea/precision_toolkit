import math


def format_percentage(x, decimals=1) -> str:
    """Convert a float or integer to percentage string.

    Args:
        x: Number (float or int) to convert to percentage.
        decimals (int, optional): Decimal places. Defaults to 1.

    Returns:
        str: Number formatted as a percentage string.

    Raises:
        ValueError: If input can't be float or decimals invalid.

    Examples:
        >>> format_percentage(0.456)
        '45.6%'
        >>> format_percentage(-0.001)
        '0.0%'
        >>> format_percentage(1, decimals=2)
        '100.00%'
    """
    try:
        number = float(x)
        if not isinstance(decimals, int) or decimals < 0:
            raise ValueError("Decimals must be non-negative int.")

        # Floating-point precision edge case handling
        if math.isclose(number, 0):
            return "0." + "0" * decimals + "%"

        return f"{number * 100:.{decimals}f}%"
    except ValueError as e:
        raise ValueError(f"Error in formatting: {e}")
