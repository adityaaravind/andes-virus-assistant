"""Community & Social Proof Panel — Phase 2 (Bug Fix & Optimization)."""
from __future__ import annotations

import streamlit as st
from datetime import datetime
from typing import Any
from alerts.community_store import get_community_data

def render_community_feed() -> None:
    """Render a robust, minimalist community activity stream without layout bugs."""
    data = get_community_data()
    feed = data.get("feed", [])
    history = data.get("history", [])
    
    # 1. HEADER (High Contrast)
    st.markdown(
        """
        <div style='display:flex; align-items:center; gap:12px; margin-bottom:1rem; background:rgba(0,180,216,0.03); padding:10px; border-radius:8px; border-left:4px solid #00b4d8;'>
            <h3 style='margin:0; font-size:0.85rem !important; letter-spacing:0.12em; color:#ffffff; text-shadow:0 0 10px rgba(0,180,216,0.4);'>📡 COMMUNITY INTEL</h3>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if not feed:
        st.caption("Awaiting transmission...")
        return

    # 2. TRENDING TAGS
    citations = {}
    for item in feed:
        if item["type"] == "citation":
            title = item["content"].split(":")[-1].strip()
            citations[title] = citations.get(title, 0) + 1
    
    if citations:
        sorted_citations = sorted(citations.items(), key=lambda x: x[1], reverse=True)
        tags_html = "<div style='display:flex; flex-wrap:wrap; gap:6px; margin-bottom:1rem;'>"
        for title, count in sorted_citations[:3]: # Even more minimalist
            tags_html += f"<span style='background:rgba(167,139,250,0.08); border:1px solid rgba(167,139,250,0.3); padding:2px 8px; border-radius:4px; font-size:0.62rem; color:#a78bfa; font-weight:700;'># {title[:25]}... ({count})</span>"
        tags_html += "</div>"
        st.markdown(tags_html, unsafe_allow_html=True)

    # 3. ACTIVITY STREAM (Consolidated to prevent HTML leak)
    log_inner = ""
    for item in feed[:6]: # 6 items is enough for minimalism
        ts = datetime.fromisoformat(item["timestamp"]).strftime("%H:%M")
        color = "#38bdf8" if item["type"] == "search" else "#ef4444" if item["type"] == "alert" else "#a78bfa"
        content = item['content']
        if item['type'] == 'citation':
            content = f"verified {content.split(':')[-1].strip()[:45]}..."
            
        log_inner += f"<div style='font-family:monospace; font-size:0.7rem; line-height:1.4; margin-bottom:4px;'><span style='color:#475569;'>[{ts}]</span> <span style='color:{color}; font-weight:800;'>{item['user_id']}</span> <span style='color:#94a3b8;'>{content}</span></div>"

    st.markdown(
        f"<div style='border-left:1px solid rgba(255,255,255,0.1); padding-left:12px; margin-bottom:1.5rem;'>{log_inner}</div>",
        unsafe_allow_html=True
    )
    
    # 4. SENTIMENT VELOCITY (Sparkline with no gap)
    if history:
        st.markdown("<p style='color:#64748b; font-size:0.5rem; font-weight:900; text-transform:uppercase; letter-spacing:0.08em; margin:0;'>Sentiment Velocity (7D)</p>", unsafe_allow_html=True)
        from ui.fear_index import _build_sentiment_trend
        fig_trend = _build_sentiment_trend(history)
        # Force a very small height in Plotly container
        st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False}, key="community_velocity_chart")
    
    st.markdown("<div style='margin-bottom:-1rem;'></div>", unsafe_allow_html=True) # Tighten spacing
