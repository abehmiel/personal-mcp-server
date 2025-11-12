# Quick Start Guide

Get up and running with the personal MCP server in under 5 minutes.

## First-Time Setup

```bash
# 1. Install dependencies and verify system
make setup

# 2. Configure Claude Desktop
make config

# 3. Restart Claude Desktop
# Quit (Cmd+Q) and reopen

# 4. Verify installation
make test
```

That's it! You're ready to use the MCP server.

## Common Commands

### Development

```bash
make test-fast      # Run tests (fast)
make quality        # Check code quality
make format         # Format code
make doctor         # Diagnose issues
```

### RAG Operations

```bash
# Index a codebase
make index REPO=~/my-project COLLECTION=my-app

# Search
make search QUERY="auth logic" COLLECTION=my-app

# List collections
make collections

# View statistics
make stats COLLECTION=my-app
```

### Troubleshooting

```bash
make doctor         # System diagnostics
make logs           # View recent logs
make clean          # Clean temp files
```

## Quick Reference

| Task | Command |
|------|---------|
| See all commands | `make help` |
| Setup from scratch | `make setup` |
| Run all tests | `make test` |
| Run fast tests | `make test-fast` |
| Check code quality | `make quality` |
| Format code | `make format` |
| Configure Claude | `make config` |
| Diagnose issues | `make doctor` |
| Index codebase | `make index REPO=/path COLLECTION=name` |
| Search | `make search QUERY="text" COLLECTION=name` |
| List collections | `make collections` |
| Clean temp files | `make clean` |
| View logs | `make logs` |
| Run benchmarks | `make benchmark` |
| Install pre-commit | `make pre-commit-install` |

## Need Help?

```bash
# Detailed help for all commands
make help

# System diagnostics
make doctor

# View documentation
cat docs/MAKEFILE.md       # Complete reference
cat docs/CLAUDE.md         # Architecture guide
cat docs/troubleshooting.md # Problem solving
```

## Next Steps

1. **Index your first codebase:**
   ```bash
   make index REPO=~/your-project COLLECTION=project-name
   ```

2. **Try searching in Claude Desktop:**
   - Open Claude Desktop
   - Ask: "What MCP tools do you have available?"
   - Ask: "Search my code for authentication logic"

3. **Set up development workflow:**
   ```bash
   make pre-commit-install  # Auto-run checks on commit
   ```

For complete documentation, see:
- [MAKEFILE.md](docs/MAKEFILE.md) - Complete command reference
- [README.md](README.md) - Full documentation
- [claude-desktop-setup.md](docs/claude-desktop-setup.md) - Integration guide
