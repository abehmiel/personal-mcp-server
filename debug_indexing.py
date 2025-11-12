#!/usr/bin/env python3
"""Debug script to trace where indexing hangs."""

import sys
import time

def log(msg):
    """Log with immediate flush."""
    print(f"[{time.time():.2f}] {msg}", flush=True)

log("Starting debug script...")

log("Step 1: Importing modules...")
from rag_server.indexer import CodebaseIndexer, IndexingConfig
from rag_server.chunking import ChunkingStrategy
log("  Imports complete")

log("Step 2: Creating config...")
config = IndexingConfig(
    chunk_size=1000,
    chunk_overlap=200,
    chunking_strategy=ChunkingStrategy.CODE,
    batch_size=100,
    show_progress=True,
)
log("  Config created")

log("Step 3: Creating indexer...")
indexer = CodebaseIndexer(db_path='./chroma_db', config=config)
log("  Indexer created")

log("Step 4: Starting index_directory...")

# Manually trace through index_directory steps
from pathlib import Path
from rag_server.context_filter import ContextFilter

directory = '/Users/Abe/Projects/world-pulls-back'
collection_name = 'world-pulls-back-test'

log("Step 4a: Resolving directory path...")
directory_path = Path(directory).resolve()
log(f"  Path resolved: {directory_path}")

log("Step 4b: Creating context filter...")
context_filter = ContextFilter(root_path=directory_path, use_defaults=True)
log("  Context filter created")

log("Step 4c: Getting filtered files...")
files = context_filter.get_filtered_files(extensions=None, recursive=True)
log(f"  Found {len(files)} files")

log("Step 4d: Deleting existing collection if exists...")
try:
    indexer.client.delete_collection(name=collection_name)
    log("  Collection deleted")
except Exception as e:
    log(f"  No existing collection to delete: {e}")

log("Step 4e: Creating collection...")
collection = indexer.client.get_or_create_collection(
    name=collection_name,
    embedding_function=indexer.embedding_fn,
    metadata={"indexed_directory": str(directory_path)},
)
log(f"  Collection created: {collection.name}")

log("Done!")
