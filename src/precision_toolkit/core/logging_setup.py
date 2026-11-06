"""Central logging configuration."""

import logging

DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s - %(message)s"


def setup_logging(
    level: int = logging.INFO,
    format_string: str = DEFAULT_LOG_FORMAT,
) -> None:
    """Configure root logging only when no handlers are already installed."""
    logging.basicConfig(level=level, format=format_string)
