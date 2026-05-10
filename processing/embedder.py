"""Embedding engine — OpenAI primary, HuggingFace fallback."""
from __future__ import annotations

import os
import time
from typing import Any

from dotenv import load_dotenv


load_dotenv()

OPENAI_MODEL = "text-embedding-3-small"
HF_MODEL = "all-MiniLM-L6-v2"
BATCH_SIZE = 100
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5.0


def embed_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Generate both 'detail' (full text) and 'summary' (title + snippet) embeddings."""
    detail_texts = [c["text"] for c in chunks]
    summary_texts = [f"{c.get('title', '')}: {c['text'][:200]}" for c in chunks]
    
    detail_embs = _embed_texts(detail_texts)
    summary_embs = _embed_texts(summary_texts)

    for chunk, d_emb, s_emb in zip(chunks, detail_embs, summary_embs):
        chunk["embedding"] = d_emb
        chunk["summary_embedding"] = s_emb

    return chunks



def _embed_texts(texts: list[str]) -> list[list[float]]:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and api_key != "your_key_here":
        return _openai_embed(texts, api_key)
    # FORCE DISABLE local models on Streamlit Cloud to save RAM
    print(f"CRITICAL: OpenAI key missing. Local models disabled to prevent OOM crash.")
    return [[0.0] * 1536 for _ in texts]


def _openai_embed(texts: list[str], api_key: str) -> list[list[float]]:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        for attempt in range(RETRY_ATTEMPTS):
            try:
                response = client.embeddings.create(
                    model=OPENAI_MODEL,
                    input=batch,
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                break
            except Exception as exc:
                if attempt == RETRY_ATTEMPTS - 1:
                    raise RuntimeError(f"OpenAI embedding failed after {RETRY_ATTEMPTS} attempts: {exc}") from exc
                time.sleep(RETRY_DELAY * (attempt + 1))

    return all_embeddings


def _huggingface_embed(texts: list[str]) -> list[list[float]]:
    from sentence_transformers import SentenceTransformer

    print(f"No OpenAI key found — using HuggingFace {HF_MODEL}")
    model = SentenceTransformer(HF_MODEL)
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        batch_embeddings = model.encode(batch, show_progress_bar=False).tolist()
        all_embeddings.extend(batch_embeddings)

    return all_embeddings


def get_embedding_provider() -> str:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and api_key != "your_key_here":
        return f"OpenAI ({OPENAI_MODEL})"
    return f"HuggingFace ({HF_MODEL})"
