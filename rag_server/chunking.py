"""
Advanced document chunking strategies for RAG.

This module provides intelligent chunking of documents with support for:
- Code-aware chunking (respects function/class boundaries)
- Semantic chunking
- Configurable chunk sizes and overlap
- Language-specific handling
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

try:
    import tiktoken
except ImportError:
    tiktoken = None  # type: ignore[assignment]

from .errors import DocumentValidationError
from .logging_config import get_logger

logger = get_logger(__name__)


class ChunkingStrategy(str, Enum):
    """Available chunking strategies."""

    FIXED = "fixed"  # Fixed-size chunks with overlap
    SEMANTIC = "semantic"  # Semantic-aware chunking
    CODE = "code"  # Code-aware chunking (respects boundaries)
    PARAGRAPH = "paragraph"  # Paragraph-based chunking


@dataclass
class ChunkMetadata:
    """Metadata for a document chunk."""

    chunk_index: int
    total_chunks: int
    char_start: int
    char_end: int
    token_count: int | None = None
    language: str | None = None
    chunk_type: str | None = None  # e.g., 'function', 'class', 'paragraph'


@dataclass
class DocumentChunk:
    """A chunk of a document with metadata."""

    text: str
    metadata: ChunkMetadata
    source_metadata: dict[str, Any]


class BaseChunker(ABC):
    """Base class for all chunking strategies."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
    ) -> None:
        """
        Initialize the chunker.

        Args:
            chunk_size: Target size of chunks (in characters or tokens)
            chunk_overlap: Overlap between chunks (in characters or tokens)
            min_chunk_size: Minimum size for a chunk
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

        # Initialize tokenizer if available
        self.tokenizer = None
        if tiktoken is not None:
            try:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
            except Exception as e:
                logger.warning(f"Failed to initialize tokenizer: {e}")

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens in

        Returns:
            int: Number of tokens (or characters if tokenizer not available)
        """
        if self.tokenizer is not None:
            try:
                return len(self.tokenizer.encode(text))
            except Exception:
                pass
        return len(text)

    @abstractmethod
    def chunk(
        self,
        text: str,
        source_metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """
        Chunk a document into smaller pieces.

        Args:
            text: Document text to chunk
            source_metadata: Metadata about the source document

        Returns:
            list[DocumentChunk]: List of document chunks
        """
        pass


class FixedSizeChunker(BaseChunker):
    """Fixed-size chunking with overlap."""

    def chunk(
        self,
        text: str,
        source_metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """Chunk document into fixed-size pieces with overlap."""
        logger.debug(f"FixedSizeChunker.chunk() called with text length: {len(text)}")
        if not text or len(text) < self.min_chunk_size:
            if not text:
                return []
            # Return entire text as single chunk if below minimum
            return [
                DocumentChunk(
                    text=text,
                    metadata=ChunkMetadata(
                        chunk_index=0,
                        total_chunks=1,
                        char_start=0,
                        char_end=len(text),
                        token_count=self.count_tokens(text),
                        chunk_type="complete",
                    ),
                    source_metadata=source_metadata or {},
                )
            ]

        chunk_texts: list[str] = []
        start = 0

        logger.debug(f"Starting chunking loop for text of length {len(text)}")
        iteration = 0
        while start < len(text):
            iteration += 1
            logger.debug(f"Loop iteration {iteration}: start={start}, text_len={len(text)}")
            end = min(start + self.chunk_size, len(text))
            logger.debug(f"  end={end}")

            # Try to break at sentence boundary if possible
            if end < len(text):
                logger.debug(f"  Looking for sentence boundaries...")
                # Look for sentence endings near the chunk boundary
                boundary_text = text[max(0, end - 100) : min(len(text), end + 100)]
                logger.debug(f"  boundary_text length: {len(boundary_text)}")
                sentence_endings = [
                    m.start() + max(0, end - 100) for m in re.finditer(r"[.!?]\s+", boundary_text)
                ]
                logger.debug(f"  Found {len(sentence_endings)} sentence endings")

                if sentence_endings:
                    # Find closest sentence ending to desired end position
                    closest = min(sentence_endings, key=lambda x: abs(x - end))
                    if abs(closest - end) < 100:  # Only use if reasonably close
                        end = closest + 1
                        logger.debug(f"  Adjusted end to {end}")

            logger.debug(f"  Extracting chunk text from {start} to {end}")
            chunk_text = text[start:end].strip()
            logger.debug(f"  Chunk text length: {len(chunk_text)}")

            if len(chunk_text) >= self.min_chunk_size:
                chunk_texts.append(chunk_text)
                logger.debug(f"  Added chunk, total chunks so far: {len(chunk_texts)}")
                new_start = end - self.chunk_overlap
                # Prevent infinite loop: ensure start always advances
                if new_start <= start:
                    start = end
                    logger.debug(f"  Overlap would cause infinite loop, moving start to: {start}")
                else:
                    start = new_start
                    logger.debug(f"  New start position: {start}")
            else:
                start = end
                logger.debug(f"  Chunk too small, moving start to: {start}")

        # Create DocumentChunk objects with metadata
        logger.debug(f"Chunking loop completed. Created {len(chunk_texts)} chunk texts")
        result: list[DocumentChunk] = []
        logger.debug(f"Starting DocumentChunk creation for {len(chunk_texts)} chunks")
        for i, chunk_text in enumerate(chunk_texts):
            logger.debug(f"Processing chunk {i+1}/{len(chunk_texts)}, length: {len(chunk_text)}")
            # Find actual position in original text
            logger.debug(f"  Finding chunk position in text...")
            char_start = text.find(chunk_text)
            char_end = char_start + len(chunk_text) if char_start != -1 else len(chunk_text)
            logger.debug(f"  Found position: {char_start}-{char_end}")

            logger.debug(f"  Counting tokens...")
            token_count = self.count_tokens(chunk_text)
            logger.debug(f"  Token count: {token_count}")

            logger.debug(f"  Creating DocumentChunk...")
            result.append(
                DocumentChunk(
                    text=chunk_text,
                    metadata=ChunkMetadata(
                        chunk_index=i,
                        total_chunks=len(chunk_texts),
                        char_start=char_start if char_start != -1 else 0,
                        char_end=char_end,
                        token_count=token_count,
                        chunk_type="fixed",
                    ),
                    source_metadata=source_metadata or {},
                )
            )
            logger.debug(f"  Chunk {i+1} created successfully")

        logger.debug(f"All {len(result)} DocumentChunks created successfully")
        return result


class CodeAwareChunker(BaseChunker):
    """Code-aware chunking that respects function and class boundaries."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
        language: str | None = None,
    ) -> None:
        """
        Initialize code-aware chunker.

        Args:
            chunk_size: Target size of chunks
            chunk_overlap: Overlap between chunks
            min_chunk_size: Minimum chunk size
            language: Programming language (auto-detected if None)
        """
        super().__init__(chunk_size, chunk_overlap, min_chunk_size)
        self.language = language

    def _detect_language(self, text: str, file_path: Path | None = None) -> str:
        """
        Detect programming language from text or file extension.

        Args:
            text: Code text
            file_path: Optional file path

        Returns:
            str: Detected language
        """
        if file_path:
            ext = file_path.suffix.lower()
            ext_map = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".jsx": "javascript",
                ".tsx": "typescript",
                ".java": "java",
                ".cpp": "cpp",
                ".c": "c",
                ".h": "c",
                ".hpp": "cpp",
                ".go": "go",
                ".rs": "rust",
                ".rb": "ruby",
                ".php": "php",
                ".swift": "swift",
                ".kt": "kotlin",
                ".scala": "scala",
            }
            return ext_map.get(ext, "unknown")

        # Simple heuristics for language detection
        if "def " in text or "import " in text or "class " in text:
            return "python"
        if "function " in text or "const " in text or "let " in text:
            return "javascript"
        if "public class" in text or "private " in text:
            return "java"

        return "unknown"

    def _find_code_boundaries(self, text: str, language: str) -> list[tuple[int, int]]:
        """
        Find function/class boundaries in code.

        Args:
            text: Code text
            language: Programming language

        Returns:
            list[tuple[int, int]]: List of (start, end) positions
        """
        boundaries: list[tuple[int, int]] = []

        if language == "python":
            # Find Python functions and classes
            pattern = r"^(def |class )"
            lines = text.split("\n")
            current_start = 0

            for i, line in enumerate(lines):
                if re.match(pattern, line.strip()):
                    # Calculate current position
                    pos = sum(len(current_line) + 1 for current_line in lines[:i])

                    if current_start > 0:
                        boundaries.append((current_start, pos))

                    current_start = pos

            # Add final boundary
            if current_start > 0:
                boundaries.append((current_start, len(text)))

        elif language in ("javascript", "typescript", "java", "cpp", "c"):
            # Find functions/methods using braces
            brace_depth = 0
            current_start = 0
            in_function = False

            for i, char in enumerate(text):
                if char == "{":
                    if brace_depth == 0:
                        current_start = max(0, i - 200)  # Include function signature
                        in_function = True
                    brace_depth += 1
                elif char == "}":
                    brace_depth -= 1
                    if brace_depth == 0 and in_function:
                        boundaries.append((current_start, i + 1))
                        in_function = False

        return boundaries

    def chunk(
        self,
        text: str,
        source_metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """Chunk code while respecting function/class boundaries."""
        metadata = source_metadata or {}
        file_path = Path(metadata.get("file_path", "")) if "file_path" in metadata else None

        # Detect language
        language = self.language or self._detect_language(text, file_path)
        metadata["language"] = language

        # Find code boundaries
        boundaries = self._find_code_boundaries(text, language)

        if not boundaries:
            # Fall back to fixed-size chunking
            logger.debug(f"No code boundaries found for {language}, using fixed chunking")
            return FixedSizeChunker(self.chunk_size, self.chunk_overlap, self.min_chunk_size).chunk(
                text, metadata
            )

        # Create chunks from boundaries
        chunks: list[str] = []
        current_chunk = ""

        for start, end in boundaries:
            code_block = text[start:end]

            if len(current_chunk) + len(code_block) > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append(current_chunk)
                current_chunk = code_block
            else:
                current_chunk += code_block

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)

        # Create DocumentChunk objects
        result: list[DocumentChunk] = []
        for i, chunk_text in enumerate(chunks):
            result.append(
                DocumentChunk(
                    text=chunk_text,
                    metadata=ChunkMetadata(
                        chunk_index=i,
                        total_chunks=len(chunks),
                        char_start=text.find(chunk_text),
                        char_end=text.find(chunk_text) + len(chunk_text),
                        token_count=self.count_tokens(chunk_text),
                        language=language,
                        chunk_type="code_block",
                    ),
                    source_metadata=metadata,
                )
            )

        return result


class ParagraphChunker(BaseChunker):
    """Paragraph-based chunking for text documents."""

    def chunk(
        self,
        text: str,
        source_metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """Chunk document by paragraphs."""
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r"\n\s*\n", text)

        chunks: list[str] = []
        current_chunk = ""

        for paragraph in paragraphs:
            para = paragraph.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                chunks.append(current_chunk)
                # Include some context from previous paragraph
                if self.chunk_overlap > 0:
                    overlap_text = current_chunk[-self.chunk_overlap :]
                    current_chunk = overlap_text + "\n\n" + para
                else:
                    current_chunk = para
            elif current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        # Create DocumentChunk objects
        result: list[DocumentChunk] = []
        for i, chunk_text in enumerate(chunks):
            result.append(
                DocumentChunk(
                    text=chunk_text,
                    metadata=ChunkMetadata(
                        chunk_index=i,
                        total_chunks=len(chunks),
                        char_start=text.find(chunk_text),
                        char_end=text.find(chunk_text) + len(chunk_text),
                        token_count=self.count_tokens(chunk_text),
                        chunk_type="paragraph",
                    ),
                    source_metadata=source_metadata or {},
                )
            )

        return result


def get_chunker(
    strategy: ChunkingStrategy | str = ChunkingStrategy.FIXED,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    min_chunk_size: int = 100,
    language: str | None = None,
) -> BaseChunker:
    """
    Get a chunker instance based on strategy.

    Args:
        strategy: Chunking strategy to use
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks
        min_chunk_size: Minimum chunk size
        language: Programming language (for code chunking)

    Returns:
        BaseChunker: Chunker instance

    Raises:
        DocumentValidationError: If strategy is unknown
    """
    if isinstance(strategy, str):
        try:
            strategy = ChunkingStrategy(strategy)
        except ValueError as e:
            raise DocumentValidationError(
                f"Unknown chunking strategy: {strategy}",
                validation_errors=[f"Available: {[s.value for s in ChunkingStrategy]}"],
            ) from e

    if strategy == ChunkingStrategy.FIXED:
        return FixedSizeChunker(chunk_size, chunk_overlap, min_chunk_size)
    if strategy == ChunkingStrategy.CODE:
        return CodeAwareChunker(chunk_size, chunk_overlap, min_chunk_size, language)
    if strategy == ChunkingStrategy.PARAGRAPH:
        return ParagraphChunker(chunk_size, chunk_overlap, min_chunk_size)
    if strategy == ChunkingStrategy.SEMANTIC:
        # For now, fall back to paragraph chunking
        logger.warning("Semantic chunking not yet implemented, using paragraph chunking")
        return ParagraphChunker(chunk_size, chunk_overlap, min_chunk_size)

    raise DocumentValidationError(
        f"Unhandled chunking strategy: {strategy}",
        validation_errors=[f"Strategy: {strategy}"],
    )
