"""
Custom exception classes for the MCP server.

This module defines all custom exceptions used throughout the application,
providing clear error messages and proper error handling capabilities.
"""

from typing import Any


class MCPServerError(Exception):
    """Base exception class for all MCP server errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """
        Initialize the exception.

        Args:
            message: Error message
            details: Optional dictionary with additional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class ChromaDBError(MCPServerError):
    """Exception raised for ChromaDB-related errors."""

    def __init__(
        self,
        message: str,
        collection_name: str | None = None,
        operation: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize ChromaDB error.

        Args:
            message: Error message
            collection_name: Name of the collection involved
            operation: Operation that failed (e.g., 'query', 'add', 'delete')
            details: Additional error details
        """
        error_details = details or {}
        if collection_name:
            error_details["collection"] = collection_name
        if operation:
            error_details["operation"] = operation
        super().__init__(message, error_details)


class EmbeddingError(MCPServerError):
    """Exception raised for embedding-related errors."""

    def __init__(
        self,
        message: str,
        model_name: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize embedding error.

        Args:
            message: Error message
            model_name: Name of the embedding model
            details: Additional error details
        """
        error_details = details or {}
        if model_name:
            error_details["model"] = model_name
        super().__init__(message, error_details)


class CollectionNotFoundError(ChromaDBError):
    """Exception raised when a requested collection doesn't exist."""

    def __init__(self, collection_name: str) -> None:
        """
        Initialize collection not found error.

        Args:
            collection_name: Name of the collection that wasn't found
        """
        super().__init__(
            f"Collection '{collection_name}' not found",
            collection_name=collection_name,
            operation="get",
        )


class DocumentValidationError(MCPServerError):
    """Exception raised when document validation fails."""

    def __init__(
        self,
        message: str,
        document_index: int | None = None,
        validation_errors: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize document validation error.

        Args:
            message: Error message
            document_index: Index of the invalid document
            validation_errors: List of validation error messages
            details: Additional error details
        """
        error_details = details or {}
        if document_index is not None:
            error_details["document_index"] = document_index
        if validation_errors:
            error_details["validation_errors"] = validation_errors
        super().__init__(message, error_details)


class DeviceConfigurationError(MCPServerError):
    """Exception raised when device configuration fails."""

    def __init__(
        self,
        message: str,
        requested_device: str | None = None,
        available_devices: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize device configuration error.

        Args:
            message: Error message
            requested_device: The device that was requested
            available_devices: List of available devices
            details: Additional error details
        """
        error_details = details or {}
        if requested_device:
            error_details["requested_device"] = requested_device
        if available_devices:
            error_details["available_devices"] = available_devices
        super().__init__(message, error_details)


class ServerInitializationError(MCPServerError):
    """Exception raised when server initialization fails."""

    def __init__(
        self,
        message: str,
        component: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize server initialization error.

        Args:
            message: Error message
            component: Component that failed to initialize
            details: Additional error details
        """
        error_details = details or {}
        if component:
            error_details["component"] = component
        super().__init__(message, error_details)


class ToolExecutionError(MCPServerError):
    """Exception raised when a tool execution fails."""

    def __init__(
        self,
        message: str,
        tool_name: str | None = None,
        arguments: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize tool execution error.

        Args:
            message: Error message
            tool_name: Name of the tool that failed
            arguments: Arguments passed to the tool
            details: Additional error details
        """
        error_details = details or {}
        if tool_name:
            error_details["tool_name"] = tool_name
        if arguments:
            # Don't include sensitive information in error details
            error_details["arguments_provided"] = list(arguments.keys())
        super().__init__(message, error_details)
