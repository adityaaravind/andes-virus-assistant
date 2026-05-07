"""Format citations and source lists for display."""
from __future__ import annotations

from typing import Any


def format_sources_list(chunks: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk.get("metadata", {})
        name = meta.get("source_name", meta.get("source", "Unknown"))
        date = meta.get("date", "")
        url = meta.get("url", "")
        date_str = f" ({date})" if date else ""
        url_str = f" — {url}" if url else ""
        lines.append(f"[{i}] {name}{date_str}{url_str}")
    return "\n".join(lines)


def format_citation_cards(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk.get("metadata", {})
        cards.append({
            "index": i,
            "title": meta.get("title", "Untitled"),
            "source_name": meta.get("source_name", meta.get("source", "Unknown")),
            "display_type": meta.get("display_source_type", "Other"),
            "date": meta.get("date", ""),
            "url": meta.get("url", ""),
            "authors": meta.get("authors", ""),
            "credibility_score": float(meta.get("credibility_score", 0.5)),
            "similarity_score": chunk.get("similarity_score", 0.0),
            "rerank_score": chunk.get("rerank_score", 0.0),
            "excerpt": chunk.get("text", "")[:300] + "..." if len(chunk.get("text", "")) > 300 else chunk.get("text", ""),
        })
    return cards


def format_inline_citation(index: int) -> str:
    return f"[{index}]"


def credibility_label(score: float) -> str:
    if score >= 0.95:
        return "Authoritative"
    if score >= 0.85:
        return "Peer-reviewed"
    if score >= 0.70:
        return "News media"
    return "Reference"
