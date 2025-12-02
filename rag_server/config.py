"""
Configuration module for RAG server.

Centralizes configuration defaults and provides easy access to settings
that may need to be changed across the codebase.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EmbeddingConfig:
    """Configuration for embedding models.

    Attributes:
        model_name: The sentence-transformers model to use for embeddings.
            See https://www.sbert.net/docs/pretrained_models.html for options.

    Popular model options (trade-offs between quality and speed):
        - "all-MiniLM-L6-v2": Fast, good quality (384 dims, ~80MB)
        - "all-mpnet-base-v2": High quality, slower (768 dims, ~420MB)
        - "BAAI/bge-small-en-v1.5": Excellent quality, fast (384 dims, ~130MB)
        - "BAAI/bge-base-en-v1.5": Better quality, moderate speed (768 dims, ~440MB)
        - "BAAI/bge-large-en-v1.5": Best quality, slowest (1024 dims, ~1.3GB)
        - "nomic-ai/nomic-embed-text-v1.5": Strong performance (768 dims, ~550MB)
        - "intfloat/e5-small-v2": Efficient, good quality (384 dims, ~130MB)
        - "intfloat/e5-base-v2": High quality (768 dims, ~420MB)
        - "intfloat/e5-large-v2": Excellent quality (1024 dims, ~1.3GB)
    """

    model_name: str = "all-MiniLM-L6-v2"


@dataclass(frozen=True)
class ServerConfig:
    """Configuration for the RAG MCP server.

    Attributes:
        db_path: Path to ChromaDB persistent storage.
        server_name: Name of the MCP server for identification.
        embedding: Embedding model configuration.
    """

    db_path: str = "./chroma_db"
    server_name: str = "personal-rag-server"
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)


# Default configuration instance
DEFAULT_EMBEDDING_MODEL = EmbeddingConfig().model_name
DEFAULT_DB_PATH = ServerConfig().db_path
DEFAULT_SERVER_NAME = ServerConfig().server_name


def get_default_config() -> ServerConfig:
    """Get the default server configuration.

    Returns:
        ServerConfig with default values.
    """
    return ServerConfig()
