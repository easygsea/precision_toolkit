import typing


def format_percentage(x: typing.Union[float, int]) -> str:
    """
    Convert a float or integer to a percentage string with one decimal place.

    Args:
        x (float | int): The number to convert to a percentage.

    Returns:
        str: The number formatted as a percentage string (e.g., '45.6%').
    """
    return f"{x * 100:.1f}%"
