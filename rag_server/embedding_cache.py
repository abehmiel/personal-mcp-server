"""
Singleton embedding function cache to prevent memory leaks.

This module provides a singleton cache for embedding functions to ensure
that only one instance of each model is loaded into memory (including GPU memory).
This prevents memory leaks when creating multiple RAGMCPServer or CodebaseIndexer instances.
"""

import logging
from typing import Any

from chromadb.utils import embedding_functions

from .config import DEFAULT_EMBEDDING_MODEL

logger = logging.getLogger(__name__)


class EmbeddingFunctionCache:
    """
    Singleton cache for embedding functions.

    This ensures that only one instance of each embedding model is loaded
    into memory, preventing memory leaks from multiple model instances.
    """

    _instance: "EmbeddingFunctionCache | None" = None
    _cache: dict[str, Any] = {}

    def __new__(cls) -> "EmbeddingFunctionCache":
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_embedding_function(
        self,
        model_name: str | None = None,
    ) -> Any:
        """
        Get or create an embedding function.

        Args:
            model_name: Name of the sentence transformer model

        Returns:
            Embedding function instance (cached if exists)
        """
        if model_name is None:
            model_name = DEFAULT_EMBEDDING_MODEL

        if model_name not in self._cache:
            logger.info(f"Loading embedding model: {model_name}")
            self._cache[model_name] = (
                embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=model_name
                )
            )
            logger.info(f"Embedding model cached: {model_name}")
        else:
            logger.debug(f"Using cached embedding model: {model_name}")

        return self._cache[model_name]

    def clear_cache(self) -> None:
        """
        Clear all cached embedding functions.

        This releases the models from memory. Use with caution as it will
        force reload on next use.
        """
        logger.info(f"Clearing {len(self._cache)} cached embedding models")
        self._cache.clear()

    def get_cache_info(self) -> dict[str, Any]:
        """
        Get information about cached models.

        Returns:
            dict with cache statistics
        """
        return {
            "cached_models": list(self._cache.keys()),
            "cache_size": len(self._cache),
        }


# Global singleton instance
_embedding_cache = EmbeddingFunctionCache()


def get_embedding_function(model_name: str | None = None) -> Any:
    """
    Get a cached embedding function.

    This is the primary interface for getting embedding functions.
    It ensures only one instance of each model exists in memory.

    Args:
        model_name: Name of the sentence transformer model.
            If None, uses the default from config.

    Returns:
        Cached embedding function instance
    """
    return _embedding_cache.get_embedding_function(model_name)


def clear_embedding_cache() -> None:
    """
    Clear the embedding function cache.

    This releases all cached models from memory.
    """
    _embedding_cache.clear_cache()


def get_cache_info() -> dict[str, Any]:
    """
    Get cache statistics.

    Returns:
        dict with information about cached models
    """
    return _embedding_cache.get_cache_info()
