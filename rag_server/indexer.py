"""
Codebase indexing system for RAG.

This module provides functionality to index codebases with intelligent chunking,
metadata extraction, and efficient batch processing.
"""

import hashlib
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import chromadb
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from .chunking import ChunkingStrategy, get_chunker
from .context_filter import ContextFilter
from .embedding_cache import get_embedding_function
from .errors import ChromaDBError
from .logging_config import get_logger
from .utils import get_optimal_device_config

logger = get_logger(__name__)


@contextmanager
def _null_context() -> Iterator[None]:
    """Null context manager for when progress is disabled."""
    yield None


@dataclass
class IndexingConfig:
    """Configuration for indexing operations."""

    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.CODE
    batch_size: int = 100
    show_progress: bool = True
    extract_metadata: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10 MB per file limit


@dataclass
class IndexingResult:
    """Result of an indexing operation."""

    total_files: int
    total_chunks: int
    files_indexed: int
    files_skipped: int
    errors: list[str]
    collection_name: str


class CodebaseIndexer:
    """
    Indexer for code repositories with advanced RAG capabilities.

    Handles file filtering, chunking, metadata extraction, and batch indexing.
    """

    def __init__(
        self,
        db_path: str | Path = "./chroma_db",
        embedding_model: str = "all-MiniLM-L6-v2",
        config: IndexingConfig | None = None,
    ) -> None:
        """
        Initialize the codebase indexer.

        Args:
            db_path: Path to ChromaDB storage
            embedding_model: Name of the embedding model
            config: Indexing configuration

        Raises:
            ChromaDBError: If initialization fails
        """
        self.db_path = Path(db_path)
        self.embedding_model = embedding_model
        self.config = config or IndexingConfig()

        # Log device configuration
        device_config = get_optimal_device_config()
        logger.info(f"Indexer using device: {device_config['device']}")

        # Initialize ChromaDB
        try:
            self.db_path.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=str(self.db_path))
            # Use cached embedding function to prevent memory leaks
            self.embedding_fn = get_embedding_function(model_name=self.embedding_model)
            logger.info(f"Indexer initialized with model: {embedding_model}")
        except Exception as e:
            raise ChromaDBError(
                f"Failed to initialize indexer: {e}",
                operation="init",
            ) from e

    def _extract_file_metadata(self, file_path: Path) -> dict[str, Any]:
        """
        Extract metadata from a file.

        Args:
            file_path: Path to the file

        Returns:
            dict[str, Any]: File metadata
        """
        stat = file_path.stat()

        metadata: dict[str, Any] = {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "file_ext": file_path.suffix,
            "file_size": stat.st_size,
            "modified_time": stat.st_mtime,
        }

        # Add language detection
        ext_to_lang = {
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
            ".md": "markdown",
            ".txt": "text",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".xml": "xml",
            ".html": "html",
            ".css": "css",
            ".sql": "sql",
            ".sh": "bash",
        }

        metadata["language"] = ext_to_lang.get(file_path.suffix, "unknown")

        # Try to extract git info if available
        try:
            git_root = file_path
            while git_root.parent != git_root:
                if (git_root / ".git").exists():
                    rel_path = file_path.relative_to(git_root)
                    metadata["git_repo_path"] = str(rel_path)
                    break
                git_root = git_root.parent
        except Exception:
            pass  # Git info is optional

        return metadata

    def _read_file_content(self, file_path: Path) -> str | None:
        """
        Read file content with encoding detection and size limits.

        Args:
            file_path: Path to the file

        Returns:
            str | None: File content or None if read fails or file too large
        """
        # Check file size before reading to prevent memory exhaustion
        try:
            file_size = file_path.stat().st_size
            if file_size > self.config.max_file_size:
                logger.warning(
                    f"Skipping {file_path}: file too large "
                    f"({file_size / 1024 / 1024:.2f} MB > "
                    f"{self.config.max_file_size / 1024 / 1024:.2f} MB limit)"
                )
                return None
        except OSError as e:
            logger.warning(f"Cannot stat {file_path}: {e}")
            return None

        encodings = ["utf-8", "utf-16", "latin-1", "cp1252"]

        for encoding in encodings:
            try:
                with file_path.open("r", encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")
                return None

        logger.warning(f"Could not decode {file_path} with any known encoding")
        return None

    def _compute_file_hash(self, file_path: Path) -> str:
        """
        Compute a hash of the file for deduplication.

        Args:
            file_path: Path to the file

        Returns:
            str: SHA256 hash of the file
        """
        sha256 = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _create_chunk_id(
        self,
        file_path: Path,
        root_directory: Path,
        file_hash: str,
        chunk_index: int,
    ) -> str:
        """
        Create a human-readable, unique chunk ID.

        The ID includes the relative file path (for readability and debugging)
        and a short content hash (for tracking duplicate files).

        Args:
            file_path: Full path to the file
            root_directory: Root directory being indexed
            file_hash: SHA256 hash of the file content
            chunk_index: Index of the chunk within the file

        Returns:
            str: A unique, readable chunk ID
                Format: "relative/path/to/file.ext#hash8#chunk_N"
                Example: "notebooks/demo/README.md#4928251e#chunk_0"
        """
        # Compute relative path from root directory
        try:
            rel_path = file_path.relative_to(root_directory)
        except ValueError:
            # If file is outside root (shouldn't happen), use absolute path
            rel_path = file_path

        # Use forward slashes for consistency across platforms
        path_str = str(rel_path).replace("\\", "/")

        # Include first 8 chars of content hash for deduplication tracking
        hash_prefix = file_hash[:8]

        # Create readable ID: path#hash#chunk_index
        return f"{path_str}#{hash_prefix}#chunk_{chunk_index}"

    def _read_file_with_hash(self, file_path: Path) -> tuple[str | None, str]:
        """
        Read file content and compute hash in one pass for efficiency.

        This avoids reading the file twice (once for content, once for hash).

        Args:
            file_path: Path to the file

        Returns:
            tuple[str | None, str]: (File content or None, SHA256 hash)
        """
        # Check file size before reading to prevent memory exhaustion
        try:
            file_size = file_path.stat().st_size
            if file_size > self.config.max_file_size:
                logger.warning(
                    f"Skipping {file_path}: file too large "
                    f"({file_size / 1024 / 1024:.2f} MB > "
                    f"{self.config.max_file_size / 1024 / 1024:.2f} MB limit)"
                )
                # Still compute hash even if content is skipped
                return None, self._compute_file_hash(file_path)
        except OSError as e:
            logger.warning(f"Cannot stat {file_path}: {e}")
            return None, ""

        # Read binary content once
        try:
            binary_content = file_path.read_bytes()
        except Exception as e:
            logger.warning(f"Error reading {file_path}: {e}")
            return None, ""

        # Compute hash from binary content
        sha256 = hashlib.sha256()
        sha256.update(binary_content)
        file_hash = sha256.hexdigest()

        # Try to decode to text
        encodings = ["utf-8", "utf-16", "latin-1", "cp1252"]
        for encoding in encodings:
            try:
                content = binary_content.decode(encoding)
                return content, file_hash
            except (UnicodeDecodeError, UnicodeError):
                continue

        # Could not decode with any encoding
        logger.warning(f"Could not decode {file_path} with any known encoding")
        return None, file_hash

    def index_directory(
        self,
        directory: str | Path,
        collection_name: str,
        file_extensions: list[str] | None = None,
        use_mcpignore: bool = True,
        force_reindex: bool = False,
    ) -> IndexingResult:
        """
        Index a directory of files.

        Args:
            directory: Directory path to index
            collection_name: Name of the collection to store documents
            file_extensions: Optional list of file extensions to include
            use_mcpignore: Whether to use .mcpignore for filtering
            force_reindex: Whether to force reindexing of existing files

        Returns:
            IndexingResult: Result of the indexing operation

        Raises:
            ChromaDBError: If indexing fails
        """
        directory_path = Path(directory).resolve()

        if not directory_path.exists():
            raise ChromaDBError(
                f"Directory does not exist: {directory}",
                operation="index",
            )

        # Create context filter
        context_filter = ContextFilter(
            root_path=directory_path,
            use_defaults=use_mcpignore,
        )

        # Get filtered files
        files = context_filter.get_filtered_files(
            extensions=file_extensions,
            recursive=True,
        )

        logger.info(f"Found {len(files)} files to index in {directory}")

        # Get or create collection
        try:
            if force_reindex:
                # Delete existing collection if it exists
                try:
                    self.client.delete_collection(name=collection_name)
                    logger.info(f"Deleted existing collection: {collection_name}")
                except Exception:
                    pass

            collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_fn,  # type: ignore[arg-type]
                metadata={"indexed_directory": str(directory_path)},
            )
        except Exception as e:
            raise ChromaDBError(
                f"Failed to create collection: {e}",
                collection_name=collection_name,
                operation="create",
            ) from e

        # Index files
        result = self._index_files(
            files=files,
            collection=collection,
            collection_name=collection_name,
            root_directory=directory_path,
        )

        logger.info(
            f"Indexing complete: {result.files_indexed} files, "
            f"{result.total_chunks} chunks, {result.files_skipped} skipped"
        )

        return result

    def _index_files(
        self,
        files: list[Path],
        collection: Any,
        collection_name: str,
        root_directory: Path,
    ) -> IndexingResult:
        """
        Index a list of files into a collection.

        Args:
            files: List of file paths
            collection: ChromaDB collection
            collection_name: Name of the collection
            root_directory: Root directory being indexed (for computing relative paths)

        Returns:
            IndexingResult: Result of indexing
        """
        total_files = len(files)
        files_indexed = 0
        files_skipped = 0
        total_chunks = 0
        errors: list[str] = []

        # Prepare chunker
        chunker = get_chunker(
            strategy=self.config.chunking_strategy,
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            min_chunk_size=self.config.min_chunk_size,
        )

        # Batch processing
        batch_texts: list[str] = []
        batch_metadatas: list[dict[str, Any]] = []
        batch_ids: list[str] = []

        # Create progress bar if enabled
        if self.config.show_progress:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
            )
        else:
            progress = None

        # Use context manager for proper progress display
        with progress if progress else _null_context():
            task = progress.add_task(f"Indexing {collection_name}...", total=total_files) if progress else None

            for file_path in files:
                try:
                    logger.debug(f"Processing file: {file_path.name}")

                    # Read file content and compute hash in one pass
                    logger.debug(f"  Reading file: {file_path.name}")
                    content, file_hash = self._read_file_with_hash(file_path)
                    if content is None:
                        logger.debug(f"  Skipped (could not read): {file_path.name}")
                        files_skipped += 1
                        if progress and task is not None:
                            progress.update(task, advance=1)
                        continue

                    # Skip empty files
                    if not content.strip():
                        logger.debug(f"  Skipped (empty): {file_path.name}")
                        files_skipped += 1
                        if progress and task is not None:
                            progress.update(task, advance=1)
                        continue

                    logger.debug(f"  File size: {len(content)} chars")

                    # Extract metadata
                    logger.debug(f"  Extracting metadata: {file_path.name}")
                    file_metadata = self._extract_file_metadata(file_path)
                    file_metadata["file_hash"] = file_hash

                    # Chunk the document
                    logger.debug(f"  Chunking: {file_path.name}")
                    chunks = chunker.chunk(content, file_metadata)
                    logger.debug(f"  Created {len(chunks)} chunks from {file_path.name}")

                    # Add chunks to batch
                    for chunk in chunks:
                        # Create human-readable chunk ID with file path and content hash
                        chunk_id = self._create_chunk_id(
                            file_path=file_path,
                            root_directory=root_directory,
                            file_hash=file_hash,
                            chunk_index=chunk.metadata.chunk_index,
                        )

                        # Prepare metadata (flatten for ChromaDB)
                        chunk_metadata = {
                            **chunk.source_metadata,
                            "chunk_index": chunk.metadata.chunk_index,
                            "total_chunks": chunk.metadata.total_chunks,
                            "char_start": chunk.metadata.char_start,
                            "char_end": chunk.metadata.char_end,
                        }

                        if chunk.metadata.token_count is not None:
                            chunk_metadata["token_count"] = chunk.metadata.token_count
                        if chunk.metadata.chunk_type is not None:
                            chunk_metadata["chunk_type"] = chunk.metadata.chunk_type

                        batch_texts.append(chunk.text)
                        batch_metadatas.append(chunk_metadata)
                        batch_ids.append(chunk_id)
                        total_chunks += 1

                        # Process batch if it reaches batch size
                        if len(batch_texts) >= self.config.batch_size:
                            logger.debug(f"  Adding batch of {len(batch_texts)} chunks to collection")
                            self._add_batch_to_collection(
                                collection,
                                batch_texts,
                                batch_metadatas,
                                batch_ids,
                            )
                            logger.debug(f"  Batch added successfully")
                            batch_texts.clear()
                            batch_metadatas.clear()
                            batch_ids.clear()

                    files_indexed += 1

                except Exception as e:
                    error_msg = f"Error indexing {file_path}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    files_skipped += 1

                if progress and task is not None:
                    progress.update(task, advance=1)

            # Add remaining batch
            if batch_texts:
                self._add_batch_to_collection(
                    collection,
                    batch_texts,
                    batch_metadatas,
                    batch_ids,
                )

        return IndexingResult(
            total_files=total_files,
            total_chunks=total_chunks,
            files_indexed=files_indexed,
            files_skipped=files_skipped,
            errors=errors,
            collection_name=collection_name,
        )

    def _add_batch_to_collection(
        self,
        collection: Any,
        texts: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ) -> None:
        """
        Add a batch of documents to a collection.

        Args:
            collection: ChromaDB collection
            texts: List of document texts
            metadatas: List of metadata dicts
            ids: List of document IDs
        """
        try:
            collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids,
            )
        except Exception as e:
            logger.error(f"Failed to add batch to collection: {e}")
            raise ChromaDBError(
                f"Failed to add batch: {e}",
                collection_name=collection.name,
                operation="add",
            ) from e

    def get_collection_stats(self, collection_name: str) -> dict[str, Any]:
        """
        Get statistics for a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            dict[str, Any]: Collection statistics

        Raises:
            ChromaDBError: If operation fails
        """
        try:
            collection = self.client.get_collection(name=collection_name)

            total_docs = collection.count()

            # Get sample metadata to analyze
            sample = collection.get(limit=min(100, total_docs))

            languages: set[str] = set()
            file_types: set[str] = set()

            if sample["metadatas"]:
                for metadata in sample["metadatas"]:
                    if metadata and isinstance(metadata, dict):
                        if "language" in metadata:
                            languages.add(metadata["language"])
                        if "file_ext" in metadata:
                            file_types.add(metadata["file_ext"])

            return {
                "collection_name": collection_name,
                "total_chunks": total_docs,
                "languages": sorted(languages),
                "file_types": sorted(file_types),
                "metadata": collection.metadata,
            }
        except Exception as e:
            raise ChromaDBError(
                f"Failed to get collection stats: {e}",
                collection_name=collection_name,
                operation="stats",
            ) from e

    def cleanup(self) -> None:
        """
        Clean up resources.

        Note: This is primarily for explicit cleanup in tests or when
        programmatically managing indexer lifecycle. The ChromaDB client
        and embedding function are designed to be long-lived resources.
        """
        logger.info("Cleaning up CodebaseIndexer resources...")
        # ChromaDB PersistentClient doesn't require explicit cleanup
        # Embedding functions are cached globally to prevent memory leaks
        # Just log that cleanup was requested
        logger.info("Cleanup complete")
