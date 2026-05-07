"""Retriever: embed query, search ChromaDB, re-rank by credibility."""
from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv


load_dotenv()

TOP_K_RETRIEVE = 6
TOP_K_RETURN = 4


def retrieve(query: str) -> list[dict[str, Any]]:
    query_embedding = _embed_query(query)
    raw_results = _search(query_embedding, k=TOP_K_RETRIEVE)
    reranked = _rerank(raw_results)
    return reranked[:TOP_K_RETURN]


def _embed_query(query: str) -> list[float]:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and api_key != "your_key_here":
        return _openai_embed_query(query, api_key)
    return _hf_embed_query(query)


def _openai_embed_query(query: str, api_key: str) -> list[float]:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
    )
    return response.data[0].embedding


def _hf_embed_query(query: str) -> list[float]:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return model.encode(query).tolist()


def _search(query_embedding: list[float], k: int) -> list[dict[str, Any]]:
    from vectorstore.store import similarity_search
    return similarity_search(query_embedding, k=k)


def _rerank(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for r in results:
        sim = r.get("similarity_score", 0.0)
        cred = float(r.get("metadata", {}).get("credibility_score", 0.5))
        r["rerank_score"] = sim * cred

    return sorted(results, key=lambda x: x["rerank_score"], reverse=True)
