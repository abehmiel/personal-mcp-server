#!/usr/bin/env python3
"""
Performance Benchmark Script

Measures embedding generation and search performance across different configurations.
"""

import time

from rich.console import Console
from rich.table import Table

console = Console()


def benchmark_embedding_speed() -> dict[str, float]:
    """Benchmark embedding generation speed."""
    console.print("[blue]Benchmarking embedding generation...[/blue]")

    try:
        import torch
        from sentence_transformers import SentenceTransformer

        from rag_server.utils import detect_device

        # Detect device
        device, platform_info = detect_device()
        console.print(f"[dim]Using device: {device} ({platform_info.system}, {platform_info.machine})[/dim]")

        # Load model
        console.print("[dim]Loading model...[/dim]")
        start = time.time()
        model = SentenceTransformer("all-MiniLM-L6-v2", device=device)
        load_time = time.time() - start

        # Prepare test data
        test_docs = [
            f"This is test document number {i} with some content about coding and software development."
            for i in range(100)
        ]

        # Warm up
        _ = model.encode(test_docs[:10])

        # Benchmark
        start = time.time()
        _ = model.encode(test_docs)
        elapsed = time.time() - start

        docs_per_sec = len(test_docs) / elapsed

        return {
            "load_time": load_time,
            "docs_per_second": docs_per_sec,
            "total_docs": len(test_docs),
            "elapsed": elapsed,
        }

    except ImportError as e:
        console.print(f"[red]Error: {e}[/red]")
        return {}


def benchmark_search() -> dict[str, float]:
    """Benchmark search performance."""
    console.print("[blue]Benchmarking search...[/blue]")

    try:
        import chromadb
        from sentence_transformers import SentenceTransformer

        from rag_server.utils import detect_device

        # Setup
        device, _ = detect_device()
        model = SentenceTransformer("all-MiniLM-L6-v2", device=device)
        client = chromadb.Client()

        # Create collection
        collection = client.create_collection("benchmark_test")

        # Add documents
        docs = [
            f"Document {i}: This is about topic {i % 10} and contains relevant information."
            for i in range(1000)
        ]
        embeddings = model.encode(docs)

        collection.add(
            documents=docs,
            embeddings=embeddings.tolist(),
            ids=[f"doc_{i}" for i in range(len(docs))],
        )

        # Benchmark search
        query = "What is topic 5 about?"
        query_embedding = model.encode([query])[0]

        # Warm up
        _ = collection.query(query_embeddings=[query_embedding.tolist()], n_results=10)

        # Benchmark
        iterations = 100
        start = time.time()
        for _ in range(iterations):
            _ = collection.query(query_embeddings=[query_embedding.tolist()], n_results=10)
        elapsed = time.time() - start

        searches_per_sec = iterations / elapsed
        avg_latency_ms = (elapsed / iterations) * 1000

        # Cleanup
        client.delete_collection("benchmark_test")

        return {
            "searches_per_second": searches_per_sec,
            "avg_latency_ms": avg_latency_ms,
            "collection_size": len(docs),
            "iterations": iterations,
        }

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return {}


def display_results(embedding_results: dict[str, float], search_results: dict[str, float]) -> None:
    """Display benchmark results."""
    console.print("\n[bold blue]Benchmark Results[/bold blue]\n")

    # Embedding results
    if embedding_results:
        table = Table(title="Embedding Generation", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        table.add_row("Model Load Time", f"{embedding_results['load_time']:.2f}s")
        table.add_row("Documents Processed", str(embedding_results["total_docs"]))
        table.add_row("Total Time", f"{embedding_results['elapsed']:.2f}s")
        table.add_row("Throughput", f"{embedding_results['docs_per_second']:.1f} docs/sec")

        console.print(table)
        console.print()

    # Search results
    if search_results:
        table = Table(title="Search Performance", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        table.add_row("Collection Size", f"{search_results['collection_size']} documents")
        table.add_row("Iterations", str(search_results["iterations"]))
        table.add_row("Throughput", f"{search_results['searches_per_second']:.1f} searches/sec")
        table.add_row("Average Latency", f"{search_results['avg_latency_ms']:.2f}ms")

        console.print(table)
        console.print()

    # Performance assessment
    if embedding_results and search_results:
        console.print("[bold]Performance Assessment:[/bold]")

        # Assess embedding speed
        docs_per_sec = embedding_results["docs_per_second"]
        if docs_per_sec > 80:
            console.print("[green]✓ Excellent embedding performance (likely using GPU)[/green]")
        elif docs_per_sec > 30:
            console.print("[yellow]○ Good embedding performance (CPU or efficient GPU)[/yellow]")
        else:
            console.print("[red]✗ Slow embedding performance (check device configuration)[/red]")

        # Assess search latency
        latency = search_results["avg_latency_ms"]
        if latency < 100:
            console.print("[green]✓ Excellent search latency[/green]")
        elif latency < 200:
            console.print("[yellow]○ Good search latency[/yellow]")
        else:
            console.print("[red]✗ Slow search performance[/red]")

        console.print()


def main() -> int:
    """Run benchmarks."""
    console.print("[bold blue]MCP Server Performance Benchmark[/bold blue]\n")

    # Run benchmarks
    embedding_results = benchmark_embedding_speed()
    console.print()

    search_results = benchmark_search()
    console.print()

    # Display results
    display_results(embedding_results, search_results)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
