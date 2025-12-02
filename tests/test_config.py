"""Tests for the configuration module."""

import pytest

from rag_server.config import (
    DEFAULT_DB_PATH,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_SERVER_NAME,
    EmbeddingConfig,
    ServerConfig,
    get_default_config,
)


class TestEmbeddingConfig:
    """Tests for EmbeddingConfig."""

    def test_default_model(self) -> None:
        """Test default embedding model."""
        config = EmbeddingConfig()
        assert config.model_name == "all-MiniLM-L6-v2"

    def test_custom_model(self) -> None:
        """Test custom embedding model."""
        config = EmbeddingConfig(model_name="BAAI/bge-small-en-v1.5")
        assert config.model_name == "BAAI/bge-small-en-v1.5"

    def test_frozen_dataclass(self) -> None:
        """Test that EmbeddingConfig is immutable."""
        config = EmbeddingConfig()
        with pytest.raises(AttributeError):
            config.model_name = "new-model"  # type: ignore[misc]


class TestServerConfig:
    """Tests for ServerConfig."""

    def test_default_values(self) -> None:
        """Test default server config values."""
        config = ServerConfig()
        assert config.db_path == "./chroma_db"
        assert config.server_name == "personal-rag-server"
        assert config.embedding.model_name == "all-MiniLM-L6-v2"

    def test_custom_values(self) -> None:
        """Test custom server config values."""
        config = ServerConfig(
            db_path="/custom/path",
            server_name="my-server",
            embedding=EmbeddingConfig(model_name="custom-model"),
        )
        assert config.db_path == "/custom/path"
        assert config.server_name == "my-server"
        assert config.embedding.model_name == "custom-model"

    def test_frozen_dataclass(self) -> None:
        """Test that ServerConfig is immutable."""
        config = ServerConfig()
        with pytest.raises(AttributeError):
            config.db_path = "/new/path"  # type: ignore[misc]


class TestModuleConstants:
    """Tests for module-level constants."""

    def test_default_embedding_model(self) -> None:
        """Test DEFAULT_EMBEDDING_MODEL constant."""
        assert DEFAULT_EMBEDDING_MODEL == "all-MiniLM-L6-v2"

    def test_default_db_path(self) -> None:
        """Test DEFAULT_DB_PATH constant."""
        assert DEFAULT_DB_PATH == "./chroma_db"

    def test_default_server_name(self) -> None:
        """Test DEFAULT_SERVER_NAME constant."""
        assert DEFAULT_SERVER_NAME == "personal-rag-server"


class TestGetDefaultConfig:
    """Tests for get_default_config function."""

    def test_returns_server_config(self) -> None:
        """Test that get_default_config returns ServerConfig."""
        config = get_default_config()
        assert isinstance(config, ServerConfig)

    def test_default_values(self) -> None:
        """Test that get_default_config returns default values."""
        config = get_default_config()
        assert config.db_path == DEFAULT_DB_PATH
        assert config.server_name == DEFAULT_SERVER_NAME
        assert config.embedding.model_name == DEFAULT_EMBEDDING_MODEL
