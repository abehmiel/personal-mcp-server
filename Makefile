# Makefile for Personal MCP Server with RAG
# Location: /Users/Abe/Projects/personal-mcp-server
# Package: rag_server
# CLI: rag-server

.PHONY: help setup install dev run test test-fast test-unit test-integration coverage \
	index search collections stats clean config config-backup config-restore \
	lint format typecheck quality docs doctor logs debug benchmark \
	pre-commit-install pre-commit-run all-checks

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Project paths
PROJECT_ROOT := $(shell pwd)
VENV_PATH := $(PROJECT_ROOT)/.venv
PYTHON := uv run python
UV := uv
CLAUDE_CONFIG := $(HOME)/Library/Application Support/Claude/claude_desktop_config.json

# Default parameters
REPO ?=
COLLECTION ?= default
QUERY ?=
DB_PATH ?= ./chroma_db

##@ Help

help: ## Display this help message
	@echo "$(BLUE)Personal MCP Server - Developer Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Usage:$(NC) make [target] [parameters]"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} \
		/^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } \
		/^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Common workflows:$(NC)"
	@echo "  make setup                           # First-time setup"
	@echo "  make test                            # Run all tests"
	@echo "  make quality                         # Check code quality"
	@echo "  make index REPO=~/code COLLECTION=my-app  # Index codebase"
	@echo "  make search QUERY=\"auth logic\" COLLECTION=my-app  # Search"
	@echo ""

##@ Setup & Installation

setup: ## Complete first-time setup (install + verify)
	@echo "$(BLUE)Starting first-time setup...$(NC)"
	@echo ""
	@$(MAKE) install
	@echo ""
	@$(MAKE) doctor
	@echo ""
	@echo "$(GREEN)Setup complete!$(NC)"
	@echo "Next steps:"
	@echo "  1. Run 'make config' to configure Claude Desktop"
	@echo "  2. Run 'make test' to verify installation"
	@echo "  3. Run 'make index REPO=/path/to/code COLLECTION=name' to index a codebase"

install: ## Install dependencies with uv sync
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@$(UV) sync
	@echo "$(GREEN)Dependencies installed successfully$(NC)"

dev: ## Install with dev dependencies
	@echo "$(BLUE)Installing with dev dependencies...$(NC)"
	@$(UV) sync --all-extras
	@echo "$(GREEN)Dev dependencies installed successfully$(NC)"

##@ Running

run: ## Start the MCP server
	@echo "$(BLUE)Starting MCP server...$(NC)"
	@echo "Press Ctrl+C to stop"
	@$(PYTHON) -m rag_server.rag_mcp_chroma

debug: ## Start server in debug mode (verbose logging)
	@echo "$(BLUE)Starting MCP server in debug mode...$(NC)"
	@echo "Press Ctrl+C to stop"
	@$(PYTHON) -m rag_server.rag_mcp_chroma --verbose

inspector: ## Start server and run it in web browser inspector mode over npx
	@echo "$(BLUE)Starting MCP server in web inspector mode...$(NC)"
	@echo "Press Ctrl+C to stop"
	npx @modelcontextprotocol/inspector @$(PYTHON) -m rag_server.rag_mcp_chroma

##@ Testing

test: ## Run all tests (fast, no coverage)
	@echo "$(BLUE)Running all tests (no coverage)...$(NC)"
	@$(PYTHON) -m pytest -v

test-fast: ## Run tests excluding slow ones
	@echo "$(BLUE)Running fast tests (excluding slow)...$(NC)"
	@$(PYTHON) -m pytest -m "not slow"

test-unit: ## Run only unit tests
	@echo "$(BLUE)Running unit tests...$(NC)"
	@$(PYTHON) -m pytest -m "unit"

test-integration: ## Run only integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	@$(PYTHON) -m pytest -m "integration"

coverage: clean-coverage increase-fd-limit ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@$(PYTHON) -m pytest --cov=rag_server --cov-report=term-missing --cov-report=html --cov-report=xml
	@echo ""
	@echo "$(GREEN)Coverage report generated:$(NC)"
	@echo "  - Terminal: see above"
	@echo "  - HTML: open htmlcov/index.html"
	@echo "  - XML: coverage.xml"

increase-fd-limit: ## Increase file descriptor limit for current shell
	@echo "$(BLUE)Checking file descriptor limit...$(NC)"
	@current=$$(ulimit -n); \
	if [ $$current -lt 4096 ]; then \
		echo "$(YELLOW)Current limit: $$current (too low)$(NC)"; \
		echo "$(BLUE)Increasing to 4096...$(NC)"; \
		ulimit -n 4096 2>/dev/null || echo "$(YELLOW)Could not increase limit (requires sudo or system config)$(NC)"; \
	else \
		echo "$(GREEN)Current limit: $$current (sufficient)$(NC)"; \
	fi

##@ RAG Operations

index: ## Index a codebase (requires REPO and COLLECTION)
	@if [ -z "$(REPO)" ]; then \
		echo "$(RED)Error: REPO parameter required$(NC)"; \
		echo "Usage: make index REPO=/path/to/code COLLECTION=my-collection"; \
		exit 1; \
	fi
	@if [ ! -d "$(REPO)" ]; then \
		echo "$(RED)Error: Directory $(REPO) does not exist$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Indexing $(REPO) into collection '$(COLLECTION)'...$(NC)"
	@$(PYTHON) -m rag_server.cli index "$(REPO)" -c "$(COLLECTION)"
	@echo "$(GREEN)Indexing complete$(NC)"

search: ## Search across collections (requires QUERY, optional COLLECTION)
	@if [ -z "$(QUERY)" ]; then \
		echo "$(RED)Error: QUERY parameter required$(NC)"; \
		echo "Usage: make search QUERY=\"your query\" COLLECTION=my-collection"; \
		exit 1; \
	fi
	@echo "$(BLUE)Searching for: '$(QUERY)'$(NC)"
	@if [ -n "$(COLLECTION)" ]; then \
		$(PYTHON) -m rag_server.cli search "$(QUERY)" -c "$(COLLECTION)"; \
	else \
		echo "$(YELLOW)Warning: No collection specified, searching default$(NC)"; \
		$(PYTHON) -m rag_server.cli search "$(QUERY)" -c default; \
	fi

collections: ## List all collections
	@echo "$(BLUE)Available collections:$(NC)"
	@$(PYTHON) -m rag_server.cli list-collections

stats: ## Show collection statistics (requires COLLECTION)
	@if [ -z "$(COLLECTION)" ]; then \
		echo "$(RED)Error: COLLECTION parameter required$(NC)"; \
		echo "Usage: make stats COLLECTION=my-collection"; \
		exit 1; \
	fi
	@echo "$(BLUE)Statistics for collection '$(COLLECTION)':$(NC)"
	@$(PYTHON) -m rag_server.cli stats -c "$(COLLECTION)"

delete-collection: ## Delete a collection (requires COLLECTION)
	@if [ -z "$(COLLECTION)" ]; then \
		echo "$(RED)Error: COLLECTION parameter required$(NC)"; \
		echo "Usage: make delete-collection COLLECTION=my-collection"; \
		exit 1; \
	fi
	@echo "$(RED)Warning: This will permanently delete collection '$(COLLECTION)'$(NC)"
	@read -p "Are you sure? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(PYTHON) -m rag_server.cli delete "$(COLLECTION)"; \
		echo "$(GREEN)Collection deleted$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

create-ignore: ## Create .mcpignore file in directory (requires REPO)
	@if [ -z "$(REPO)" ]; then \
		echo "$(RED)Error: REPO parameter required$(NC)"; \
		echo "Usage: make create-ignore REPO=/path/to/directory"; \
		exit 1; \
	fi
	@echo "$(BLUE)Creating .mcpignore in $(REPO)...$(NC)"
	@$(PYTHON) -m rag_server.cli create-ignore "$(REPO)"
	@echo "$(GREEN).mcpignore created$(NC)"

##@ Code Quality

lint: ## Run ruff linting
	@echo "$(BLUE)Running ruff linting...$(NC)"
	@$(PYTHON) -m ruff check .

lint-fix: ## Run ruff linting with auto-fix
	@echo "$(BLUE)Running ruff linting with auto-fix...$(NC)"
	@$(PYTHON) -m ruff check --fix .
	@echo "$(GREEN)Linting complete$(NC)"

format: ## Format code with ruff
	@echo "$(BLUE)Formatting code with ruff...$(NC)"
	@$(PYTHON) -m ruff format .
	@echo "$(GREEN)Code formatted successfully$(NC)"

typecheck: ## Run mypy type checking
	@echo "$(BLUE)Running mypy type checking...$(NC)"
	@$(PYTHON) -m mypy rag_server

quality: ## Run all quality checks (lint, format check, typecheck)
	@echo "$(BLUE)Running all quality checks...$(NC)"
	@echo ""
	@echo "$(BLUE)1/3 Linting...$(NC)"
	@$(MAKE) lint
	@echo ""
	@echo "$(BLUE)2/3 Format checking...$(NC)"
	@$(PYTHON) -m ruff format --check .
	@echo ""
	@echo "$(BLUE)3/3 Type checking...$(NC)"
	@$(MAKE) typecheck
	@echo ""
	@echo "$(GREEN)All quality checks passed!$(NC)"

all-checks: ## Run quality checks and tests
	@echo "$(BLUE)Running comprehensive checks...$(NC)"
	@$(MAKE) quality
	@echo ""
	@$(MAKE) test-fast
	@echo ""
	@echo "$(GREEN)All checks passed!$(NC)"

##@ Claude Desktop Configuration

config: ## Setup/verify Claude Desktop configuration
	@echo "$(BLUE)Configuring Claude Desktop...$(NC)"
	@$(PYTHON) scripts/configure_claude.py
	@echo ""
	@echo "$(YELLOW)Important:$(NC) Restart Claude Desktop for changes to take effect"

config-backup: ## Backup existing Claude Desktop config
	@echo "$(BLUE)Backing up Claude Desktop configuration...$(NC)"
	@if [ -f "$(CLAUDE_CONFIG)" ]; then \
		cp "$(CLAUDE_CONFIG)" "$(CLAUDE_CONFIG).backup.$$(date +%Y%m%d_%H%M%S)"; \
		echo "$(GREEN)Backup created$(NC)"; \
	else \
		echo "$(YELLOW)No existing config to backup$(NC)"; \
	fi

config-restore: ## Restore backed-up config (interactive)
	@echo "$(BLUE)Available backups:$(NC)"
	@ls -1t "$(HOME)/Library/Application Support/Claude/"*.backup.* 2>/dev/null || echo "No backups found"
	@echo ""
	@echo "To restore, manually copy the backup file to:"
	@echo "  $(CLAUDE_CONFIG)"

config-show: ## Show current Claude Desktop configuration
	@if [ -f "$(CLAUDE_CONFIG)" ]; then \
		echo "$(BLUE)Current configuration:$(NC)"; \
		cat "$(CLAUDE_CONFIG)" | $(PYTHON) -m json.tool; \
	else \
		echo "$(YELLOW)No configuration file found$(NC)"; \
	fi

##@ Utilities

clean: ## Clean temporary files, caches, and build artifacts (does NOT delete chroma_db)
	@echo "$(BLUE)Cleaning temporary files...$(NC)"
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf .ruff_cache
	@rm -rf htmlcov
	@rm -rf .coverage* coverage.xml
	@rm -rf dist build *.egg-info
	@rm -rf **/__pycache__
	@rm -rf **/*.pyc
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete$(NC)"

clean-coverage: ## Clean ONLY coverage files
	@echo "$(BLUE)Cleaning coverage files...$(NC)"
	@rm -rf .coverage .coverage.* htmlcov coverage.xml
	@echo "$(GREEN)Coverage files cleaned$(NC)"

clean-db: ## Clean ChromaDB data (WARNING: deletes all collections)
	@echo "$(RED)Warning: This will delete ALL indexed data$(NC)"
	@read -p "Are you sure? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf $(DB_PATH); \
		echo "$(GREEN)Database cleaned$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

doctor: ## Diagnose setup issues
	@echo "$(BLUE)Running diagnostics...$(NC)"
	@echo ""
	@$(PYTHON) scripts/doctor.py

logs: ## View server logs
	@echo "$(BLUE)Server logs:$(NC)"
	@if [ -f "mcp_server.log" ]; then \
		tail -n 100 mcp_server.log; \
	else \
		echo "$(YELLOW)No log file found. Run 'make run' to generate logs.$(NC)"; \
	fi

logs-follow: ## Follow server logs in real-time
	@echo "$(BLUE)Following server logs (Ctrl+C to stop)...$(NC)"
	@tail -f mcp_server.log 2>/dev/null || echo "$(YELLOW)No log file found$(NC)"

benchmark: ## Run performance benchmarks
	@echo "$(BLUE)Running benchmarks...$(NC)"
	@$(PYTHON) scripts/benchmark.py

##@ Git Hooks

pre-commit-install: ## Install pre-commit git hook
	@echo "$(BLUE)Installing pre-commit hook...$(NC)"
	@mkdir -p .git/hooks
	@cp scripts/pre-commit.sh .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "$(GREEN)Pre-commit hook installed$(NC)"
	@echo "Hook will run: format, lint, typecheck, and fast tests"

pre-commit-run: ## Run pre-commit checks manually
	@echo "$(BLUE)Running pre-commit checks...$(NC)"
	@./scripts/pre-commit.sh

##@ Documentation

docs: ## Generate and serve documentation
	@echo "$(BLUE)Documentation available:$(NC)"
	@echo "  - README.md: User guide"
	@echo "  - docs/CLAUDE.md: AI assistant guide"
	@echo "  - docs/claude-desktop-setup.md: Integration guide"
	@echo "  - docs/usage-examples.md: Practical examples"
	@echo "  - docs/troubleshooting.md: Problem solving"
	@echo ""
	@echo "$(YELLOW)Tip:$(NC) View in your favorite Markdown viewer or IDE"

##@ Development

watch-test: ## Watch files and run tests on change (requires entr)
	@if command -v entr >/dev/null 2>&1; then \
		echo "$(BLUE)Watching for changes (Ctrl+C to stop)...$(NC)"; \
		find rag_server tests -name "*.py" | entr -c make test-fast; \
	else \
		echo "$(RED)Error: entr not installed$(NC)"; \
		echo "Install with: brew install entr"; \
		exit 1; \
	fi

shell: ## Start Python shell with project loaded
	@echo "$(BLUE)Starting Python shell...$(NC)"
	@$(PYTHON)

# Default target
.DEFAULT_GOAL := help
