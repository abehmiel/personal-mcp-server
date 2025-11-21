"""Tests for codebase indexer."""

from pathlib import Path

import pytest

from rag_server.chunking import ChunkingStrategy
from rag_server.errors import ChromaDBError
from rag_server.indexer import (
    CodebaseIndexer,
    IndexingConfig,
    IndexingResult,
)


@pytest.fixture
def sample_codebase(temp_dir: Path) -> Path:
    """Create a sample codebase for testing."""
    # Create directory structure
    src_dir = temp_dir / "src"
    src_dir.mkdir()

    # Create Python files
    (src_dir / "main.py").write_text("""
def main():
    print("Hello, world!")

if __name__ == "__main__":
    main()
""")

    (src_dir / "utils.py").write_text("""
def helper_function():
    return 42

class HelperClass:
    def __init__(self):
        self.value = 0
""")

    # Create a test directory
    test_dir = temp_dir / "tests"
    test_dir.mkdir()
    (test_dir / "test_main.py").write_text("""
def test_main():
    assert True
""")

    # Create files that should be ignored
    git_dir = temp_dir / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("git config")

    pycache = temp_dir / "__pycache__"
    pycache.mkdir()
    (pycache / "main.pyc").write_bytes(b"compiled")

    return temp_dir


class TestIndexingConfig:
    """Tests for IndexingConfig."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = IndexingConfig()

        assert config.chunk_size == 1000
        assert config.chunk_overlap == 200
        assert config.chunking_strategy == ChunkingStrategy.CODE
        assert config.batch_size == 100

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = IndexingConfig(
            chunk_size=500,
            chunk_overlap=100,
            chunking_strategy=ChunkingStrategy.FIXED,
            batch_size=50,
        )

        assert config.chunk_size == 500
        assert config.chunk_overlap == 100
        assert config.chunking_strategy == ChunkingStrategy.FIXED
        assert config.batch_size == 50


class TestCodebaseIndexer:
    """Tests for CodebaseIndexer."""

    def test_initialization(self, temp_dir: Path) -> None:
        """Test indexer initialization."""
        db_path = temp_dir / "test_db"
        indexer = CodebaseIndexer(db_path=db_path)

        assert indexer.db_path == db_path
        assert db_path.exists()

    def test_extract_file_metadata(self, temp_dir: Path) -> None:
        """Test file metadata extraction."""
        indexer = CodebaseIndexer(db_path=temp_dir / "db")

        test_file = temp_dir / "test.py"
        test_file.write_text("# Test file")

        metadata = indexer._extract_file_metadata(test_file)

        assert metadata["file_path"] == str(test_file)
        assert metadata["file_name"] == "test.py"
        assert metadata["file_ext"] == ".py"
        assert metadata["language"] == "python"
        assert metadata["file_size"] > 0
        assert "modified_time" in metadata

    def test_language_detection(self, temp_dir: Path) -> None:
        """Test language detection for various file types."""
        indexer = CodebaseIndexer(db_path=temp_dir / "db")

        test_cases = [
            ("test.py", "python"),
            ("test.js", "javascript"),
            ("test.ts", "typescript"),
            ("test.java", "java"),
            ("test.md", "markdown"),
            ("test.json", "json"),
            ("test.unknown", "unknown"),
        ]

        for filename, expected_lang in test_cases:
            file_path = temp_dir / filename
            file_path.write_text("test")
            metadata = indexer._extract_file_metadata(file_path)
            assert metadata["language"] == expected_lang

    def test_read_file_content(self, temp_dir: Path) -> None:
        """Test reading file content."""
        indexer = CodebaseIndexer(db_path=temp_dir / "db")

        test_file = temp_dir / "test.txt"
        content = "Hello, world!"
        test_file.write_text(content)

        read_content = indexer._read_file_content(test_file)

        assert read_content == content

    def test_read_file_content_encoding_fallback(self, temp_dir: Path) -> None:
        """Test encoding fallback when reading files."""
        indexer = CodebaseIndexer(db_path=temp_dir / "db")

        test_file = temp_dir / "test.txt"
        # Write with specific encoding
        test_file.write_text("Test content", encoding="utf-8")

        content = indexer._read_file_content(test_file)

        assert content is not None
        assert "Test content" in content

    def test_compute_file_hash(self, temp_dir: Path) -> None:
        """Test file hash computation."""
        indexer = CodebaseIndexer(db_path=temp_dir / "db")

        test_file = temp_dir / "test.txt"
        test_file.write_text("Content")

        hash1 = indexer._compute_file_hash(test_file)
        hash2 = indexer._compute_file_hash(test_file)

        # Same file should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hash length

        # Different content should produce different hash
        test_file.write_text("Different content")
        hash3 = indexer._compute_file_hash(test_file)
        assert hash1 != hash3

    def test_create_chunk_id(self, temp_dir: Path) -> None:
        """Test chunk ID generation with readable file paths."""
        indexer = CodebaseIndexer(db_path=temp_dir / "db")

        root_dir = temp_dir / "project"
        root_dir.mkdir()

        # Create two files with same content (simulating duplicates)
        file1 = root_dir / "src" / "module1.py"
        file1.parent.mkdir(parents=True)
        file1.write_text("print('hello')")

        file2 = root_dir / "tests" / "test_module1.py"
        file2.parent.mkdir(parents=True)
        file2.write_text("print('hello')")

        # Compute hashes (should be identical)
        hash1 = indexer._compute_file_hash(file1)
        hash2 = indexer._compute_file_hash(file2)
        assert hash1 == hash2, "Files with same content should have same hash"

        # Generate chunk IDs
        chunk_id1 = indexer._create_chunk_id(file1, root_dir, hash1, 0)
        chunk_id2 = indexer._create_chunk_id(file2, root_dir, hash2, 0)

        # IDs should be different (different paths) but include same content hash
        assert chunk_id1 != chunk_id2, "Files at different paths should have different IDs"
        assert "src/module1.py" in chunk_id1, "ID should include file path"
        assert "tests/test_module1.py" in chunk_id2, "ID should include file path"
        assert hash1[:8] in chunk_id1, "ID should include content hash"
        assert hash2[:8] in chunk_id2, "ID should include content hash"
        assert "chunk_0" in chunk_id1, "ID should include chunk index"
        assert "chunk_0" in chunk_id2, "ID should include chunk index"

        # Test chunk index changes
        chunk_id1_1 = indexer._create_chunk_id(file1, root_dir, hash1, 1)
        assert chunk_id1_1 != chunk_id1, "Different chunk indices should produce different IDs"
        assert "chunk_1" in chunk_id1_1, "ID should reflect correct chunk index"

    @pytest.mark.slow
    def test_index_directory(self, sample_codebase: Path, temp_dir: Path) -> None:
        """Test indexing a directory."""
        db_path = temp_dir / "test_db"
        config = IndexingConfig(show_progress=False)
        indexer = CodebaseIndexer(db_path=db_path, config=config)

        result = indexer.index_directory(
            directory=sample_codebase,
            collection_name="test_collection",
            file_extensions=[".py"],
        )

        assert isinstance(result, IndexingResult)
        assert result.collection_name == "test_collection"
        assert result.files_indexed > 0
        assert result.total_chunks > 0
        # .git and __pycache__ files should be filtered out
        assert result.files_skipped >= 0

    @pytest.mark.slow
    def test_index_directory_force_reindex(self, sample_codebase: Path, temp_dir: Path) -> None:
        """Test force reindexing."""
        db_path = temp_dir / "test_db"
        config = IndexingConfig(show_progress=False)
        indexer = CodebaseIndexer(db_path=db_path, config=config)

        # Index once
        result1 = indexer.index_directory(
            directory=sample_codebase,
            collection_name="test_collection",
            file_extensions=[".py"],
        )

        # Index again with force
        result2 = indexer.index_directory(
            directory=sample_codebase,
            collection_name="test_collection",
            file_extensions=[".py"],
            force_reindex=True,
        )

        assert result2.files_indexed > 0

    def test_index_directory_nonexistent_raises_error(self, temp_dir: Path) -> None:
        """Test that indexing nonexistent directory raises error."""
        indexer = CodebaseIndexer(db_path=temp_dir / "db")

        with pytest.raises(ChromaDBError, match="does not exist"):
            indexer.index_directory(
                directory="/nonexistent/path",
                collection_name="test",
            )

    @pytest.mark.slow
    def test_get_collection_stats(self, sample_codebase: Path, temp_dir: Path) -> None:
        """Test getting collection statistics."""
        db_path = temp_dir / "test_db"
        config = IndexingConfig(show_progress=False)
        indexer = CodebaseIndexer(db_path=db_path, config=config)

        # Index directory first
        indexer.index_directory(
            directory=sample_codebase,
            collection_name="test_collection",
            file_extensions=[".py"],
        )

        # Get stats
        stats = indexer.get_collection_stats("test_collection")

        assert stats["collection_name"] == "test_collection"
        assert stats["total_chunks"] > 0
        assert "languages" in stats
        assert "python" in stats["languages"]

    def test_get_collection_stats_nonexistent_raises_error(self, temp_dir: Path) -> None:
        """Test that getting stats for nonexistent collection raises error."""
        indexer = CodebaseIndexer(db_path=temp_dir / "db")

        with pytest.raises(ChromaDBError):
            indexer.get_collection_stats("nonexistent_collection")

    @pytest.mark.slow
    def test_batch_processing(self, temp_dir: Path) -> None:
        """Test batch processing of files."""
        # Create many small files
        src_dir = temp_dir / "src"
        src_dir.mkdir()

        for i in range(10):
            (src_dir / f"file{i}.py").write_text(f"# File {i}\nprint({i})")

        db_path = temp_dir / "test_db"
        config = IndexingConfig(batch_size=3, show_progress=False)
        indexer = CodebaseIndexer(db_path=db_path, config=config)

        result = indexer.index_directory(
            directory=temp_dir,
            collection_name="batch_test",
        )

        assert result.files_indexed == 10
        assert result.total_chunks > 0


class TestIndexingResult:
    """Tests for IndexingResult dataclass."""

    def test_indexing_result_creation(self) -> None:
        """Test creating IndexingResult."""
        result = IndexingResult(
            total_files=10,
            total_chunks=50,
            files_indexed=8,
            files_skipped=2,
            errors=["Error 1", "Error 2"],
            collection_name="test",
        )

        assert result.total_files == 10
        assert result.total_chunks == 50
        assert result.files_indexed == 8
        assert result.files_skipped == 2
        assert len(result.errors) == 2
        assert result.collection_name == "test"
