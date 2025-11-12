# Automation Scripts

This directory contains automation scripts used by the Makefile to enhance developer experience.

## Scripts Overview

### configure_claude.py

**Purpose:** Automates Claude Desktop configuration

**Usage:**
```bash
make config
# or
python scripts/configure_claude.py
```

**Features:**
- Locates Claude Desktop config automatically
- Creates timestamped backups
- Merges with existing configurations
- Validates JSON syntax
- Interactive confirmation prompts
- Beautiful Rich UI

**When to use:** Setting up Claude Desktop integration for the first time or updating configuration.

---

### doctor.py

**Purpose:** System diagnostics and health checks

**Usage:**
```bash
make doctor
# or
python scripts/doctor.py
```

**Checks:**
1. Python version (≥3.10)
2. uv package manager
3. Virtual environment
4. Core dependencies
5. PyTorch backend (MPS/CUDA/CPU)
6. ChromaDB functionality
7. CLI command availability
8. Test suite

**Output:**
- Status table with ✓/✗ indicators
- System information
- Warnings and recommendations

**When to use:** Troubleshooting setup issues, verifying installation, checking hardware acceleration.

---

### benchmark.py

**Purpose:** Performance benchmarking

**Usage:**
```bash
make benchmark
# or
python scripts/benchmark.py
```

**Benchmarks:**
1. Embedding generation speed
2. Search performance

**Output:**
- Documents/second for embeddings
- Searches/second
- Average latency
- Performance assessment

**When to use:** Verifying GPU acceleration, comparing hardware, performance tuning.

---

### pre-commit.sh

**Purpose:** Git pre-commit hook

**Installation:**
```bash
make pre-commit-install
```

**Manual run:**
```bash
make pre-commit-run
# or
./scripts/pre-commit.sh
```

**Checks (in order):**
1. Code formatting (ruff format)
2. Linting (ruff check)
3. Type checking (mypy)
4. Fast tests (pytest -m "not slow")

**When to use:** Automatically on git commit (if installed) or manually before committing.

---

## Script Architecture

All scripts follow these principles:

1. **Reusable:** Can be run directly or via Makefile
2. **Validated:** Return proper exit codes
3. **User-friendly:** Rich library for beautiful output
4. **Type-safe:** Full type hints for mypy checking
5. **Error handling:** Comprehensive try/catch blocks
6. **Documented:** Clear docstrings and comments

## Dependencies

Scripts use project dependencies:
- `rich` - Beautiful terminal output
- `click` - CLI framework (where applicable)
- Standard library - pathlib, subprocess, json, etc.

All dependencies are installed via `make install` or `make dev`.

## Development

### Adding a New Script

1. Create script in `scripts/` directory
2. Add shebang: `#!/usr/bin/env python3`
3. Import from project: `from rag_server import ...`
4. Use Rich for output
5. Add proper error handling
6. Make executable: `chmod +x scripts/your_script.py`
7. Add Makefile target
8. Document in this README

### Testing Scripts

```bash
# Test individually
python scripts/doctor.py
python scripts/configure_claude.py
python scripts/benchmark.py
./scripts/pre-commit.sh

# Test via Makefile
make doctor
make config
make benchmark
make pre-commit-run
```

## Troubleshooting

### Script not found
```bash
# Make sure you're in project root
cd /Users/Abe/Projects/personal-mcp-server

# Check script exists
ls -la scripts/
```

### Permission denied
```bash
# Make executable
chmod +x scripts/*.py scripts/*.sh
```

### Import errors
```bash
# Ensure dependencies installed
make install

# Check virtual environment
ls -la .venv/
```

### Rich not displaying colors
```bash
# Check terminal supports colors
echo $TERM

# Force color output
export FORCE_COLOR=1
```

## See Also

- [MAKEFILE.md](../docs/MAKEFILE.md) - Complete Makefile reference
- [CLAUDE.md](../docs/CLAUDE.md) - Architecture and development guide
- [troubleshooting.md](../docs/troubleshooting.md) - Problem solving
