"""Tests for logging configuration."""

import logging
from pathlib import Path

from rag_server.logging_config import (
    LoggerContextManager,
    get_logger,
    log_exception,
    setup_logging,
)


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_basic_setup(self) -> None:
        """Test basic logging setup."""
        logger = setup_logging(level=logging.INFO, logger_name="test.basic")
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_detailed_format(self) -> None:
        """Test logging with detailed format."""
        logger = setup_logging(level=logging.DEBUG, detailed=True, logger_name="test.detailed")
        assert logger.level == logging.DEBUG

    def test_with_log_file(self, temp_dir: Path) -> None:
        """Test logging with file handler."""
        log_file = temp_dir / "test.log"
        logger = setup_logging(level=logging.INFO, log_file=log_file, logger_name="test.file")

        # Verify log file was created
        assert log_file.exists()

        # Verify file handler was added
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger(self) -> None:
        """Test getting a logger instance."""
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"


class TestLoggerContextManager:
    """Tests for LoggerContextManager class."""

    def test_temporary_level_change(self) -> None:
        """Test temporary log level change."""
        logger = get_logger("test.context")
        original_level = logging.INFO
        logger.setLevel(original_level)

        with LoggerContextManager(logger, level=logging.DEBUG):
            assert logger.level == logging.DEBUG

        assert logger.level == original_level

    def test_temporary_handler_addition(self) -> None:
        """Test temporary handler addition."""
        logger = get_logger("test.handler")
        original_handler_count = len(logger.handlers)

        test_handler = logging.NullHandler()
        with LoggerContextManager(logger, handler=test_handler):
            assert len(logger.handlers) == original_handler_count + 1

        assert len(logger.handlers) == original_handler_count


class TestLogException:
    """Tests for log_exception function."""

    def test_log_exception_basic(self) -> None:
        """Test basic exception logging."""
        logger = get_logger("test.exception")
        exception = ValueError("Test error")

        # Should not raise
        log_exception(logger, exception, "Test message")

    def test_log_exception_with_level(self) -> None:
        """Test exception logging with custom level."""
        logger = get_logger("test.exception.level")
        exception = RuntimeError("Runtime error")

        # Should not raise
        log_exception(logger, exception, "Custom message", level=logging.WARNING)
