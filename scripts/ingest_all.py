"""Orchestrate full ingestion pipeline: scrape → chunk → embed → store."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.pubmed_scraper import fetch_abstracts
from ingestion.who_scraper import download_who_pdfs
from ingestion.pdf_parser import parse_all_pdfs
from ingestion.news_scraper import scrape_all_feeds
from ingestion.wikipedia_loader import load_wikipedia_articles
from processing.chunker import chunk_documents
from processing.embedder import embed_chunks, get_embedding_provider
from processing.metadata_tagger import tag_chunks
from vectorstore.store import add_documents, get_stats, get_existing_ids, _chunk_id


console = Console()


def run_ingestion(fast: bool = False) -> None:
    import gc
    import os
    console.rule("[bold blue]Andes Virus Research Assistant — Incremental Ingestion Pipeline")
    if fast:
        console.print("[bold yellow]⚡ FAST MODE ACTIVE: Reducing scrape depth[/bold yellow]")

    # Cache existing IDs to avoid re-embedding
    try:
        existing_ids = get_existing_ids()
        console.print(f"  [dim]Found {len(existing_ids)} existing chunks in DB[/dim]")
    except Exception:
        existing_ids = set()
        console.print("  [dim]Could not retrieve existing IDs, assuming empty DB[/dim]")

    def _process_batch(source_name: str, docs: list[dict[str, Any]]) -> None:
        if not docs:
            return
        console.print(f"  [blue]→ Processing batch: {source_name} ({len(docs)} docs)[/blue]")
        chunks = chunk_documents(docs)
        if chunks:
            # FILTER NEW CHUNKS BEFORE TAGGING AND EMBEDDING
            new_chunks = []
            for c in chunks:
                cid = _chunk_id(c)
                # Qdrant IDs are often ints or stored differently, handle both
                if cid not in existing_ids and str(int(cid, 16) % (2**63)) not in existing_ids:
                    new_chunks.append(c)
            
            if not new_chunks:
                console.print(f"  [dim]✓ {source_name}: All {len(chunks)} chunks already indexed[/dim]")
                return

            console.print(f"  [dim]  {len(new_chunks)} / {len(chunks)} are new. Tagging and embedding...[/dim]")
            new_chunks = tag_chunks(new_chunks)
            try:
                new_chunks = embed_chunks(new_chunks)
                added = add_documents(new_chunks)
                console.print(f"  [green]✓ {source_name} batch complete:[/green] {added} new chunks stored")

                # FIRE REAL-TIME SIGNAL FOR EACH SOURCE
                try:
                    from alerts.signal_dispatcher import fire_ingestion_signal
                    fire_ingestion_signal(source_name, len(docs), len(new_chunks))
                except ImportError:
                    pass  # Signal system not available
            except Exception as e:
                console.print(f"  [red]✖ {source_name} batch failed:[/red] {e}")
        
        # Explicit cleanup after every batch
        del docs
        del chunks
        gc.collect()

    # 1. PubMed
    try:
        limit = 20 if fast else 200
        pubmed_docs = fetch_abstracts(max_results=limit)
        _process_batch("PubMed", pubmed_docs)
    except Exception as exc:
        console.print(f"  [yellow]⚠ PubMed failed:[/yellow] {exc}")

    # 2. WHO PDFs
    try:
        # Skip PDFs in fast mode if they already exist
        pdf_dir = Path("data/raw/who_reports")
        if not fast or not any(pdf_dir.glob("*.pdf")):
            download_who_pdfs()
        pdf_docs = parse_all_pdfs()
        _process_batch("WHO_PDFs", pdf_docs)
    except Exception as exc:
        console.print(f"  [yellow]⚠ WHO/PDF failed:[/yellow] {exc}")

    # 3. News RSS
    try:
        news_docs = scrape_all_feeds()
        if fast:
            news_docs = news_docs[:30] # Cap news in fast mode
        _process_batch("News_RSS", news_docs)
    except Exception as exc:
        console.print(f"  [yellow]⚠ News scraping failed:[/yellow] {exc}")

    # 4. Wikipedia
    try:
        if not fast:
            wiki_docs = load_wikipedia_articles()
            _process_batch("Wikipedia", wiki_docs)
    except Exception as exc:
        console.print(f"  [yellow]⚠ Wikipedia failed:[/yellow] {exc}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", action="store_true", help="Fast ingestion mode")
    args = parser.parse_args()
    run_ingestion(fast=args.fast)
