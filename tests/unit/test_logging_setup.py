"""Tests for the shared project logging setup."""

import logging

from precision_toolkit.core.logging_setup import DEFAULT_LOG_FORMAT, setup_logging


def test_setup_logging_configures_root_logger() -> None:
    """Setup helper should configure the root logger format."""
    setup_logging()

    root_logger = logging.getLogger()
    handler = root_logger.handlers[0]

    assert root_logger.level == logging.INFO
    assert root_logger.handlers
    assert handler.formatter is not None
    assert handler.formatter._fmt == DEFAULT_LOG_FORMAT
