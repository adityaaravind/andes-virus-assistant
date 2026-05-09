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
from vectorstore.store import add_documents, get_stats


console = Console()


def run_ingestion() -> None:
    import gc
    console.rule("[bold blue]Andes Virus Research Assistant — Incremental Ingestion Pipeline")

    def _process_batch(source_name: str, docs: list[dict[str, Any]]) -> None:
        if not docs:
            return
        console.print(f"  [blue]→ Processing batch: {source_name} ({len(docs)} docs)[/blue]")
        chunks = chunk_documents(docs)
        if chunks:
            chunks = tag_chunks(chunks)
            try:
                chunks = embed_chunks(chunks)
                added = add_documents(chunks)
                console.print(f"  [green]✓ {source_name} batch complete:[/green] {added} chunks stored")
            except Exception as e:
                console.print(f"  [red]✖ {source_name} batch failed:[/red] {e}")
        
        # Explicit cleanup after every batch
        del docs
        del chunks
        gc.collect()

    # 1. PubMed
    try:
        pubmed_docs = fetch_abstracts(max_results=200)
        _process_batch("PubMed", pubmed_docs)
    except Exception as exc:
        console.print(f"  [yellow]⚠ PubMed failed:[/yellow] {exc}")

    # 2. WHO PDFs
    try:
        download_who_pdfs()
        pdf_docs = parse_all_pdfs()
        _process_batch("WHO_PDFs", pdf_docs)
    except Exception as exc:
        console.print(f"  [yellow]⚠ WHO/PDF failed:[/yellow] {exc}")

    # 3. News RSS
    try:
        news_docs = scrape_all_feeds()
        _process_batch("News_RSS", news_docs)
    except Exception as exc:
        console.print(f"  [yellow]⚠ News scraping failed:[/yellow] {exc}")

    # 4. Wikipedia
    try:
        wiki_docs = load_wikipedia_articles()
        _process_batch("Wikipedia", wiki_docs)
    except Exception as exc:
        console.print(f"  [yellow]⚠ Wikipedia failed:[/yellow] {exc}")

    # Summary table
    stats = get_stats()
    table = Table(title="Vector Store Stats", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Total chunks in DB", str(stats["total_chunks"]))
    table.add_row("Collection", stats["collection_name"])
    table.add_row("Status", stats["status"])
    console.print(table)
    console.rule("[bold green]Ingestion complete — ready to launch app")


if __name__ == "__main__":
    run_ingestion()
