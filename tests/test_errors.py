"""Tests for custom exception classes."""

from rag_server.errors import (
    ChromaDBError,
    CollectionNotFoundError,
    DeviceConfigurationError,
    DocumentValidationError,
    EmbeddingError,
    MCPServerError,
    ServerInitializationError,
    ToolExecutionError,
)


class TestMCPServerError:
    """Tests for base MCPServerError class."""

    def test_basic_error(self) -> None:
        """Test basic error creation."""
        error = MCPServerError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {}

    def test_error_with_details(self) -> None:
        """Test error with details."""
        details = {"key": "value", "count": 42}
        error = MCPServerError("Test error", details=details)
        assert error.details == details
        assert "key=value" in str(error)
        assert "count=42" in str(error)


class TestChromaDBError:
    """Tests for ChromaDBError class."""

    def test_chromadb_error_basic(self) -> None:
        """Test basic ChromaDB error."""
        error = ChromaDBError("Database error")
        assert "Database error" in str(error)

    def test_chromadb_error_with_collection(self) -> None:
        """Test ChromaDB error with collection name."""
        error = ChromaDBError("Query failed", collection_name="test_collection")
        assert error.details["collection"] == "test_collection"

    def test_chromadb_error_with_operation(self) -> None:
        """Test ChromaDB error with operation."""
        error = ChromaDBError("Operation failed", operation="add")
        assert error.details["operation"] == "add"

    def test_chromadb_error_full(self) -> None:
        """Test ChromaDB error with all parameters."""
        error = ChromaDBError(
            "Full error",
            collection_name="my_collection",
            operation="query",
            details={"extra": "info"},
        )
        assert error.details["collection"] == "my_collection"
        assert error.details["operation"] == "query"
        assert error.details["extra"] == "info"


class TestEmbeddingError:
    """Tests for EmbeddingError class."""

    def test_embedding_error_basic(self) -> None:
        """Test basic embedding error."""
        error = EmbeddingError("Embedding failed")
        assert "Embedding failed" in str(error)

    def test_embedding_error_with_model(self) -> None:
        """Test embedding error with model name."""
        error = EmbeddingError("Model error", model_name="all-MiniLM-L6-v2")
        assert error.details["model"] == "all-MiniLM-L6-v2"


class TestCollectionNotFoundError:
    """Tests for CollectionNotFoundError class."""

    def test_collection_not_found(self) -> None:
        """Test collection not found error."""
        error = CollectionNotFoundError("missing_collection")
        assert "missing_collection" in str(error)
        assert error.details["collection"] == "missing_collection"
        assert error.details["operation"] == "get"


class TestDocumentValidationError:
    """Tests for DocumentValidationError class."""

    def test_document_validation_basic(self) -> None:
        """Test basic document validation error."""
        error = DocumentValidationError("Invalid document")
        assert "Invalid document" in str(error)

    def test_document_validation_with_index(self) -> None:
        """Test document validation error with index."""
        error = DocumentValidationError("Invalid document", document_index=5)
        assert error.details["document_index"] == 5

    def test_document_validation_with_errors(self) -> None:
        """Test document validation error with validation errors."""
        validation_errors = ["Field missing", "Invalid type"]
        error = DocumentValidationError("Validation failed", validation_errors=validation_errors)
        assert error.details["validation_errors"] == validation_errors


class TestDeviceConfigurationError:
    """Tests for DeviceConfigurationError class."""

    def test_device_config_basic(self) -> None:
        """Test basic device configuration error."""
        error = DeviceConfigurationError("Device error")
        assert "Device error" in str(error)

    def test_device_config_with_devices(self) -> None:
        """Test device configuration error with device info."""
        error = DeviceConfigurationError(
            "Device not available",
            requested_device="mps",
            available_devices=["cpu"],
        )
        assert error.details["requested_device"] == "mps"
        assert error.details["available_devices"] == ["cpu"]


class TestServerInitializationError:
    """Tests for ServerInitializationError class."""

    def test_server_init_basic(self) -> None:
        """Test basic server initialization error."""
        error = ServerInitializationError("Init failed")
        assert "Init failed" in str(error)

    def test_server_init_with_component(self) -> None:
        """Test server initialization error with component."""
        error = ServerInitializationError("Init failed", component="ChromaDB")
        assert error.details["component"] == "ChromaDB"


class TestToolExecutionError:
    """Tests for ToolExecutionError class."""

    def test_tool_execution_basic(self) -> None:
        """Test basic tool execution error."""
        error = ToolExecutionError("Tool failed")
        assert "Tool failed" in str(error)

    def test_tool_execution_with_details(self) -> None:
        """Test tool execution error with full details."""
        arguments = {"query": "test", "n_results": 5}
        error = ToolExecutionError(
            "Execution failed", tool_name="search_documents", arguments=arguments
        )
        assert error.details["tool_name"] == "search_documents"
        assert "arguments_provided" in error.details
        assert "query" in error.details["arguments_provided"]
        assert "n_results" in error.details["arguments_provided"]
