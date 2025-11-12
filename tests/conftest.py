"""
Pytest configuration and shared fixtures.

This module provides common fixtures and configuration for all tests.
"""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from rag_server.embedding_cache import clear_embedding_cache


@pytest.fixture(autouse=True)
def clear_cache_between_tests() -> Generator[None, None, None]:
    """
    Automatically clear the embedding cache between tests.

    This prevents memory leaks during testing by ensuring each test
    starts with a clean embedding cache. The autouse=True makes this
    run for every test automatically.
    """
    # Clear cache before test
    clear_embedding_cache()
    yield
    # Clear cache after test
    clear_embedding_cache()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for testing.

    Yields:
        Path: Path to temporary directory

    Examples:
        >>> def test_something(temp_dir):
        ...     test_file = temp_dir / "test.txt"
        ...     test_file.write_text("test")
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_documents() -> list[str]:
    """
    Provide sample documents for testing.

    Returns:
        list[str]: List of sample document texts
    """
    return [
        "Python is a high-level programming language.",
        "Machine learning is a subset of artificial intelligence.",
        "Vector databases are used for similarity search.",
        "ChromaDB is an open-source embedding database.",
        "RAG stands for Retrieval-Augmented Generation.",
    ]


@pytest.fixture
def sample_metadata() -> list[dict[str, str]]:
    """
    Provide sample metadata for testing.

    Returns:
        list[dict[str, str]]: List of metadata dictionaries
    """
    return [
        {"source": "documentation", "topic": "programming"},
        {"source": "research", "topic": "ai"},
        {"source": "documentation", "topic": "databases"},
        {"source": "documentation", "topic": "databases"},
        {"source": "research", "topic": "ai"},
    ]


@pytest.fixture
def mock_collection_name() -> str:
    """
    Provide a test collection name.

    Returns:
        str: Test collection name
    """
    return "test_collection"
