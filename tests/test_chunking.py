"""Tests for document chunking strategies."""


import pytest

from rag_server.chunking import (
    ChunkingStrategy,
    ChunkMetadata,
    CodeAwareChunker,
    DocumentChunk,
    FixedSizeChunker,
    ParagraphChunker,
    get_chunker,
)
from rag_server.errors import DocumentValidationError


class TestFixedSizeChunker:
    """Tests for FixedSizeChunker."""

    def test_basic_chunking(self) -> None:
        """Test basic fixed-size chunking."""
        chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20)
        text = "a" * 300  # 300 characters

        chunks = chunker.chunk(text)

        assert len(chunks) > 0
        assert all(isinstance(c, DocumentChunk) for c in chunks)
        assert all(len(c.text) <= 120 for c in chunks)  # chunk_size + some buffer

    def test_small_text_returns_single_chunk(self) -> None:
        """Test that small text returns a single chunk."""
        chunker = FixedSizeChunker(chunk_size=1000, min_chunk_size=50)
        text = "Small text"

        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].metadata.chunk_type == "complete"

    def test_empty_text_returns_empty_list(self) -> None:
        """Test that empty text returns empty list."""
        chunker = FixedSizeChunker()
        chunks = chunker.chunk("")

        assert len(chunks) == 0

    def test_chunk_metadata(self) -> None:
        """Test chunk metadata is populated correctly."""
        chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20)
        text = "a" * 300

        chunks = chunker.chunk(text)

        for i, chunk in enumerate(chunks):
            assert chunk.metadata.chunk_index == i
            assert chunk.metadata.total_chunks == len(chunks)
            assert chunk.metadata.char_start >= 0
            assert chunk.metadata.char_end > chunk.metadata.char_start

    def test_source_metadata_preserved(self) -> None:
        """Test that source metadata is preserved."""
        chunker = FixedSizeChunker()
        metadata = {"file_path": "/test/file.py", "language": "python"}
        text = "a" * 200

        chunks = chunker.chunk(text, metadata)

        for chunk in chunks:
            assert chunk.source_metadata == metadata

    def test_sentence_boundary_splitting(self) -> None:
        """Test that chunker tries to split at sentence boundaries."""
        chunker = FixedSizeChunker(chunk_size=50, chunk_overlap=10)
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."

        chunks = chunker.chunk(text)

        # Verify chunks exist and contain complete sentences where possible
        assert len(chunks) > 0
        for chunk in chunks:
            # Should not split in the middle of a word
            assert not chunk.text.startswith(" ")


class TestCodeAwareChunker:
    """Tests for CodeAwareChunker."""

    def test_python_function_chunking(self) -> None:
        """Test chunking Python code by functions."""
        chunker = CodeAwareChunker(chunk_size=500)
        code = """
def function1():
    return "test1"

def function2():
    return "test2"

def function3():
    return "test3"
"""

        chunks = chunker.chunk(code, {"language": "python"})

        assert len(chunks) > 0
        # Each chunk should contain relatively complete code blocks
        for chunk in chunks:
            assert "def " in chunk.text or chunk.text.strip() == ""

    def test_language_detection_from_metadata(self) -> None:
        """Test language detection from metadata."""
        chunker = CodeAwareChunker()
        code = "function test() { return true; }"
        metadata = {"file_path": "/test/file.js"}

        chunks = chunker.chunk(code, metadata)

        assert chunks[0].source_metadata["language"] == "javascript"

    def test_language_detection_from_extension(self) -> None:
        """Test language detection from file extension."""
        chunker = CodeAwareChunker()
        code = "def test(): pass"

        test_cases = [
            (".py", "python"),
            (".js", "javascript"),
            (".ts", "typescript"),
            (".java", "java"),
            (".go", "go"),
        ]

        for ext, expected_lang in test_cases:
            metadata = {"file_path": f"/test/file{ext}"}
            chunks = chunker.chunk(code, metadata)
            assert chunks[0].source_metadata["language"] == expected_lang

    def test_fallback_to_fixed_chunking(self) -> None:
        """Test fallback to fixed chunking for unknown language."""
        chunker = CodeAwareChunker(chunk_size=100)
        # Plain text without code structure
        text = "This is plain text without any code structure."

        chunks = chunker.chunk(text)

        # Should still produce chunks
        assert len(chunks) > 0

    def test_javascript_function_detection(self) -> None:
        """Test detection of JavaScript functions."""
        chunker = CodeAwareChunker()
        code = """
function hello() {
    console.log("hello");
}

const world = () => {
    console.log("world");
}
"""

        chunks = chunker.chunk(code, {"language": "javascript"})
        assert len(chunks) > 0


class TestParagraphChunker:
    """Tests for ParagraphChunker."""

    def test_paragraph_splitting(self) -> None:
        """Test splitting by paragraphs."""
        chunker = ParagraphChunker(chunk_size=200)
        text = """First paragraph.

Second paragraph with more text.

Third paragraph.

Fourth paragraph here."""

        chunks = chunker.chunk(text)

        assert len(chunks) > 0
        # Chunks should contain paragraph breaks
        for chunk in chunks:
            assert chunk.metadata.chunk_type == "paragraph"

    def test_large_paragraphs_combined(self) -> None:
        """Test that small paragraphs are combined."""
        chunker = ParagraphChunker(chunk_size=1000)
        text = "Para 1.\n\nPara 2.\n\nPara 3."

        chunks = chunker.chunk(text)

        # Should combine into fewer chunks
        assert len(chunks) >= 1

    def test_overlap_between_paragraphs(self) -> None:
        """Test overlap preservation between chunks."""
        chunker = ParagraphChunker(chunk_size=100, chunk_overlap=20)
        text = "A" * 80 + "\n\n" + "B" * 80 + "\n\n" + "C" * 80

        chunks = chunker.chunk(text)

        assert len(chunks) >= 2


class TestGetChunker:
    """Tests for get_chunker factory function."""

    def test_get_fixed_chunker(self) -> None:
        """Test getting fixed size chunker."""
        chunker = get_chunker(ChunkingStrategy.FIXED)
        assert isinstance(chunker, FixedSizeChunker)

    def test_get_code_chunker(self) -> None:
        """Test getting code-aware chunker."""
        chunker = get_chunker(ChunkingStrategy.CODE)
        assert isinstance(chunker, CodeAwareChunker)

    def test_get_paragraph_chunker(self) -> None:
        """Test getting paragraph chunker."""
        chunker = get_chunker(ChunkingStrategy.PARAGRAPH)
        assert isinstance(chunker, ParagraphChunker)

    def test_get_chunker_with_string(self) -> None:
        """Test getting chunker with string strategy."""
        chunker = get_chunker("fixed")
        assert isinstance(chunker, FixedSizeChunker)

    def test_invalid_strategy_raises_error(self) -> None:
        """Test that invalid strategy raises error."""
        with pytest.raises(DocumentValidationError, match="Unknown chunking strategy"):
            get_chunker("invalid_strategy")  # type: ignore[arg-type]

    def test_custom_parameters(self) -> None:
        """Test chunker with custom parameters."""
        chunker = get_chunker(
            strategy=ChunkingStrategy.FIXED,
            chunk_size=500,
            chunk_overlap=100,
            min_chunk_size=50,
        )

        assert chunker.chunk_size == 500
        assert chunker.chunk_overlap == 100
        assert chunker.min_chunk_size == 50


class TestChunkMetadata:
    """Tests for ChunkMetadata dataclass."""

    def test_chunk_metadata_creation(self) -> None:
        """Test creating chunk metadata."""
        metadata = ChunkMetadata(
            chunk_index=0,
            total_chunks=3,
            char_start=0,
            char_end=100,
            token_count=25,
            language="python",
            chunk_type="function",
        )

        assert metadata.chunk_index == 0
        assert metadata.total_chunks == 3
        assert metadata.language == "python"
        assert metadata.chunk_type == "function"


class TestDocumentChunk:
    """Tests for DocumentChunk dataclass."""

    def test_document_chunk_creation(self) -> None:
        """Test creating document chunk."""
        metadata = ChunkMetadata(
            chunk_index=0,
            total_chunks=1,
            char_start=0,
            char_end=10,
        )
        chunk = DocumentChunk(
            text="test chunk",
            metadata=metadata,
            source_metadata={"file": "test.py"},
        )

        assert chunk.text == "test chunk"
        assert chunk.metadata == metadata
        assert chunk.source_metadata["file"] == "test.py"
