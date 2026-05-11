"""Chat panel — streaming answers, rate limiting, feedback, export."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import streamlit as st

from rag.prompt_templates import STARTER_QUESTIONS
from rag.citation_formatter import format_citation_cards

RATE_LIMIT = 25          # queries per session
FEEDBACK_LOG = Path("data/feedback.jsonl")
FEEDBACK_LOG.parent.mkdir(parents=True, exist_ok=True)

def _query_count() -> int:
    return st.session_state.get("query_count", 0)

def _rate_limited() -> bool:
    return _query_count() >= RATE_LIMIT

def _increment_count() -> None:
    st.session_state["query_count"] = _query_count() + 1

def _render_rate_bar() -> None:
    used = _query_count()
    pct  = used / RATE_LIMIT * 100
    color = "#22c55e" if pct < 60 else "#f59e0b" if pct < 85 else "#ef4444"
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:0.4rem;margin-bottom:0.2rem;">
<div style="flex:1;height:3px;background:rgba(255,255,255,0.05);border-radius:2px;">
<div style="width:{pct:.0f}%;height:100%;background:{color};border-radius:2px;transition:width 0.3s;"></div>
</div>
<span style="color:{color};font-size:0.6rem;font-family:monospace;font-weight:900;">{used}/{RATE_LIMIT}</span>
</div>""",
        unsafe_allow_html=True,
    )

def _log_feedback(question: str, answer: str, rating: str) -> None:
    record = {
        "ts":       datetime.utcnow().isoformat(),
        "rating":   rating,
        "question": question[:300],
        "answer":   answer[:500],
    }
    with FEEDBACK_LOG.open("a") as f:
        f.write(json.dumps(record) + "\n")

def _render_feedback(msg_idx: int, question: str, answer: str) -> None:
    key_up   = f"fb_up_{msg_idx}"
    key_down = f"fb_dn_{msg_idx}"
    logged   = f"fb_logged_{msg_idx}"

    if st.session_state.get(logged):
        st.markdown("<p style='font-size:10px; color:#4ade80; margin:0;'>✓ Feedback recorded</p>", unsafe_allow_html=True)
        return

    col1, col2, col3 = st.columns([1, 1, 10])
    with col1:
        if st.button("👍", key=key_up, help="Helpful"):
            _log_feedback(question, answer, "positive")
            st.session_state[logged] = True
            st.rerun()
    with col2:
        if st.button("👎", key=key_down, help="Not helpful"):
            _log_feedback(question, answer, "negative")
            st.session_state[logged] = True
            st.rerun()

def _export_answer(question: str, answer: str, sources: list[dict]) -> str:
    lines = [
        "ANDES VIRUS RESEARCH ASSISTANT — ANSWER EXPORT",
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "=" * 60,
        f"\nQUESTION:\n{question}",
        f"\nANSWER:\n{answer}",
    ]
    if sources:
        lines.append("\nSOURCES:")
        for s in sources:
            name = s.get("source_name", s.get("source", "Unknown"))
            url  = s.get("url", "")
            date = s.get("date", "")
            lines.append(f"  • {name} ({date}) {url}")
    lines.append("\n" + "=" * 60)
    lines.append("Not medical advice. For emergencies contact local health authority.")
    return "\n".join(lines)

def render_chat_panel(
    on_source_update: Callable[[list[dict[str, Any]]], None],
) -> None:
    st.markdown("<p style='font-size:0.8rem; font-weight:900; margin:0; color:#94a3b8;'>ASK A QUESTION</p>", unsafe_allow_html=True)
    _render_rate_bar()

    # Custom CSS to compress chat bubbles and reduce padding
    st.markdown("""
        <style>
            .stChatMessage { padding: 0.4rem !important; margin-bottom: 0.4rem !important; }
            .stChatMessage [data-testid="stMarkdownContainer"] p { font-size: 0.85rem !important; line-height: 1.4 !important; }
            .stChatAvatar { width: 24px !important; height: 24px !important; font-size: 14px !important; }
            .stChatInput { padding-top: 0.5rem !important; }
        </style>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    _render_starter_questions()

    chat_container = st.container()
    with chat_container:
        for i, msg in enumerate(st.session_state.messages):
            with st.chat_message(msg["role"], avatar=_avatar(msg["role"])):
                st.markdown(msg["content"])
                if msg["role"] == "assistant":
                    if msg.get("sources"):
                        _render_inline_source_list(msg["sources"])

                    q = _get_paired_question(i)
                    col_fb, col_exp = st.columns([4, 1])
                    with col_fb:
                        _render_feedback(i, q, msg["content"])
                    with col_exp:
                        if msg["content"] and q:
                            txt = _export_answer(q, msg["content"], msg.get("raw_sources", []))
                            st.download_button(
                                "💾",
                                data=txt,
                                file_name=f"andes_answer_{i}.txt",
                                mime="text/plain",
                                key=f"export_{i}",
                                help="Save Answer"
                            )

    if _rate_limited():
        st.warning(f"Limit ({RATE_LIMIT}) reached.", icon="⛔")
        return

    chain = st.session_state.get("rag_chain")

    if prompt := st.chat_input("Ask about the outbreak..."):
        _handle_streaming_query(prompt, chain, on_source_update)

def _handle_streaming_query(
    prompt: str,
    chain: Any,
    on_source_update: Callable[[list[dict[str, Any]]], None],
) -> None:
    _increment_count()
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🧬"):
        if chain is None:
            answer = "⚠️ RAG chain not initialized."
            st.markdown(answer)
            citation_cards = []
        else:
            try:
                answer = st.write_stream(chain.stream(prompt))
                meta   = st.session_state.pop("_last_rag_meta", {})
                raw_chunks    = meta.get("raw_chunks", [])
                citation_cards = format_citation_cards(raw_chunks) if raw_chunks else []
                if citation_cards:
                    _render_inline_source_list(citation_cards)
                on_source_update(citation_cards)
            except Exception as exc:
                answer = f"⚠️ Query error: {exc}"
                st.markdown(answer)
                citation_cards = []

    st.session_state.messages.append({
        "role":        "assistant",
        "content":     answer,
        "sources":     citation_cards,
        "raw_sources": [c for c in citation_cards],
    })

def _get_paired_question(assistant_idx: int) -> str:
    msgs = st.session_state.get("messages", [])
    if assistant_idx > 0 and msgs[assistant_idx - 1]["role"] == "user":
        return msgs[assistant_idx - 1]["content"]
    return ""

def _render_starter_questions() -> None:
    if st.session_state.messages:
        return

    st.markdown(
        "<p style='color: #64748b; font-size:0.75rem; margin-bottom:0.2rem;'>SUGGESTIONS:</p>",
        unsafe_allow_html=True,
    )
    # Compact chips for starter questions
    cols = st.columns(2)
    for i, question in enumerate(STARTER_QUESTIONS[:4]):
        with cols[i % 2]:
            if st.button(question, key=f"starter_{i}", use_container_width=True):
                st.session_state["_starter_query"] = question
                st.rerun()

    if "_starter_query" in st.session_state:
        q = st.session_state.pop("_starter_query")
        st.session_state.messages.append({"role": "user", "content": q})
        st.rerun()

def _render_inline_source_list(cards: list[dict[str, Any]]) -> None:
    if not cards:
        return
    parts = []
    for card in cards:
        idx  = card.get("index", "?")
        name = card.get("source_name", "Source")
        parts.append(f"**[{idx}]** {name}")
    st.markdown(f"<p style='font-size:10px; color:#94a3b8; margin:0;'>Sources: {' · '.join(parts)}</p>", unsafe_allow_html=True)

def _avatar(role: str) -> str:
    return "🧬" if role == "assistant" else "🧑‍💻"
