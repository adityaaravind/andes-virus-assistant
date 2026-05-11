"""AI Automated Threat Feed — Real-time news classification and tactical analysis."""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from typing import Any

import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ui.news_ticker import fetch_headlines

# --- STYLING & CONFIG ---
SEVERITY_META = {
    "CRITICAL": {"color": "#dc2626", "bg": "rgba(220, 38, 38, 0.15)", "glow": "rgba(220, 38, 38, 0.4)"},
    "HIGH":     {"color": "#f59e0b", "bg": "rgba(245, 158, 11, 0.15)", "glow": "rgba(245, 158, 11, 0.4)"},
    "ELEVATED": {"color": "#eab308", "bg": "rgba(234, 179, 8, 0.15)", "glow": "rgba(234, 179, 8, 0.4)"},
    "LOW":      {"color": "#00b4d8", "bg": "rgba(0, 180, 216, 0.15)", "glow": "rgba(0, 180, 216, 0.4)"},
}

THREAT_PROMPT = """
You are a high-level Threat Intelligence AI monitoring the MV Hondius Andes virus outbreak.
Analyze the following news headline and summary.

HEADLINE: {title}
SUMMARY: {summary}

Classify this intelligence into a tactical threat report.
You MUST respond with a valid JSON object in exactly this format:
{{
  "severity": "CRITICAL" | "HIGH" | "ELEVATED" | "LOW",
  "category": "e.g. Containment, Medical, Logistics, Public Order, Media",
  "intel_summary": "One concise sentence of tactical analysis"
}}

Rules:
1. 'severity' should be based on the impact on the global or local outbreak containment.
2. 'intel_summary' must be professional and tactical.
3. Respond ONLY with JSON.
"""

@st.cache_data(ttl=3600, show_spinner=False)
def _analyze_threat(title: str, summary: str) -> dict[str, str]:
    """Use AI to classify a news item into a tactical threat profile."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or "your_key" in api_key:
        # Fallback if no API key
        return {
            "severity": "LOW",
            "category": "OSINT",
            "intel_summary": "Automated analysis offline. Manual verification required."
        }

    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)
        prompt = ChatPromptTemplate.from_template(THREAT_PROMPT)
        chain = prompt | llm
        
        response = chain.invoke({"title": title, "summary": summary})
        # Extract JSON from response (handling potential markdown fences)
        clean_text = re.sub(r"```json|```", "", response.content).strip()
        return json.loads(clean_text)
    except Exception as e:
        logging.error(f"Threat analysis failed: {e}")
        return {
            "severity": "LOW",
            "category": "ERROR",
            "intel_summary": "System anomaly during classification. Data unverified."
        }

def render_threat_feed() -> None:
    """Render the AI-powered tactical threat feed."""
    col_title, col_ts = st.columns([5, 1.5])
    with col_title:
        st.markdown(
            '<div style="display:flex; align-items:center; gap:10px;">'
            '<span class="live-dot" style="background:#dc2626; box-shadow: 0 0 10px #dc2626;"></span>'
            '<h2 style="color:#f8fafc; font-size:1.15rem; font-weight:900; margin:0; letter-spacing:0.05em;">🔴 LIVE THREAT INTELLIGENCE</h2>'
            '</div>',
            unsafe_allow_html=True,
        )
    with col_ts:
        st.markdown(
            f"<p style='color:#64748b; font-size:0.65rem; text-align:right; margin:0; line-height:1.2;'>"
            f"AI CLASSIFICATION ACTIVE<br>{datetime.utcnow().strftime('%H:%M UTC')}</p>",
            unsafe_allow_html=True,
        )

    with st.spinner("Analyzing incoming signals..."):
        # Get latest 10 news items
        raw_articles = fetch_headlines(max_per_feed=8)
        # Cap at 10 items for performance
        articles = raw_articles[:10]

    if not articles:
        st.info("No active threat signals detected in current OSINT window.", icon="📡")
        return

    # Build scrolling feed
    feed_html = """
    <div style="height:480px; overflow-y:auto; padding:5px; scrollbar-width:thin; scrollbar-color:rgba(148,163,184,0.3) transparent;">
    <style>
        .threat-item {
            background: rgba(13, 27, 42, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-left: 4px solid var(--s-color);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 12px;
            transition: all 0.2s ease;
            position: relative;
            overflow: hidden;
        }
        .threat-item:hover {
            background: rgba(13, 27, 42, 0.6);
            box-shadow: 0 0 20px var(--s-glow);
            transform: translateX(4px);
        }
        .severity-badge {
            background: var(--s-bg);
            color: var(--s-color);
            font-size: 0.55rem;
            font-weight: 900;
            padding: 2px 6px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            border: 1px solid var(--s-color);
        }
    </style>
    """

    for art in articles:
        # Get AI classification
        intel = _analyze_threat(art['title'], art['summary'])
        sev = intel.get("severity", "LOW").upper()
        meta = SEVERITY_META.get(sev, SEVERITY_META["LOW"])
        
        feed_html += f"""
        <div class="threat-item" style="--s-color: {meta['color']}; --s-bg: {meta['bg']}; --s-glow: {meta['glow']};">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <div style="display:flex; gap:8px; align-items:center;">
                    <span class="severity-badge">{sev}</span>
                    <span style="color:#94a3b8; font-size:0.6rem; font-weight:800; text-transform:uppercase;">[ {intel.get('category', 'GENERAL')} ]</span>
                </div>
                <span style="color:#475569; font-size:0.55rem; font-family:monospace;">{art['date']}</span>
            </div>
            <a href="{art['url']}" target="_blank" style="text-decoration:none; color:#f1f5f9; font-size:0.85rem; font-weight:700; line-height:1.2; display:block; margin-bottom:6px;">
                {art['title']}
            </a>
            <p style="color:#38bdf8; font-size:0.7rem; font-weight:600; margin:0; font-family:monospace; line-height:1.3; opacity:0.9;">
                > ANALYSIS: {intel.get('intel_summary', 'Awaiting verification...')}
            </p>
        </div>
        """

    feed_html += "</div>"
    st.markdown(feed_html, unsafe_allow_html=True)
