"""Attach credibility scores and normalized metadata to chunks."""
from __future__ import annotations

from typing import Any


CREDIBILITY_MAP: dict[str, float] = {
    "WHO": 1.0,
    "CDC": 1.0,
    "PubMed": 0.9,
    "research": 0.9,
    "Reuters": 0.75,
    "BBC Health": 0.75,
    "ECDC": 0.9,
    "news": 0.7,
    "Al Jazeera": 0.65,
    "Wikipedia": 0.6,
    "encyclopedia": 0.6,
    "PDF": 0.8,
    "unknown": 0.5,
}

SOURCE_TYPE_LABELS: dict[str, str] = {
    "WHO": "WHO",
    "CDC": "WHO",
    "PubMed": "PubMed",
    "research": "PubMed",
    "news": "News",
    "Reuters": "News",
    "BBC Health": "News",
    "Al Jazeera": "News",
    "Wikipedia": "Wikipedia",
    "encyclopedia": "Wikipedia",
    "ECDC": "WHO",
    "PDF": "WHO",
}


def tag_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for chunk in chunks:
        _apply_tags(chunk)
    return chunks


def _apply_tags(chunk: dict[str, Any]) -> None:
    source = chunk.get("source", "")
    source_type = chunk.get("source_type", "")

    credibility = _resolve_credibility(source, source_type)
    display_type = _resolve_display_type(source, source_type)

    chunk["credibility_score"] = credibility
    chunk["display_source_type"] = display_type
    chunk["source_name"] = source or source_type or "Unknown"


def _resolve_credibility(source: str, source_type: str) -> float:
    for key in (source, source_type):
        if key in CREDIBILITY_MAP:
            return CREDIBILITY_MAP[key]
    for key, score in CREDIBILITY_MAP.items():
        if key.lower() in source.lower() or key.lower() in source_type.lower():
            return score
    return CREDIBILITY_MAP["unknown"]


def _resolve_display_type(source: str, source_type: str) -> str:
    for key in (source, source_type):
        if key in SOURCE_TYPE_LABELS:
            return SOURCE_TYPE_LABELS[key]
    for key, label in SOURCE_TYPE_LABELS.items():
        if key.lower() in source.lower() or key.lower() in source_type.lower():
            return label
    return "Other"
