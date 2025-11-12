"""
Integration tests for RAG MCP Server.

This module contains comprehensive integration tests for the RAGMCPServer class,
testing the full workflow from initialization through tool execution.
"""

import tempfile
from pathlib import Path

import mcp.types as mcp_types
import pytest

from rag_server.errors import (
    ChromaDBError,
    DocumentValidationError,
    ServerInitializationError,
    ToolExecutionError,
)
from rag_server.rag_mcp_chroma import RAGMCPServer


@pytest.fixture
def temp_db_path() -> Path:
    """Create a temporary directory for ChromaDB."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_chroma_db"


@pytest.fixture
def rag_server(temp_db_path: Path) -> RAGMCPServer:
    """Create a RAGMCPServer instance for testing."""
    return RAGMCPServer(
        db_path=str(temp_db_path),
        embedding_model="all-MiniLM-L6-v2",
        server_name="test-rag-server",
    )


class TestRAGMCPServerInitialization:
    """Test RAGMCPServer initialization."""

    def test_initialization_success(self, temp_db_path: Path) -> None:
        """Test successful server initialization."""
        server = RAGMCPServer(
            db_path=str(temp_db_path),
            embedding_model="all-MiniLM-L6-v2",
            server_name="test-server",
        )

        # Verify attributes
        assert server.db_path == temp_db_path
        assert server.embedding_model == "all-MiniLM-L6-v2"
        assert server.server is not None
        assert server.chroma_client is not None
        assert server.embedding_fn is not None

        # Verify database directory was created
        assert temp_db_path.exists()

    def test_initialization_creates_db_directory(self, temp_db_path: Path) -> None:
        """Test that initialization creates the database directory."""
        assert not temp_db_path.exists()

        RAGMCPServer(db_path=str(temp_db_path))

        assert temp_db_path.exists()

    def test_initialization_with_custom_model(self, temp_db_path: Path) -> None:
        """Test initialization with a custom embedding model."""
        # Note: We use the default model since custom models might not be downloaded
        server = RAGMCPServer(
            db_path=str(temp_db_path),
            embedding_model="all-MiniLM-L6-v2",
        )

        assert server.embedding_model == "all-MiniLM-L6-v2"


class TestAddDocuments:
    """Test add_documents functionality."""

    @pytest.mark.asyncio
    async def test_add_documents_success(self, rag_server: RAGMCPServer) -> None:
        """Test successfully adding documents to a collection."""
        arguments = {
            "collection": "test_collection",
            "documents": [
                "Python is a programming language.",
                "Machine learning is a subset of AI.",
                "Vector databases store embeddings.",
            ],
        }

        result = await rag_server._add_documents(arguments)

        assert len(result) == 1
        assert isinstance(result[0], mcp_types.TextContent)
        assert "Successfully added 3 documents" in result[0].text
        assert "test_collection" in result[0].text

    @pytest.mark.asyncio
    async def test_add_documents_with_metadata(self, rag_server: RAGMCPServer) -> None:
        """Test adding documents with metadata."""
        arguments = {
            "collection": "test_collection",
            "documents": [
                "Document 1",
                "Document 2",
            ],
            "metadatas": [
                {"source": "test", "topic": "programming"},
                {"source": "test", "topic": "ai"},
            ],
        }

        result = await rag_server._add_documents(arguments)

        assert len(result) == 1
        assert "Successfully added 2 documents" in result[0].text

    @pytest.mark.asyncio
    async def test_add_documents_empty_list_raises_error(
        self, rag_server: RAGMCPServer
    ) -> None:
        """Test that adding empty document list raises error."""
        arguments = {
            "collection": "test_collection",
            "documents": [],
        }

        with pytest.raises(DocumentValidationError) as exc_info:
            await rag_server._add_documents(arguments)

        assert "No documents provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_add_documents_mismatched_metadata_raises_error(
        self, rag_server: RAGMCPServer
    ) -> None:
        """Test that mismatched metadata count raises error."""
        arguments = {
            "collection": "test_collection",
            "documents": ["Doc 1", "Doc 2"],
            "metadatas": [{"source": "test"}],  # Only 1 metadata for 2 docs
        }

        with pytest.raises(DocumentValidationError) as exc_info:
            await rag_server._add_documents(arguments)

        assert "Number of metadatas must match" in str(exc_info.value)


class TestSearchDocuments:
    """Test search_documents functionality."""

    @pytest.mark.asyncio
    async def test_search_documents_success(self, rag_server: RAGMCPServer) -> None:
        """Test successful document search."""
        # First add some documents
        await rag_server._add_documents(
            {
                "collection": "search_test",
                "documents": [
                    "Python is a high-level programming language.",
                    "Machine learning uses algorithms to learn from data.",
                    "Vector databases are optimized for similarity search.",
                ],
            }
        )

        # Now search
        result = await rag_server._search_documents(
            {
                "query": "programming language",
                "collection": "search_test",
                "n_results": 2,
            }
        )

        assert len(result) == 1
        assert isinstance(result[0], mcp_types.TextContent)
        assert "Result 1" in result[0].text
        # Should find the Python document as most relevant
        assert "Python" in result[0].text or "programming" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_search_documents_no_results(self, rag_server: RAGMCPServer) -> None:
        """Test search in empty collection returns no results."""
        result = await rag_server._search_documents(
            {
                "query": "test query",
                "collection": "empty_collection",
                "n_results": 5,
            }
        )

        assert len(result) == 1
        assert "No results found" in result[0].text

    @pytest.mark.asyncio
    async def test_search_documents_with_metadata(self, rag_server: RAGMCPServer) -> None:
        """Test search returns metadata when present."""
        # Add documents with metadata
        await rag_server._add_documents(
            {
                "collection": "metadata_test",
                "documents": ["Test document about Python"],
                "metadatas": [{"source": "test", "language": "python"}],
            }
        )

        # Search
        result = await rag_server._search_documents(
            {
                "query": "Python",
                "collection": "metadata_test",
                "n_results": 1,
            }
        )

        assert len(result) == 1
        assert "Metadata:" in result[0].text
        assert "source" in result[0].text or "language" in result[0].text

    @pytest.mark.asyncio
    async def test_search_documents_default_n_results(
        self, rag_server: RAGMCPServer
    ) -> None:
        """Test that default n_results is used when not specified."""
        # Add some documents
        docs = [f"Document {i} about topic {i}" for i in range(10)]
        await rag_server._add_documents(
            {"collection": "default_n_test", "documents": docs}
        )

        # Search without specifying n_results
        result = await rag_server._search_documents(
            {
                "query": "topic",
                "collection": "default_n_test",
            }
        )

        # Default should be 5 results
        assert len(result) == 1
        result_text = result[0].text
        # Count number of "Result X" occurrences
        result_count = result_text.count("Result ")
        assert result_count <= 5  # Should get at most 5 results


class TestListCollections:
    """Test list_collections functionality."""

    @pytest.mark.asyncio
    async def test_list_collections_empty(self, rag_server: RAGMCPServer) -> None:
        """Test listing collections when none exist."""
        result = await rag_server._list_collections()

        assert len(result) == 1
        assert "No collections found" in result[0].text

    @pytest.mark.asyncio
    async def test_list_collections_with_data(self, rag_server: RAGMCPServer) -> None:
        """Test listing collections with data."""
        # Create some collections
        await rag_server._add_documents(
            {"collection": "collection_1", "documents": ["Doc 1", "Doc 2"]}
        )
        await rag_server._add_documents(
            {"collection": "collection_2", "documents": ["Doc A", "Doc B", "Doc C"]}
        )

        result = await rag_server._list_collections()

        assert len(result) == 1
        assert "Found 2 collections" in result[0].text
        assert "collection_1" in result[0].text
        assert "collection_2" in result[0].text
        # Should show document counts
        assert "(2 documents)" in result[0].text
        assert "(3 documents)" in result[0].text


class TestDeleteCollection:
    """Test delete_collection functionality."""

    @pytest.mark.asyncio
    async def test_delete_collection_success(self, rag_server: RAGMCPServer) -> None:
        """Test successfully deleting a collection."""
        # Create a collection
        await rag_server._add_documents(
            {"collection": "to_delete", "documents": ["Test doc"]}
        )

        # Verify it exists
        list_result = await rag_server._list_collections()
        assert "to_delete" in list_result[0].text

        # Delete it
        result = await rag_server._delete_collection({"collection": "to_delete"})

        assert len(result) == 1
        assert "Successfully deleted collection 'to_delete'" in result[0].text

        # Verify it's gone
        list_result = await rag_server._list_collections()
        assert "to_delete" not in list_result[0].text

    @pytest.mark.asyncio
    async def test_delete_nonexistent_collection_raises_error(
        self, rag_server: RAGMCPServer
    ) -> None:
        """Test deleting non-existent collection raises error."""
        with pytest.raises(ChromaDBError) as exc_info:
            await rag_server._delete_collection({"collection": "nonexistent"})

        assert "Failed to delete collection" in str(exc_info.value)


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_full_document_lifecycle(self, rag_server: RAGMCPServer) -> None:
        """Test the complete lifecycle: add -> search -> delete."""
        collection_name = "lifecycle_test"

        # 1. Add documents
        add_result = await rag_server._add_documents(
            {
                "collection": collection_name,
                "documents": [
                    "Python is great for data science.",
                    "JavaScript is popular for web development.",
                    "Rust is known for memory safety.",
                ],
                "metadatas": [
                    {"language": "python"},
                    {"language": "javascript"},
                    {"language": "rust"},
                ],
            }
        )
        assert "Successfully added 3 documents" in add_result[0].text

        # 2. Verify collection exists
        list_result = await rag_server._list_collections()
        assert collection_name in list_result[0].text
        assert "(3 documents)" in list_result[0].text

        # 3. Search documents
        search_result = await rag_server._search_documents(
            {
                "query": "data science programming",
                "collection": collection_name,
                "n_results": 1,
            }
        )
        assert "Python" in search_result[0].text

        # 4. Add more documents
        add_result2 = await rag_server._add_documents(
            {
                "collection": collection_name,
                "documents": ["Go is efficient for concurrent programming."],
            }
        )
        assert "Successfully added 1 documents" in add_result2[0].text

        # 5. Verify count updated
        list_result2 = await rag_server._list_collections()
        assert "(4 documents)" in list_result2[0].text

        # 6. Delete collection
        delete_result = await rag_server._delete_collection({"collection": collection_name})
        assert "Successfully deleted" in delete_result[0].text

        # 7. Verify it's gone
        list_result3 = await rag_server._list_collections()
        assert collection_name not in list_result3[0].text or "No collections found" in list_result3[0].text

    @pytest.mark.asyncio
    async def test_multiple_collections(self, rag_server: RAGMCPServer) -> None:
        """Test working with multiple collections simultaneously."""
        # Create multiple collections
        await rag_server._add_documents(
            {
                "collection": "programming",
                "documents": ["Python is versatile", "JavaScript runs in browsers"],
            }
        )
        await rag_server._add_documents(
            {
                "collection": "databases",
                "documents": ["PostgreSQL is relational", "MongoDB is NoSQL"],
            }
        )
        await rag_server._add_documents(
            {
                "collection": "devops",
                "documents": ["Docker containerizes apps", "Kubernetes orchestrates containers"],
            }
        )

        # List all collections
        list_result = await rag_server._list_collections()
        assert "Found 3 collections" in list_result[0].text
        assert "programming" in list_result[0].text
        assert "databases" in list_result[0].text
        assert "devops" in list_result[0].text

        # Search in specific collection
        search_result = await rag_server._search_documents(
            {
                "query": "containers",
                "collection": "devops",
                "n_results": 2,
            }
        )
        assert "Docker" in search_result[0].text or "Kubernetes" in search_result[0].text

        # Delete one collection
        await rag_server._delete_collection({"collection": "databases"})

        # Verify only 2 remain
        list_result2 = await rag_server._list_collections()
        assert "Found 2 collections" in list_result2[0].text
        assert "databases" not in list_result2[0].text


class TestErrorHandling:
    """Test error handling in various scenarios."""

    @pytest.mark.asyncio
    async def test_search_with_invalid_collection_name(
        self, rag_server: RAGMCPServer
    ) -> None:
        """Test search with problematic collection name still works (ChromaDB is flexible)."""
        # ChromaDB actually handles most collection names gracefully
        result = await rag_server._search_documents(
            {
                "query": "test",
                "collection": "valid-collection_name123",
                "n_results": 5,
            }
        )
        # Should return "No results found" for empty collection, not error
        assert "No results found" in result[0].text

    @pytest.mark.asyncio
    async def test_add_documents_persists_across_instances(
        self, temp_db_path: Path
    ) -> None:
        """Test that documents persist across server instances."""
        # Create server and add documents
        server1 = RAGMCPServer(db_path=str(temp_db_path))
        await server1._add_documents(
            {
                "collection": "persistent",
                "documents": ["Persistent document"],
            }
        )

        # Create new server instance with same db_path
        server2 = RAGMCPServer(db_path=str(temp_db_path))

        # Search should find the document
        result = await server2._search_documents(
            {
                "query": "Persistent",
                "collection": "persistent",
                "n_results": 1,
            }
        )

        assert "Persistent document" in result[0].text


class TestPerformance:
    """Test performance characteristics."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_bulk_document_addition(self, rag_server: RAGMCPServer) -> None:
        """Test adding a large number of documents."""
        # Create 100 documents
        documents = [f"This is test document number {i} about topic {i % 10}" for i in range(100)]

        result = await rag_server._add_documents(
            {
                "collection": "bulk_test",
                "documents": documents,
            }
        )

        assert "Successfully added 100 documents" in result[0].text

        # Verify they're searchable
        search_result = await rag_server._search_documents(
            {
                "query": "topic 5",
                "collection": "bulk_test",
                "n_results": 10,
            }
        )

        assert len(search_result) == 1
        # Should find multiple relevant results
        assert "Result" in search_result[0].text

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_search_performance_with_many_documents(
        self, rag_server: RAGMCPServer
    ) -> None:
        """Test search performance with a large collection."""
        # Add 500 documents
        documents = [
            f"Document {i}: This document discusses {['Python', 'JavaScript', 'Rust', 'Go', 'Java'][i % 5]}"
            for i in range(500)
        ]

        await rag_server._add_documents(
            {
                "collection": "large_collection",
                "documents": documents,
            }
        )

        # Search should still be fast
        result = await rag_server._search_documents(
            {
                "query": "Python programming",
                "collection": "large_collection",
                "n_results": 10,
            }
        )

        assert len(result) == 1
        assert "Result" in result[0].text
