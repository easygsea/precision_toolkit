"""Tests for the shared project logging setup."""

import logging
from pathlib import Path

import pytest

from precision_toolkit.core.logging_setup import DEFAULT_LOG_FORMAT, setup_logging


def test_setup_logging_configures_root_logger(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setup helper should configure the root logger format."""
    root_logger = logging.getLogger()
    monkeypatch.setattr(root_logger, "handlers", [])
    monkeypatch.setattr(root_logger, "level", logging.WARNING)

    try:
        setup_logging()

        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) == 1
        handler = root_logger.handlers[0]
        assert handler.formatter is not None
        assert handler.formatter._fmt == DEFAULT_LOG_FORMAT
    finally:
        for handler in root_logger.handlers:
            handler.close()


def test_setup_logging_preserves_application_logging(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Setup helper must not replace, close, or reconfigure existing handlers."""
    root_logger = logging.getLogger()
    log_path = tmp_path / "application.log"
    handler = logging.FileHandler(log_path)
    other_handler = logging.NullHandler()
    try:
        formatter = logging.Formatter("application: %(message)s")
        handler.setFormatter(formatter)
        handler.setLevel(logging.ERROR)
        handlers = [handler, other_handler]
        monkeypatch.setattr(root_logger, "handlers", handlers)
        monkeypatch.setattr(root_logger, "level", logging.WARNING)

        setup_logging(level=logging.DEBUG, format_string="%(message)s")

        assert root_logger.handlers is handlers
        assert root_logger.handlers == [handler, other_handler]
        assert root_logger.level == logging.WARNING
        assert handler.level == logging.ERROR
        assert handler.formatter is formatter
        assert handler.stream is not None
        assert not handler.stream.closed
        root_logger.error("still configured")
        assert log_path.read_text() == "application: still configured\n"
    finally:
        handler.close()
        other_handler.close()
