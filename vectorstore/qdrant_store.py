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

COLLECTION_NAME = "andes_virus_research_v11"
VECTOR_DIM      = 1536   # text-embedding-3-small
BATCH_SIZE      = 100
VERSION         = "1.1"


def _client() -> QdrantClient:
    url     = os.getenv("QDRANT_URL", "")
    api_key = os.getenv("QDRANT_API_KEY", "")
    return QdrantClient(url=url, api_key=api_key, timeout=30)


def _ensure_collection(client: QdrantClient) -> None:
    existing = {c.name for c in client.get_collections().collections}
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                "summary": VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
                "detail":  VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
            },
            # v1.1 Foundation for hybrid search
            # sparse_vectors_config={"text-sparse": SparseVectorParams(index=SparseIndexParams(on_disk=True))}
        )
        logging.info("Qdrant: created collection %s with Named Vectors", COLLECTION_NAME)


def get_existing_ids() -> set[str]:
    client = _client()
    _ensure_collection(client)
    # Qdrant scroll to get all IDs (simplified for large collections, but works here)
    ids = set()
    offset = None
    while True:
        points, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            with_payload=False,
            with_vectors=False,
            limit=10000,
            offset=offset,
        )
        for p in points:
            # Convert back to hex-like string if needed, or keep as int
            ids.add(str(p.id))
        if not next_offset:
            break
        offset = next_offset
    return ids


def add_documents(chunks: list[dict[str, Any]]) -> int:
    if not chunks:
        return 0
    client = _client()
    _ensure_collection(client)

    points = []
    for chunk in chunks:
        detail_emb = chunk.get("embedding")
        summary_emb = chunk.get("summary_embedding") or detail_emb
        if not detail_emb:
            continue
        cid = _chunk_id(chunk)
        points.append(PointStruct(
            id=int(cid, 16) % (2**63),
            vector={
                "summary": summary_emb,
                "detail":  detail_emb
            },
            payload=_build_payload(chunk),
        ))

    if not points:
        return 0

    added = 0
    for i in range(0, len(points), BATCH_SIZE):
        batch = points[i : i + BATCH_SIZE]
        client.upsert(collection_name=COLLECTION_NAME, points=batch)
        added += len(batch)

    logging.info("Qdrant: upserted %d points to %s", added, COLLECTION_NAME)
    return added


# Alias
upsert_chunks = add_documents


def recommend_similar_chunks(
    chunk_id: int,
    limit: int = 5,
    where: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Qdrant Recommendation API: find chunks similar to a specific point."""
    client = _client()
    qdrant_filter = None
    if where:
        conditions = [
            FieldCondition(key=k, match=MatchValue(value=v))
            for k, v in where.items()
        ]
        qdrant_filter = Filter(must=conditions)

    try:
        results = client.recommend(
            collection_name=COLLECTION_NAME,
            positive=[chunk_id],
            limit=limit,
            query_filter=qdrant_filter,
            with_payload=True,
        )
        return _format_results(results)
    except Exception as e:
        logging.warning("Recommendation failed: %s", e)
        return []


def similarity_search(
    query_embedding: list[float],
    k: int = 6,
    where: dict[str, Any] | None = None,
    vector_name: str = "detail",
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
            query_vector=(vector_name, query_embedding),
            limit=min(k, count),
            query_filter=qdrant_filter,
            with_payload=True,
        )
    except Exception as e:
        logging.warning("Search failed: %s", e)
        return []

    return _format_results(results)



def _format_results(results: Any) -> list[dict[str, Any]]:
    """Helper to unify result formats from Qdrant API."""
    formatted_results = []
    for r in results:
        try:
            if hasattr(r, 'payload') and hasattr(r, 'score'):
                formatted_results.append({
                    "id":               getattr(r, 'id', None),
                    "text":             r.payload.get("text", ""),
                    "metadata":         {k: v for k, v in r.payload.items() if k != "text"},
                    "similarity_score": r.score,
                })
            elif isinstance(r, dict):
                payload = r.get('payload', {})
                formatted_results.append({
                    "id":               r.get('id'),
                    "text":             payload.get("text", ""),
                    "metadata":         {k: v for k, v in payload.items() if k != "text"},
                    "similarity_score": r.get('score', 0.0),
                })
        except Exception as e:
            logging.warning("Error processing result: %s", e)
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
            "version":         VERSION,
        }
    except Exception as exc:
        return {"total_chunks": 0, "status": f"error: {exc}", "backend": "qdrant", "version": VERSION}



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
