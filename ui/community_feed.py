"""Community & Social Proof Panel — Phase 2 (Bug Fix & Optimization)."""
from __future__ import annotations

import streamlit as st
from datetime import datetime
from typing import Any
from alerts.community_store import get_community_data, get_trending_topics

def render_community_feed() -> None:
    """Render a live tactical intelligence stream with trending research topics."""
    # Real-time refresh (every 30 seconds for community data)
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=30000, key="community_refresh")

    data = get_community_data()
    feed = data.get("feed", [])
    trending = get_trending_topics(limit=5)
    
    # 1. HEADER
    st.markdown(
        """
        <div class="cyber-header" title="Real-time tactical intelligence: user research trends, verified citations, and system alerts.">
            <div style='display:flex; align-items:center; gap:12px; background:rgba(0,180,216,0.03); padding:10px; border-radius:8px; border-left:4px solid #00b4d8; cursor:help;'>
                <h3 style='margin:0; font-size:0.85rem !important; letter-spacing:0.12em; color:#ffffff; text-shadow:0 0 10px rgba(0,180,216,0.4);'>📡 TACTICAL INTEL</h3>
                <span class="live-dot" style="width:6px; height:6px; background:#22c55e; box-shadow:0 0 10px #22c55e;"></span>
                <span style='color:#00b4d8; font-size:0.6rem; font-weight:900; opacity:0.6; border:1px solid #00b4d844; padding:1px 5px; border-radius:4px;'>LIVE_FEED</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 2. TRENDING RESEARCH TOPICS
    if trending:
        st.markdown("<p style='color:#64748b; font-size:0.6rem; font-weight:900; text-transform:uppercase; margin:0.8rem 0 0.4rem;'>🔥 Trending Research</p>", unsafe_allow_html=True)
        tags_html = "<div style='display:flex; flex-wrap:wrap; gap:6px; margin-bottom:1rem;'>"
        for topic, count in trending:
            tags_html += f"""
            <div style='background:rgba(251,191,36,0.05); border:1px solid rgba(251,191,36,0.2); padding:4px 10px; border-radius:15px; display:flex; align-items:center; gap:6px;'>
                <span style='color:#fbbf24; font-size:0.65rem; font-weight:800;'>{topic}</span>
                <span style='background:#fbbf24; color:#000; font-size:0.55rem; padding:0 4px; border-radius:3px; font-weight:900;'>{count}</span>
            </div>
            """
        tags_html += "</div>"
        st.markdown(tags_html, unsafe_allow_html=True)

    if not feed:
        st.caption("Awaiting transmission...")
        return

    # 3. TACTICAL SIGNAL STREAM
    st.markdown("<p style='color:#64748b; font-size:0.6rem; font-weight:900; text-transform:uppercase; margin:0.5rem 0 0.4rem;'>📡 Signal Stream</p>", unsafe_allow_html=True)
    log_inner = ""
    for item in feed[:20]: # Show up to 20 signals in the scroll window
        ts = datetime.fromisoformat(item["timestamp"]).strftime("%H:%M:%S")
        
        # Color based on signal priority
        if item["type"] == "alert":
            color = "#ef4444" # Critical Alert
            prefix = "🚨 ALERT"
        elif item["type"] == "citation":
            color = "#a78bfa" # Verified Science
            prefix = "🏛️ VERIFIED"
        elif item["type"] == "search":
            color = "#38bdf8" # Intelligence Gathering
            prefix = "🔍 INTEL"
        else:
            color = "#94a3b8"
            prefix = "📡 SIGNAL"

        content = item['content']
        if item['type'] == 'citation':
            content = f"Source verified: {content.split(':')[-1].strip()[:60]}..."
        elif item['type'] == 'search':
            content = f"Query: {content.replace('queried: ', '')}"
            
        log_inner += (
            f"<div style='font-family:monospace; font-size:0.7rem; line-height:1.4; margin-bottom:6px; display:flex; gap:10px;'>"
            f"<span style='color:#475569; min-width:60px;'>[{ts}]</span>"
            f"<span style='color:{color}; font-weight:900; min-width:75px;'>{prefix}</span>"
            f"<span style='color:#f1f5f9;'>{content}</span></div>"
        )

    st.markdown(
        f"""
        <div style='
            background: rgba(0,0,0,0.2);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 12px;
            height: 200px;
            overflow-y: auto;
            border-left: 3px solid rgba(0,180,216,0.3);
            scrollbar-width: thin;
            scrollbar-color: #00b4d8 rgba(0,0,0,0.1);
        '>
            {log_inner}
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("<div style='margin-bottom:-1rem;'></div>", unsafe_allow_html=True) 
