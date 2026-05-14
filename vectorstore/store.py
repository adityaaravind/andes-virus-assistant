"""Vector store router — picks Qdrant Cloud or local ChromaDB based on env vars.

  QDRANT_URL set  → Qdrant Cloud  (use on Streamlit Cloud / any hosted env)
  QDRANT_URL unset → ChromaDB local (default for local dev)

All callers should import from here, not directly from chroma_store or qdrant_store.
"""
from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

_q_url = os.getenv("QDRANT_URL", "")
# Ignore placeholders like "your-cluster..." or empty strings
_use_qdrant = bool(_q_url and "your-cluster" not in _q_url and "http" in _q_url)

if _use_qdrant:
    from vectorstore.qdrant_store import (   # noqa: F401
        add_documents,
        upsert_chunks,
        similarity_search as _similarity_search,
        recommend_similar_chunks,
        get_stats,
        get_existing_ids,
        _chunk_id,
    )
else:
    from vectorstore.chroma_store import (   # noqa: F401
        add_documents,
        similarity_search as _similarity_search,
        get_stats,
        get_existing_ids,
        _chunk_id,
    )
    upsert_chunks = add_documents            # noqa: F811
    def recommend_similar_chunks(*args, **kwargs): return []


def similarity_search(query, k: int = 6, **kwargs):
    """Search with text query (auto-generates embeddings) or embedding vector."""
    if isinstance(query, str):
        # Generate embedding from text query
        from rag.retriever import _embed_query
        query_embedding = _embed_query(query)
        return _similarity_search(query_embedding, k=k, **kwargs)
    else:
        # Assume it's already an embedding
        return _similarity_search(query, k=k, **kwargs)
