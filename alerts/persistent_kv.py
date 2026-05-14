"""Tiny key-value store: Qdrant (persistent) when QDRANT_URL set, else local JSON files."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

_COLLECTION = "alert_kv"
_VECTOR_DIM = 4  # stub — Qdrant requires vectors; we only use payload

_CACHED_CLIENT = None
_CHECKED_COLLECTIONS = set()

def _hash_id(key: str) -> int:
    """Convert key to 63-bit integer for Qdrant point ID."""
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (2**63)

def _client():
    global _CACHED_CLIENT
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams
        
        if _CACHED_CLIENT is None:
            url = os.getenv("QDRANT_URL")
            api_key = os.getenv("QDRANT_API_KEY")
            if not url:
                raise RuntimeError("QDRANT_URL not set")
            _CACHED_CLIENT = QdrantClient(url=url, api_key=api_key, timeout=10)
        
        if _COLLECTION not in _CHECKED_COLLECTIONS:
            names = [col.name for col in _CACHED_CLIENT.get_collections().collections]
            if _COLLECTION not in names:
                _CACHED_CLIENT.create_collection(
                    _COLLECTION,
                    vectors_config=VectorParams(size=_VECTOR_DIM, distance=Distance.COSINE),
                )
            _CHECKED_COLLECTIONS.add(_COLLECTION)
            
        return _CACHED_CLIENT
    except Exception as e:
        # Clear cache on error to allow retry
        _CACHED_CLIENT = None
        raise RuntimeError(f"Qdrant client error: {str(e)}")


def _qdrant_available() -> bool:
    """Check if Qdrant is configured and client is available."""
    if not os.getenv("QDRANT_URL"):
        return False
    return True

def kv_get(key: str, default: Any = None) -> Any:
    if _qdrant_available():
        try:
            client = _client()
            result = client.retrieve(_COLLECTION, ids=[_hash_id(key)], with_payload=True)
            if result:
                return result[0].payload.get("value", default)
            return default # Key not found in Qdrant, return default
        except Exception as e:
            # Check if we should use graceful fallback (enabled by default)
            import os
            fallback = os.getenv("QDRANT_GRACEFUL_FALLBACK", "true").lower() == "true"
            if fallback:
                # Fall back to local JSON
                path = Path(f"data/kv_{key}.json")
                if path.exists():
                    try:
                        return json.loads(path.read_text())
                    except Exception:
                        pass
                return default
            else:
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
    if _qdrant_available():
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
        except (Exception, ImportError):
            pass
    path = Path(f"data/kv_{key}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2))
