#!/usr/bin/env python3
"""
Claude Desktop Configuration Automation Script

Automatically configures Claude Desktop to use the personal MCP server.
Handles backup, validation, and merging of configurations.
"""

import json
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()


def get_config_path() -> Path:
    """Get the Claude Desktop configuration file path."""
    return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"


def get_project_root() -> Path:
    """Get the project root directory."""
    # This script is in scripts/, so parent is project root
    return Path(__file__).parent.parent


def load_config(config_path: Path) -> dict[str, Any]:
    """Load existing configuration or return empty dict."""
    if config_path.exists():
        try:
            with open(config_path) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            console.print(f"[red]Error: Invalid JSON in config file: {e}[/red]")
            console.print("[yellow]Creating backup and starting fresh...[/yellow]")
            backup_config(config_path)
            return {}
    return {}


def backup_config(config_path: Path) -> Path | None:
    """Create a timestamped backup of the config file."""
    if not config_path.exists():
        return None

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config_path.with_suffix(f".backup.{timestamp}.json")

    try:
        import shutil

        shutil.copy2(config_path, backup_path)
        console.print(f"[green]Backup created:[/green] {backup_path}")
        return backup_path
    except Exception as e:
        console.print(f"[red]Error creating backup: {e}[/red]")
        return None


def find_uv_path() -> str:
    """Find the full path to uv executable."""
    import shutil

    uv_path = shutil.which("uv")
    if uv_path:
        return uv_path

    # Common locations to check
    common_paths = [
        Path.home() / ".local/bin/uv",
        Path("/opt/homebrew/bin/uv"),
        Path("/usr/local/bin/uv"),
    ]

    for path in common_paths:
        if path.exists():
            return str(path)

    # Fallback - just use "uv" and hope it's in PATH
    console.print("[yellow]Warning: Could not find uv in common locations[/yellow]")
    console.print("[yellow]Using 'uv' - you may need to edit the config manually[/yellow]")
    return "uv"


def get_mcp_config() -> dict[str, Any]:
    """Generate the MCP server configuration."""
    project_root = get_project_root()
    uv_path = find_uv_path()

    return {
        "command": uv_path,
        "args": ["run", "python", "-m", "rag_server.rag_mcp_chroma"],
        "cwd": str(project_root),
        "env": {},
    }


def merge_config(existing: dict[str, Any], new_server_config: dict[str, Any]) -> dict[str, Any]:
    """Merge new MCP server config with existing configuration."""
    # Ensure mcpServers key exists
    if "mcpServers" not in existing:
        existing["mcpServers"] = {}

    # Add or update our server
    existing["mcpServers"]["rag-server"] = new_server_config

    return existing


def validate_json(config: dict[str, Any]) -> bool:
    """Validate that config is valid JSON."""
    try:
        json.dumps(config)
        return True
    except (TypeError, ValueError) as e:
        console.print(f"[red]Invalid JSON structure: {e}[/red]")
        return False


def save_config(config_path: Path, config: dict[str, Any]) -> bool:
    """Save configuration to file."""
    try:
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write with nice formatting
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
            f.write("\n")  # Add newline at end

        return True
    except Exception as e:
        console.print(f"[red]Error saving configuration: {e}[/red]")
        return False


def show_config(config: dict[str, Any]) -> None:
    """Display the configuration in a readable format."""
    config_str = json.dumps(config, indent=2)
    console.print(Panel(config_str, title="Configuration", border_style="blue"))


def show_next_steps() -> None:
    """Show user what to do next."""
    console.print("\n[bold green]Configuration complete![/bold green]\n")
    console.print("[yellow]Next steps:[/yellow]")
    console.print("  1. [bold]Restart Claude Desktop[/bold] for changes to take effect")
    console.print("     - Quit Claude Desktop completely (Cmd+Q)")
    console.print("     - Reopen Claude Desktop")
    console.print("\n  2. [bold]Verify the integration:[/bold]")
    console.print("     - Open a new chat in Claude")
    console.print('     - The MCP server should appear in the "Available Tools" section')
    console.print('     - Try asking: "What MCP tools do you have available?"')
    console.print("\n  3. [bold]Index a codebase:[/bold]")
    console.print("     - make index REPO=/path/to/code COLLECTION=my-app")
    console.print("\n  4. [bold]Search in Claude:[/bold]")
    console.print('     - Ask Claude: "Search my indexed code for authentication logic"')


def main() -> int:
    """Main configuration workflow."""
    console.print("[bold blue]Claude Desktop MCP Configuration Tool[/bold blue]\n")

    # Get paths
    config_path = get_config_path()
    project_root = get_project_root()
    uv_path = find_uv_path()

    console.print(f"[dim]Config location: {config_path}[/dim]")
    console.print(f"[dim]Project root: {project_root}[/dim]")
    console.print(f"[dim]uv path: {uv_path}[/dim]\n")

    # Load existing config
    existing_config = load_config(config_path)

    # Check if our server already exists
    if "mcpServers" in existing_config and "rag-server" in existing_config["mcpServers"]:
        console.print("[yellow]MCP server 'rag-server' already configured.[/yellow]")
        if not Confirm.ask("Do you want to update the configuration?", default=True):
            console.print("[dim]Configuration unchanged.[/dim]")
            return 0

    # Create backup if config exists
    if config_path.exists():
        backup_config(config_path)

    # Generate new server config
    new_server_config = get_mcp_config()

    # Merge configurations
    merged_config = merge_config(existing_config, new_server_config)

    # Show what will be saved
    console.print("\n[bold]New configuration:[/bold]")
    show_config(merged_config)

    # Confirm
    if not Confirm.ask("\nSave this configuration?", default=True):
        console.print("[yellow]Configuration cancelled.[/yellow]")
        return 0

    # Validate
    if not validate_json(merged_config):
        console.print("[red]Configuration validation failed![/red]")
        return 1

    # Save
    if not save_config(config_path, merged_config):
        console.print("[red]Failed to save configuration![/red]")
        return 1

    # Success!
    show_next_steps()
    return 0


if __name__ == "__main__":
    sys.exit(main())
