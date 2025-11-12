# Makefile Command Reference

Complete guide to all developer automation commands for the personal MCP server project.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Setup & Installation](#setup--installation)
3. [Running the Server](#running-the-server)
4. [Testing](#testing)
5. [RAG Operations](#rag-operations)
6. [Code Quality](#code-quality)
7. [Claude Desktop Configuration](#claude-desktop-configuration)
8. [Utilities](#utilities)
9. [Development Tools](#development-tools)
10. [Troubleshooting](#troubleshooting)

---

## Quick Start

### First Time Setup

```bash
# Clone the repository
cd /Users/Abe/Projects/personal-mcp-server

# Complete setup (installs dependencies and runs diagnostics)
make setup

# Configure Claude Desktop integration
make config

# Verify everything works
make test
```

### Daily Development Workflow

```bash
# Check code quality before committing
make quality

# Run tests
make test-fast

# Index a codebase
make index REPO=~/my-project COLLECTION=my-app

# Search the index
make search QUERY="authentication logic" COLLECTION=my-app
```

---

## Setup & Installation

### `make setup`

**Complete first-time setup**

Runs installation and diagnostic checks. This is your one-command setup.

```bash
make setup
```

**What it does:**
1. Installs all dependencies via `uv sync`
2. Runs system diagnostics (`make doctor`)
3. Provides next steps

**When to use:** First time setting up the project or after a fresh clone.

---

### `make install`

**Install dependencies**

```bash
make install
```

**What it does:** Runs `uv sync` to install all production dependencies.

**When to use:**
- First time setup
- After pulling changes that modify `pyproject.toml`
- After manually editing dependencies

---

### `make dev`

**Install with development dependencies**

```bash
make dev
```

**What it does:** Runs `uv sync --all-extras` to install dev tools (pytest, ruff, mypy).

**When to use:** Setting up for development work (testing, linting, type checking).

---

## Running the Server

### `make run`

**Start the MCP server**

```bash
make run
```

**What it does:** Starts the MCP server in normal mode.

**Output:** Logs to stderr, MCP protocol on stdout/stdin.

**Stop:** Press `Ctrl+C`

**When to use:**
- Testing the server locally
- Debugging connection issues
- Manual testing before Claude Desktop integration

---

### `make debug`

**Start server in debug mode**

```bash
make debug
```

**What it does:** Starts server with verbose logging enabled.

**When to use:** Troubleshooting server issues, understanding behavior.

---

## Testing

### `make test`

**Run all tests**

```bash
make test
```

**What it does:** Runs entire test suite (91 tests) with coverage reporting.

**When to use:** Before committing, after making changes, CI/CD validation.

---

### `make test-fast`

**Run fast tests only**

```bash
make test-fast
```

**What it does:** Runs all tests except those marked with `@pytest.mark.slow`.

**When to use:**
- Quick validation during development
- Pre-commit checks
- Rapid feedback loop

**Speed:** ~10-15 seconds vs ~30+ seconds for full suite.

---

### `make test-unit`

**Run unit tests only**

```bash
make test-unit
```

**What it does:** Runs tests marked with `@pytest.mark.unit`.

**When to use:** Testing isolated components without external dependencies.

---

### `make test-integration`

**Run integration tests only**

```bash
make test-integration
```

**What it does:** Runs tests marked with `@pytest.mark.integration`.

**When to use:** Testing component interactions (ChromaDB, embeddings, etc.).

---

### `make coverage`

**Generate detailed coverage report**

```bash
make coverage
```

**What it does:** Runs tests with detailed coverage analysis.

**Output:**
- Terminal report with missing lines
- HTML report in `htmlcov/index.html`
- XML report in `coverage.xml`

**When to use:** Checking test coverage, identifying untested code.

**View HTML report:**
```bash
open htmlcov/index.html
```

---

## RAG Operations

### `make index`

**Index a codebase**

```bash
make index REPO=/path/to/code COLLECTION=my-collection
```

**Parameters:**
- `REPO`: Path to directory to index (required)
- `COLLECTION`: Name for the collection (required)

**Examples:**
```bash
# Index a Python project
make index REPO=~/projects/my-app COLLECTION=my-app

# Index documentation
make index REPO=~/docs/api COLLECTION=api-docs

# Index with relative path
make index REPO=../other-project COLLECTION=other
```

**What it does:**
1. Validates directory exists
2. Runs `rag-server index` command
3. Creates embeddings for all code files
4. Stores in ChromaDB collection

**Respects:** `.mcpignore` files for filtering

---

### `make search`

**Search indexed collections**

```bash
make search QUERY="your search query" COLLECTION=my-collection
```

**Parameters:**
- `QUERY`: Search query (required)
- `COLLECTION`: Collection to search (optional, defaults to "default")

**Examples:**
```bash
# Search specific collection
make search QUERY="authentication logic" COLLECTION=my-app

# Search with complex query
make search QUERY="error handling middleware" COLLECTION=backend

# Quote handling
make search QUERY="database connection pool" COLLECTION=infra
```

**Output:** Ranked search results with file paths and relevance scores.

---

### `make collections`

**List all collections**

```bash
make collections
```

**What it does:** Shows all indexed collections with metadata.

**Output:** Table with collection names, document counts, and sizes.

---

### `make stats`

**Show collection statistics**

```bash
make stats COLLECTION=my-collection
```

**Parameters:**
- `COLLECTION`: Collection name (required)

**What it does:** Displays detailed statistics for a collection.

**Output:**
- Document count
- Embedding dimensions
- Storage size
- Metadata summary

---

### `make delete-collection`

**Delete a collection**

```bash
make delete-collection COLLECTION=my-collection
```

**Parameters:**
- `COLLECTION`: Collection name (required)

**What it does:** Permanently deletes a collection (with confirmation).

**Warning:** This is irreversible! You'll be prompted to confirm.

---

### `make create-ignore`

**Create .mcpignore file**

```bash
make create-ignore REPO=/path/to/directory
```

**Parameters:**
- `REPO`: Directory path (required)

**What it does:** Creates a `.mcpignore` file with sensible defaults.

**When to use:** Before indexing a new codebase to exclude unwanted files.

---

## Code Quality

### `make lint`

**Run code linting**

```bash
make lint
```

**What it does:** Runs `ruff check` to find code quality issues.

**When to use:** Before committing, during code review.

---

### `make lint-fix`

**Auto-fix linting issues**

```bash
make lint-fix
```

**What it does:** Runs `ruff check --fix` to automatically fix issues.

**When to use:** Quick cleanup of import ordering, formatting, simple issues.

---

### `make format`

**Format code**

```bash
make format
```

**What it does:** Runs `ruff format` to format all Python files.

**When to use:** Before committing, maintaining code style consistency.

---

### `make typecheck`

**Run type checking**

```bash
make typecheck
```

**What it does:** Runs `mypy` to check type hints.

**When to use:** Ensuring type safety, catching type-related bugs.

---

### `make quality`

**Run all quality checks**

```bash
make quality
```

**What it does:** Runs linting, format checking, and type checking.

**Workflow:**
1. Lint with ruff
2. Check formatting (without modifying)
3. Type check with mypy

**When to use:** Comprehensive pre-commit validation.

---

### `make all-checks`

**Run quality checks and tests**

```bash
make all-checks
```

**What it does:** Runs `make quality` followed by `make test-fast`.

**When to use:** Full validation before pushing code.

---

## Claude Desktop Configuration

### `make config`

**Configure Claude Desktop**

```bash
make config
```

**What it does:**
1. Locates Claude Desktop config file
2. Backs up existing configuration
3. Adds/updates MCP server entry
4. Validates JSON syntax
5. Provides restart instructions

**Output:** Interactive configuration wizard.

**When to use:**
- First-time setup
- After moving project location
- Updating server configuration

---

### `make config-backup`

**Backup current configuration**

```bash
make config-backup
```

**What it does:** Creates timestamped backup of Claude Desktop config.

**Backup location:** `~/Library/Application Support/Claude/`

**Format:** `claude_desktop_config.json.backup.YYYYMMDD_HHMMSS`

---

### `make config-restore`

**Restore a backup**

```bash
make config-restore
```

**What it does:** Lists available backups with instructions.

**Note:** Restoration is manual for safety.

---

### `make config-show`

**Show current configuration**

```bash
make config-show
```

**What it does:** Pretty-prints current Claude Desktop config.

**When to use:** Verifying configuration, debugging connection issues.

---

## Utilities

### `make clean`

**Clean temporary files**

```bash
make clean
```

**What it does:** Removes:
- `.pytest_cache`
- `.mypy_cache`
- `.ruff_cache`
- `htmlcov/`
- `.coverage` files
- `__pycache__/` directories
- Build artifacts

**When to use:**
- Starting fresh
- Freeing disk space
- Before committing to ensure clean state

**Safe:** Does not delete source code or databases.

---

### `make clean-db`

**Clean ChromaDB data**

```bash
make clean-db
```

**What it does:** Deletes `./chroma_db/` directory.

**Warning:** This deletes ALL indexed collections permanently!

**Confirmation:** Prompts before deletion.

**When to use:**
- Starting over with indexing
- Testing from clean state
- Freeing significant disk space

---

### `make doctor`

**Run system diagnostics**

```bash
make doctor
```

**What it does:** Checks:
- Python version (≥3.10)
- uv installation
- Virtual environment
- Dependencies
- PyTorch backend (MPS/CUDA/CPU)
- ChromaDB functionality
- CLI command availability
- Test suite

**Output:**
- Colored status table
- System information
- Warnings and recommendations

**When to use:**
- Troubleshooting setup issues
- After fresh install
- Verifying hardware acceleration

---

### `make logs`

**View server logs**

```bash
make logs
```

**What it does:** Shows last 100 lines of `mcp_server.log`.

**When to use:** Debugging server issues, checking for errors.

---

### `make logs-follow`

**Follow logs in real-time**

```bash
make logs-follow
```

**What it does:** Tails the log file with live updates.

**Stop:** Press `Ctrl+C`

**When to use:** Monitoring server activity during testing.

---

### `make benchmark`

**Run performance benchmarks**

```bash
make benchmark
```

**What it does:**
1. Benchmarks embedding generation speed
2. Benchmarks search performance
3. Displays results and performance assessment

**Output:**
- Documents/second for embedding
- Searches/second
- Average latency
- Performance rating

**When to use:**
- Comparing hardware
- Verifying GPU acceleration
- Performance tuning

---

## Development Tools

### `make pre-commit-install`

**Install git pre-commit hook**

```bash
make pre-commit-install
```

**What it does:** Installs pre-commit hook that runs:
1. Code formatting
2. Linting
3. Type checking
4. Fast tests

**When to use:** Once per clone to enable automatic checks.

---

### `make pre-commit-run`

**Run pre-commit checks manually**

```bash
make pre-commit-run
```

**What it does:** Runs the same checks as the git hook without committing.

**When to use:** Testing before commit, manual validation.

---

### `make watch-test`

**Watch files and auto-run tests**

```bash
make watch-test
```

**What it does:** Watches Python files and reruns fast tests on changes.

**Requires:** `entr` (`brew install entr`)

**Stop:** Press `Ctrl+C`

**When to use:** Test-driven development, rapid feedback.

---

### `make shell`

**Start Python shell**

```bash
make shell
```

**What it does:** Opens Python REPL with project loaded.

**When to use:** Interactive debugging, testing snippets.

---

### `make docs`

**View documentation**

```bash
make docs
```

**What it does:** Lists all available documentation files.

**When to use:** Finding documentation, learning about the project.

---

## Troubleshooting

### Common Issues

#### "No rule to make target"
```bash
# Error
make: *** No rule to make target 'xyz'.

# Solution
Run 'make help' to see available commands
```

#### "REPO parameter required"
```bash
# Error
Error: REPO parameter required

# Solution
make index REPO=/path/to/code COLLECTION=name
```

#### "Collection not found"
```bash
# Error
Collection 'xyz' not found

# Solution
make collections  # List available collections
```

#### Tests fail
```bash
# Run diagnostics first
make doctor

# Check specific test
make test-fast -v

# Clean and retry
make clean
make test
```

#### MPS not available
```bash
# Check status
make doctor

# Should show "PyTorch Backend: MPS (Apple Silicon GPU)"
# If not, check macOS version and PyTorch installation
```

---

## Parameter Reference

### Environment Variables

You can set these in your shell or pass them to make:

```bash
# Database path (default: ./chroma_db)
make collections DB_PATH=~/my-db

# Collection name (for operations)
make stats COLLECTION=my-collection

# Repository path (for indexing)
make index REPO=~/code COLLECTION=name

# Search query
make search QUERY="search term" COLLECTION=name
```

---

## Tips & Best Practices

### Development Workflow

**Before starting work:**
```bash
make doctor      # Verify setup
make test-fast   # Ensure starting state is good
```

**During development:**
```bash
make watch-test  # Continuous testing
```

**Before committing:**
```bash
make quality     # Code quality
make test-fast   # Quick validation
```

**Before pushing:**
```bash
make all-checks  # Comprehensive validation
```

### Indexing Best Practices

**1. Use .mcpignore**
```bash
make create-ignore REPO=/path/to/project
# Edit .mcpignore to exclude unwanted files
make index REPO=/path/to/project COLLECTION=name
```

**2. Organize collections by project/purpose**
```bash
make index REPO=~/backend COLLECTION=backend-api
make index REPO=~/frontend COLLECTION=frontend-app
make index REPO=~/docs COLLECTION=documentation
```

**3. Check stats after indexing**
```bash
make stats COLLECTION=backend-api
```

### Performance Optimization

**Use fast tests during development:**
```bash
make test-fast  # Excludes slow integration tests
```

**Run full tests before pushing:**
```bash
make test  # Complete validation
```

**Monitor performance:**
```bash
make benchmark  # Check embedding/search speed
```

---

## Automation Scripts

All scripts are located in `scripts/`:

- **configure_claude.py**: Claude Desktop configuration
- **doctor.py**: System diagnostics
- **benchmark.py**: Performance benchmarking
- **pre-commit.sh**: Git pre-commit hook

You can run these directly if needed:
```bash
python scripts/doctor.py
python scripts/configure_claude.py
python scripts/benchmark.py
./scripts/pre-commit.sh
```

---

## Getting Help

**View all commands:**
```bash
make help
```

**View this documentation:**
```bash
cat docs/MAKEFILE.md
# or open in your editor
```

**Check system status:**
```bash
make doctor
```

**View logs:**
```bash
make logs
```

---

## Version Information

**Document Version:** 1.0
**Last Updated:** 2025-11-11
**Phase:** 3 - Developer Experience Automation
**Status:** Complete

---

## See Also

- [README.md](../README.md) - Project overview
- [CLAUDE.md](CLAUDE.md) - AI assistant guide
- [claude-desktop-setup.md](claude-desktop-setup.md) - Integration guide
- [usage-examples.md](usage-examples.md) - Practical examples
- [troubleshooting.md](troubleshooting.md) - Problem solving
