"""
Logging configuration for the MCP server.

This module provides a centralized logging setup with support for
file and console handlers, structured logging, and context management.
"""

import logging
import sys
from pathlib import Path

# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - "
    "%(filename)s:%(lineno)d - %(funcName)s() - %(message)s"
)


def setup_logging(
    level: int = logging.INFO,
    log_file: Path | None = None,
    detailed: bool = False,
    logger_name: str | None = None,
) -> logging.Logger:
    """
    Set up logging configuration for the application.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_file: Optional path to log file. If None, only console logging is used.
        detailed: If True, uses detailed log format with file and line information
        logger_name: Optional logger name. If None, returns root logger.

    Returns:
        logging.Logger: Configured logger instance

    Examples:
        >>> logger = setup_logging(level=logging.DEBUG, detailed=True)
        >>> logger.info("Server started")
        >>> logger = setup_logging(
        ...     level=logging.INFO,
        ...     log_file=Path("logs/server.log"),
        ...     logger_name="mcp.server"
        ... )
    """
    log_format = DETAILED_FORMAT if detailed else DEFAULT_FORMAT

    # Get or create logger
    logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler (use stderr for MCP servers to avoid interfering with stdio JSON-RPC)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)

    # Prevent propagation to root logger if we have a named logger
    if logger_name:
        logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    This is a convenience function for getting module-specific loggers
    that inherit from the root logger configuration.

    Args:
        name: Logger name (typically __name__ from the calling module)

    Returns:
        logging.Logger: Logger instance

    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing request")
    """
    return logging.getLogger(name)


class LoggerContextManager:
    """
    Context manager for temporary logging configuration changes.

    This allows temporarily changing log levels or adding handlers
    within a specific context.

    Examples:
        >>> logger = get_logger(__name__)
        >>> with LoggerContextManager(logger, level=logging.DEBUG):
        ...     logger.debug("This will be logged")
        >>> # Logger reverts to original level after context
    """

    def __init__(
        self,
        logger: logging.Logger,
        level: int | None = None,
        handler: logging.Handler | None = None,
    ) -> None:
        """
        Initialize the context manager.

        Args:
            logger: Logger instance to modify
            level: Optional new log level for the context
            handler: Optional handler to add for the context
        """
        self.logger = logger
        self.new_level = level
        self.handler = handler
        self.original_level = logger.level
        self.handler_added = False

    def __enter__(self) -> logging.Logger:
        """Enter the context and apply changes."""
        if self.new_level is not None:
            self.logger.setLevel(self.new_level)

        if self.handler is not None:
            self.logger.addHandler(self.handler)
            self.handler_added = True

        return self.logger

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Exit the context and revert changes."""
        self.logger.setLevel(self.original_level)

        if self.handler_added and self.handler is not None:
            self.logger.removeHandler(self.handler)


def log_exception(
    logger: logging.Logger,
    exception: Exception,
    message: str = "An error occurred",
    level: int = logging.ERROR,
) -> None:
    """
    Log an exception with context and stack trace.

    Args:
        logger: Logger instance to use
        exception: Exception to log
        message: Context message to include
        level: Log level (default: ERROR)

    Examples:
        >>> logger = get_logger(__name__)
        >>> try:
        ...     raise ValueError("Invalid input")
        ... except ValueError as e:
        ...     log_exception(logger, e, "Failed to process input")
    """
    logger.log(
        level,
        f"{message}: {type(exception).__name__}: {exception!s}",
        exc_info=True,
    )
