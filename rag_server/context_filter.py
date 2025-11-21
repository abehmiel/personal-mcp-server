"""
Context filtering system with .mcpignore and .gitignore support.

This module provides functionality to filter files and directories based on
patterns similar to .gitignore, allowing users to exclude unwanted content
from being indexed. Both .mcpignore and .gitignore files are supported.
"""

import os
from pathlib import Path
from typing import Any

import pathspec

from .errors import MCPServerError
from .logging_config import get_logger

logger = get_logger(__name__)


# Default ignore patterns
DEFAULT_IGNORE_PATTERNS = [
    # Version control
    ".git/",
    ".git/**",
    ".svn/",
    ".hg/",
    # Dependencies
    "node_modules/",
    "node_modules/**",
    "vendor/",
    "venv/",
    ".venv/",
    "env/",
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".Python",
    # Build artifacts
    "build/",
    "dist/",
    "*.egg-info/",
    ".eggs/",
    "target/",
    "out/",
    "bin/",
    "obj/",
    # Haskell/Cabal build artifacts
    "dist-newstyle/",
    "dist-newstyle/**",
    ".stack-work/",
    ".stack-work/**",
    "*.hi",
    "*.o",
    "*.dyn_hi",
    "*.dyn_o",
    ".cabal-sandbox/",
    "cabal.sandbox.config",
    # Additional build artifacts
    ".gradle/",
    ".mvn/",
    # IDE
    ".idea/",
    ".vscode/",
    "*.swp",
    "*.swo",
    "*~",
    ".DS_Store",
    # Temporary files
    "*.tmp",
    "*.temp",
    ".cache/",
    # Logs
    "*.log",
    "logs/",
    # Database
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "chroma_db/",
    # Media files (often too large for code indexing)
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.ico",
    "*.svg",
    "*.mp4",
    "*.mp3",
    "*.wav",
    "*.avi",
    "*.mov",
    # Archives
    "*.zip",
    "*.tar",
    "*.tar.gz",
    "*.rar",
    "*.7z",
    # Lock files
    "*.lock",
    "package-lock.json",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
]


class ContextFilter:
    """
    Context filter for excluding files and directories from indexing.

    Supports both .mcpignore and .gitignore files with glob patterns.
    .mcpignore patterns take precedence, and .gitignore is used as fallback.
    """

    def __init__(
        self,
        root_path: Path,
        ignore_file: str = ".mcpignore",
        use_defaults: bool = True,
        custom_patterns: list[str] | None = None,
    ) -> None:
        """
        Initialize the context filter.

        Args:
            root_path: Root directory path for filtering
            ignore_file: Name of the ignore file (default: .mcpignore)
            use_defaults: Whether to use default ignore patterns
            custom_patterns: Additional custom patterns to ignore

        Raises:
            MCPServerError: If initialization fails
        """
        self.root_path = Path(root_path).resolve()
        self.ignore_file = ignore_file

        if not self.root_path.exists():
            raise MCPServerError(
                f"Root path does not exist: {self.root_path}",
                details={"path": str(self.root_path)},
            )

        # Collect all patterns
        patterns: list[str] = []

        if use_defaults:
            patterns.extend(DEFAULT_IGNORE_PATTERNS)

        if custom_patterns:
            patterns.extend(custom_patterns)

        # Load patterns from ignore files (.mcpignore takes precedence, .gitignore as fallback)
        ignore_files_to_check = [
            self.root_path / ignore_file,  # .mcpignore (primary)
            self.root_path / ".gitignore",  # .gitignore (fallback)
        ]

        for ignore_file_path in ignore_files_to_check:
            if ignore_file_path.exists():
                try:
                    file_patterns = self._load_ignore_file(ignore_file_path)
                    patterns.extend(file_patterns)
                    logger.info(f"Loaded {len(file_patterns)} patterns from {ignore_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to load ignore file {ignore_file_path}: {e}")

        # Create pathspec matcher
        self.spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
        logger.info(f"Context filter initialized with {len(patterns)} patterns")

    def _load_ignore_file(self, file_path: Path) -> list[str]:
        """
        Load patterns from an ignore file.

        Args:
            file_path: Path to the ignore file

        Returns:
            list[str]: List of patterns
        """
        patterns: list[str] = []
        with file_path.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#"):
                    patterns.append(line)
        return patterns

    def should_ignore(self, path: Path) -> bool:
        """
        Check if a path should be ignored.

        Optimized version that avoids expensive resolve() calls.

        Args:
            path: Path to check

        Returns:
            bool: True if the path should be ignored
        """
        try:
            # Resolve the path to handle symlinks (e.g., /var -> /private/var on macOS)
            # This ensures relative_to() works correctly when root_path was resolved in __init__
            resolved_path = path.resolve() if path.is_absolute() else path

            # Get relative path from root
            if resolved_path.is_absolute():
                rel_path = resolved_path.relative_to(self.root_path)
            else:
                rel_path = resolved_path

            rel_path_str = str(rel_path)

            # Check if path matches any ignore pattern
            if self.spec.match_file(rel_path_str):
                return True

            # Also check if it's a directory and should be ignored
            if resolved_path.is_dir() and self.spec.match_file(f"{rel_path_str}/"):
                return True

            return False
        except ValueError:
            # Path is not relative to root, ignore it
            return True

    def filter_paths(self, paths: list[Path]) -> list[Path]:
        """
        Filter a list of paths based on ignore patterns.

        Args:
            paths: List of paths to filter

        Returns:
            list[Path]: Filtered list of paths
        """
        filtered = [p for p in paths if not self.should_ignore(p)]
        ignored_count = len(paths) - len(filtered)

        if ignored_count > 0:
            logger.debug(f"Filtered out {ignored_count} paths")

        return filtered

    def get_filtered_files(
        self,
        extensions: list[str] | None = None,
        recursive: bool = True,
    ) -> list[Path]:
        """
        Get all non-ignored files from the root path.

        Uses os.walk() with early directory pruning for efficient filtering.

        Args:
            extensions: Optional list of file extensions to include (e.g., ['.py', '.js'])
            recursive: Whether to search recursively

        Returns:
            list[Path]: List of non-ignored file paths
        """
        files: list[Path] = []

        if recursive:
            # Use os.walk for efficient directory-level filtering
            for dirpath, dirnames, filenames in os.walk(self.root_path):
                dir_path = Path(dirpath)

                # Filter directories in-place to prevent walking into ignored dirs
                # This is the key optimization - we prune entire subtrees
                dirnames[:] = [
                    d
                    for d in dirnames
                    if not self.should_ignore(dir_path / d)
                ]

                # Process files in current directory
                for filename in filenames:
                    file_path = dir_path / filename

                    # Skip ignored files
                    if self.should_ignore(file_path):
                        continue

                    # Filter by extension
                    if extensions is not None and file_path.suffix not in extensions:
                        continue

                    files.append(file_path)
        else:
            for path in self.root_path.glob("*"):
                if (
                    path.is_file()
                    and not self.should_ignore(path)
                    and (extensions is None or path.suffix in extensions)
                ):
                    files.append(path)

        logger.info(f"Found {len(files)} files after filtering")
        return files

    def create_ignore_file(
        self,
        patterns: list[str] | None = None,
        overwrite: bool = False,
    ) -> Path:
        """
        Create a .mcpignore file in the root path.

        Args:
            patterns: Patterns to write (uses defaults if None)
            overwrite: Whether to overwrite existing file

        Returns:
            Path: Path to the created file

        Raises:
            MCPServerError: If file exists and overwrite is False
        """
        ignore_file_path = self.root_path / self.ignore_file

        if ignore_file_path.exists() and not overwrite:
            raise MCPServerError(
                f"Ignore file already exists: {ignore_file_path}",
                details={"path": str(ignore_file_path)},
            )

        patterns_to_write = patterns if patterns is not None else DEFAULT_IGNORE_PATTERNS

        with ignore_file_path.open("w", encoding="utf-8") as f:
            f.write("# MCP Server Ignore File\n")
            f.write("# This file specifies patterns for files to exclude from indexing\n")
            f.write("# Syntax is similar to .gitignore\n\n")

            for pattern in patterns_to_write:
                f.write(f"{pattern}\n")

        logger.info(f"Created ignore file with {len(patterns_to_write)} patterns")
        return ignore_file_path

    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the context filter.

        Returns:
            dict[str, Any]: Statistics dictionary
        """
        total_files = sum(1 for _ in self.root_path.rglob("*") if _.is_file())
        filtered_files = len(self.get_filtered_files())
        ignored_files = total_files - filtered_files

        return {
            "root_path": str(self.root_path),
            "total_files": total_files,
            "filtered_files": filtered_files,
            "ignored_files": ignored_files,
            "ignore_percentage": (
                round(ignored_files / total_files * 100, 2) if total_files > 0 else 0
            ),
        }
