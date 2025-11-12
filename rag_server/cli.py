"""
Command-line interface for the RAG server.

Provides commands for indexing, searching, and managing collections.
"""

import logging
import sys
import traceback
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .chunking import ChunkingStrategy
from .context_filter import ContextFilter
from .errors import ChromaDBError, MCPServerError
from .indexer import CodebaseIndexer, IndexingConfig
from .logging_config import setup_logging

console = Console()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--db-path", default="./chroma_db", help="Path to ChromaDB storage")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, db_path: str) -> None:
    """RAG Server - Intelligent codebase indexing and search."""
    # Setup logging
    setup_logging(
        level=logging.DEBUG if verbose else logging.INFO,
        detailed=verbose,
        logger_name="rag_server",
    )

    # Store in context
    ctx.ensure_object(dict)
    ctx.obj["db_path"] = db_path
    ctx.obj["verbose"] = verbose


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option("--collection", "-c", required=True, help="Collection name")
@click.option(
    "--extensions",
    "-e",
    multiple=True,
    help="File extensions to include (e.g., .py .js)",
)
@click.option(
    "--strategy",
    "-s",
    type=click.Choice(["fixed", "code", "paragraph", "semantic"]),
    default="code",
    help="Chunking strategy",
)
@click.option("--chunk-size", default=1000, help="Chunk size in characters")
@click.option("--chunk-overlap", default=200, help="Chunk overlap in characters")
@click.option("--batch-size", default=100, help="Batch size for processing")
@click.option("--force", is_flag=True, help="Force reindex (delete existing collection)")
@click.option("--no-ignore", is_flag=True, help="Disable .mcpignore filtering")
@click.pass_context
def index(
    ctx: click.Context,
    directory: str,
    collection: str,
    extensions: tuple[str, ...],
    strategy: str,
    chunk_size: int,
    chunk_overlap: int,
    batch_size: int,
    force: bool,
    no_ignore: bool,
) -> None:
    """Index a codebase directory."""
    try:
        console.print(
            Panel.fit(
                f"[bold blue]Indexing:[/bold blue] {directory}\n"
                f"[bold]Collection:[/bold] {collection}\n"
                f"[bold]Strategy:[/bold] {strategy}",
                title="RAG Indexer",
            )
        )

        # Prepare config
        config = IndexingConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunking_strategy=ChunkingStrategy(strategy),
            batch_size=batch_size,
            show_progress=True,
        )

        # Initialize indexer
        indexer = CodebaseIndexer(
            db_path=ctx.obj["db_path"],
            config=config,
        )

        # Convert extensions tuple to list
        file_extensions = list(extensions) if extensions else None

        # Index directory
        result = indexer.index_directory(
            directory=directory,
            collection_name=collection,
            file_extensions=file_extensions,
            use_mcpignore=not no_ignore,
            force_reindex=force,
        )

        # Display results
        console.print("\n[bold green]Indexing Complete![/bold green]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Files", str(result.total_files))
        table.add_row("Files Indexed", str(result.files_indexed))
        table.add_row("Files Skipped", str(result.files_skipped))
        table.add_row("Total Chunks", str(result.total_chunks))

        console.print(table)

        if result.errors:
            console.print(f"\n[bold red]Errors ({len(result.errors)}):[/bold red]")
            for error in result.errors[:5]:  # Show first 5 errors
                console.print(f"  - {error}")
            if len(result.errors) > 5:
                console.print(f"  ... and {len(result.errors) - 5} more errors")

    except (MCPServerError, ChromaDBError) as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        if ctx.obj["verbose"]:
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.pass_context
def list_collections(ctx: click.Context) -> None:
    """List all collections."""
    try:
        indexer = CodebaseIndexer(db_path=ctx.obj["db_path"])

        collections = indexer.client.list_collections()

        if not collections:
            console.print("[yellow]No collections found.[/yellow]")
            return

        console.print(
            Panel.fit(
                f"[bold]Found {len(collections)} collection(s)[/bold]",
                title="Collections",
            )
        )

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Collection", style="cyan")
        table.add_column("Documents", style="green")
        table.add_column("Languages", style="yellow")

        for coll in collections:
            stats = indexer.get_collection_stats(coll.name)
            languages = ", ".join(stats["languages"][:3])
            if len(stats["languages"]) > 3:
                languages += f" +{len(stats['languages']) - 3}"

            table.add_row(
                coll.name,
                str(stats["total_chunks"]),
                languages or "N/A",
            )

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("collection")
@click.pass_context
def stats(ctx: click.Context, collection: str) -> None:
    """Show statistics for a collection."""
    try:
        indexer = CodebaseIndexer(db_path=ctx.obj["db_path"])
        stats_data = indexer.get_collection_stats(collection)

        console.print(
            Panel.fit(
                f"[bold blue]Collection:[/bold blue] {collection}",
                title="Collection Statistics",
            )
        )

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Chunks", str(stats_data["total_chunks"]))
        table.add_row("Languages", ", ".join(stats_data["languages"]) or "N/A")
        table.add_row("File Types", ", ".join(stats_data["file_types"]) or "N/A")

        if stats_data.get("metadata"):
            indexed_dir = stats_data["metadata"].get("indexed_directory", "N/A")
            table.add_row("Indexed Directory", indexed_dir)

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("query")
@click.option("--collection", "-c", required=True, help="Collection to search")
@click.option("--limit", "-n", default=5, help="Number of results")
@click.pass_context
def search(ctx: click.Context, query: str, collection: str, limit: int) -> None:
    """Search for code in a collection."""
    try:
        indexer = CodebaseIndexer(db_path=ctx.obj["db_path"])

        console.print(
            Panel.fit(
                f"[bold blue]Query:[/bold blue] {query}\n[bold]Collection:[/bold] {collection}",
                title="Search",
            )
        )

        # Get collection
        coll = indexer.client.get_collection(
            name=collection,
            embedding_function=indexer.embedding_fn,  # type: ignore[arg-type]
        )

        # Search
        results = coll.query(
            query_texts=[query],
            n_results=limit,
        )

        if not results["documents"] or not results["documents"][0]:
            console.print("[yellow]No results found.[/yellow]")
            return

        # Display results
        console.print(f"\n[bold green]Found {len(results['documents'][0])} results:[/bold green]\n")

        for i, (doc, metadata, distance) in enumerate(
            zip(
                results["documents"][0],
                results["metadatas"][0],  # type: ignore[index]
                results["distances"][0],  # type: ignore[index]
                strict=True,
            ),
            1,
        ):
            file_path = metadata.get("file_path", "Unknown") if metadata else "Unknown"
            language = metadata.get("language", "unknown") if metadata else "unknown"
            relevance = max(0, 1 - distance) * 100  # Convert distance to relevance percentage

            console.print(
                Panel(
                    f"[bold cyan]File:[/bold cyan] {file_path}\n"
                    f"[bold cyan]Language:[/bold cyan] {language}\n"
                    f"[bold cyan]Relevance:[/bold cyan] {relevance:.1f}%\n\n"
                    f"[white]{doc[:500]}...[/white]"
                    if len(doc) > 500
                    else f"[white]{doc}[/white]",
                    title=f"Result {i}",
                    border_style="blue",
                )
            )

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("collection")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete(ctx: click.Context, collection: str, yes: bool) -> None:
    """Delete a collection."""
    try:
        if not yes:
            click.confirm(
                f"Are you sure you want to delete collection '{collection}'?",
                abort=True,
            )

        indexer = CodebaseIndexer(db_path=ctx.obj["db_path"])
        indexer.client.delete_collection(name=collection)

        console.print(f"[bold green]Collection '{collection}' deleted successfully.[/bold green]")

    except click.Abort:
        console.print("[yellow]Cancelled.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option("--output", "-o", help="Output file (default: <directory>/.mcpignore)")
@click.pass_context
def create_ignore(_ctx: click.Context, directory: str, output: str | None) -> None:
    """Create a .mcpignore file with default patterns."""
    try:
        dir_path = Path(directory)
        context_filter = ContextFilter(root_path=dir_path)

        # Note: output parameter is reserved for future use
        _ = output

        created_path = context_filter.create_ignore_file(overwrite=True)

        console.print(f"[bold green]Created .mcpignore file:[/bold green] {created_path}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
