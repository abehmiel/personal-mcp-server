#!/bin/bash
#
# Pre-commit hook for personal-mcp-server
# Runs code quality checks and fast tests before allowing commit
#
# Install: make pre-commit-install
# Run manually: ./scripts/pre-commit.sh or make pre-commit-run

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Running pre-commit checks...${NC}\n"

# Function to print status
check_step() {
    local step=$1
    echo -e "${BLUE}[$step]${NC}"
}

# Function to print success
success() {
    echo -e "${GREEN}✓ $1${NC}\n"
}

# Function to print error
error() {
    echo -e "${RED}✗ $1${NC}\n"
}

# Change to project root
cd "$(dirname "$0")/.."

# 1. Format code
check_step "1/4 Formatting code"
if uv run ruff format .; then
    success "Code formatted"
else
    error "Format failed"
    exit 1
fi

# 2. Lint code
check_step "2/4 Linting code"
if uv run ruff check .; then
    success "Linting passed"
else
    error "Linting failed"
    echo -e "${YELLOW}Tip: Run 'make lint-fix' to auto-fix issues${NC}\n"
    exit 1
fi

# 3. Type check
check_step "3/4 Type checking"
if uv run mypy rag_server; then
    success "Type checking passed"
else
    error "Type checking failed"
    exit 1
fi

# 4. Run fast tests
check_step "4/4 Running fast tests"
if uv run pytest -m "not slow" -q; then
    success "Fast tests passed"
else
    error "Tests failed"
    exit 1
fi

echo -e "${GREEN}All pre-commit checks passed!${NC}"
echo -e "${YELLOW}Proceeding with commit...${NC}\n"
exit 0
