"""
Personal MCP Server with RAG capabilities.

This package provides a Model Context Protocol (MCP) server implementation
with Retrieval-Augmented Generation (RAG) capabilities using ChromaDB.
"""

__version__ = "0.1.0"

from .config import (
    DEFAULT_DB_PATH,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_SERVER_NAME,
    EmbeddingConfig,
    ServerConfig,
    get_default_config,
)
from .embedding_cache import clear_embedding_cache, get_cache_info, get_embedding_function
from .errors import (
    ChromaDBError,
    CollectionNotFoundError,
    DeviceConfigurationError,
    DocumentValidationError,
    EmbeddingError,
    MCPServerError,
    ServerInitializationError,
    ToolExecutionError,
)
from .logging_config import get_logger, log_exception, setup_logging
from .utils import (
    DeviceType,
    PlatformInfo,
    configure_torch_device,
    detect_device,
    get_device_memory_info,
    get_optimal_device_config,
)

__all__ = [
    "DEFAULT_DB_PATH",
    "DEFAULT_EMBEDDING_MODEL",
    "DEFAULT_SERVER_NAME",
    "ChromaDBError",
    "CollectionNotFoundError",
    "DeviceConfigurationError",
    "DeviceType",
    "DocumentValidationError",
    "EmbeddingConfig",
    "EmbeddingError",
    "MCPServerError",
    "PlatformInfo",
    "ServerConfig",
    "ServerInitializationError",
    "ToolExecutionError",
    "__version__",
    "clear_embedding_cache",
    "configure_torch_device",
    "detect_device",
    "get_cache_info",
    "get_default_config",
    "get_device_memory_info",
    "get_embedding_function",
    "get_logger",
    "get_optimal_device_config",
    "log_exception",
    "setup_logging",
]

# RAGMCPServer is not included in __init__ to avoid package name conflicts
# Import it directly: from rag_server.rag_mcp_chroma import RAGMCPServer
