"""Vector store router — picks Qdrant Cloud or local ChromaDB based on env vars.

  QDRANT_URL set  → Qdrant Cloud  (use on Streamlit Cloud / any hosted env)
  QDRANT_URL unset → ChromaDB local (default for local dev)

All callers should import from here, not directly from chroma_store or qdrant_store.
"""
from __future__ import annotations

import os

_use_qdrant = bool(os.getenv("QDRANT_URL"))

if _use_qdrant:
    from vectorstore.qdrant_store import (   # noqa: F401
        add_documents,
        upsert_chunks,
        similarity_search,
        recommend_similar_chunks,
        get_stats,
    )
else:
    from vectorstore.chroma_store import (   # noqa: F401
        add_documents,
        similarity_search,
        get_stats,
    )
    upsert_chunks = add_documents            # noqa: F811
    def recommend_similar_chunks(*args, **kwargs): return []
