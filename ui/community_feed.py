"""Community & Social Proof Panel — Phase 2 (Minimalist Redesign)."""
from __future__ import annotations

import streamlit as st
from datetime import datetime
from typing import Any
from alerts.community_store import get_community_data

def render_community_feed() -> None:
    """Render a minimalist, high-contrast community activity stream."""
    data = get_community_data()
    feed = data.get("feed", [])
    
    # Header with a subtle neon anchor
    st.markdown(
        """
        <div style='display:flex; align-items:center; gap:10px; margin-bottom:1rem;'>
            <div style='width:3px; height:15px; background:#00b4d8; box-shadow:0 0 10px #00b4d8;'></div>
            <h3 style='margin:0; font-size:0.85rem !important; letter-spacing:0.1em; color:#00b4d8;'>COMMUNITY INTEL</h3>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if not feed:
        st.caption("Awaiting community transmission...")
        return

    # 1. Trending Strip (Minimalist Tags)
    citations = {}
    for item in feed:
        if item["type"] == "citation":
            title = item["content"].split(":")[-1].strip()
            citations[title] = citations.get(title, 0) + 1
    
    if citations:
        sorted_citations = sorted(citations.items(), key=lambda x: x[1], reverse=True)
        tags_html = "<div style='display:flex; flex-wrap:wrap; gap:8px; margin-bottom:1.5rem;'>"
        for title, count in sorted_citations[:4]:
            tags_html += f"""
            <div style="background:rgba(167, 139, 250, 0.1); border:1px solid rgba(167, 139, 250, 0.4); 
            padding:3px 10px; border-radius:15px; font-size:0.65rem; color:#a78bfa; font-weight:700;">
                <span style="opacity:0.6;">#</span> {title[:35]}... <span style="margin-left:5px; opacity:0.8;">({count})</span>
            </div>
            """
        tags_html += "</div>"
        st.markdown(tags_html, unsafe_allow_html=True)

    # 2. Activity Stream (Sleek Terminal Style)
    log_html = "<div style='border-left: 1px solid rgba(255,255,255,0.1); padding-left:15px; margin-left:5px; display:flex; flex-direction:column; gap:12px;'>"
    for item in feed[:8]: # Just the top 8 for minimalism
        ts = datetime.fromisoformat(item["timestamp"]).strftime("%H:%M")
        color = "#38bdf8" if item["type"] == "search" else "#ef4444" if item["type"] == "alert" else "#a78bfa"
        
        # Determine a more minimalist display content
        content = item['content']
        if item['type'] == 'citation':
            content = f"verified {content.split(':')[-1].strip()[:50]}..."
            
        log_html += f"""
        <div style="font-family: monospace; font-size: 0.72rem; line-height: 1.2;">
            <span style="color:#475569; font-weight:700;">[{ts}]</span> 
            <span style="color:{color}; font-weight:900;">{item['user_id']}</span>
            <span style="color:#94a3b8;"> {content}</span>
        </div>
        """
    log_html += "</div>"
    st.markdown(log_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
