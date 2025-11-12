"""Tests for context filtering system."""

from pathlib import Path

import pytest

from rag_server.context_filter import ContextFilter
from rag_server.errors import MCPServerError


class TestContextFilter:
    """Tests for ContextFilter class."""

    def test_initialization(self, temp_dir: Path) -> None:
        """Test basic initialization."""
        context_filter = ContextFilter(root_path=temp_dir)
        assert context_filter.root_path == temp_dir.resolve()

    def test_initialization_nonexistent_path_raises_error(self) -> None:
        """Test that nonexistent path raises error."""
        with pytest.raises(MCPServerError, match="Root path does not exist"):
            ContextFilter(root_path=Path("/nonexistent/path"))

    def test_should_ignore_git_directory(self, temp_dir: Path) -> None:
        """Test that .git directory is ignored."""
        git_dir = temp_dir / ".git"
        git_dir.mkdir()

        context_filter = ContextFilter(root_path=temp_dir)
        assert context_filter.should_ignore(git_dir)

    def test_should_ignore_node_modules(self, temp_dir: Path) -> None:
        """Test that node_modules is ignored."""
        node_modules = temp_dir / "node_modules"
        node_modules.mkdir()

        context_filter = ContextFilter(root_path=temp_dir)
        assert context_filter.should_ignore(node_modules)

    def test_should_ignore_pycache(self, temp_dir: Path) -> None:
        """Test that __pycache__ is ignored."""
        pycache = temp_dir / "__pycache__"
        pycache.mkdir()

        context_filter = ContextFilter(root_path=temp_dir)
        assert context_filter.should_ignore(pycache)

    def test_should_not_ignore_regular_file(self, temp_dir: Path) -> None:
        """Test that regular files are not ignored."""
        test_file = temp_dir / "test.py"
        test_file.write_text("# Test file")

        context_filter = ContextFilter(root_path=temp_dir)
        assert not context_filter.should_ignore(test_file)

    def test_custom_patterns(self, temp_dir: Path) -> None:
        """Test custom ignore patterns."""
        custom_file = temp_dir / "custom.tmp"
        custom_file.write_text("temp")

        context_filter = ContextFilter(
            root_path=temp_dir,
            custom_patterns=["*.tmp"],
        )
        assert context_filter.should_ignore(custom_file)

    def test_filter_paths(self, temp_dir: Path) -> None:
        """Test filtering a list of paths."""
        # Create test files
        py_file = temp_dir / "test.py"
        py_file.write_text("code")

        git_file = temp_dir / ".git" / "config"
        git_file.parent.mkdir()
        git_file.write_text("config")

        paths = [py_file, git_file]
        context_filter = ContextFilter(root_path=temp_dir)
        filtered = context_filter.filter_paths(paths)

        assert py_file in filtered
        assert git_file not in filtered

    def test_get_filtered_files(self, temp_dir: Path) -> None:
        """Test getting filtered files from directory."""
        # Create test structure
        (temp_dir / "test.py").write_text("code")
        (temp_dir / "README.md").write_text("docs")

        git_dir = temp_dir / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("config")

        context_filter = ContextFilter(root_path=temp_dir)
        files = context_filter.get_filtered_files()

        # Should include Python and Markdown files
        assert len(files) >= 2
        file_names = {f.name for f in files}
        assert "test.py" in file_names
        assert "README.md" in file_names
        assert "config" not in file_names

    def test_get_filtered_files_with_extensions(self, temp_dir: Path) -> None:
        """Test filtering by file extensions."""
        (temp_dir / "test.py").write_text("code")
        (temp_dir / "README.md").write_text("docs")
        (temp_dir / "data.json").write_text("{}")

        context_filter = ContextFilter(root_path=temp_dir)
        py_files = context_filter.get_filtered_files(extensions=[".py"])

        assert len(py_files) == 1
        assert py_files[0].name == "test.py"

    def test_create_ignore_file(self, temp_dir: Path) -> None:
        """Test creating a .mcpignore file."""
        context_filter = ContextFilter(root_path=temp_dir, use_defaults=False)
        ignore_file = context_filter.create_ignore_file()

        assert ignore_file.exists()
        assert ignore_file.name == ".mcpignore"

        # Verify content
        content = ignore_file.read_text()
        assert "# MCP Server Ignore File" in content
        assert ".git/" in content

    def test_create_ignore_file_custom_patterns(self, temp_dir: Path) -> None:
        """Test creating ignore file with custom patterns."""
        context_filter = ContextFilter(root_path=temp_dir, use_defaults=False)
        custom_patterns = ["*.test", "temp/"]
        ignore_file = context_filter.create_ignore_file(patterns=custom_patterns)

        content = ignore_file.read_text()
        assert "*.test" in content
        assert "temp/" in content

    def test_create_ignore_file_exists_raises_error(self, temp_dir: Path) -> None:
        """Test that creating existing file raises error."""
        context_filter = ContextFilter(root_path=temp_dir, use_defaults=False)
        context_filter.create_ignore_file()

        with pytest.raises(MCPServerError, match="already exists"):
            context_filter.create_ignore_file(overwrite=False)

    def test_create_ignore_file_overwrite(self, temp_dir: Path) -> None:
        """Test overwriting existing ignore file."""
        context_filter = ContextFilter(root_path=temp_dir, use_defaults=False)
        context_filter.create_ignore_file()

        # Should not raise
        ignore_file = context_filter.create_ignore_file(overwrite=True)
        assert ignore_file.exists()

    def test_load_ignore_file(self, temp_dir: Path) -> None:
        """Test loading patterns from .mcpignore file."""
        # Create .mcpignore with custom patterns
        ignore_file = temp_dir / ".mcpignore"
        ignore_file.write_text("# Comment\n*.custom\ntemp/\n\n# Another comment\n")

        context_filter = ContextFilter(root_path=temp_dir, use_defaults=False)

        # Test that custom patterns are loaded
        custom_file = temp_dir / "test.custom"
        custom_file.write_text("test")
        assert context_filter.should_ignore(custom_file)

    def test_get_stats(self, temp_dir: Path) -> None:
        """Test getting filter statistics."""
        # Create test files
        (temp_dir / "test.py").write_text("code")
        git_dir = temp_dir / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("config")

        context_filter = ContextFilter(root_path=temp_dir)
        stats = context_filter.get_stats()

        assert "root_path" in stats
        assert "total_files" in stats
        assert "filtered_files" in stats
        assert "ignored_files" in stats
        assert "ignore_percentage" in stats

        assert stats["total_files"] >= 2
        assert stats["ignored_files"] >= 1

    def test_no_defaults(self, temp_dir: Path) -> None:
        """Test filter without default patterns."""
        git_dir = temp_dir / ".git"
        git_dir.mkdir()

        context_filter = ContextFilter(root_path=temp_dir, use_defaults=False)

        # .git should NOT be ignored when defaults are disabled
        # (unless there's a .mcpignore file)
        # Since we're not using defaults and no .mcpignore exists,
        # .git should not be ignored
        assert not context_filter.should_ignore(git_dir)
