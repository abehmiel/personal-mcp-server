# Claude Desktop Integration Guide

This comprehensive guide walks you through integrating your personal MCP server with Claude Desktop on macOS. By the end, Claude will be able to search and manage your document collections.

## Table of Contents

1. [Automated Setup (Recommended)](#automated-setup-recommended)
2. [Prerequisites](#prerequisites)
3. [Understanding the Configuration](#understanding-the-configuration)
4. [Manual Step-by-Step Setup](#manual-step-by-step-setup)
5. [Configuration File Explained](#configuration-file-explained)
6. [Verifying the Integration](#verifying-the-integration)
7. [Troubleshooting Connection Issues](#troubleshooting-connection-issues)
8. [Multiple MCP Servers](#multiple-mcp-servers)
9. [Advanced Configuration](#advanced-configuration)

---

## Automated Setup (Recommended)

**We've made configuration incredibly easy!** Use our interactive configuration wizard:

```bash
# From your project directory
cd /Users/Abe/Projects/personal-mcp-server

# Run the automated configuration wizard
make config
```

### What the wizard does:

1. **Auto-detects** your project path
2. **Validates** your virtual environment
3. **Creates backup** of existing config (if any)
4. **Generates** proper JSON configuration
5. **Verifies** Claude Desktop directory exists
6. **Provides** clear next steps

### Output example:

```
=== Claude Desktop Configuration Wizard ===

✅ Project root: /Users/Abe/Projects/personal-mcp-server
✅ Python path: /Users/Abe/Projects/personal-mcp-server/.venv/bin/python
✅ Virtual environment: Valid

Creating configuration...
✅ Config written to ~/Library/Application Support/Claude/claude_desktop_config.json
✅ Backup created: claude_desktop_config.json.backup

Next steps:
1. Completely quit Claude Desktop (Cmd+Q)
2. Reopen Claude Desktop
3. Look for the hammer icon (🔨) - you should see 4 tools
4. Run 'make doctor' to verify setup
```

### Verify configuration:

```bash
# Run system diagnostics
make doctor

# Check if tools appear in Claude Desktop
# Look for: search_documents, add_documents, list_collections, delete_collection
```

**That's it!** If you prefer manual configuration or want to understand what's happening, continue reading below.

---

## Prerequisites

Before starting, ensure you have:

- [ ] **Claude Desktop** installed and working
  - Download from [claude.ai/download](https://claude.ai/download)
  - Verify you can open and chat with Claude

- [ ] **MCP Server installed** and tested
  - Project location: `/Users/Abe/Projects/personal-mcp-server`
  - Tests passing: `uv run pytest` shows 141 tests passing
  - Virtual environment created: `.venv` directory exists

- [ ] **Python 3.10+** with dependencies installed
  - Check: `python3 --version`
  - Dependencies installed via `uv sync`

- [ ] **Admin/write permissions** to your user directory
  - You'll need to create/edit config files in `~/Library`

---

## Understanding the Configuration

### What We're Setting Up

```
┌─────────────────────────────────────────┐
│        Claude Desktop App               │
│  - Reads config file on startup         │
│  - Spawns MCP server process            │
│  - Communicates via stdio               │
└────────────┬────────────────────────────┘
             │
             │ Spawns process
             │
┌────────────▼────────────────────────────┐
│    MCP Server (Your Python App)         │
│  - Runs as subprocess                   │
│  - Listens on stdin for commands        │
│  - Sends responses on stdout            │
│  - Logs to stderr                       │
└─────────────────────────────────────────┘
```

### Configuration File Location

**Path:** `~/Library/Application Support/Claude/claude_desktop_config.json`

**Important Notes:**
- This directory may not exist yet (you'll create it)
- Spaces in the path must be handled carefully in terminal
- File must be valid JSON (strict syntax)
- Changes require Claude Desktop restart

---

## Manual Step-by-Step Setup

### Step 1: Locate Your Project Path

First, get the absolute path to your project:

```bash
# Navigate to your project
cd /Users/Abe/Projects/personal-mcp-server

# Get the absolute path
pwd
# Output: /Users/Abe/Projects/personal-mcp-server
```

**Copy this path** - you'll need it for the config file.

### Step 2: Verify Python Virtual Environment

Confirm your virtual environment exists and works:

```bash
# Check .venv exists
ls -la /Users/Abe/Projects/personal-mcp-server/.venv/bin/python

# Test it runs
/Users/Abe/Projects/personal-mcp-server/.venv/bin/python --version
# Should show: Python 3.10 or higher

# Test the MCP server can import
/Users/Abe/Projects/personal-mcp-server/.venv/bin/python -c "from rag_server.rag_mcp_chroma import RAGMCPServer; print('Success')"
# Should print: Success
```

If any of these fail, run `uv sync` first.

### Step 3: Create Configuration Directory

Create the Claude configuration directory if it doesn't exist:

```bash
# Create directory (mkdir -p won't error if it exists)
mkdir -p ~/Library/Application\ Support/Claude

# Verify it was created
ls -la ~/Library/Application\ Support/ | grep Claude
```

### Step 4: Create Configuration File

Create the configuration file with your editor of choice:

**Option A: Using nano (beginner-friendly)**
```bash
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Option B: Using vim**
```bash
vim ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Option C: Using VS Code**
```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Option D: Using TextEdit**
```bash
open -a TextEdit ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Step 5: Add Configuration

Paste this configuration into the file:

```json
{
  "mcpServers": {
    "rag-server": {
      "command": "/Users/Abe/.local/bin/uv",
      "args": [
        "run",
        "python",
        "-m",
        "rag_server.rag_mcp_chroma"
      ],
      "cwd": "/Users/Abe/Projects/personal-mcp-server",
      "env": {}
    }
  }
}
```

**IMPORTANT:**
- Replace `/Users/Abe/Projects/personal-mcp-server` with your actual project path if different
- Replace `/Users/Abe/.local/bin/uv` with your uv path (run `which uv` to find it)

**Save the file:**
- **nano:** Press `Ctrl+O`, then `Enter`, then `Ctrl+X`
- **vim:** Press `Esc`, then type `:wq`, then `Enter`
- **VS Code/TextEdit:** Use File → Save

### Step 6: Validate JSON Syntax

Ensure your JSON is valid:

```bash
# Using Python (available on all Macs)
python3 -c "import json; json.load(open('$HOME/Library/Application Support/Claude/claude_desktop_config.json')); print('✅ Valid JSON')"
```

If this prints "✅ Valid JSON", you're good. If it errors, check for:
- Missing commas
- Extra commas
- Unclosed quotes
- Unclosed brackets

### Step 7: Restart Claude Desktop

**Completely quit** Claude Desktop (not just close the window):

1. **Option A:** Use menu bar
   - Click "Claude" in menu bar
   - Click "Quit Claude" (or press `Cmd+Q`)

2. **Option B:** Use Dock
   - Right-click Claude in Dock
   - Click "Quit"

3. **Option C:** Use Activity Monitor
   - Open Activity Monitor
   - Search for "Claude"
   - Select and click "X" to quit

**Then restart:**
- Open Claude Desktop from Applications or Spotlight

**Wait for startup:** Give it 10-15 seconds to initialize.

---

## Configuration File Explained

Let's break down each part of the configuration:

```json
{
  "mcpServers": {                    // Top-level key (required)
    "rag-server": {                  // Server identifier (your choice)
      "command": "/Users/YourUsername/.local/bin/uv",  // Full path to uv (required!)
      "args": [                      // Command-line arguments
        "run",                       // uv run command
        "python",                    // Run python
        "-m",                        // Run as module
        "rag_server.rag_mcp_chroma"  // Module name
      ],
      "cwd": "/path/to/project",     // Working directory (important!)
      "env": {}                      // Environment variables
    }
  }
}
```

### Field Descriptions

**`mcpServers`** (required)
- Object containing all MCP server configurations
- Can have multiple servers (see [Multiple MCP Servers](#multiple-mcp-servers))

**`rag-server`** (your choice)
- Identifier for this server
- Shows up in Claude's logs
- Use descriptive names like "rag-server", "code-search", "document-db"

**`command`** (required)
- Full path to uv executable (Claude Desktop doesn't have full PATH)
- Find your uv path with `which uv` (commonly `/Users/YourUsername/.local/bin/uv`)
- Using `uv` is recommended as it manages the Python environment automatically

**`args`** (required)
- Array of command-line arguments
- `run python` tells uv to run Python in the project's environment
- `-m` tells Python to run a module
- `rag_server.rag_mcp_chroma` is the module name

**`cwd`** (required)
- Current working directory for the server
- Should point to project root
- Use absolute paths, not `~` or `./`

**`env`** (optional)
- Environment variables for the subprocess
- Empty object `{}` is fine when using `cwd`
- Can include variables like `LOG_LEVEL` if needed

### Path Requirements

**Absolute paths required:**
```json
// ✅ Good - full paths for both command and cwd
"command": "/Users/Abe/.local/bin/uv",
"cwd": "/Users/Abe/Projects/personal-mcp-server"

// ❌ Bad - bare command won't work (Claude Desktop has limited PATH)
"command": "uv"

// ❌ Bad - relative paths won't work
"cwd": "~/Projects/personal-mcp-server"
"cwd": "./personal-mcp-server"
"cwd": "."
```

**No shell expansion:**
- `~` is not expanded to home directory
- Environment variables like `$HOME` are not expanded
- Use full, explicit paths

---

## Verifying the Integration

### Automated Verification (Recommended)

Run the diagnostic tool to verify everything:

```bash
make doctor
```

This checks:
- Claude Desktop config exists and is valid JSON
- Python path is correct
- Virtual environment is working
- MCP server can be imported
- All dependencies are installed

### Visual Verification

1. **Open Claude Desktop**

2. **Look for tool indicator**
   - In the chat input area, look for a hammer/wrench icon (🔨)
   - Or a tools menu/button

3. **Click the tools button**
   - Should show a list of available tools
   - Look for these four tools:
     - `search_documents`
     - `add_documents`
     - `list_collections`
     - `delete_collection`

**If you see these tools, success!** 🎉

### Testing the Connection

Try these commands in Claude:

**Test 1: List collections**
```
What collections do I have in my knowledge base?
```

Expected: Claude uses `list_collections` tool and shows results (may be empty initially)

**Test 2: Add a document**
```
Can you add this document to a collection called "test-collection":
"This is a test document for my personal MCP server."
```

Expected: Claude uses `add_documents` tool and confirms success

**Test 3: Search**
```
Search the "test-collection" for information about MCP servers.
```

Expected: Claude uses `search_documents` and finds the document you just added

### Checking Logs

If something isn't working, check Claude Desktop logs:

**Log Location:** `~/Library/Logs/Claude/`

```bash
# View recent logs
ls -lt ~/Library/Logs/Claude/ | head -10

# View the most recent log
tail -n 50 ~/Library/Logs/Claude/mcp*.log

# Follow logs in real-time (useful for debugging)
tail -f ~/Library/Logs/Claude/mcp*.log
```

**What to look for:**
- Server startup messages
- Error messages (look for red/error keywords)
- Tool registration confirmations
- Request/response logs

---

## Troubleshooting Connection Issues

### First Step: Run Diagnostics

**Before diving into specific issues, run our diagnostic tool:**

```bash
make doctor
```

This will check 8+ critical areas and tell you exactly what's wrong. It's faster and more accurate than manual troubleshooting!

### Issue: Tools Don't Appear

**Symptom:** No hammer icon, no tools visible

**Quick Fix:**

```bash
# Run diagnostics
make doctor

# If config is invalid, reconfigure
make config

# Check logs for errors
make logs
```

**Manual Solutions:**

1. **Verify config file exists:**
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Check JSON validity:**
   ```bash
   python3 -c "import json; print(json.load(open('$HOME/Library/Application Support/Claude/claude_desktop_config.json')))"
   ```

3. **Restart Claude Desktop completely:**
   - Quit (Cmd+Q)
   - Wait 5 seconds
   - Reopen

4. **Check Python path:**
   ```bash
   /Users/Abe/Projects/personal-mcp-server/.venv/bin/python --version
   ```

### Issue: "Module not found" Error

**Symptom:** Logs show `ModuleNotFoundError: No module named 'mcp'`

**Solutions:**

1. **Verify PYTHONPATH in config:**
   ```json
   "env": {
     "PYTHONPATH": "/Users/Abe/Projects/personal-mcp-server"
   }
   ```

2. **Ensure dependencies installed:**
   ```bash
   cd /Users/Abe/Projects/personal-mcp-server
   uv sync
   ```

3. **Test import manually:**
   ```bash
   cd /Users/Abe/Projects/personal-mcp-server
   .venv/bin/python -c "from rag_server.rag_mcp_chroma import RAGMCPServer; print('OK')"
   ```

### Issue: Server Starts Then Crashes

**Symptom:** Tools appear briefly, then disappear

**Solutions:**

1. **Check for missing dependencies:**
   ```bash
   cd /Users/Abe/Projects/personal-mcp-server
   uv run python -m rag_server.rag_mcp_chroma
   # Look for error messages
   ```

2. **Verify ChromaDB directory is writable:**
   ```bash
   ls -la /Users/Abe/Projects/personal-mcp-server/chroma_db
   # Should show your user as owner
   ```

3. **Check disk space:**
   ```bash
   df -h /Users/Abe/Projects/personal-mcp-server
   ```

### Issue: "Permission Denied" Error

**Symptom:** Can't execute Python or write to directories

**Solutions:**

1. **Fix Python permissions:**
   ```bash
   chmod +x /Users/Abe/Projects/personal-mcp-server/.venv/bin/python
   ```

2. **Fix directory permissions:**
   ```bash
   chmod -R u+w /Users/Abe/Projects/personal-mcp-server
   ```

### Issue: Slow or Unresponsive

**Symptom:** Tools appear but take forever to respond

**Causes & Solutions:**

1. **First-time model download:**
   - Normal on first run
   - Model downloads ~90MB
   - Wait 2-3 minutes
   - Subsequent runs will be fast

2. **CPU vs GPU:**
   - Check logs for device: "Device configuration: mps" (good) or "cpu" (slower)
   - On Apple Silicon, MPS should be available

3. **Large collections:**
   - Many documents (>100k) can slow search
   - Consider splitting into multiple collections

### Issue: Wrong Python Version

**Symptom:** Import errors, syntax errors

**Solution:**

Ensure config points to virtual environment Python:

```bash
# Check which Python
/Users/Abe/Projects/personal-mcp-server/.venv/bin/python --version

# Should be 3.10 or higher
# Should NOT be system Python (/usr/bin/python3)
```

---

## Multiple MCP Servers

You can run multiple MCP servers simultaneously. Each provides different tools.

### Configuration Example

```json
{
  "mcpServers": {
    "rag-server": {
      "command": "/Users/Abe/.local/bin/uv",
      "args": ["run", "python", "-m", "rag_server.rag_mcp_chroma"],
      "cwd": "/Users/Abe/Projects/personal-mcp-server",
      "env": {}
    },
    "file-system": {
      "command": "/usr/local/bin/node",
      "args": ["/Users/Abe/mcp-servers/filesystem/index.js"],
      "cwd": "/Users/Abe/mcp-servers/filesystem",
      "env": {}
    },
    "database": {
      "command": "/Users/Abe/.local/bin/uv",
      "args": ["run", "python", "-m", "db_server"],
      "cwd": "/Users/Abe/mcp-servers/db-server",
      "env": {
        "DB_PATH": "/Users/Abe/data/my-database.db"
      }
    }
  }
}
```

### Key Points

- Each server has a unique identifier
- Each can use different languages (Python, Node, etc.)
- All tools from all servers are available to Claude
- Servers run independently

---

## Advanced Configuration

### Custom Environment Variables

You can pass additional environment variables:

```json
{
  "mcpServers": {
    "rag-server": {
      "command": "/Users/Abe/.local/bin/uv",
      "args": [
        "run",
        "python",
        "-m",
        "rag_server.rag_mcp_chroma"
      ],
      "cwd": "/Users/Abe/Projects/personal-mcp-server",
      "env": {
        "LOG_LEVEL": "DEBUG",
        "CHROMA_DB_PATH": "/Users/Abe/data/chroma_db",
        "EMBEDDING_MODEL": "all-MiniLM-L6-v2"
      }
    }
  }
}
```

**Note:** The current implementation doesn't read these environment variables yet. This is a pattern for future enhancements.

### Alternative Command Patterns

**Using uv (recommended):**
```json
{
  "command": "/Users/Abe/.local/bin/uv",
  "args": ["run", "python", "-m", "rag_server.rag_mcp_chroma"],
  "cwd": "/Users/Abe/Projects/personal-mcp-server"
}
```

**Note:** Find your uv path with `which uv`. Common locations:
- `/Users/YourUsername/.local/bin/uv` (uv installer default)
- `/opt/homebrew/bin/uv` (Homebrew on Apple Silicon)
- `/usr/local/bin/uv` (Homebrew on Intel)

**Using shell script wrapper:**
```json
{
  "command": "/Users/Abe/Projects/personal-mcp-server/start-server.sh",
  "args": []
}
```

Where `start-server.sh` contains:
```bash
#!/bin/bash
cd /Users/Abe/Projects/personal-mcp-server
uv run python -m rag_server.rag_mcp_chroma
```

### Debugging Configuration

For detailed logging, create a debug configuration:

```json
{
  "mcpServers": {
    "rag-server-debug": {
      "command": "/Users/Abe/.local/bin/uv",
      "args": ["run", "python", "-m", "rag_server.rag_mcp_chroma"],
      "cwd": "/Users/Abe/Projects/personal-mcp-server",
      "env": {
        "PYTHONUNBUFFERED": "1",
        "MCP_DEBUG": "1",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

---

## Configuration Checklist

Before asking for help, verify:

- [ ] Config file exists at `~/Library/Application Support/Claude/claude_desktop_config.json`
- [ ] JSON syntax is valid (test with Python)
- [ ] Python path points to virtual environment
- [ ] Python path is absolute (no `~` or relative paths)
- [ ] PYTHONPATH points to project root
- [ ] Virtual environment has dependencies installed (`uv sync`)
- [ ] Server runs standalone (`uv run personal-mcp-server`)
- [ ] Claude Desktop completely restarted (Cmd+Q, then reopen)
- [ ] Waited 10-15 seconds after restart
- [ ] Checked Claude Desktop logs for errors

---

## Getting Help

If you're still having issues:

1. **Check logs:**
   ```bash
   tail -n 100 ~/Library/Logs/Claude/mcp*.log
   ```

2. **Test server manually:**
   ```bash
   cd /Users/Abe/Projects/personal-mcp-server
   uv run personal-mcp-server
   # Should run without errors (Ctrl+C to stop)
   ```

3. **Verify all dependencies:**
   ```bash
   cd /Users/Abe/Projects/personal-mcp-server
   uv run pytest
   # All 141 tests should pass
   ```

4. **Consult documentation:**
   - [Troubleshooting Guide](troubleshooting.md)
   - [MCP Concepts](mcp-concepts.md)
   - [Project README](../README.md)

5. **Report issue:**
   - Include config file (redact personal info)
   - Include relevant log excerpts
   - Describe what you've tried
   - Note your macOS and Python versions

---

## Quick Reference

### Config File Location
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Minimal Configuration
```json
{
  "mcpServers": {
    "rag-server": {
      "command": "/Users/Abe/.local/bin/uv",
      "args": [
        "run",
        "python",
        "-m",
        "rag_server.rag_mcp_chroma"
      ],
      "cwd": "/Users/Abe/Projects/personal-mcp-server",
      "env": {}
    }
  }
}
```

**Important:** Replace paths with your actual values:
- `/Users/Abe/.local/bin/uv` → Your uv path (find with `which uv`)
- `/Users/Abe/Projects/personal-mcp-server` → Your project path

### Test Commands
```bash
# Validate JSON
python3 -c "import json; json.load(open('$HOME/Library/Application Support/Claude/claude_desktop_config.json')); print('Valid')"

# Test uv and Python
cd /Users/Abe/Projects/personal-mcp-server && uv run python --version

# Test imports
cd /Users/Abe/Projects/personal-mcp-server && uv run python -c "from rag_server.rag_mcp_chroma import RAGMCPServer"

# Run server standalone
cd /Users/Abe/Projects/personal-mcp-server && uv run personal-mcp-server
```

---

**Success Criteria:** You should now see four tools in Claude Desktop (search_documents, add_documents, list_collections, delete_collection) and be able to interact with your document collections through natural language.

**Document Version:** 1.0
**Last Updated:** 2025-11-11
