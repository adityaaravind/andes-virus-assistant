"""Tiny key-value store: Qdrant (persistent) when QDRANT_URL set, else local JSON files."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

_COLLECTION = "alert_kv"
_VECTOR_DIM = 4  # stub — Qdrant requires vectors; we only use payload


def _hash_id(key: str) -> int:
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (2 ** 63)


def _client():
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams
    c = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
    names = [col.name for col in c.get_collections().collections]
    if _COLLECTION not in names:
        c.create_collection(
            _COLLECTION,
            vectors_config=VectorParams(size=_VECTOR_DIM, distance=Distance.COSINE),
        )
    return c


def kv_get(key: str, default: Any = None) -> Any:
    if os.getenv("QDRANT_URL"):
        try:
            result = _client().retrieve(_COLLECTION, ids=[_hash_id(key)], with_payload=True)
            if result:
                return result[0].payload.get("value", default)
            return default # Key not found in Qdrant, return default
        except Exception as e:
            # DO NOT fall back to local JSON if Qdrant is configured but failing.
            # This prevents overwriting remote data with empty local data.
            raise RuntimeError(f"Qdrant persistence failure: {str(e)}") from e
    
    path = Path(f"data/kv_{key}.json")
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return default


def kv_set(key: str, value: Any) -> None:
    if os.getenv("QDRANT_URL"):
        try:
            from qdrant_client.models import PointStruct
            _client().upsert(
                _COLLECTION,
                points=[PointStruct(
                    id=_hash_id(key),
                    vector=[0.0] * _VECTOR_DIM,
                    payload={"key": key, "value": value},
                )],
            )
            return
        except Exception:
            pass
    path = Path(f"data/kv_{key}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2))
