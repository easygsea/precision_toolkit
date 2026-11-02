"""Central logging configuration."""

import logging

DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s - %(message)s"


def setup_logging(
    level: int = logging.INFO,
    format_string: str = DEFAULT_LOG_FORMAT,
) -> None:
    """Configure the package root logger with the standard format."""
    logging.basicConfig(level=level, format=format_string, force=True)
