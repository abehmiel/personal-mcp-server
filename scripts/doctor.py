#!/usr/bin/env python3
"""
System Diagnostics Script

Verifies that all components of the MCP server are properly configured.
Checks Python version, dependencies, hardware, and functionality.
"""

import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add parent directory to path so we can import rag_server
sys.path.insert(0, str(Path(__file__).parent.parent))
from rag_server.config import DEFAULT_EMBEDDING_MODEL

console = Console()


def check_mark(passed: bool) -> str:
    """Return colored checkmark or X."""
    return "[green]✓[/green]" if passed else "[red]✗[/red]"


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


class SystemDoctor:
    """System diagnostics checker."""

    def __init__(self) -> None:
        """Initialize the doctor."""
        self.checks: list[tuple[str, bool, str]] = []
        self.warnings: list[str] = []
        self.project_root = get_project_root()

    def add_check(self, name: str, passed: bool, message: str = "") -> None:
        """Add a check result."""
        self.checks.append((name, passed, message))

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def check_python_version(self) -> None:
        """Check Python version."""
        version = sys.version_info
        min_version = (3, 10)
        passed = version >= min_version

        version_str = f"{version.major}.{version.minor}.{version.micro}"
        message = f"Python {version_str}"

        if not passed:
            message += f" (requires {min_version[0]}.{min_version[1]}+)"

        self.add_check("Python Version", passed, message)

    def check_uv_installed(self) -> None:
        """Check if uv is installed."""
        try:
            result = subprocess.run(
                ["uv", "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
            passed = result.returncode == 0
            message = result.stdout.strip() if passed else "Not installed"
        except FileNotFoundError:
            passed = False
            message = "Not found in PATH"

        self.add_check("uv Package Manager", passed, message)

        if not passed:
            self.add_warning("Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")

    def check_venv_exists(self) -> None:
        """Check if virtual environment exists."""
        venv_path = self.project_root / ".venv"
        passed = venv_path.exists()
        message = str(venv_path) if passed else "Not found"

        self.add_check("Virtual Environment", passed, message)

        if not passed:
            self.add_warning("Run: make install")

    def check_dependencies(self) -> None:
        """Check critical dependencies."""
        critical_deps = [
            "chromadb",
            "sentence_transformers",
            "torch",
            "mcp",
            "rich",
            "click",
        ]

        all_passed = True
        missing = []

        for dep in critical_deps:
            try:
                __import__(dep)
            except ImportError:
                all_passed = False
                missing.append(dep)

        if all_passed:
            message = f"{len(critical_deps)} packages installed"
        else:
            message = f"Missing: {', '.join(missing)}"

        self.add_check("Core Dependencies", all_passed, message)

        if not all_passed:
            self.add_warning("Run: make install")

    def check_torch_backend(self) -> None:
        """Check PyTorch backend availability."""
        try:
            import torch

            if torch.backends.mps.is_available():
                backend = "MPS (Apple Silicon GPU)"
                passed = True
            elif torch.cuda.is_available():
                backend = "CUDA (NVIDIA GPU)"
                passed = True
            else:
                backend = "CPU only"
                passed = True
                self.add_warning("Using CPU backend. Performance will be slower than MPS/CUDA.")

            self.add_check("PyTorch Backend", passed, backend)
        except ImportError:
            self.add_check("PyTorch Backend", False, "PyTorch not installed")

    def check_chromadb(self) -> None:
        """Check ChromaDB initialization."""
        try:
            import chromadb

            # Try to create ephemeral client
            client = chromadb.Client()
            passed = True
            message = f"ChromaDB {chromadb.__version__}"
        except Exception as e:
            passed = False
            message = f"Error: {str(e)[:50]}"

        self.add_check("ChromaDB", passed, message)

    def check_embedding_model(self) -> None:
        """Check embedding model configuration."""
        try:
            # Verify sentence_transformers is available
            import sentence_transformers  # noqa: F401

            model_name = DEFAULT_EMBEDDING_MODEL
            passed = True
            message = f"Configured: {model_name}"

            self.add_check("Embedding Model", passed, message)

        except ImportError:
            self.add_check("Embedding Model", False, "sentence_transformers not installed")

    def check_cli_command(self) -> None:
        """Check if CLI command is available."""
        try:
            result = subprocess.run(
                ["uv", "run", "rag-server", "--help"],
                capture_output=True,
                text=True,
                check=False,
                cwd=self.project_root,
            )
            passed = result.returncode == 0
            message = "rag-server command available"
        except Exception as e:
            passed = False
            message = str(e)[:50]

        self.add_check("CLI Command", passed, message)

    def check_tests(self) -> None:
        """Check if tests can run."""
        try:
            result = subprocess.run(
                ["uv", "run", "pytest", "--collect-only", "-q"],
                capture_output=True,
                text=True,
                check=False,
                cwd=self.project_root,
            )
            passed = result.returncode == 0

            if passed:
                # Count tests from output
                lines = result.stdout.strip().split("\n")
                test_count = sum(1 for line in lines if "test_" in line)
                message = f"{test_count} tests found" if test_count > 0 else "Tests collected"
            else:
                message = "Collection failed"

        except Exception as e:
            passed = False
            message = str(e)[:50]

        self.add_check("Test Suite", passed, message)

    def check_platform_info(self) -> dict[str, Any]:
        """Get platform information."""
        return {
            "Platform": platform.system(),
            "Version": platform.version(),
            "Machine": platform.machine(),
            "Processor": platform.processor() or "Unknown",
            "Python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        }

    def check_memory(self) -> str:
        """Get memory information (macOS only)."""
        if platform.system() != "Darwin":
            return "N/A"

        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
                check=True,
            )
            mem_bytes = int(result.stdout.strip())
            mem_gb = mem_bytes / (1024**3)
            return f"{mem_gb:.1f} GB"
        except Exception:
            return "Unknown"

    def run_all_checks(self) -> bool:
        """Run all diagnostic checks."""
        console.print("[bold blue]Running System Diagnostics[/bold blue]\n")

        # Run checks
        self.check_python_version()
        self.check_uv_installed()
        self.check_venv_exists()
        self.check_dependencies()
        self.check_torch_backend()
        self.check_chromadb()
        self.check_embedding_model()
        self.check_cli_command()
        self.check_tests()

        # Display results
        self.display_results()

        # Show platform info
        self.display_platform_info()

        # Show warnings
        if self.warnings:
            self.display_warnings()

        # Return overall status
        return all(passed for _, passed, _ in self.checks)

    def display_results(self) -> None:
        """Display check results in a table."""
        table = Table(title="Diagnostic Results", show_header=True)
        table.add_column("Check", style="cyan")
        table.add_column("Status", justify="center", width=8)
        table.add_column("Details", style="dim")

        for name, passed, message in self.checks:
            status = check_mark(passed)
            table.add_row(name, status, message)

        console.print(table)
        console.print()

        # Summary
        total = len(self.checks)
        passed_count = sum(1 for _, passed, _ in self.checks if passed)

        if passed_count == total:
            console.print(f"[bold green]All {total} checks passed![/bold green]\n")
        else:
            failed = total - passed_count
            console.print(
                f"[bold yellow]{passed_count}/{total} checks passed ({failed} failed)[/bold yellow]\n"
            )

    def display_platform_info(self) -> None:
        """Display platform information."""
        info = self.check_platform_info()
        info["Memory"] = self.check_memory()

        table = Table(title="System Information", show_header=False, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        for key, value in info.items():
            table.add_row(key, str(value))

        console.print(table)
        console.print()

    def display_warnings(self) -> None:
        """Display warnings and recommendations."""
        warning_text = "\n".join(f"  • {w}" for w in self.warnings)
        console.print(
            Panel(
                warning_text,
                title="[yellow]Warnings & Recommendations[/yellow]",
                border_style="yellow",
            )
        )
        console.print()


def main() -> int:
    """Run diagnostics."""
    doctor = SystemDoctor()
    all_passed = doctor.run_all_checks()

    if all_passed:
        console.print("[bold green]System is ready to use![/bold green]")
        console.print("\nNext steps:")
        console.print("  • Run 'make config' to configure Claude Desktop")
        console.print("  • Run 'make index REPO=/path/to/code COLLECTION=name' to index code")
        console.print("  • Run 'make test' to verify everything works")
        return 0
    console.print("[bold red]Some checks failed. Please address the issues above.[/bold red]")
    return 1


if __name__ == "__main__":
    sys.exit(main())
