"""RAG chain: retrieval → prompt → LLM → structured response."""
from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from rag.prompt_templates import build_rag_prompt
from rag.retriever import retrieve
from rag.citation_formatter import format_sources_list
from alerts.community_store import add_insight


load_dotenv()

DEFAULT_MODEL = "gpt-4o-mini"
MAX_TOKENS = 1024
TEMPERATURE = 0.1


def build_chain() -> "RAGChain":
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key == "your_key_here":
        # Return fallback chain when no API key
        return FallbackRAGChain()

    llm = ChatOpenAI(
        model=DEFAULT_MODEL,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        api_key=api_key,
        streaming=True,
    )
    prompt = build_rag_prompt()
    return RAGChain(llm=llm, prompt=prompt)


class FallbackRAGChain:
    """Fallback RAG chain that provides answers using retrieved chunks without OpenAI."""

    def query(self, question: str) -> dict[str, Any]:
        chunks = retrieve(question)
        if not chunks:
            return {
                "answer": "No relevant information found in the knowledge base for this question.",
                "sources": [],
                "chunks_used": 0,
                "raw_chunks": [],
            }

        # Generate answer from retrieved chunks without LLM
        answer_parts = []
        answer_parts.append("Based on the available research:")

        for i, chunk in enumerate(chunks[:3], 1):
            text = chunk.get('text', '')[:300]  # First 300 chars
            answer_parts.append(f"\n{i}. {text}...")

        sources = [chunk.get("metadata", {}) for chunk in chunks]

        import streamlit as st
        user_id = st.session_state.get("user_id", "anon")
        add_insight("search", f"queried knowledge base: '{question[:60]}...'", user_id)
        
        for source in sources:
             title = source.get("title")
             if title:
                 add_insight("citation", f"extracted evidence: {title}", user_id)

        return {
            "answer": "\n".join(answer_parts),
            "sources": sources,
            "chunks_used": len(chunks),
            "raw_chunks": chunks,
        }

    def stream(self, question: str):
        """Simple streaming implementation."""
        result = self.query(question)
        yield result["answer"]

        import streamlit as st
        st.session_state["_last_rag_meta"] = {
            "sources": result["sources"],
            "raw_chunks": result["raw_chunks"]
        }


class RAGChain:
    def __init__(self, llm: ChatOpenAI, prompt: Any) -> None:
        self._llm = llm
        self._prompt = prompt

    def _prepare(self, question: str) -> tuple[list[Any], list[dict], list[dict]]:
        from rag.session_memory import get_session_context
        from processing.embedder import _embed_texts
        
        # Get query embedding for memory lookup
        q_emb = _embed_texts([question])[0]
        past_context = get_session_context("default_session", q_emb)

        chunks = retrieve(question)
        if not chunks:
            return [], [], []

        context_parts: list[str] = []
        if past_context:
            context_parts.append(f"PREVIOUS SESSION CONTEXT:\n{past_context}")

        for i, chunk in enumerate(chunks, start=1):

            meta = chunk.get("metadata", {})
            title  = meta.get("title", "Unknown")
            source = meta.get("source_name", meta.get("source", "Unknown"))
            context_parts.append(f"[{i}] ({source} — {title})\n{chunk['text']}")

        context      = "\n\n---\n\n".join(context_parts)
        sources_list = format_sources_list(chunks)
        messages     = self._prompt.format_messages(
            context=context,
            sources_list=sources_list,
            question=question,
        )
        return messages, chunks, [chunk.get("metadata", {}) for chunk in chunks]

    def query(self, question: str) -> dict[str, Any]:
        messages, chunks, sources = self._prepare(question)
        if not chunks:
            return {
                "answer": (
                    "I don't have sufficient information in my sources to answer "
                    "this question. The vector store may be empty — "
                    "please run `python scripts/ingest_all.py` first."
                ),
                "sources": [],
                "chunks_used": 0,
                "raw_chunks": [],
            }
        response = self._llm.invoke(messages)
        
        # Save session context
        from rag.session_memory import save_session_context
        from processing.embedder import _embed_texts
        summary = f"User asked: {question}\nAssistant answered: {response.content[:200]}..."
        try:
            q_emb = _embed_texts([question])[0]
            save_session_context("default_session", summary, q_emb)
        except: pass

        import streamlit as st
        user_id = st.session_state.get("user_id", "anon")
        add_insight("search", f"isolated intel: '{question[:60]}...'", user_id)
        
        for source in sources:
             title = source.get("title")
             if title:
                 add_insight("citation", f"verified source: {title}", user_id)

        return {
            "answer":      response.content,
            "sources":     sources,
            "chunks_used": len(chunks),
            "raw_chunks":  chunks,
        }

    def stream(self, question: str):
        """Yield (token, meta) where meta is None until last chunk."""
        messages, chunks, sources = self._prepare(question)
        if not chunks:
            yield ("I don't have sufficient information in my sources to answer this question.", {"sources": [], "raw_chunks": []})
            return
        for chunk in self._llm.stream(messages):
            yield chunk.content
        # Sentinel: push metadata as final value via session state
        import streamlit as st
        st.session_state["_last_rag_meta"] = {"sources": sources, "raw_chunks": chunks}
