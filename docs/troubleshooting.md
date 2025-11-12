# Troubleshooting Guide

This comprehensive guide helps you diagnose and fix common issues with your personal MCP server. Issues are organized by category with clear solutions.

## Table of Contents

1. [Automated Diagnostics (START HERE)](#automated-diagnostics-start-here)
2. [Quick Diagnostic Checklist](#quick-diagnostic-checklist)
3. [Installation Issues](#installation-issues)
4. [Claude Desktop Integration](#claude-desktop-integration)
5. [MCP Server Errors](#mcp-server-errors)
6. [Mac-Specific Issues](#mac-specific-issues)
7. [Performance Issues](#performance-issues)
8. [ChromaDB Issues](#chromadb-issues)
9. [Python and Dependency Issues](#python-and-dependency-issues)
10. [Makefile Issues](#makefile-issues)
11. [Common Error Messages](#common-error-messages)
12. [Emergency Recovery](#emergency-recovery)
13. [Getting Help](#getting-help)

---

## Automated Diagnostics (START HERE)

**Before anything else, run our comprehensive diagnostic tool:**

```bash
make doctor
```

### What it checks:

1. **System Information**
   - macOS version and platform
   - Python version and location
   - uv installation and version

2. **Project Structure**
   - Virtual environment exists and is valid
   - All required dependencies installed
   - Package can be imported

3. **Configuration**
   - Claude Desktop config exists
   - JSON is valid
   - Paths are correct
   - Python interpreter is accessible

4. **ChromaDB**
   - Database directory exists
   - Directory is writable
   - No corruption detected

5. **Performance**
   - Device detection (MPS/CPU)
   - Memory availability
   - Disk space

6. **Server Health**
   - MCP server can start
   - Tools can be registered
   - No import errors

7. **Tests**
   - Test suite runs
   - All tests pass

8. **Git Status**
   - Clean working directory
   - No uncommitted changes

### Sample Output:

```
=== Personal MCP Server - System Diagnostics ===

✅ macOS: 14.6.0 (Darwin)
✅ Python: 3.12.8 (/Users/Abe/Projects/personal-mcp-server/.venv/bin/python)
✅ uv: 0.5.24
✅ Virtual environment: Valid
✅ Dependencies: All installed
✅ Claude config: Valid
✅ ChromaDB: Healthy
✅ Device: MPS (Apple Silicon GPU)
✅ Memory: 16GB available
✅ Disk space: 50GB free
✅ Tests: 91 passed

All checks passed! Your system is healthy.
```

### If Issues Are Found:

The doctor will tell you exactly what's wrong and how to fix it:

```
❌ Claude config: File not found

Fix: Run 'make config' to create the configuration file.
```

**This diagnostic tool solves 90% of issues immediately.** Only continue to specific sections below if `make doctor` doesn't resolve your problem.

---

## Quick Diagnostic Checklist

If you can't use `make doctor`, run through this manual checklist:

```bash
# Automated diagnostics (recommended)
make doctor

# Manual checks (if make is unavailable):

# 1. Check Python version
python3 --version
# Should be 3.10 or higher

# 2. Verify project location
cd /Users/Abe/Projects/personal-mcp-server
pwd
# Should output the project path

# 3. Check virtual environment
ls -la .venv/bin/python
# Should exist

# 4. Test dependencies
uv sync
# Should complete without errors

# 5. Run tests
make test
# Or: uv run pytest
# Should show 141 tests passing

# 6. Test server import
uv run python -c "from rag_server.rag_mcp_chroma import RAGMCPServer; print('OK')"
# Should print: OK

# 7. Check Claude config
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
# Should show valid JSON
```

**If all checks pass but issues persist, continue to specific sections below.**

---

## Installation Issues

### Issue: `uv: command not found`

**Problem:** The `uv` package manager isn't installed.

**Solution:**

```bash
# Install uv using official installer
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using Homebrew
brew install uv

# Verify installation
uv --version
```

### Issue: `uv sync` Fails with Network Error

**Problem:** Can't download packages due to network issues.

**Solutions:**

1. **Check internet connection:**
   ```bash
   ping -c 3 pypi.org
   ```

2. **Try with a different network:**
   - Switch from WiFi to ethernet or vice versa
   - Try a different WiFi network
   - Use a VPN if on restricted network

3. **Check firewall settings:**
   - macOS Firewall might be blocking
   - Corporate firewalls may restrict PyPI access

4. **Use mirror (if available):**
   ```bash
   uv sync --index-url https://pypi.python.org/simple
   ```

### Issue: Dependencies Install But Tests Fail

**Problem:** Dependencies installed but pytest shows failures.

**Diagnosis:**

```bash
# Run tests with verbose output
uv run pytest -v

# Check specific test file
uv run pytest tests/test_utils.py -v
```

**Common causes:**
- Incompatible Python version
- Platform-specific issues
- Missing system dependencies

**Solution:**

```bash
# Reinstall dependencies
rm -rf .venv
uv sync

# Run tests again
uv run pytest
```

### Issue: Disk Space Error During Installation

**Problem:** "No space left on device" error.

**Solution:**

```bash
# Check available disk space
df -h

# Clean up if needed
# 1. Delete old Python packages
rm -rf ~/Library/Caches/pip
rm -rf ~/.cache/uv

# 2. Clean project artifacts
cd /Users/Abe/Projects/personal-mcp-server
rm -rf htmlcov .coverage .pytest_cache .mypy_cache .ruff_cache

# 3. Check PyTorch cache (large)
du -sh ~/Library/Caches/torch
# Can delete if needed: rm -rf ~/Library/Caches/torch
```

---

## Claude Desktop Integration

### Issue: Tools Don't Appear in Claude Desktop

**Problem:** No hammer icon, no tools visible in Claude Desktop.

**Diagnostic steps:**

1. **Verify config file exists:**
   ```bash
   ls -la ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Check config contents:**
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

3. **Validate JSON syntax:**
   ```bash
   python3 -c "import json; json.load(open('$HOME/Library/Application Support/Claude/claude_desktop_config.json')); print('✅ Valid JSON')"
   ```

**Solutions:**

**If config doesn't exist:**
```bash
# Create directory
mkdir -p ~/Library/Application\ Support/Claude

# Create config file
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
# Paste configuration from claude-desktop-setup.md
```

**If JSON is invalid:**
```bash
# Common issues:
# - Missing commas between items
# - Extra comma after last item
# - Unclosed quotes or brackets
# - Using single quotes instead of double quotes

# Fix and validate again
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**If config is valid but tools don't appear:**
```bash
# 1. Completely quit Claude Desktop
# Press Cmd+Q (not just close window)

# 2. Wait 5 seconds

# 3. Reopen Claude Desktop

# 4. Wait 10-15 seconds for initialization
```

### Issue: Tools Appear Then Disappear

**Problem:** Tools show briefly then vanish.

**Cause:** Server is crashing after startup.

**Diagnosis:**

```bash
# Check Claude Desktop logs
tail -f ~/Library/Logs/Claude/mcp*.log
```

**Look for:**
- Python errors
- Import failures
- Permission denied
- File not found

**Solutions based on error:**

**ModuleNotFoundError:**
```bash
cd /Users/Abe/Projects/personal-mcp-server
uv sync
```

**Permission denied:**
```bash
chmod +x /Users/Abe/Projects/personal-mcp-server/.venv/bin/python
chmod -R u+w /Users/Abe/Projects/personal-mcp-server
```

**ChromaDB error:**
```bash
# Ensure directory is writable
mkdir -p /Users/Abe/Projects/personal-mcp-server/chroma_db
chmod u+w /Users/Abe/Projects/personal-mcp-server/chroma_db
```

### Issue: Wrong Tools Appear

**Problem:** Seeing tools from a different MCP server.

**Solution:**

```bash
# Check config for multiple servers
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Verify the "personal-rag" section is correct
# Make sure command points to YOUR project, not another
```

### Issue: Tools Work But Are Slow

**Problem:** Tools respond but take a long time.

**See:** [Performance Issues](#performance-issues) section below.

---

## MCP Server Errors

### Issue: Server Won't Start

**Problem:** Running `uv run personal-mcp-server` produces errors.

**Diagnosis:**

```bash
# Run with detailed output
cd /Users/Abe/Projects/personal-mcp-server
uv run python -m rag_server.rag_mcp_chroma
# Read the error messages
```

**Common errors and solutions:**

**"No module named 'rag_server'":**
```bash
# Ensure the package is installed
cd /Users/Abe/Projects/personal-mcp-server
uv sync

# Test import works:
cd /Users/Abe/Projects/personal-mcp-server
PYTHONPATH=/Users/Abe/Projects/personal-mcp-server uv run python -c "from rag_server.rag_mcp_chroma import RAGMCPServer"
```

**"chromadb.errors" or ChromaDB failure:**
```bash
# Reinstall ChromaDB
uv sync --reinstall-package chromadb

# Delete and recreate ChromaDB directory
rm -rf chroma_db
mkdir chroma_db
```

**"torch" errors:**
```bash
# Reinstall PyTorch
uv sync --reinstall-package torch

# Check MPS availability (Apple Silicon)
python3 -c "import torch; print(f'MPS available: {torch.backends.mps.is_available()}')"
```

### Issue: Tool Calls Return Errors

**Problem:** Tools execute but return error messages.

**Diagnosis:**

Look at the error message Claude shows. Common patterns:

**"Collection not found":**
```
# Normal on first use
# Create collection by adding documents first
```

**"No documents provided":**
```
# Trying to add empty list
# Ensure you're providing actual documents
```

**"Number of metadatas must match number of documents":**
```
# Metadata array length doesn't match documents
# Either omit metadata or provide matching count
```

### Issue: Search Returns No Results

**Problem:** Searching returns "No results found" even though documents exist.

**Causes:**

1. **Wrong collection name:**
   ```
   # Check what collections you have
   Ask Claude: "List my collections"
   ```

2. **Query too specific:**
   ```
   # Try broader query
   Instead of: "Python async/await with asyncio and event loops"
   Try: "Python async programming"
   ```

3. **Documents not actually indexed:**
   ```
   # Verify document count
   Ask Claude: "List my collections"
   # Should show document count
   ```

**Solutions:**

```bash
# Test query directly (advanced)
cd /Users/Abe/Projects/personal-mcp-server
python3 -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collections = client.list_collections()
for c in collections:
    print(f'{c.name}: {c.count()} documents')
"
```

---

## Mac-Specific Issues

### Issue: MPS Not Available on Apple Silicon

**Problem:** Logs show "Device: cpu" instead of "Device: mps" on M1/M2/M3 Mac.

**Diagnosis:**

```bash
python3 -c "import torch; print(f'MPS available: {torch.backends.mps.is_available()}'); print(f'MPS built: {torch.backends.mps.is_built()}')"
```

**Solutions:**

**If MPS is not built:**
```bash
# PyTorch wasn't built with MPS support
# Reinstall PyTorch
pip uninstall torch
pip install torch --pre --extra-index-url https://download.pytorch.org/whl/nightly/cpu
```

**If MPS is built but not available:**
- Ensure macOS 12.3 or later (MPS requires this)
- Restart your Mac
- Check for macOS updates

**If still not working:**
```bash
# CPU fallback is automatic and still works fine
# Performance impact is moderate for this use case
```

### Issue: "Bad CPU Type in Executable"

**Problem:** Error about wrong CPU architecture.

**Cause:** Running x86_64 binary on Apple Silicon or vice versa.

**Solution:**

```bash
# Check your architecture
uname -m
# arm64 = Apple Silicon
# x86_64 = Intel

# Reinstall dependencies for correct architecture
rm -rf .venv
uv sync

# Verify Python architecture matches
file .venv/bin/python
# Should show "arm64" on M1/M2/M3
# Should show "x86_64" on Intel
```

### Issue: Rosetta 2 Compatibility

**Problem:** Running into Rosetta 2 translation issues.

**Solution:**

```bash
# Install native Python if on Apple Silicon
# Don't use Python installed through Rosetta

# Check if Python is native
file $(which python3)
# Should show "arm64" not "x86_64"

# If x86_64, install native Python:
# 1. Download from python.org
# 2. Or use Homebrew: brew install python@3.11
```

### Issue: macOS Gatekeeper Blocking

**Problem:** macOS prevents running Python scripts from the internet.

**Solution:**

```bash
# Remove quarantine attribute
xattr -d com.apple.quarantine /Users/Abe/Projects/personal-mcp-server/.venv/bin/python

# Or for entire directory
xattr -dr com.apple.quarantine /Users/Abe/Projects/personal-mcp-server
```

---

## Performance Issues

### Issue: First Run Very Slow

**Problem:** Initial startup takes 2-3 minutes.

**Explanation:** This is **normal**. First run downloads:
- Sentence transformer model (~90MB)
- Model tokenizer and config
- Other model artifacts

**Where models are stored:**
```bash
# Models cache location
ls -lh ~/.cache/torch/sentence_transformers/

# Disk usage
du -sh ~/.cache/torch/sentence_transformers/
```

**Subsequent runs should be fast (<5 seconds).**

### Issue: Slow Embedding Generation

**Problem:** Adding documents takes a long time.

**Benchmarks:**
- Apple Silicon (M1/M2/M3): ~100 docs/second
- Intel Mac: ~30 docs/second

**If slower than expected:**

1. **Check device being used:**
   ```bash
   # Look in logs when server starts
   # Should see: "Device configuration: mps" (Apple Silicon)
   # Or: "Device configuration: cpu" (Intel or fallback)
   ```

2. **Close other applications:**
   - Free up RAM
   - Reduce CPU competition

3. **Monitor Activity Monitor:**
   - Python should use significant CPU during embedding
   - If not, something's wrong

4. **Batch operations:**
   - Add documents in batches (100-1000 at a time)
   - More efficient than one at a time

### Issue: Slow Search

**Problem:** Searches take several seconds.

**Expected latency:**
- Small collection (<1000 docs): <100ms
- Medium collection (1000-10k docs): <500ms
- Large collection (>10k docs): <2s

**If significantly slower:**

1. **Check collection size:**
   ```
   Ask Claude: "List my collections"
   # Shows document counts
   ```

2. **Consider splitting large collections:**
   - Separate by topic
   - Archive old documents
   - Create time-based collections

3. **Check disk I/O:**
   ```bash
   # Run during search
   iostat 1
   # High disk activity may indicate slow disk
   ```

4. **Ensure ChromaDB directory is on fast storage:**
   - Should be on internal SSD, not external drive
   - Not on network share

### Issue: Memory Issues

**Problem:** Python process uses too much memory.

**Expected memory usage:**
- Base: ~500MB
- With model: ~900MB
- With large collections: +100-500MB

**If using >2GB:**

1. **Check for memory leaks:**
   ```bash
   # Monitor over time
   while true; do
     ps aux | grep python | grep mcp
     sleep 10
   done
   ```

2. **Restart Claude Desktop:**
   - Restarts the MCP server process
   - Clears any accumulated memory

3. **Split large collections:**
   - Reduces memory footprint
   - Improves performance

---

## ChromaDB Issues

### Issue: ChromaDB Database Corruption

**Problem:** "Database is corrupted" or "Cannot open database" errors.

**Solution:**

```bash
# Backup existing database (if has important data)
cp -r /Users/Abe/Projects/personal-mcp-server/chroma_db /Users/Abe/Projects/personal-mcp-server/chroma_db.backup

# Delete corrupted database
rm -rf /Users/Abe/Projects/personal-mcp-server/chroma_db

# Restart server (will create fresh database)
# Re-index your documents
```

### Issue: ChromaDB Version Mismatch

**Problem:** "ChromaDB version incompatible" error.

**Solution:**

```bash
# Update ChromaDB
uv sync --upgrade-package chromadb

# May need to recreate database
rm -rf chroma_db
```

### Issue: Collections Disappear

**Problem:** Collections were there, now they're gone.

**Possible causes:**

1. **Wrong ChromaDB path:**
   - Server might be using different directory
   - Check logs for ChromaDB path

2. **Directory deleted accidentally:**
   - Check if `chroma_db/` exists
   - Check if you have backups

3. **Permissions changed:**
   ```bash
   # Fix permissions
   chmod -R u+rw /Users/Abe/Projects/personal-mcp-server/chroma_db
   ```

**Prevention:**
```bash
# Backup ChromaDB regularly
cp -r chroma_db chroma_db.backup.$(date +%Y%m%d)

# Or use Time Machine to backup project directory
```

---

## Python and Dependency Issues

### Issue: Python Version Conflict

**Problem:** Wrong Python version being used.

**Check version:**
```bash
/Users/Abe/Projects/personal-mcp-server/.venv/bin/python --version
```

**Should be 3.10 or higher.**

**If wrong version:**
```bash
# Recreate virtual environment with correct Python
rm -rf .venv
python3.11 -m venv .venv  # or python3.12, python3.13
uv sync
```

### Issue: Import Errors

**Problem:** "ModuleNotFoundError" or "ImportError".

**Diagnosis:**

```bash
# Test import
cd /Users/Abe/Projects/personal-mcp-server
.venv/bin/python -c "from rag_server.rag_mcp_chroma import RAGMCPServer"

# Check installed packages
.venv/bin/pip list | grep -E "(mcp|chromadb|torch|sentence-transformers)"
```

**Solutions:**

```bash
# Reinstall dependencies
uv sync

# If still failing, reinstall specific package
uv sync --reinstall-package package-name

# Nuclear option: fresh install
rm -rf .venv
rm uv.lock
uv sync
```

### Issue: Dependency Conflicts

**Problem:** "Dependency conflict" or "incompatible versions" error.

**Solution:**

```bash
# Update uv itself
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clear lock file and re-resolve
rm uv.lock
uv sync

# Check for conflicting system packages
pip list | grep -E "(mcp|chromadb|torch)"
# Should be empty or show different versions
```

---

## Makefile Issues

### Issue: `make: command not found`

**Problem:** macOS doesn't have make installed.

**Solution:**

```bash
# Install Xcode Command Line Tools (includes make)
xcode-select --install

# Verify installation
make --version
```

### Issue: Makefile Commands Don't Work

**Problem:** Running `make` commands produces errors.

**Diagnosis:**

```bash
# Check if Makefile exists
ls -la Makefile

# Try running with verbose output
make help
```

**Solutions:**

```bash
# Ensure you're in project root
cd /Users/Abe/Projects/personal-mcp-server
pwd  # Should show project path

# If Makefile is missing, you may need to pull latest code
git pull origin main

# Try a simple command
make help
```

### Issue: Make Commands Are Slow

**Problem:** Make commands take longer than expected.

**Causes:**

1. **First-time model download** - Normal on first run
2. **Many files to process** - Large codebases take time
3. **System resources** - High CPU/memory usage

**Solutions:**

```bash
# Use faster test variant
make test-fast  # Instead of make test

# Check system resources
top -l 1 | head -n 10

# Close other applications to free resources
```

### Issue: Permission Denied When Running Make Commands

**Problem:** `make config` or other commands fail with permission errors.

**Solution:**

```bash
# Fix project permissions
chmod -R u+w /Users/Abe/Projects/personal-mcp-server

# Fix virtual environment permissions
chmod +x .venv/bin/python
```

---

## Common Error Messages

### "Address already in use"

**Cause:** Trying to run server on port that's occupied.

**Note:** This MCP server uses stdio, not network ports, so this error is unusual.

**If you see it:**
- You might be running a different MCP implementation
- Check for other Python processes

### "Permission denied"

**Causes:**
1. Can't execute Python binary
2. Can't write to ChromaDB directory
3. Can't write to logs directory

**Solution:**
```bash
chmod +x /Users/Abe/Projects/personal-mcp-server/.venv/bin/python
chmod -R u+w /Users/Abe/Projects/personal-mcp-server
```

### "No such file or directory"

**Causes:**
1. Config points to wrong path
2. Virtual environment doesn't exist
3. Project moved/renamed

**Solution:**
```bash
# Verify paths in config
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Ensure paths are absolute and correct
# Recreate venv if missing
uv sync
```

### "Illegal instruction"

**Cause:** Binary compiled for different CPU architecture.

**Solution:**
```bash
# Reinstall for correct architecture
rm -rf .venv
uv sync
```

### "Segmentation fault"

**Cause:** Serious error in native code (PyTorch, ChromaDB).

**Solutions:**

1. **Update to latest versions:**
   ```bash
   uv sync --upgrade
   ```

2. **Reinstall PyTorch:**
   ```bash
   uv sync --reinstall-package torch
   ```

3. **Check for macOS updates:**
   - Some segfaults fixed in newer macOS versions

4. **Report issue:**
   - Include full error traceback
   - Note your macOS and hardware

---

## Getting Help

### Information to Gather

When asking for help, include:

1. **Environment info:**
   ```bash
   # macOS version
   sw_vers

   # Python version
   python3 --version

   # uv version
   uv --version

   # Hardware
   uname -m  # Architecture
   sysctl hw.model  # Mac model
   ```

2. **Error messages:**
   ```bash
   # Claude Desktop logs
   tail -n 100 ~/Library/Logs/Claude/mcp*.log > error.log

   # Server output
   cd /Users/Abe/Projects/personal-mcp-server
   uv run personal-mcp-server 2>&1 | tee server.log
   ```

3. **Configuration:**
   ```bash
   # Config file (remove personal info)
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

4. **Steps to reproduce:**
   - What were you doing when error occurred?
   - Can you reproduce it consistently?
   - What have you tried already?

### Where to Get Help

1. **Check documentation:**
   - [README.md](../README.md)
   - [CLAUDE.md](CLAUDE.md)
   - [claude-desktop-setup.md](claude-desktop-setup.md)

2. **Search existing issues:**
   - GitHub Issues (if project is public)
   - Look for similar problems

3. **Community resources:**
   - MCP Discord
   - Anthropic community forums
   - Stack Overflow (tag: model-context-protocol)

4. **File an issue:**
   - Include information gathered above
   - Be specific and detailed
   - Include steps to reproduce

### Self-Help Debugging

**Enable verbose logging:**
```python
# In rag_mcp_chroma.py, temporarily change:
log_level = logging.DEBUG  # Instead of INFO
```

**Test components individually:**
```bash
# Test ChromaDB
python3 -c "import chromadb; print('ChromaDB OK')"

# Test embeddings
python3 -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('all-MiniLM-L6-v2'); print('Embeddings OK')"

# Test MCP SDK
python3 -c "import mcp; print('MCP SDK OK')"
```

**Check system resources:**
```bash
# Disk space
df -h

# Memory
vm_stat

# CPU
top -l 1 | head -n 10
```

---

## Prevention Tips

### Regular Maintenance

```bash
# Weekly: Update dependencies
cd /Users/Abe/Projects/personal-mcp-server
uv sync --upgrade

# Monthly: Clean caches
rm -rf ~/.cache/uv
rm -rf ~/Library/Caches/pip
# Model cache: rm -rf ~/.cache/torch (only if needed)

# Quarterly: Backup ChromaDB
cp -r chroma_db chroma_db.backup.$(date +%Y%m%d)
```

### Best Practices

1. **Keep backups of ChromaDB**
2. **Document your collections** (what's in them)
3. **Monitor disk space** (embeddings grow over time)
4. **Update regularly** (new versions, bug fixes)
5. **Test after updates** (run pytest)
6. **Keep config file backed up**

### Monitoring

```bash
# Create a health check script
cat > check_health.sh << 'EOF'
#!/bin/bash
echo "=== Personal MCP Server Health Check ==="
echo ""
echo "Python version:"
python3 --version
echo ""
echo "Dependencies:"
cd /Users/Abe/Projects/personal-mcp-server
uv run python -c "from rag_server.rag_mcp_chroma import RAGMCPServer; print('✅ Imports OK')"
echo ""
echo "ChromaDB:"
[ -d chroma_db ] && echo "✅ ChromaDB directory exists" || echo "❌ ChromaDB directory missing"
echo ""
echo "Collections:"
uv run python -c "import chromadb; client = chromadb.PersistentClient(path='./chroma_db'); print(f'✅ {len(client.list_collections())} collections')"
EOF

chmod +x check_health.sh
./check_health.sh
```

---

## Emergency Recovery

### Quick Recovery (Recommended)

Use our automated cleanup and reinstall:

```bash
# Clean temporary files and caches
make clean

# Reinstall from scratch
make setup

# Reconfigure Claude Desktop
make config

# Verify everything works
make doctor
```

### Complete Manual Reset

If everything is broken and you need to start fresh:

```bash
# 1. Backup ChromaDB if it has important data
cp -r /Users/Abe/Projects/personal-mcp-server/chroma_db ~/Desktop/chroma_db.backup

# 2. Clean project using make (preferred)
make clean

# Or manually clean everything
cd /Users/Abe/Projects/personal-mcp-server
rm -rf .venv
rm -rf chroma_db
rm -rf .mypy_cache .pytest_cache .ruff_cache htmlcov
rm uv.lock

# 3. Fresh install using make
make setup

# Or manual install
uv sync

# 4. Test
make test
# Or: uv run pytest

# 5. Reconfigure Claude Desktop
make config
# Or manually: nano ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 6. Restart Claude Desktop (Cmd+Q, then reopen)

# 7. Verify setup
make doctor

# 8. Restore data if needed
cp -r ~/Desktop/chroma_db.backup chroma_db
```

### Nuclear Option

If even the above doesn't work:

```bash
# Delete everything and re-clone
cd ~/Projects
rm -rf personal-mcp-server
git clone https://github.com/yourusername/personal-mcp-server.git
cd personal-mcp-server
make setup
make config
```

---

**Remember:** Most issues have simple solutions. Always start with `make doctor` before escalating to complex debugging or emergency recovery.

**Document Version:** 1.0
**Last Updated:** 2025-11-11
