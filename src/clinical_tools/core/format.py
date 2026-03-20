"""Formatting utilities."""

from clinical_tools.core.constants import DEFAULT_DECIMALS


def format_percentage(x: int | float, decimals: int = DEFAULT_DECIMALS) -> str:
    """Return x as a percentage string with given decimals."""
    if not isinstance(decimals, int) or decimals < 0:
        raise ValueError("Decimals must be a non-negative integer.")

    return f"{x * 100:.{decimals}f}%"


def parse_percentage_and_float(x: str | float) -> float:
    """Convert a string with '%' or a float to float. Raises ValueError if invalid."""
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
