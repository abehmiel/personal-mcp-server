#!/usr/bin/env python3
"""
Personal RAG MCP Server using ChromaDB.

This module implements an MCP (Model Context Protocol) server that provides
RAG (Retrieval-Augmented Generation) capabilities using ChromaDB as the
vector database backend.
"""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any

import chromadb

# Import from external MCP SDK package
# NOTE: This relies on the 'mcp' package installed via pip, not our local package
import mcp.types as mcp_types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Import from our local package - use relative imports to avoid conflicts
from .config import DEFAULT_DB_PATH, DEFAULT_EMBEDDING_MODEL, DEFAULT_SERVER_NAME
from .embedding_cache import get_embedding_function
from .errors import (
    ChromaDBError,
    DocumentValidationError,
    ServerInitializationError,
    ToolExecutionError,
)
from .logging_config import get_logger, log_exception, setup_logging
from .utils import get_optimal_device_config

# Initialize logging
logger = get_logger(__name__)


class RAGMCPServer:
    """
    RAG MCP Server implementation using ChromaDB.

    This class encapsulates the MCP server logic for document storage,
    retrieval, and management using ChromaDB as the backend.
    """

    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        server_name: str = DEFAULT_SERVER_NAME,
    ) -> None:
        """
        Initialize the RAG MCP server.

        Args:
            db_path: Path to ChromaDB persistent storage
            embedding_model: Name of the sentence transformer model to use
            server_name: Name of the MCP server

        Raises:
            ServerInitializationError: If server initialization fails
        """
        # Resolve db_path: if absolute, use as-is; if relative, make it relative to script location
        if Path(db_path).is_absolute():
            self.db_path = Path(db_path)
        else:
            # Make relative paths relative to the project root (parent of rag_server)
            self.db_path = Path(__file__).parent.parent / db_path.lstrip("./")

        self.embedding_model = embedding_model
        self.server = Server(server_name)

        try:
            # Log device configuration
            device_config = get_optimal_device_config()
            logger.info(f"Device configuration: {device_config['device']}")
            for recommendation in device_config["recommendations"]:
                logger.info(f"  - {recommendation}")

            # Initialize ChromaDB client
            self.db_path.mkdir(parents=True, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(path=str(self.db_path))
            logger.info(f"ChromaDB client initialized at {self.db_path}")

            # Initialize embedding function (cached to prevent memory leaks)
            self.embedding_fn = get_embedding_function(model_name=self.embedding_model)
            logger.info(f"Embedding model loaded: {self.embedding_model}")

            # Register handlers
            self._register_handlers()
            logger.info("MCP server handlers registered")

        except Exception as e:
            log_exception(logger, e, "Failed to initialize RAG MCP server")
            raise ServerInitializationError(
                "Server initialization failed", component="RAGMCPServer", details={"error": str(e)}
            ) from e

    def _register_handlers(self) -> None:
        """Register MCP server handlers for tools."""

        @self.server.list_tools()
        async def list_tools() -> list[mcp_types.Tool]:
            """List available MCP tools."""
            return [
                mcp_types.Tool(
                    name="search_documents",
                    description="Search through your personal document collection",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query",
                            },
                            "collection": {
                                "type": "string",
                                "description": "Collection name (e.g., 'research', 'code', 'notes')",
                            },
                            "n_results": {
                                "type": "integer",
                                "description": "Number of results to return",
                                "default": 5,
                            },
                        },
                        "required": ["query", "collection"],
                    },
                ),
                mcp_types.Tool(
                    name="add_documents",
                    description="Add documents to your knowledge base",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "collection": {"type": "string"},
                            "documents": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "metadatas": {
                                "type": "array",
                                "items": {"type": "object"},
                            },
                        },
                        "required": ["collection", "documents"],
                    },
                ),
                mcp_types.Tool(
                    name="list_collections",
                    description="List all available collections in the database",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                mcp_types.Tool(
                    name="delete_collection",
                    description="Delete a collection from the database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "collection": {
                                "type": "string",
                                "description": "Name of the collection to delete",
                            },
                        },
                        "required": ["collection"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
            """Handle tool calls."""
            logger.info(f"Tool called: {name} with arguments: {list(arguments.keys())}")

            try:
                if name == "search_documents":
                    return await self._search_documents(arguments)
                if name == "add_documents":
                    return await self._add_documents(arguments)
                if name == "list_collections":
                    return await self._list_collections()
                if name == "delete_collection":
                    return await self._delete_collection(arguments)
                raise ToolExecutionError(
                    f"Unknown tool: {name}", tool_name=name, arguments=arguments
                )
            except (ChromaDBError, DocumentValidationError, ToolExecutionError) as e:
                log_exception(logger, e, f"Tool execution failed: {name}")
                return [
                    mcp_types.TextContent(
                        type="text",
                        text=f"Error: {e!s}",
                    )
                ]
            except Exception as e:
                log_exception(logger, e, f"Unexpected error during tool execution: {name}")
                raise ToolExecutionError(
                    f"Tool execution failed: {e!s}", tool_name=name, arguments=arguments
                ) from e

    async def _search_documents(self, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
        """
        Search documents in a collection.

        Args:
            arguments: Tool arguments containing query, collection, and n_results

        Returns:
            list[mcp_types.TextContent]: Search results

        Raises:
            ChromaDBError: If search operation fails
        """
        collection_name = arguments["collection"]
        query = arguments["query"]
        n_results = arguments.get("n_results", 5)

        try:
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_fn,  # type: ignore[arg-type]
            )

            results = collection.query(query_texts=[query], n_results=n_results)

            if not results["documents"] or not results["documents"][0]:
                logger.info(f"No results found for query in collection '{collection_name}'")
                return [mcp_types.TextContent(type="text", text="No results found")]

            response: list[str] = []
            for i, (doc, metadata, distance) in enumerate(
                zip(
                    results["documents"][0],
                    results["metadatas"][0],  # type: ignore[index]
                    results["distances"][0],  # type: ignore[index]
                    strict=True,
                )
            ):
                response.append(f"Result {i + 1} (distance: {distance:.3f}):\n{doc}\n")
                if metadata:
                    response.append(f"Metadata: {metadata}\n")

            logger.info(
                f"Search completed: {len(results['documents'][0])} results "
                f"from collection '{collection_name}'"
            )
            return [mcp_types.TextContent(type="text", text="\n".join(response))]

        except Exception as e:
            raise ChromaDBError(
                f"Search failed: {e!s}",
                collection_name=collection_name,
                operation="query",
            ) from e

    async def _add_documents(self, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
        """
        Add documents to a collection.

        Args:
            arguments: Tool arguments containing collection, documents, and metadatas

        Returns:
            list[mcp_types.TextContent]: Success message

        Raises:
            DocumentValidationError: If document validation fails
            ChromaDBError: If add operation fails
        """
        collection_name = arguments["collection"]
        docs = arguments["documents"]
        metadatas = arguments.get("metadatas")

        # Validate documents
        if not docs:
            raise DocumentValidationError("No documents provided", validation_errors=["Empty list"])

        if metadatas is not None and len(metadatas) != len(docs):
            raise DocumentValidationError(
                "Number of metadatas must match number of documents",
                validation_errors=[f"Documents: {len(docs)}, Metadatas: {len(metadatas)}"],
            )

        try:
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_fn,  # type: ignore[arg-type]
            )

            # Generate unique IDs for documents
            ids = [str(uuid.uuid4()) for _ in range(len(docs))]

            # Add documents with or without metadata
            if metadatas is not None:
                collection.add(documents=docs, metadatas=metadatas, ids=ids)
            else:
                collection.add(documents=docs, ids=ids)

            logger.info(f"Added {len(docs)} documents to collection '{collection_name}'")
            return [
                mcp_types.TextContent(
                    type="text",
                    text=f"Successfully added {len(docs)} documents to collection '{collection_name}'",
                )
            ]

        except Exception as e:
            raise ChromaDBError(
                f"Failed to add documents: {e!s}",
                collection_name=collection_name,
                operation="add",
            ) from e

    async def _list_collections(self) -> list[mcp_types.TextContent]:
        """
        List all collections.

        Returns:
            list[mcp_types.TextContent]: List of collection names

        Raises:
            ChromaDBError: If list operation fails
        """
        try:
            collections = self.chroma_client.list_collections()
            collection_names = [col.name for col in collections]

            if not collection_names:
                return [mcp_types.TextContent(type="text", text="No collections found")]

            response = f"Found {len(collection_names)} collections:\n"
            for name in sorted(collection_names):
                collection = self.chroma_client.get_collection(name)
                count = collection.count()
                response += f"  - {name} ({count} documents)\n"

            logger.info(f"Listed {len(collection_names)} collections")
            return [mcp_types.TextContent(type="text", text=response)]

        except Exception as e:
            raise ChromaDBError(f"Failed to list collections: {e!s}", operation="list") from e

    async def _delete_collection(self, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
        """
        Delete a collection.

        Args:
            arguments: Tool arguments containing collection name

        Returns:
            list[mcp_types.TextContent]: Success message

        Raises:
            ChromaDBError: If delete operation fails
        """
        collection_name = arguments["collection"]

        try:
            self.chroma_client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection '{collection_name}'")
            return [
                mcp_types.TextContent(
                    type="text",
                    text=f"Successfully deleted collection '{collection_name}'",
                )
            ]

        except Exception as e:
            raise ChromaDBError(
                f"Failed to delete collection: {e!s}",
                collection_name=collection_name,
                operation="delete",
            ) from e

    def cleanup(self) -> None:
        """
        Clean up resources.

        Note: This is primarily for explicit cleanup in tests or when
        programmatically managing server lifecycle. The ChromaDB client
        and embedding function are designed to be long-lived resources.
        """
        logger.info("Cleaning up RAG MCP server resources...")
        # ChromaDB PersistentClient doesn't require explicit cleanup
        # Embedding functions are cached globally to prevent memory leaks
        # Just log that cleanup was requested
        logger.info("Cleanup complete")

    async def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting RAG MCP server...")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


def main() -> None:
    """Main entry point for the server."""
    # Set up logging
    log_level = logging.INFO
    setup_logging(level=log_level, detailed=True, logger_name="rag_server")

    logger.info("Initializing RAG MCP server...")

    try:
        server = RAGMCPServer()
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        log_exception(logger, e, "Fatal error")
        raise


if __name__ == "__main__":
    main()
