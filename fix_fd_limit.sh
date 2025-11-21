#!/bin/bash
# Fix file descriptor limit for test environment
# This script increases the file descriptor limit to prevent
# coverage.py SQLite errors when running tests

echo "=== File Descriptor Limit Fix ==="
echo ""

current_limit=$(ulimit -n)
echo "Current file descriptor limit: $current_limit"

if [ "$current_limit" -lt 4096 ]; then
    echo "Limit is too low (needs at least 4096 for pytest + coverage + ChromaDB)"
    echo ""
    echo "Attempting to increase limit to 4096..."

    if ulimit -n 4096 2>/dev/null; then
        echo "✅ Successfully increased limit to 4096 for this session"
        echo ""
        echo "To make this permanent, add this line to your ~/.zshrc:"
        echo "    ulimit -n 4096"
    else
        echo "❌ Could not increase limit"
        echo ""
        echo "To fix permanently, add this to ~/.zshrc:"
        echo "    ulimit -n 4096"
        echo ""
        echo "If that doesn't work, you may need to increase system limits:"
        echo "    sudo launchctl limit maxfiles 65536 200000"
    fi
else
    echo "✅ File descriptor limit is sufficient ($current_limit >= 4096)"
fi

echo ""
echo "=== Recommendations ==="
echo "1. Use 'make test' for fast tests without coverage (low FD usage)"
echo "2. Use 'make coverage' for coverage reports (higher FD usage, but handled)"
echo "3. The Makefile now automatically handles FD limits when running coverage"
