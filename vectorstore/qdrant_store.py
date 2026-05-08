"""Qdrant Cloud vector store — persistent storage for Streamlit Cloud deployment.

Set QDRANT_URL and QDRANT_API_KEY in environment / Streamlit secrets to activate.
Falls back to local ChromaDB when these are absent (local dev).
"""
from __future__ import annotations

import hashlib
import logging
import os
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

COLLECTION_NAME = "andes_virus_research"
VECTOR_DIM      = 1536   # text-embedding-3-small
BATCH_SIZE      = 100


def _client() -> QdrantClient:
    url     = os.getenv("QDRANT_URL", "")
    api_key = os.getenv("QDRANT_API_KEY", "")
    return QdrantClient(url=url, api_key=api_key, timeout=30)


def _ensure_collection(client: QdrantClient) -> None:
    existing = {c.name for c in client.get_collections().collections}
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )
        logging.info("Qdrant: created collection %s", COLLECTION_NAME)


def add_documents(chunks: list[dict[str, Any]]) -> int:
    if not chunks:
        return 0
    client = _client()
    _ensure_collection(client)

    points = []
    for chunk in chunks:
        emb = chunk.get("embedding")
        if not emb:
            continue
        cid = _chunk_id(chunk)
        points.append(PointStruct(
            id=int(cid, 16) % (2**63),   # Qdrant requires uint64
            vector=emb,
            payload=_build_payload(chunk),
        ))

    if not points:
        return 0

    added = 0
    for i in range(0, len(points), BATCH_SIZE):
        batch = points[i : i + BATCH_SIZE]
        client.upsert(collection_name=COLLECTION_NAME, points=batch)
        added += len(batch)

    logging.info("Qdrant: upserted %d points", added)
    return added


# Alias
upsert_chunks = add_documents


def similarity_search(
    query_embedding: list[float],
    k: int = 6,
    where: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    client = _client()
    _ensure_collection(client)

    qdrant_filter = None
    if where:
        conditions = [
            FieldCondition(key=k, match=MatchValue(value=v))
            for k, v in where.items()
        ]
        qdrant_filter = Filter(must=conditions)

    count = client.count(collection_name=COLLECTION_NAME).count
    if count == 0:
        return []

    try:
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=min(k, count),
            query_filter=qdrant_filter,
            with_payload=True,
        )
    except AttributeError:
        # Try newer API format
        try:
            results = client.search_points(
                collection_name=COLLECTION_NAME,
                query=query_embedding,
                limit=min(k, count),
                filter=qdrant_filter,
                with_payload=True,
            )
        except:
            # Try with named arguments for v1.9+
            results = client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_embedding,
                limit=min(k, count),
                query_filter=qdrant_filter,
                with_payload=True,
            )

    # Handle different result formats from different API versions
    formatted_results = []
    for r in results:
        try:
            # Standard format with .payload and .score attributes
            if hasattr(r, 'payload') and hasattr(r, 'score'):
                formatted_results.append({
                    "text":             r.payload.get("text", ""),
                    "metadata":         {k: v for k, v in r.payload.items() if k != "text"},
                    "similarity_score": r.score,
                })
            # Tuple format (id, score, payload)
            elif isinstance(r, tuple) and len(r) >= 3:
                payload = r[2] if len(r) > 2 else {}
                score = r[1] if len(r) > 1 else 0.0
                formatted_results.append({
                    "text":             payload.get("text", ""),
                    "metadata":         {k: v for k, v in payload.items() if k != "text"},
                    "similarity_score": score,
                })
            # Dict format
            elif isinstance(r, dict):
                payload = r.get('payload', {})
                score = r.get('score', 0.0)
                formatted_results.append({
                    "text":             payload.get("text", ""),
                    "metadata":         {k: v for k, v in payload.items() if k != "text"},
                    "similarity_score": score,
                })
            else:
                # Fallback - skip malformed results
                logging.warning("Unknown result format: %s", type(r))
        except Exception as e:
            logging.warning("Error processing search result: %s", e)
            continue

    return formatted_results


def get_stats() -> dict[str, Any]:
    try:
        client = _client()
        _ensure_collection(client)
        count = client.count(collection_name=COLLECTION_NAME).count
        return {
            "total_chunks":    count,
            "collection_name": COLLECTION_NAME,
            "status":          "ready" if count > 0 else "empty",
            "backend":         "qdrant",
        }
    except Exception as exc:
        return {"total_chunks": 0, "status": f"error: {exc}", "backend": "qdrant"}


def _chunk_id(chunk: dict[str, Any]) -> str:
    url  = chunk.get("url", "")
    idx  = chunk.get("chunk_index", 0)
    text = chunk.get("text", "")[:50]
    raw  = f"{url}::{idx}::{text}"
    return hashlib.md5(raw.encode()).hexdigest()


def _build_payload(chunk: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {"text": chunk.get("text", "")}
    for key in (
        "source", "source_type", "source_name", "display_source_type",
        "title", "url", "date", "authors", "doi", "filename",
    ):
        payload[key] = str(chunk.get(key, ""))
    payload["credibility_score"] = float(chunk.get("credibility_score", 0.5))
    payload["chunk_index"]       = int(chunk.get("chunk_index", 0))
    payload["chunk_total"]       = int(chunk.get("chunk_total", 1))
    return payload
