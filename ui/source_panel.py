"""Source sidebar panel — expandable citation cards."""
from __future__ import annotations

from typing import Any

import streamlit as st

from rag.citation_formatter import credibility_label


TYPE_COLORS = {
    "WHO": ("#22c55e", "🏥"),
    "PubMed": ("#3b82f6", "🔬"),
    "News": ("#eab308", "📰"),
    "Wikipedia": ("#94a3b8", "📖"),
    "Other": ("#64748b", "📄"),
}


def render_source_panel(citation_cards: list[dict[str, Any]]) -> None:
    st.markdown("### Sources")

    if not citation_cards:
        st.markdown(
            "<p style='color:#64748b;font-size:0.85rem;'>Ask a question to see cited sources here.</p>",
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"<p style='color:#94a3b8;font-size:0.8rem;'>{len(citation_cards)} source(s) used</p>",
        unsafe_allow_html=True,
    )

    for card in citation_cards:
        _render_source_card(card)


def _render_source_card(card: dict[str, Any]) -> None:
    idx = card.get("index", "?")
    title = card.get("title", "Untitled")
    source_name = card.get("source_name", "Unknown")
    display_type = card.get("display_type", "Other")
    date = card.get("date", "")
    url = card.get("url", "")
    authors = card.get("authors", "")
    credibility = card.get("credibility_score", 0.5)
    excerpt = card.get("excerpt", "")

    color, icon = TYPE_COLORS.get(display_type, TYPE_COLORS["Other"])
    cred_label = credibility_label(credibility)

    header = f"{icon} [{idx}] {_truncate(title, 50)}"

    with st.expander(header, expanded=False):
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(
                f"<span style='background:rgba(255,255,255,0.1);color:{color};"
                f"border-radius:4px;padding:2px 8px;font-size:0.7rem;font-weight:700;"
                f"text-transform:uppercase;'>{display_type}</span>",
                unsafe_allow_html=True,
            )
        with col2:
            stars = "★" * round(credibility * 5)
            st.markdown(
                f"<span style='color:#eab308;font-size:0.75rem;' title='{cred_label}'>"
                f"{stars} {cred_label}</span>",
                unsafe_allow_html=True,
            )

        st.markdown(f"**Source:** {source_name}")
        if date:
            st.markdown(f"**Date:** {date}")
        if authors:
            st.markdown(f"**Authors:** {_truncate(authors, 80)}")
        if url:
            st.markdown(f"**[Open source ↗]({url})**")
        if excerpt:
            st.markdown("---")
            st.markdown(
                f"<p style='color:#94a3b8;font-size:0.8rem;font-style:italic;'>{excerpt}</p>",
                unsafe_allow_html=True,
            )


def _truncate(text: str, max_len: int) -> str:
    return text if len(text) <= max_len else text[:max_len].rstrip() + "…"
