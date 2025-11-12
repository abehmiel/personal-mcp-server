# Personal MCP Server with RAG

A self-hosted Model Context Protocol (MCP) server with Retrieval-Augmented Generation (RAG) capabilities, designed for Mac users who want to extend Claude's context window using their own documents.

## What is This?

This project provides a **self-hosted MCP server** that lets Claude Desktop access and search through your personal knowledge base using RAG technology. No external API keys required - everything runs locally on your Mac.

**In simple terms:** It's like giving Claude a searchable library of your documents, code, and notes that it can reference during conversations.

## Key Features

- **Self-Hosted**: Runs entirely on your Mac - no external services required
- **RAG-Powered**: Uses Retrieval-Augmented Generation for intelligent document search
- **Claude Desktop Integration**: Works seamlessly with Claude Desktop app
- **Mac Optimized**: Automatic Apple Silicon (M1/M2/M3) GPU acceleration via MPS
- **Vector Search**: ChromaDB for efficient semantic search
- **No API Keys**: All processing happens locally
- **Type Safe**: Full type hints with mypy validation
- **Well Tested**: Comprehensive test suite with 141 passing tests

## Why Use This?

Traditional AI conversations are limited by context windows. This MCP server solves that by:

1. **Indexing your documents** into a local vector database
2. **Searching semantically** - finds relevant content even without exact keyword matches
3. **Providing context** to Claude automatically during conversations
4. **Running locally** - your data never leaves your machine

Perfect for developers, researchers, writers, or anyone with a large collection of documents they want Claude to reference.

## Quick Start

Get your personal MCP server running in under 5 minutes with our automated setup!

### Prerequisites

Before you begin, make sure you have:

- **macOS** 11.0 or later (Intel or Apple Silicon)
- **Python** 3.10 or higher
- **[uv](https://github.com/astral-sh/uv)** - Modern Python package manager (v0.5.24+)
- **Claude Desktop** app installed
- **10GB+ disk space** for dependencies and vector database

### One-Command Setup

We've automated the entire setup process! Just run:

```bash
# Clone the repository
git clone https://github.com/yourusername/personal-mcp-server.git
cd personal-mcp-server

# Complete automated setup (installs dependencies + runs diagnostics)
make setup

# Configure Claude Desktop (interactive wizard)
make config

# That's it! Restart Claude Desktop (Cmd+Q, then reopen)
```

The setup command will:
- Install all dependencies
- Create virtual environment
- Run system diagnostics
- Verify everything works

The config command will:
- Auto-detect your project path
- Create proper JSON configuration
- Backup existing config
- Provide clear next steps

**See it in action:** The whole process takes less than 5 minutes!

### Manual Installation (Alternative)

If you prefer manual setup or need more control:

#### 1. Clone and Install

```bash
# Navigate to where you want to install
cd ~/Projects

# Clone the repository
git clone https://github.com/yourusername/personal-mcp-server.git
cd personal-mcp-server

# Install dependencies (this may take a few minutes)
uv sync

# Verify installation
uv run pytest
```

You should see "141 passed" indicating everything is working correctly.

#### 2. Configure Claude Desktop

You can use the automated wizard:

```bash
make config
```

Or manually create the config file:

```bash
# Open the config file in your editor
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Add this configuration (replace `/path/to/` with your actual path):

```json
{
  "mcpServers": {
    "rag-server": {
      "command": "/Users/YourUsername/.local/bin/uv",
      "args": [
        "run",
        "python",
        "-m",
        "rag_server.rag_mcp_chroma"
      ],
      "cwd": "/Users/YourUsername/Projects/personal-mcp-server",
      "env": {}
    }
  }
}
```

**Important - Replace these paths with your actual values:**

1. **Project path:** Replace `/Users/YourUsername/Projects/personal-mcp-server` with your actual project path
   - Find it by running: `pwd` in your project directory

2. **uv path:** Replace `/Users/YourUsername/.local/bin/uv` with your uv installation path
   - Find it by running: `which uv`
   - Common locations:
     - `/Users/YourUsername/.local/bin/uv` (uv installer default)
     - `/opt/homebrew/bin/uv` (Homebrew on Apple Silicon)
     - `/usr/local/bin/uv` (Homebrew on Intel)

**Why full paths?** Claude Desktop doesn't inherit your full system PATH, so you must provide absolute paths to all executables.

#### 3. Restart Claude Desktop

Completely quit and restart Claude Desktop for the changes to take effect.

### Verify It's Working

Run system diagnostics to ensure everything is properly configured:

```bash
make doctor
```

This will check:
- Python version and location
- uv installation
- Virtual environment
- Dependencies
- ChromaDB setup
- Claude Desktop configuration
- And more!

In Claude Desktop, look for the hammer icon (🔨) in the input area. Click it to see available tools. You should see:

- search_documents
- add_documents
- list_collections
- delete_collection

Congratulations! Your MCP server is now connected.

**Troubleshooting?** If anything doesn't work, `make doctor` will tell you exactly what's wrong and how to fix it.

## Basic Usage

### Adding Documents

You can add documents through Claude Desktop using natural language:

```
Can you add these documents to a collection called "my-notes":
- Document 1: "Python is a high-level programming language"
- Document 2: "Machine learning is a subset of AI"
```

Or programmatically:

```python
from rag_server.rag_mcp_chroma import RAGMCPServer

server = RAGMCPServer()
# Use server methods to add documents
```

**Preferred API for adding an entire project**

If you run the following makefile command from this directory, it will index an entire project directory
and respect that project's .gitignore, ignoring files in that pattern (useful for repos with large amounts
of on-disk data):

```bash
make index REPO=/path/to/repo COLLECTION=repo-name
```

In fact, you could create the following bash function and put it in your .profile or something similar
to have a command available to index the current project directory. Do this at the main project hierarchy level,
where you'd have the project's .gitignore, README.md, and so on, and replace the "/path/to/personal-mcp-server"
with the absolute path to this directory:

```bash
 # Personal RAG MCP server index
   indexme() {
       local repo_path="$PWD"
       local collection_name=$(basename "$PWD")
       local mcp_server_path="/path/to/personal-mcp-server"

       echo "📚 Indexing current directory..."
       echo "  Repository: $repo_path"
       echo "  Collection: $collection_name"
       echo ""

       # Navigate to the MCP server directory, run make, then return
       (cd "$mcp_server_path" && make index REPO="$repo_path" COLLECTION="$collection_name")

       local exit_code=$?
       if [ $exit_code -eq 0 ]; then
           echo ""
           echo "✅ Successfully indexed $collection_name"
       else
           echo ""
           echo "❌ Indexing failed with exit code $exit_code"
           return $exit_code
       fi
   }
```

### Searching Documents

Ask Claude to search your documents:

```
Search my "my-notes" collection for information about Python
```

Claude will use the MCP server to search and provide relevant results.

### Managing Collections

List your collections:
```
What collections do I have in my knowledge base?
```

Delete a collection:
```
Delete the "old-notes" collection
```

## Available Tools

The server provides these MCP tools:

### 1. search_documents
Search through your document collections using semantic search.

**Parameters:**
- `query` (string, required): What to search for
- `collection` (string, required): Which collection to search
- `n_results` (integer, optional): Number of results (default: 5)

### 2. add_documents
Add new documents to a collection.

**Parameters:**
- `collection` (string, required): Collection name
- `documents` (array, required): List of document texts
- `metadatas` (array, optional): List of metadata objects

### 3. list_collections
List all available collections with document counts.

**Parameters:** None

### 4. delete_collection
Delete a collection from the database.

**Parameters:**
- `collection` (string, required): Collection name to delete

## Project Structure

```
personal-mcp-server/
├── rag_server/                 # Main package
│   ├── __init__.py            # Package exports
│   ├── errors.py              # Custom exception classes
│   ├── logging_config.py      # Logging utilities
│   ├── rag_mcp_chroma.py      # MCP server implementation
│   ├── utils.py               # Device detection utilities
│   └── py.typed               # Type hint marker
├── tests/                      # Test suite
│   ├── conftest.py            # Pytest fixtures
│   ├── test_errors.py         # Error handling tests
│   ├── test_logging_config.py # Logging tests
│   └── test_utils.py          # Utility tests
├── docs/                       # Documentation
│   ├── CLAUDE.md              # AI assistant guide
│   ├── mcp-concepts.md        # MCP education
│   ├── rag-explained.md       # RAG education
│   ├── claude-desktop-setup.md # Integration guide
│   ├── usage-examples.md      # Practical examples
│   ├── troubleshooting.md     # Problem solving
│   └── development.md         # Contributor guide
├── pyproject.toml             # Project configuration
├── uv.lock                    # Dependency lock file
├── LICENSE                    # MIT License
└── README.md                  # This file
```

## Development

We've automated all common development tasks with a comprehensive Makefile. Here are the most useful commands:

### Quick Reference

```bash
# Setup and configuration
make setup              # Complete first-time setup
make config             # Configure Claude Desktop
make doctor             # Run system diagnostics

# Testing
make test               # Run all tests
make test-fast          # Quick tests (skip slow ones)
make coverage           # Generate coverage report

# Code quality
make quality            # Run all quality checks
make format             # Auto-format code
make lint               # Check code style
make typecheck          # Type checking with mypy

# Development workflow
make watch-test         # Auto-run tests on file changes
make pre-commit-install # Install git hooks
make all-checks         # All checks before commit

# Utility
make clean              # Clean temporary files
make logs               # View server logs
make benchmark          # Run performance tests
make help               # See all commands
```

### Running Tests

```bash
# Recommended: Use make commands
make test               # Run all tests (141 tests)
make test-fast          # Skip slow tests (~15 seconds)
make coverage           # Generate HTML coverage report

# Alternative: Direct pytest
uv run pytest
uv run pytest --cov=rag_server --cov-report=html
uv run pytest tests/test_utils.py
uv run pytest -v
```

### Code Quality

```bash
# Recommended: Use make commands
make quality            # Lint + type check (fast)
make format             # Auto-format with ruff
make lint               # Check code style
make typecheck          # Run mypy

# Run all checks before committing
make all-checks         # Quality + tests

# Alternative: Direct commands
uv run ruff check .
uv run ruff check --fix .
uv run ruff format .
uv run mypy rag_server
```

### Daily Development Workflow

```bash
# Morning: Verify everything works
make doctor

# During development: Auto-run tests
make watch-test

# Before committing
make quality
make test-fast

# One-time: Install pre-commit hooks
make pre-commit-install
# Now quality checks run automatically on git commit!
```

### Running the Server Standalone

```bash
# Recommended
make run                # Start server

# Alternative methods
uv run personal-mcp-server
uv run python -m rag_server.rag_mcp_chroma
make inspector          # Run queryable server over a webUI 
```

The server runs in stdio mode, communicating via standard input/output (designed for MCP protocol).

**See all commands:** Run `make help` for the complete list of 40+ developer commands.

## Documentation

Comprehensive documentation is available:

**Getting Started:**
- **[QUICK_START.md](QUICK_START.md)** - 2-minute quick start guide
- **[AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md)** - Developer experience automation overview
- **[README.md](README.md)** - This file (comprehensive overview)

**Setup and Integration:**
- **[docs/claude-desktop-setup.md](docs/claude-desktop-setup.md)** - Detailed integration guide
- **[docs/MAKEFILE.md](docs/MAKEFILE.md)** - Complete command reference (40+ commands)

**Usage and Examples:**
- **[docs/usage-examples.md](docs/usage-examples.md)** - Practical workflows and examples
- **[docs/troubleshooting.md](docs/troubleshooting.md)** - Problem solving with `make doctor`

**Development:**
- **[docs/CLAUDE.md](docs/CLAUDE.md)** - Technical architecture and development guide
- **[docs/development.md](docs/development.md)** - Contributing guidelines
- **[docs/CHANGELOG.md](docs/CHANGELOG.md)** - Project evolution and versions

**Learning Resources:**
- **[docs/mcp-concepts.md](docs/mcp-concepts.md)** - Understanding the Model Context Protocol
- **[docs/rag-explained.md](docs/rag-explained.md)** - How RAG works and why it matters

## Troubleshooting

**First step: Run diagnostics!**

```bash
make doctor
```

This comprehensive health check will diagnose most issues automatically and provide specific fixes. It checks:
- Python version and location
- uv installation
- Virtual environment setup
- Dependencies
- ChromaDB configuration
- Claude Desktop config
- MCP server imports
- System resources

### Common Issues

**Claude Desktop Doesn't Show the Tools**

```bash
# Check configuration
make doctor

# View Claude Desktop logs
make logs

# Reconfigure if needed
make config
```

**Import Errors or Module Not Found**

```bash
# Reinstall dependencies
uv sync

# Verify installation
make test
```

**Performance Issues**

```bash
# Check performance metrics
make benchmark

# View diagnostics
make doctor
```

**Something's Broken?**

```bash
# Clean and start fresh
make clean
make setup

# If still broken, emergency recovery
rm -rf .venv chroma_db
make setup
```

### More Help

See the [detailed troubleshooting guide](docs/troubleshooting.md) for comprehensive solutions. The troubleshooting doc is organized by `make doctor` diagnostic categories for easy reference.

## Mac-Specific Optimizations

This project is optimized for Mac:

- **Apple Silicon Support**: Automatic MPS (Metal Performance Shaders) GPU acceleration
- **Intel Mac Compatible**: Works on Intel-based Macs too
- **Native Wheels**: ARM64 wheels for faster installation on M-series chips
- **Device Detection**: Automatically selects the best compute device

The server will log which device it's using on startup.

## System Requirements

**Minimum:**
- macOS 11.0+
- Python 3.10+
- 4GB RAM
- 10GB disk space

**Recommended:**
- macOS 13.0+
- Python 3.11+
- 8GB+ RAM (for large document collections)
- 20GB+ disk space
- Apple Silicon Mac (M1/M2/M3) for GPU acceleration

## Contributing

Contributions are welcome! We've made it easy to contribute with automated quality checks:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes with tests
4. Run quality checks: `make all-checks`
5. Commit with clear messages (pre-commit hooks run automatically)
6. Push and create a Pull Request

**Developer Experience Features:**
- `make pre-commit-install` - Auto-run quality checks on commit
- `make watch-test` - Auto-run tests on file changes
- `make quality` - Quick linting and type checking
- `make all-checks` - Comprehensive checks before push

See [docs/development.md](docs/development.md) for detailed contribution guidelines.

## Roadmap

**Current Status: Phase 4 Complete** (All automation and documentation finalized)

### Completed Features
- ✅ Phase 1: Infrastructure (Python, testing, type safety)
- ✅ Phase 2: RAG Implementation (MCP server, ChromaDB, embeddings)
- ✅ Phase 3: Developer Experience (Makefile, automation, diagnostics)
- ✅ Phase 4: Documentation (comprehensive docs, examples, guides)

### Upcoming Features
- [ ] Advanced document chunking strategies
- [ ] Metadata filtering and search refinement
- [ ] Multi-collection search
- [ ] Document update and versioning
- [ ] CLI tool for codebase indexing
- [ ] .mcpignore support
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Docker containerization
- [ ] Performance optimizations

See [docs/CHANGELOG.md](docs/CHANGELOG.md) for detailed project history.

## Technology Stack

- **Language**: Python 3.10+
- **MCP SDK**: Official Anthropic MCP Python SDK
- **Vector Database**: ChromaDB
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Deep Learning**: PyTorch with MPS support
- **Validation**: Pydantic v2
- **Testing**: pytest with asyncio support
- **Code Quality**: ruff, mypy
- **Package Manager**: uv (Rust-based, fast)

## Security & Privacy

Your data stays on your machine:
- No external API calls for embeddings
- No data sent to cloud services
- All processing happens locally
- ChromaDB stores data in `./chroma_db/` by default

You have complete control over your data.

## Performance

Performance varies by hardware:

**Apple Silicon (M1/M2/M3):**
- First run: 2-3 minutes (model download)
- Subsequent runs: Instant startup
- Embedding speed: ~100 documents/second
- Search latency: <100ms

**Intel Mac:**
- First run: 2-3 minutes (model download)
- Subsequent runs: Instant startup
- Embedding speed: ~30 documents/second
- Search latency: <200ms

## License

MIT License - see [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Abraham Hmiel

## Acknowledgments

- Built with [MCP](https://modelcontextprotocol.io/) by Anthropic
- Uses [ChromaDB](https://www.trychroma.com/) for vector storage
- Embeddings via [Sentence Transformers](https://www.sbert.net/)
- Package management by [uv](https://github.com/astral-sh/uv)

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/personal-mcp-server/issues)
- **Documentation**: See `docs/` directory
- **MCP Resources**: [Model Context Protocol Documentation](https://modelcontextprotocol.io/)

## Learn More

New to MCP or RAG? Check out these educational guides:

- [Understanding MCP](docs/mcp-concepts.md) - What is the Model Context Protocol?
- [RAG Explained](docs/rag-explained.md) - How Retrieval-Augmented Generation works
- [Usage Examples](docs/usage-examples.md) - Practical use cases and workflows

---

**Status**: Phase 4 Complete ✅ | Production Ready 🚀

**Quick Links:**
- [Quick Start](QUICK_START.md) - Get running in 2 minutes
- [Automation Guide](AUTOMATION_GUIDE.md) - Developer experience overview
- [Command Reference](docs/MAKEFILE.md) - All 40+ make commands
- [Troubleshooting](docs/troubleshooting.md) - Solutions to common issues

Made with ❤️ for the Claude community
