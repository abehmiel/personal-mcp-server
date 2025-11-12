# Development and Contribution Guide

This guide helps developers contribute to the personal MCP server project. Whether you're fixing bugs, adding features, or improving documentation, this guide will help you work effectively.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment Setup](#development-environment-setup)
3. [Project Architecture](#project-architecture)
4. [Development Workflow](#development-workflow)
5. [Code Quality Standards](#code-quality-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [Submitting Changes](#submitting-changes)
8. [Project Roadmap](#project-roadmap)
9. [Code Review Process](#code-review-process)
10. [Release Process](#release-process)

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- **macOS** 11.0 or later (primary development platform)
- **Python** 3.10+ installed
- **uv** package manager (v0.5.24+)
- **Git** for version control
- **Text editor/IDE** (VS Code, PyCharm, etc.)
- **Basic Python knowledge** and async/await understanding
- **Understanding of MCP** (see [mcp-concepts.md](mcp-concepts.md))

### Fork and Clone

1. **Fork the repository** on GitHub (click Fork button)

2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/personal-mcp-server.git
   cd personal-mcp-server
   ```

3. **Add upstream remote:**
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/personal-mcp-server.git
   ```

4. **Verify remotes:**
   ```bash
   git remote -v
   # origin: your fork
   # upstream: original repo
   ```

---

## Development Environment Setup

### Initial Setup

We've automated the entire development environment setup:

```bash
# Automated setup (recommended)
make setup              # Complete first-time setup
make dev                # Install with dev dependencies

# Verify everything works
make doctor             # System diagnostics
make test               # Run test suite

# Alternative: Manual setup
uv sync                 # Install dependencies
uv run pytest           # Verify installation
uv run ruff check .     # Check code style
uv run mypy mcp         # Type checking
```

### Quick Start for Contributors

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/personal-mcp-server.git
cd personal-mcp-server

# 2. One command setup
make setup

# 3. Install git hooks (automatic quality checks on commit)
make pre-commit-install

# 4. Start developing!
make watch-test         # Auto-run tests on file changes
```

### IDE Configuration

#### VS Code

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".venv": true,
    ".mypy_cache": true,
    ".pytest_cache": true,
    ".ruff_cache": true
  }
}
```

Create `.vscode/launch.json` for debugging:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: MCP Server",
      "type": "python",
      "request": "launch",
      "module": "mcp.rag_mcp_chroma",
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "Python: Current Test",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-v"],
      "console": "integratedTerminal"
    }
  ]
}
```

Install recommended extensions:
- Python (Microsoft)
- Ruff (Astral)
- Mypy Type Checker
- GitLens

#### PyCharm

1. **Set Python interpreter:**
   - File → Settings → Project → Python Interpreter
   - Select `.venv/bin/python`

2. **Configure code style:**
   - File → Settings → Editor → Code Style → Python
   - Set line length to 100
   - Enable "Optimize imports on the fly"

3. **Enable type checking:**
   - File → Settings → Tools → Python Integrated Tools
   - Type checker: Mypy

### Environment Variables

Create `.env` file (not in git) for local development:

```bash
# Development settings
LOG_LEVEL=DEBUG
CHROMA_DB_PATH=./chroma_db_dev
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

---

## Project Architecture

### Package Structure

```
mcp/
├── __init__.py           # Package exports
├── errors.py             # Exception hierarchy
├── logging_config.py     # Logging utilities
├── rag_mcp_chroma.py     # Main server implementation
└── utils.py              # Device detection utilities
```

### Key Components

**RAGMCPServer** (`rag_mcp_chroma.py`)
- Main server class
- Tool registration and handling
- ChromaDB integration
- Async request/response processing

**Error Handling** (`errors.py`)
- Custom exception hierarchy
- Detailed error information
- Consistent error reporting

**Utilities** (`utils.py`)
- Device detection (MPS, CUDA, CPU)
- Platform information
- Configuration helpers

**Logging** (`logging_config.py`)
- Centralized logging setup
- Structured logging
- Context managers for temporary log levels

### Design Principles

1. **Type Safety:** Full type hints everywhere
2. **Error Handling:** Use custom exceptions with context
3. **Async First:** All I/O operations are async
4. **Separation of Concerns:** Each module has clear responsibility
5. **Testability:** Design for easy testing
6. **Documentation:** Docstrings for all public APIs

---

## Development Workflow

### Branch Strategy

```bash
# Keep your fork updated
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/my-feature
# or
git checkout -b fix/bug-description
```

**Branch naming:**
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `test/description` - Test improvements
- `refactor/description` - Code refactoring

### Daily Development Workflow (With Automation)

```bash
# Morning: Check system health
make doctor             # Comprehensive diagnostics

# Start development: Auto-run tests
make watch-test         # Tests run on every file change

# During development: Quick checks
make quality            # Fast lint + type check
make test-fast          # Quick test run

# Before committing: Full verification
make all-checks         # Quality + all tests

# Commit: Pre-commit hooks run automatically
git commit -m "feat: add feature"
# Hooks automatically run:
# - format code
# - lint code
# - type check
# - run tests
```

### Making Changes

1. **Make focused changes:**
   - One logical change per commit
   - Keep commits small and reviewable
   - Don't mix unrelated changes

2. **Write tests first** (TDD approach with automation):
   ```bash
   # Write test
   nano tests/test_new_feature.py

   # Start watch mode (auto-runs tests on save)
   make watch-test

   # Run specific test manually
   make test-unit
   # Or: uv run pytest tests/test_new_feature.py

   # Implement feature (tests auto-run with watch-test)
   nano mcp/rag_mcp_chroma.py

   # Verify all tests pass
   make test
   ```

3. **Run quality checks frequently:**
   ```bash
   # Recommended: Fast automated check
   make quality            # Lint + type check (~5 seconds)

   # Alternative: Direct commands
   uv run ruff check .
   uv run ruff check . && uv run mypy mcp && uv run pytest
   ```

4. **Auto-format code:**
   ```bash
   # Format before committing
   make format             # Runs ruff format

   # Or let pre-commit hooks do it automatically
   make pre-commit-install # One-time setup
   # Now formatting happens on every commit!
   ```

5. **Commit changes:**
   ```bash
   git add .
   git commit -m "feat(rag): Add document chunking

   Implements sliding window chunking strategy with configurable
   overlap. Improves search relevance for long documents.

   - Add chunk_documents() function
   - Add ChunkingStrategy enum
   - Add tests for chunking
   - Update documentation

   Closes #42"

   # Pre-commit hooks run automatically:
   # ✅ Code formatted
   # ✅ Linting passed
   # ✅ Type checking passed
   # ✅ Tests passed
   ```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Adding/updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `chore`: Maintenance tasks

**Examples:**

```bash
# Feature
git commit -m "feat(search): Add metadata filtering support"

# Bug fix
git commit -m "fix(chromadb): Handle empty collections gracefully"

# Documentation
git commit -m "docs(readme): Update installation instructions"

# Test
git commit -m "test(utils): Add tests for device detection"
```

---

## Code Quality Standards

### Code Style

**Line Length:** 100 characters maximum

**Imports:** Organized in three groups:
```python
# Standard library
import logging
from pathlib import Path
from typing import Any

# Third-party
import chromadb
from sentence_transformers import SentenceTransformer

# Local
from .errors import ChromaDBError
from .utils import detect_device
```

**Type Hints:** Required for all functions:
```python
# Good
def process_documents(
    documents: list[str],
    metadata: list[dict[str, Any]] | None = None
) -> list[str]:
    """Process documents and return IDs."""
    ...

# Bad - no type hints
def process_documents(documents, metadata=None):
    ...
```

**Docstrings:** Required for public functions (Google style):
```python
def search_documents(
    query: str,
    collection: str,
    n_results: int = 5
) -> list[dict[str, Any]]:
    """
    Search documents in a collection.

    Args:
        query: Search query string
        collection: Name of collection to search
        n_results: Number of results to return

    Returns:
        List of document dictionaries with content and metadata

    Raises:
        CollectionNotFoundError: If collection doesn't exist
        ChromaDBError: If search operation fails

    Example:
        >>> results = search_documents("Python tips", "my-notes", 5)
        >>> for doc in results:
        ...     print(doc["content"])
    """
    ...
```

### Linting

**Recommended: Use make commands**

```bash
# Check for issues
make lint               # Run ruff check

# Auto-fix issues
make lint-fix           # Run ruff check --fix

# Format code
make format             # Run ruff format

# All quality checks
make quality            # Lint + type check
```

**Alternative: Direct ruff commands**

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

**Common ruff rules:**
- No unused imports
- No unused variables
- Proper import ordering
- PEP 8 compliance
- Security best practices

### Type Checking

**Recommended: Use make commands**

```bash
# Check types
make typecheck          # Run mypy on mcp package

# Combined with linting
make quality            # Lint + type check
```

**Alternative: Direct mypy command**

```bash
# Check types
uv run mypy mcp

# Should output: Success: no issues found
```

**Type checking guidelines:**
- Use `list[str]` not `List[str]` (Python 3.10+)
- Use `dict[str, Any]` not `Dict[str, Any]`
- Use `| None` not `Optional[...]`
- Avoid `Any` when possible
- Use Protocol for structural typing

---

## Testing Guidelines

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_errors.py           # Error handling tests
├── test_logging_config.py   # Logging tests
├── test_utils.py            # Utility tests
└── test_rag_mcp_chroma.py   # Server tests (to be added)
```

### Writing Tests

**Use pytest fixtures:**
```python
import pytest
from pathlib import Path

@pytest.fixture
def temp_collection(tmp_path: Path) -> str:
    """Create a temporary test collection."""
    # Setup
    collection_name = "test_collection"
    # Use tmp_path for isolation
    yield collection_name
    # Teardown happens automatically
```

**Test naming:**
```python
# Good names
def test_search_returns_relevant_documents():
    ...

def test_add_documents_with_metadata():
    ...

def test_delete_collection_removes_all_documents():
    ...

# Bad names
def test_search():
    ...

def test1():
    ...
```

**Arrange-Act-Assert pattern:**
```python
def test_add_documents_succeeds():
    # Arrange
    server = RAGMCPServer()
    documents = ["doc1", "doc2"]
    collection = "test"

    # Act
    result = await server._add_documents({
        "collection": collection,
        "documents": documents
    })

    # Assert
    assert len(result) == 1
    assert "Successfully added" in result[0].text
```

### Test Coverage

**Minimum coverage:** 80% for new code

```bash
# Run with coverage
uv run pytest --cov=mcp --cov-report=html

# View report
open htmlcov/index.html
```

**What to test:**
- ✅ Happy path (normal operation)
- ✅ Error cases (invalid input, failures)
- ✅ Edge cases (empty lists, null values)
- ✅ Async behavior (concurrent operations)
- ✅ Integration points (ChromaDB, embeddings)

**What not to test:**
- ❌ Third-party library internals
- ❌ Standard library functions
- ❌ Trivial getters/setters
- ❌ Private helper functions (test via public API)

### Running Tests

**Recommended: Use make commands**

```bash
# All tests (141 tests)
make test               # Full test suite

# Fast tests (skip slow ones)
make test-fast          # ~15 seconds

# Unit tests only
make test-unit          # Fast unit tests

# Integration tests
make test-integration   # Slower integration tests

# Coverage report
make coverage           # HTML coverage report

# Watch mode (auto-run on file changes)
make watch-test         # Continuous testing
```

**Alternative: Direct pytest commands**

```bash
# All tests
uv run pytest

# Specific file
uv run pytest tests/test_utils.py

# Specific test
uv run pytest tests/test_utils.py::test_detect_device

# With verbose output
uv run pytest -v

# Stop on first failure
uv run pytest -x

# Run only unit tests
uv run pytest -m unit

# Skip slow tests
uv run pytest -m "not slow"

# Parallel execution (if many tests)
uv run pytest -n auto
```

---

## Submitting Changes

### Pre-Submission Checklist

**Automated approach (recommended):**

```bash
# Run all checks in one command
make all-checks

# This runs:
# 1. Code formatting
# 2. Linting
# 3. Type checking
# 4. Full test suite

# If all pass, you're ready to submit!
```

**Manual verification (alternative):**

```bash
# 1. All tests pass
make test
# ✅ 141 passed (or more)

# 2. No linting issues
make lint
# ✅ All checks passed!

# 3. No type errors
make typecheck
# ✅ Success: no issues found

# 4. Code formatted
make format

# 5. Documentation updated
# If you changed behavior, update relevant docs

# 6. Tests added
# New features need tests

# 7. Commit messages follow format
git log --oneline -5
```

**With pre-commit hooks installed:**

```bash
# Hooks automatically check on every commit
make pre-commit-install

# Just commit and push!
git commit -m "feat: add feature"
git push

# All quality checks ran automatically during commit
```

### Creating Pull Request

1. **Push to your fork:**
   ```bash
   git push origin feature/my-feature
   ```

2. **Open PR on GitHub:**
   - Go to original repository
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill in PR template

3. **PR Title Format:**
   ```
   feat(scope): Brief description

   Examples:
   feat(rag): Add document chunking strategy
   fix(chromadb): Handle empty collections
   docs(readme): Update installation guide
   ```

4. **PR Description Template:**
   ```markdown
   ## Description
   Brief description of changes and motivation.

   ## Changes
   - Change 1
   - Change 2
   - Change 3

   ## Testing
   - [ ] Unit tests added/updated
   - [ ] Integration tests pass
   - [ ] Manual testing performed

   ## Documentation
   - [ ] Docstrings updated
   - [ ] README updated (if needed)
   - [ ] Relevant docs updated

   ## Checklist
   - [ ] Tests pass
   - [ ] Linting passes
   - [ ] Type checking passes
   - [ ] Commit messages follow format

   ## Related Issues
   Closes #42
   Relates to #38
   ```

### PR Best Practices

**Keep PRs focused:**
- One feature/fix per PR
- Avoid mixing refactoring with features
- Keep changes reviewable (<400 lines ideal)

**Respond to feedback:**
- Address all comments
- Ask questions if unclear
- Update PR based on feedback
- Request re-review when done

**Keep PR updated:**
- Rebase on main regularly
- Resolve conflicts promptly
- Keep CI passing

---

## Project Roadmap

### Current Phase: 2b - Documentation (In Progress)

Comprehensive documentation for users and developers.

### Planned Phases

**Phase 2a: RAG Implementation** (Next)
- [ ] Advanced document chunking
- [ ] Metadata filtering
- [ ] Multi-collection search
- [ ] .mcpignore support
- [ ] CLI tool for indexing

**Phase 3: DX Optimization**
- [ ] Makefile for common commands
- [ ] Pre-commit hooks
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Docker containerization
- [ ] Performance benchmarking

**Phase 4: Documentation Finalization**
- [ ] Update docs with Makefile commands
- [ ] Add screenshots
- [ ] Video tutorials
- [ ] API reference generation

**Phase 5: Integration Testing**
- [ ] End-to-end tests
- [ ] Claude Desktop integration tests
- [ ] Performance testing
- [ ] Load testing

**Phase 6: Code Review & Release**
- [ ] Comprehensive code review
- [ ] Security audit
- [ ] v1.0 release
- [ ] PyPI publication

### Feature Requests

Want to propose a feature?

1. **Check existing issues** first
2. **Open issue** with template:
   ```markdown
   ## Feature Description
   Clear description of feature

   ## Motivation
   Why is this needed?

   ## Proposed Solution
   How would it work?

   ## Alternatives Considered
   Other approaches

   ## Additional Context
   Screenshots, examples, etc.
   ```

3. **Discuss before implementing** - get feedback first

---

## Code Review Process

### For Contributors

**What to expect:**
- Review within 2-3 days typically
- Constructive feedback
- Requests for changes
- Approval when ready

**How to respond:**
- Be respectful and professional
- Ask questions if unclear
- Make requested changes
- Mark conversations as resolved

### For Reviewers

**What to check:**

1. **Functionality:**
   - Does it work as intended?
   - Are edge cases handled?
   - Is error handling appropriate?

2. **Code Quality:**
   - Is it readable and maintainable?
   - Are names clear and descriptive?
   - Is it well-structured?

3. **Tests:**
   - Are there adequate tests?
   - Do tests cover edge cases?
   - Are tests clear and focused?

4. **Documentation:**
   - Are docstrings present and clear?
   - Is behavior documented?
   - Are examples provided?

5. **Performance:**
   - Are there obvious inefficiencies?
   - Is async used appropriately?
   - Are resources managed properly?

**Review guidelines:**
- Be kind and constructive
- Explain the "why" behind suggestions
- Distinguish between "must fix" and "nice to have"
- Approve when it's good enough (not perfect)

---

## Release Process

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR:** Breaking changes
- **MINOR:** New features (backward compatible)
- **PATCH:** Bug fixes

### Release Checklist

```bash
# 1. Update version in pyproject.toml
# 2. Update CHANGELOG.md
# 3. Run full test suite
uv run pytest

# 4. Run quality checks
uv run ruff check .
uv run mypy mcp

# 5. Build package
python -m build

# 6. Test package locally
pip install dist/personal_mcp_server-*.whl

# 7. Create git tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 8. Create GitHub release
# - Write release notes
# - Attach built package
# - Publish release

# 9. Publish to PyPI (when ready)
# python -m twine upload dist/*
```

---

## Additional Resources

### Learning Resources

**Python:**
- [Python asyncio docs](https://docs.python.org/3/library/asyncio.html)
- [Type hints guide](https://docs.python.org/3/library/typing.html)
- [Pytest documentation](https://docs.pytest.org/)

**MCP:**
- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/anthropics/anthropic-mcp-python)
- [mcp-concepts.md](mcp-concepts.md)

**RAG:**
- [ChromaDB docs](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [rag-explained.md](rag-explained.md)

### Project Documentation

- [README.md](../README.md) - Project overview
- [CLAUDE.md](CLAUDE.md) - Technical details
- [claude-desktop-setup.md](claude-desktop-setup.md) - Integration
- [troubleshooting.md](troubleshooting.md) - Problem solving

### Development Tools

```bash
# Install recommended tools
brew install gh  # GitHub CLI
pip install pre-commit  # Git hooks (future)
pip install ipython  # Better REPL
```

---

## Getting Help

**For development questions:**
1. Check this guide and other docs
2. Search existing issues
3. Ask in discussions/Discord
4. Open an issue if needed

**For reviewing PRs:**
- Tag relevant reviewers
- Provide context in description
- Be patient and responsive

**For proposing changes:**
- Discuss first for large changes
- Open issue before PR
- Get feedback early

---

## Thank You!

Thank you for contributing to this project! Every contribution, whether code, documentation, bug reports, or suggestions, helps make this tool better for everyone.

**Happy coding!** 🚀

---

**Document Version:** 1.0
**Last Updated:** 2025-11-11
**For Questions:** Open an issue or discussion on GitHub
