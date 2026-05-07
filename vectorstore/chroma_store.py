"""ChromaDB wrapper for document storage and similarity search."""
from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv


load_dotenv()

COLLECTION_NAME = "andes_virus_research"
DEFAULT_PERSIST_DIR = "./vectorstore/db"
DEFAULT_K = 6


def _chromadb():
    """Lazy import — avoids crash on Python 3.14 where opentelemetry/protobuf breaks at import."""
    import chromadb
    from chromadb.config import Settings
    return chromadb, Settings


def get_client():
    chromadb, Settings = _chromadb()
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", DEFAULT_PERSIST_DIR)
    os.makedirs(persist_dir, exist_ok=True)
    return chromadb.PersistentClient(
        path=persist_dir,
        settings=Settings(anonymized_telemetry=False),
    )


def get_collection(client=None):
    if client is None:
        client = get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def add_documents(chunks: list[dict[str, Any]]) -> int:
    collection = get_collection()
    existing_ids = set(collection.get()["ids"])

    new_chunks = [c for c in chunks if _chunk_id(c) not in existing_ids]
    if not new_chunks:
        return 0

    ids = [_chunk_id(c) for c in new_chunks]
    embeddings = [c["embedding"] for c in new_chunks]
    documents = [c["text"] for c in new_chunks]
    metadatas = [_build_metadata(c) for c in new_chunks]

    batch_size = 500
    added = 0
    for i in range(0, len(new_chunks), batch_size):
        collection.add(
            ids=ids[i : i + batch_size],
            embeddings=embeddings[i : i + batch_size],
            documents=documents[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
        )
        added += len(ids[i : i + batch_size])

    return added


def similarity_search(
    query_embedding: list[float],
    k: int = DEFAULT_K,
    where: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    collection = get_collection()

    kwargs: dict[str, Any] = {
        "query_embeddings": [query_embedding],
        "n_results": min(k, collection.count()),
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where

    if kwargs["n_results"] == 0:
        return []

    results = collection.query(**kwargs)
    output: list[dict[str, Any]] = []

    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        similarity = 1.0 - dist
        output.append({
            "text": doc,
            "metadata": meta,
            "similarity_score": similarity,
        })

    return output


def get_stats() -> dict[str, Any]:
    try:
        collection = get_collection()
        count = collection.count()
        return {
            "total_chunks": count,
            "collection_name": COLLECTION_NAME,
            "status": "ready" if count > 0 else "empty",
        }
    except Exception as exc:
        return {"total_chunks": 0, "status": f"error: {exc}"}


def _chunk_id(chunk: dict[str, Any]) -> str:
    import hashlib
    url = chunk.get("url", "")
    idx = chunk.get("chunk_index", 0)
    text_hash = hashlib.md5(chunk["text"].encode()).hexdigest()[:8]
    raw = f"{url}::{idx}::{text_hash}"
    return hashlib.md5(raw.encode()).hexdigest()


def _build_metadata(chunk: dict[str, Any]) -> dict[str, str | float | int]:
    meta: dict[str, str | float | int] = {}
    for key in (
        "source", "source_type", "source_name", "display_source_type",
        "title", "url", "date", "authors", "doi", "filename",
    ):
        val = chunk.get(key, "")
        meta[key] = str(val) if val else ""

    meta["credibility_score"] = float(chunk.get("credibility_score", 0.5))
    meta["chunk_index"] = int(chunk.get("chunk_index", 0))
    meta["chunk_total"] = int(chunk.get("chunk_total", 1))
    return meta
