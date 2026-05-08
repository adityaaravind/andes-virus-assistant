"""Qdrant-backed session memory for keeping track of conversation history."""
from __future__ import annotations

import os
from typing import Any
from qdrant_client.models import PointStruct, VectorParams, Distance

_COLLECTION = "session_memory"

def _client():
    from vectorstore.qdrant_store import _client as qc
    return qc()

def _ensure_session_col():
    client = _client()
    existing = {c.name for c in client.get_collections().collections}
    if _COLLECTION not in existing:
        client.create_collection(
            _COLLECTION,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )

def save_session_context(session_id: str, text: str, vector: list[float]):
    """Save a summary of the latest exchange."""
    if not os.getenv("QDRANT_URL"): return
    _ensure_session_col()
    import hashlib
    point_id = int(hashlib.md5(session_id.encode()).hexdigest(), 16) % (2**63)
    _client().upsert(
        _COLLECTION,
        points=[PointStruct(
            id=point_id,
            vector=vector,
            payload={"session_id": session_id, "summary": text}
        )]
    )

def get_session_context(session_id: str, query_vector: list[float]) -> str:
    """Find similar past context in the same session."""
    if not os.getenv("QDRANT_URL"): return ""
    _ensure_session_col()
    import hashlib
    point_id = int(hashlib.md5(session_id.encode()).hexdigest(), 16) % (2**63)
    try:
        # We look for the exact session point first
        res = _client().retrieve(_COLLECTION, ids=[point_id])
        if res:
            return res[0].payload.get("summary", "")
    except:
        pass
    return ""
