"""
Integration tests for CLI commands.

This module contains comprehensive integration tests for all CLI commands,
testing end-to-end workflows from the command line interface.
"""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from rag_server.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_codebase(tmp_path: Path) -> Path:
    """Create a temporary codebase for testing."""
    # Create a simple Python project structure
    project = tmp_path / "test_project"
    project.mkdir()

    # Create some Python files
    (project / "main.py").write_text(
        """
def main():
    '''Main entry point for the application.'''
    print("Hello, World!")

if __name__ == "__main__":
    main()
"""
    )

    (project / "utils.py").write_text(
        """
def add(a, b):
    '''Add two numbers together.'''
    return a + b

def multiply(a, b):
    '''Multiply two numbers.'''
    return a * b

class Calculator:
    '''A simple calculator class.'''

    def divide(self, a, b):
        '''Divide a by b.'''
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
"""
    )

    (project / "README.md").write_text(
        """
# Test Project

This is a test project for demonstrating the RAG server.

## Features
- Simple calculator functions
- Main entry point
- Error handling
"""
    )

    # Create a subdirectory
    tests_dir = project / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_utils.py").write_text(
        """
import pytest
from utils import add, multiply, Calculator

def test_add():
    assert add(2, 3) == 5

def test_multiply():
    assert multiply(4, 5) == 20

def test_calculator_divide():
    calc = Calculator()
    assert calc.divide(10, 2) == 5
"""
    )

    return project


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Create a temporary database path."""
    return tmp_path / "test_db"


class TestIndexCommand:
    """Test the index command."""

    def test_index_basic(
        self, runner: CliRunner, temp_codebase: Path, temp_db_path: Path
    ) -> None:
        """Test basic indexing operation."""
        result = runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "index",
                str(temp_codebase),
                "--collection",
                "test_collection",
            ],
        )

        assert result.exit_code == 0
        assert "Indexing complete" in result.output or "indexed" in result.output.lower()

    def test_index_with_extensions(
        self, runner: CliRunner, temp_codebase: Path, temp_db_path: Path
    ) -> None:
        """Test indexing with specific file extensions."""
        result = runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "index",
                str(temp_codebase),
                "--collection",
                "python_only",
                "--extensions",
                ".py",
            ],
        )

        assert result.exit_code == 0

    def test_index_with_strategy(
        self, runner: CliRunner, temp_codebase: Path, temp_db_path: Path
    ) -> None:
        """Test indexing with different chunking strategies."""
        for strategy in ["fixed", "code", "paragraph"]:
            result = runner.invoke(
                cli,
                [
                    "--db-path",
                    str(temp_db_path),
                    "index",
                    str(temp_codebase),
                    "--collection",
                    f"{strategy}_collection",
                    "--strategy",
                    strategy,
                ],
            )

            assert result.exit_code == 0

    def test_index_with_custom_chunk_size(
        self, runner: CliRunner, temp_codebase: Path, temp_db_path: Path
    ) -> None:
        """Test indexing with custom chunk size."""
        result = runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "index",
                str(temp_codebase),
                "--collection",
                "custom_chunks",
                "--chunk-size",
                "500",
                "--chunk-overlap",
                "100",
            ],
        )

        assert result.exit_code == 0

    def test_index_force_reindex(
        self, runner: CliRunner, temp_codebase: Path, temp_db_path: Path
    ) -> None:
        """Test force reindexing."""
        # Index once
        runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "index",
                str(temp_codebase),
                "--collection",
                "force_test",
            ],
        )

        # Force reindex
        result = runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "index",
                str(temp_codebase),
                "--collection",
                "force_test",
                "--force",
            ],
        )

        assert result.exit_code == 0

    def test_index_nonexistent_directory(
        self, runner: CliRunner, temp_db_path: Path
    ) -> None:
        """Test indexing non-existent directory fails gracefully."""
        result = runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "index",
                "/nonexistent/directory",
                "--collection",
                "test",
            ],
        )

        assert result.exit_code != 0


class TestSearchCommand:
    """Test the search command."""

    def test_search_after_index(
        self, runner: CliRunner, temp_codebase: Path, temp_db_path: Path
    ) -> None:
        """Test searching after indexing."""
        # First index
        runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "index",
                str(temp_codebase),
                "--collection",
                "search_test",
            ],
        )

        # Then search
        result = runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "search",
                "calculator",
                "--collection",
                "search_test",
            ],
        )

        assert result.exit_code == 0
        # Should find the Calculator class or related content
        assert "calculator" in result.output.lower() or "result" in result.output.lower()

    def test_search_with_n_results(
        self, runner: CliRunner, temp_codebase: Path, temp_db_path: Path
    ) -> None:
        """Test search with custom number of results."""
        # Index first
        runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "index",
                str(temp_codebase),
                "--collection",
                "n_results_test",
            ],
        )

        # Search with custom n_results
        result = runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "search",
                "function",
                "--collection",
                "n_results_test",
                "--n-results",
                "3",
            ],
        )

        assert result.exit_code == 0

    def test_search_empty_collection(
        self, runner: CliRunner, temp_db_path: Path
    ) -> None:
        """Test searching an empty/non-existent collection."""
        result = runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "search",
                "test query",
                "--collection",
                "empty_collection",
            ],
        )

        # Should not crash, might show "no results" or similar
        assert result.exit_code == 0


class TestListCollectionsCommand:
    """Test the list-collections command."""

    def test_list_empty_collections(
        self, runner: CliRunner, temp_db_path: Path
    ) -> None:
        """Test listing when no collections exist."""
        result = runner.invoke(cli, ["--db-path", str(temp_db_path), "list-collections"])

        assert result.exit_code == 0
        # Should indicate no collections or show empty list
        assert "no collections" in result.output.lower() or "0" in result.output

    def test_list_after_indexing(
        self, runner: CliRunner, temp_codebase: Path, temp_db_path: Path
    ) -> None:
        """Test listing collections after creating them."""
        # Create multiple collections
        for i in range(3):
            runner.invoke(
                cli,
                [
                    "--db-path",
                    str(temp_db_path),
                    "index",
                    str(temp_codebase),
                    "--collection",
                    f"collection_{i}",
                ],
            )

        # List collections
        result = runner.invoke(cli, ["--db-path", str(temp_db_path), "list-collections"])

        assert result.exit_code == 0
        assert "collection_0" in result.output
        assert "collection_1" in result.output
        assert "collection_2" in result.output


class TestStatsCommand:
    """Test the stats command."""

    def test_stats_after_index(
        self, runner: CliRunner, temp_codebase: Path, temp_db_path: Path
    ) -> None:
        """Test getting stats for a collection."""
        # Index first
        runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "index",
                str(temp_codebase),
                "--collection",
                "stats_test",
            ],
        )

        # Get stats
        result = runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "stats",
                "--collection",
                "stats_test",
            ],
        )

        assert result.exit_code == 0
        # Should show statistics
        assert "stats_test" in result.output.lower() or "statistics" in result.output.lower()

    def test_stats_nonexistent_collection(
        self, runner: CliRunner, temp_db_path: Path
    ) -> None:
        """Test getting stats for non-existent collection."""
        result = runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "stats",
                "--collection",
                "nonexistent",
            ],
        )

        # Should fail gracefully
        assert result.exit_code != 0


class TestDeleteCommand:
    """Test the delete command."""

    def test_delete_collection(
        self, runner: CliRunner, temp_codebase: Path, temp_db_path: Path
    ) -> None:
        """Test deleting a collection."""
        # Create a collection
        runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "index",
                str(temp_codebase),
                "--collection",
                "to_delete",
            ],
        )

        # Verify it exists
        list_result = runner.invoke(
            cli, ["--db-path", str(temp_db_path), "list-collections"]
        )
        assert "to_delete" in list_result.output

        # Delete it (with --yes to skip confirmation)
        result = runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "delete",
                "--collection",
                "to_delete",
                "--yes",
            ],
        )

        assert result.exit_code == 0

        # Verify it's gone
        list_result2 = runner.invoke(
            cli, ["--db-path", str(temp_db_path), "list-collections"]
        )
        assert "to_delete" not in list_result2.output

    def test_delete_nonexistent_collection(
        self, runner: CliRunner, temp_db_path: Path
    ) -> None:
        """Test deleting non-existent collection."""
        result = runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "delete",
                "--collection",
                "nonexistent",
                "--yes",
            ],
        )

        # Should fail gracefully
        assert result.exit_code != 0


class TestCreateIgnoreCommand:
    """Test the create-ignore command."""

    def test_create_ignore_basic(
        self, runner: CliRunner, temp_codebase: Path
    ) -> None:
        """Test creating .mcpignore file."""
        result = runner.invoke(
            cli,
            [
                "create-ignore",
                "--directory",
                str(temp_codebase),
            ],
        )

        assert result.exit_code == 0
        # Check file was created
        ignore_file = temp_codebase / ".mcpignore"
        assert ignore_file.exists()
        content = ignore_file.read_text()
        # Should contain common patterns
        assert ".git" in content or "node_modules" in content

    def test_create_ignore_with_custom_patterns(
        self, runner: CliRunner, temp_codebase: Path
    ) -> None:
        """Test creating .mcpignore with custom patterns."""
        result = runner.invoke(
            cli,
            [
                "create-ignore",
                "--directory",
                str(temp_codebase),
                "--patterns",
                "*.tmp",
                "--patterns",
                "*.log",
            ],
        )

        assert result.exit_code == 0
        ignore_file = temp_codebase / ".mcpignore"
        assert ignore_file.exists()
        content = ignore_file.read_text()
        assert "*.tmp" in content
        assert "*.log" in content

    def test_create_ignore_exists_error(
        self, runner: CliRunner, temp_codebase: Path
    ) -> None:
        """Test that creating .mcpignore when it exists fails without --force."""
        # Create first time
        runner.invoke(
            cli,
            [
                "create-ignore",
                "--directory",
                str(temp_codebase),
            ],
        )

        # Try again without force
        result = runner.invoke(
            cli,
            [
                "create-ignore",
                "--directory",
                str(temp_codebase),
            ],
        )

        assert result.exit_code != 0

    def test_create_ignore_force_overwrite(
        self, runner: CliRunner, temp_codebase: Path
    ) -> None:
        """Test force overwriting .mcpignore."""
        # Create first time
        runner.invoke(
            cli,
            [
                "create-ignore",
                "--directory",
                str(temp_codebase),
            ],
        )

        # Force overwrite
        result = runner.invoke(
            cli,
            [
                "create-ignore",
                "--directory",
                str(temp_codebase),
                "--force",
            ],
        )

        assert result.exit_code == 0


class TestCLIVerboseMode:
    """Test verbose mode across commands."""

    def test_verbose_flag(
        self, runner: CliRunner, temp_codebase: Path, temp_db_path: Path
    ) -> None:
        """Test that verbose flag enables detailed logging."""
        result = runner.invoke(
            cli,
            [
                "--verbose",
                "--db-path",
                str(temp_db_path),
                "index",
                str(temp_codebase),
                "--collection",
                "verbose_test",
            ],
        )

        # Should not crash with verbose mode
        assert result.exit_code == 0


class TestEndToEndCLIWorkflow:
    """Test complete end-to-end CLI workflows."""

    @pytest.mark.integration
    def test_full_workflow(
        self, runner: CliRunner, temp_codebase: Path, temp_db_path: Path
    ) -> None:
        """Test complete workflow: create-ignore -> index -> search -> stats -> delete."""
        # 1. Create ignore file
        result = runner.invoke(
            cli, ["create-ignore", "--directory", str(temp_codebase)]
        )
        assert result.exit_code == 0

        # 2. Index the codebase
        result = runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "index",
                str(temp_codebase),
                "--collection",
                "workflow_test",
            ],
        )
        assert result.exit_code == 0

        # 3. List collections
        result = runner.invoke(cli, ["--db-path", str(temp_db_path), "list-collections"])
        assert result.exit_code == 0
        assert "workflow_test" in result.output

        # 4. Search
        result = runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "search",
                "calculator",
                "--collection",
                "workflow_test",
            ],
        )
        assert result.exit_code == 0

        # 5. Get stats
        result = runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "stats",
                "--collection",
                "workflow_test",
            ],
        )
        assert result.exit_code == 0

        # 6. Delete
        result = runner.invoke(
            cli,
            [
                "--db-path",
                str(temp_db_path),
                "delete",
                "--collection",
                "workflow_test",
                "--yes",
            ],
        )
        assert result.exit_code == 0

        # 7. Verify deletion
        result = runner.invoke(cli, ["--db-path", str(temp_db_path), "list-collections"])
        assert result.exit_code == 0
        assert "workflow_test" not in result.output
