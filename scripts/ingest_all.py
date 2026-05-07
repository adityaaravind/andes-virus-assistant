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
    console.rule("[bold blue]Andes Virus Research Assistant — Ingestion Pipeline")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:

        # Fetch raw documents
        all_docs: list[dict[str, Any]] = []

        task = progress.add_task("Fetching PubMed abstracts...", total=None)
        try:
            pubmed_docs = fetch_abstracts(max_results=200)
            console.print(f"  [green]✓ PubMed:[/green] {len(pubmed_docs)} articles")
            all_docs.extend(pubmed_docs)
        except Exception as exc:
            console.print(f"  [yellow]⚠ PubMed failed:[/yellow] {exc}")
        progress.remove_task(task)

        task = progress.add_task("Downloading WHO PDFs...", total=None)
        try:
            who_results = download_who_pdfs()
            downloaded = [r for r in who_results if r["status"] in ("downloaded", "cached")]
            console.print(f"  [green]✓ WHO PDFs:[/green] {len(downloaded)} files")
        except Exception as exc:
            console.print(f"  [yellow]⚠ WHO scraper failed:[/yellow] {exc}")
        progress.remove_task(task)

        task = progress.add_task("Parsing PDFs...", total=None)
        try:
            pdf_docs = parse_all_pdfs()
            console.print(f"  [green]✓ PDFs parsed:[/green] {len(pdf_docs)} documents")
            all_docs.extend(pdf_docs)
        except Exception as exc:
            console.print(f"  [yellow]⚠ PDF parsing failed:[/yellow] {exc}")
        progress.remove_task(task)

        task = progress.add_task("Scraping news RSS feeds...", total=None)
        try:
            news_docs = scrape_all_feeds()
            console.print(f"  [green]✓ News:[/green] {len(news_docs)} articles")
            all_docs.extend(news_docs)
        except Exception as exc:
            console.print(f"  [yellow]⚠ News scraping failed:[/yellow] {exc}")
        progress.remove_task(task)

        task = progress.add_task("Loading Wikipedia articles...", total=None)
        try:
            wiki_docs = load_wikipedia_articles()
            console.print(f"  [green]✓ Wikipedia:[/green] {len(wiki_docs)} articles")
            all_docs.extend(wiki_docs)
        except Exception as exc:
            console.print(f"  [yellow]⚠ Wikipedia failed:[/yellow] {exc}")
        progress.remove_task(task)

        console.print(f"\n[bold]Total raw documents:[/bold] {len(all_docs)}")

        if not all_docs:
            console.print("[red]No documents fetched. Check network connectivity and API access.[/red]")
            return

        # Chunk
        task = progress.add_task("Chunking documents...", total=None)
        chunks = chunk_documents(all_docs)
        progress.remove_task(task)
        console.print(f"  [green]✓ Chunks created:[/green] {len(chunks)}")

        # Tag metadata
        task = progress.add_task("Tagging metadata...", total=None)
        chunks = tag_chunks(chunks)
        progress.remove_task(task)

        # Embed
        provider = get_embedding_provider()
        task = progress.add_task(f"Embedding ({provider})...", total=None)
        try:
            chunks = embed_chunks(chunks)
        except Exception as exc:
            console.print(f"[red]Embedding failed: {exc}[/red]")
            return
        progress.remove_task(task)
        console.print(f"  [green]✓ Embeddings generated:[/green] {len(chunks)}")

        # Store
        task = progress.add_task("Storing in ChromaDB...", total=None)
        added = add_documents(chunks)
        progress.remove_task(task)
        console.print(f"  [green]✓ New chunks stored:[/green] {added}")

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
