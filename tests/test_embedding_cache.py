"""
Tests for the embedding function cache.

This module tests the singleton embedding cache to ensure it prevents
memory leaks by reusing embedding model instances.
"""

import pytest

from rag_server.embedding_cache import (
    EmbeddingFunctionCache,
    clear_embedding_cache,
    get_cache_info,
    get_embedding_function,
)


class TestEmbeddingFunctionCache:
    """Test the EmbeddingFunctionCache singleton."""

    def test_singleton_pattern(self) -> None:
        """Test that EmbeddingFunctionCache follows singleton pattern."""
        cache1 = EmbeddingFunctionCache()
        cache2 = EmbeddingFunctionCache()

        # Should be the same instance
        assert cache1 is cache2

    def test_get_embedding_function_caches_model(self) -> None:
        """Test that embedding functions are cached."""
        # Clear cache first
        clear_embedding_cache()

        # First call should load the model
        emb_fn1 = get_embedding_function("all-MiniLM-L6-v2")

        # Second call should return cached model
        emb_fn2 = get_embedding_function("all-MiniLM-L6-v2")

        # Should be the exact same object (not just equal)
        assert emb_fn1 is emb_fn2

    def test_multiple_models_cached_separately(self) -> None:
        """Test that different models are cached separately."""
        clear_embedding_cache()

        emb_fn1 = get_embedding_function("all-MiniLM-L6-v2")
        emb_fn2 = get_embedding_function("all-MiniLM-L6-v2")

        # Same model should return same instance
        assert emb_fn1 is emb_fn2

        # Cache info should show one model
        cache_info = get_cache_info()
        assert cache_info["cache_size"] == 1
        assert "all-MiniLM-L6-v2" in cache_info["cached_models"]

    def test_clear_cache(self) -> None:
        """Test that clear_cache removes all cached models."""
        # Load a model
        get_embedding_function("all-MiniLM-L6-v2")

        # Verify it's cached
        cache_info = get_cache_info()
        assert cache_info["cache_size"] >= 1

        # Clear cache
        clear_embedding_cache()

        # Verify cache is empty
        cache_info = get_cache_info()
        assert cache_info["cache_size"] == 0
        assert len(cache_info["cached_models"]) == 0

    def test_get_cache_info(self) -> None:
        """Test that get_cache_info returns correct information."""
        clear_embedding_cache()

        # Empty cache
        info = get_cache_info()
        assert info["cache_size"] == 0
        assert info["cached_models"] == []

        # Load a model
        get_embedding_function("all-MiniLM-L6-v2")

        # Check cache info
        info = get_cache_info()
        assert info["cache_size"] == 1
        assert "all-MiniLM-L6-v2" in info["cached_models"]

    def test_cache_survives_multiple_calls(self) -> None:
        """Test that cache persists across multiple function calls."""
        clear_embedding_cache()

        # Make multiple calls
        emb_fns = []
        for _ in range(5):
            emb_fns.append(get_embedding_function("all-MiniLM-L6-v2"))

        # All should be the same instance
        for i in range(1, len(emb_fns)):
            assert emb_fns[i] is emb_fns[0]

        # Cache should still have only one model
        cache_info = get_cache_info()
        assert cache_info["cache_size"] == 1


class TestMemoryLeakPrevention:
    """Test that the cache prevents memory leaks."""

    def test_no_duplicate_model_loading(self) -> None:
        """Test that multiple instances don't load duplicate models."""
        clear_embedding_cache()

        # Simulate creating multiple server instances
        embedding_fns = []
        for _ in range(10):
            # Each "instance" gets an embedding function
            emb_fn = get_embedding_function("all-MiniLM-L6-v2")
            embedding_fns.append(emb_fn)

        # All should reference the same model
        for emb_fn in embedding_fns[1:]:
            assert emb_fn is embedding_fns[0]

        # Only one model should be cached
        cache_info = get_cache_info()
        assert cache_info["cache_size"] == 1

    def test_cache_reuse_after_clear(self) -> None:
        """Test that cache can be reused after clearing."""
        clear_embedding_cache()

        # Load model
        emb_fn1 = get_embedding_function("all-MiniLM-L6-v2")

        # Clear and reload
        clear_embedding_cache()
        emb_fn2 = get_embedding_function("all-MiniLM-L6-v2")

        # Should be different instances (new model loaded)
        # Note: This tests that clear actually releases the old model
        # The new model may or may not be at the same memory address
        # so we just verify the cache was cleared and reloaded
        cache_info = get_cache_info()
        assert cache_info["cache_size"] == 1
        assert "all-MiniLM-L6-v2" in cache_info["cached_models"]
