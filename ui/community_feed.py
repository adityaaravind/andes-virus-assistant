"""Community & Social Proof Panel — Phase 2."""
from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from typing import Any
from alerts.community_store import get_community_data

def render_community_feed() -> None:
    """Render the central intelligence feed and trending evidence."""
    data = get_community_data()
    feed = data.get("feed", [])
    
    st.markdown("### 📡 Community Intelligence")
    
    col_log, col_trending = st.columns([1.8, 1])
    
    with col_log:
        st.markdown(
            "<p style='color:#94a3b8; font-size:0.75rem; font-weight:800; margin-bottom:1rem; letter-spacing:0.1em; opacity:0.8; text-transform:uppercase;'>📡 TRANSMISSION LOG</p>",
            unsafe_allow_html=True
        )
        
        if not feed:
            st.markdown(
                "<div style='background:rgba(255,255,255,0.02); border:1px dashed rgba(255,255,255,0.1); border-radius:10px; padding:2rem; text-align:center;'>"
                "<p style='color:#64748b; font-size:0.8rem; margin:0;'>Waiting for incoming community insights...</p></div>",
                unsafe_allow_html=True
            )
        else:
            log_html = "<div style='display:flex; flex-direction:column; gap:0.5rem;'>"
            for item in feed[:15]: # Show last 15
                ts = datetime.fromisoformat(item["timestamp"]).strftime("%H:%M:%S")
                icon = "🔍" if item["type"] == "search" else "📢" if item["type"] == "alert" else "📚"
                color = "#38bdf8" if item["type"] == "search" else "#ef4444" if item["type"] == "alert" else "#a78bfa"
                
                log_html += f"""
                <div style="background:rgba(15, 23, 42, 0.4); border-left: 3px solid {color}; padding: 0.6rem 0.8rem; border-radius: 4px; font-family: 'Inter', monospace;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2px;">
                        <span style="color:{color}; font-size:0.6rem; font-weight:900; text-transform:uppercase; letter-spacing:0.05em;">{item['type']}</span>
                        <span style="color:#475569; font-size:0.55rem; font-weight:700;">{ts}</span>
                    </div>
                    <p style="color:#cbd5e1; font-size:0.72rem; margin:0; line-height:1.3;">
                        <span style="color:#64748b; font-weight:700;">{item['user_id']}</span> {item['content']}
                    </p>
                </div>
                """
            log_html += "</div>"
            st.markdown(log_html, unsafe_allow_html=True)

    with col_trending:
        st.markdown(
            "<p style='color:#94a3b8; font-size:0.75rem; font-weight:800; margin-bottom:1rem; letter-spacing:0.1em; opacity:0.8; text-transform:uppercase;'>📈 TRENDING EVIDENCE</p>",
            unsafe_allow_html=True
        )
        
        # Calculate trending citations from feed
        citations = {}
        for item in feed:
            if item["type"] == "citation":
                title = item["content"].split(":")[-1].strip()
                citations[title] = citations.get(title, 0) + 1
        
        sorted_citations = sorted(citations.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_citations:
             st.markdown(
                "<div style='background:rgba(167, 139, 250, 0.03); border:1px solid rgba(167, 139, 250, 0.1); border-radius:10px; padding:1.2rem;'>"
                "<p style='color:#94a3b8; font-size:0.7rem; margin:0;'>Aggregate peer-verified citations will appear here as researchers query the knowledge base.</p></div>",
                unsafe_allow_html=True
            )
        else:
            for title, count in sorted_citations[:5]:
                st.markdown(
                    f"""
                    <div class="stat-card" style="padding: 0.8rem !important; min-height: 60px !important; margin-bottom: 0.5rem !important; border-color: rgba(167, 139, 250, 0.2) !important;">
                        <div style="display:flex; gap:10px; align-items:center;">
                            <div style="background:rgba(167, 139, 250, 0.1); color:#a78bfa; padding:4px 8px; border-radius:4px; font-weight:900; font-size:0.8rem;">{count}</div>
                            <p style="color:#f8fafc; font-size:0.7rem; font-weight:600; margin:0; line-height:1.2; overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;">{title}</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    st.markdown("<br>", unsafe_allow_html=True)
