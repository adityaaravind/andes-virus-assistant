"""Fear index component — user voting on outbreak fear level."""
from __future__ import annotations

import os
import hashlib
import json
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from alerts.persist_helper import bg_kv_set, get_persisted_value
from alerts.community_store import log_sentiment_snapshot, get_community_data

_FEAR_KEY = "fear_index_votes"

FEAR_LEVELS = {
    1: {"label": "calm", "desc": "Not worried", "color": "#22c55e"},
    2: {"label": "concerned", "desc": "Slightly worried", "color": "#f59e0b"},
    3: {"label": "worried", "desc": "Moderately fearful", "color": "#ef4444"},
    4: {"label": "fearful", "desc": "Very worried", "color": "#dc2626"},
    5: {"label": "panicked", "desc": "Extremely fearful", "color": "#991b1b"},
}

def _get_stable_user_id() -> str:
    """Generate a unique session-based ID to ensure individual lockout periods."""
    if "stable_user_id" not in st.session_state:
        # Generate a random unique ID for this specific session
        import uuid
        st.session_state.stable_user_id = f"u_{str(uuid.uuid4())[:12]}"
    return st.session_state.stable_user_id

def _load_fear_data() -> dict[str, Any]:
    data = get_persisted_value(_FEAR_KEY)
    if data: return data
    return {"votes": [], "last_updated": datetime.utcnow().isoformat()}

def _get_user_lockout_remaining(user_id: str) -> int:
    """Returns seconds remaining in the 6-hour lockout. 0 if no lockout."""
    data = _load_fear_data()
    votes = data.get("votes", [])
    user_votes = [v for v in votes if v.get("user_id") == user_id]
    if not user_votes:
        return 0
    
    last_vote = datetime.fromisoformat(user_votes[-1]["timestamp"])
    elapsed = (datetime.utcnow() - last_vote).total_seconds()
    remaining = (6 * 3600) - elapsed
    return int(max(0, remaining))

def _save_fear_vote(level: int, user_id: str) -> None:
    st.session_state.fear_slider_input = level
    st.session_state.just_voted = True

    try:
        data = _load_fear_data()
        old_count = len(data.get("votes", []))
        data["votes"] = [v for v in data["votes"] if v.get("user_id") != user_id]
        data["votes"].append({
            "level": level,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
        data["votes"] = data["votes"][-2000:]
        data["last_updated"] = datetime.utcnow().isoformat()
        new_count = len(data["votes"])

        from alerts.persistent_kv import kv_set
        kv_set(_FEAR_KEY, data)

        # FIRE REAL-TIME SIGNAL FOR VOTE CHANGE
        avg_fear, _, label, _, _, web_sentiment = _calculate_fear_average()

        from alerts.notifier import send_ntfy
        send_ntfy(
            os.getenv("NTFY_DEFAULT_TOPIC", "HANTAVIRUS"),
            f"🗳️ Fear Index Updated: {label.upper()}",
            f"New vote recorded (Level {level}/5).\n"
            f"Current fear score: {avg_fear:.2f}\n"
            f"Total votes: {new_count}\n"
            f"Status: {label}",
            "info"
        )

        # Log the vote signal
        from alerts.alert_manager import _log_alert
        _log_alert(
            f"Fear Index Vote: {label}",
            f"Vote level {level}, new avg: {avg_fear:.2f}, total votes: {new_count}"
        )

    except Exception as e:
        st.error(f"Persistence error: {str(e)}")

@st.cache_data(ttl=60, show_spinner=False)
def _calculate_web_sentiment() -> float:
    try:
        from ui.news_ticker import fetch_headlines
        articles = fetch_headlines()
        if not articles: return 2.5
        fear_keywords = {"outbreak": 0.5, "deadly": 0.8, "death": 0.8, "emergency": 0.6, "quarantine": 0.7, "risk": 0.4}
        total_score = 0.0
        relevant_count = 0
        for art in articles[:50]:
            text = (art.get("title", "") + " " + art.get("summary", "")).lower()
            article_score = 1.0
            for kw, weight in fear_keywords.items():
                if kw in text: article_score += weight
            total_score += min(article_score, 5.0)
            relevant_count += 1
        return round(total_score / relevant_count, 2) if relevant_count > 0 else 2.5
    except Exception: return 2.5

def _calculate_fear_average() -> tuple[float, int, str, str, str, float]:
    data = _load_fear_data()
    votes = data.get("votes", [])
    web_score = _calculate_web_sentiment()
    if not votes:
        avg = web_score
    else:
        total_weight = 0
        weighted_sum = 0
        for i, vote in enumerate(reversed(votes)):
            weight = 1 + (i / len(votes)) * 0.5
            weighted_sum += vote["level"] * weight
            total_weight += weight
        user_avg = weighted_sum / total_weight
        avg = (user_avg * 0.6) + (web_score * 0.4)
    closest_level = min(FEAR_LEVELS.keys(), key=lambda x: abs(x - avg))
    level_info = FEAR_LEVELS[closest_level]
    return avg, len(votes), level_info["label"], level_info["desc"], level_info["color"], web_score

@st.cache_data(ttl=60, show_spinner=False)
def _build_fear_gauge(avg_fear: float, color: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=avg_fear,
        number={"suffix": "/5", "font": {"size": 52, "color": "#f8fafc", "family": "monospace"}},
        gauge={"axis": {"range": [1, 5]}, "bar": {"color": color}, "bgcolor": "rgba(27,46,69,0.6)"},
        title={"text": "PUBLIC FEAR SCORE", "font": {"size": 13, "color": "#94a3b8", "family": "monospace"}},
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={"color": "#f8fafc"}, margin=dict(l=20, r=20, t=30, b=10), height=280)
    return fig

@st.cache_data(ttl=60, show_spinner=False)
def _build_sentiment_trend(history: list[dict[str, Any]]) -> go.Figure:
    if not history: return go.Figure()
    dates = [datetime.fromisoformat(p["timestamp"]) for p in history]
    user_scores = [p.get("user_score", p.get("score", 2.5)) for p in history]
    web_scores = [p.get("web_score", p.get("score", 2.5)) for p in history]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=user_scores, name="User Consensus", mode="lines", line=dict(color="#00f5ff", width=4)))
    fig.add_trace(go.Scatter(x=dates, y=web_scores, name="Web Sentiment", mode="lines", line=dict(color="#a78bfa", width=2, dash="dot")))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=40, t=10, b=10), height=140, xaxis=dict(visible=False), yaxis=dict(visible=True, range=[0.5, 5.5]))
    return fig

def render_fear_index() -> None:
    avg_fear, vote_count, label, desc, color, web_sentiment = _calculate_fear_average()
    live_fear = round(avg_fear, 2)
    log_sentiment_snapshot(avg_fear, web_sentiment)
    community = get_community_data()
    user_id = _get_stable_user_id()
    lockout_sec = _get_user_lockout_remaining(user_id)
    is_locked = (lockout_sec > 0)

    # Session-level lock: Allow voting once per session even if not globally locked
    # unless they JUST voted in this specific turn.
    if st.session_state.get("just_voted"):
        is_locked = True

    # ── 1. BIO-HAZARD THREAT LEVEL BAR (REPLACES GAUGE) ──
    threat_pct = (live_fear - 1) / 4 * 100
    threat_html = f"""
    <div style="background:rgba(15, 23, 42, 0.6); border: 1px solid {color}44; border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem; backdrop-filter: blur(10px); position:relative; overflow:hidden;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <div>
                <p style="color:#94a3b8; font-size:0.65rem; font-weight:800; letter-spacing:0.1em; margin:0; font-family:monospace;">🧬 PUBLIC WORRY METER</p>
                <h2 style="margin:0; font-size:1.8rem; font-weight:950; color:white; letter-spacing:-0.02em;">{label.upper()}</h2>
            </div>
            <div style="text-align:right;">
                <p style="color:{color}; font-size:2rem; font-weight:900; margin:0; line-height:1; font-family:monospace;">{live_fear:.2f}</p>
                <p style="color:#94a3b8; font-size:0.5rem; font-weight:800; margin:0; text-transform:uppercase;">WORRY SCORE</p>
            </div>
        </div>
        <div style="height:12px; background:rgba(255,255,255,0.05); border-radius:100px; overflow:hidden; border:1px solid rgba(255,255,255,0.1);">
            <div style="width:{threat_pct}%; height:100%; background:linear-gradient(90deg, #22c55e, #f59e0b, #ef4444); transition: width 1s ease-in-out; position:relative;">
                <div style="position:absolute; right:0; top:0; height:100%; width:4px; background:white; box-shadow:0 0 15px white;"></div>
            </div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:8px;">
             <span style="color:#94a3b8; font-size:0.55rem; font-weight:700;">STABLE</span>
             <span style="color:#ef4444; font-size:0.55rem; font-weight:900; animation:pulse-fear 1.5s infinite;">CRITICAL</span>
        </div>
        <div style="margin-top:12px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.05); display:flex; justify-content:space-between; align-items:center;">
             <div style="display:flex; gap:12px;">
                 <span style="color:#64748b; font-size:0.6rem; font-weight:800;">TOTAL VOTES: <b style="color:white;">{vote_count}</b></span>
                 <span style="color:#64748b; font-size:0.6rem; font-weight:800;">USER AVG: <b style="color:#00f5ff;">{round((live_fear - web_sentiment * 0.4) / 0.6, 2) if vote_count > 0 else live_fear:.1f}</b></span>
                 <span style="color:#64748b; font-size:0.6rem; font-weight:800;">WEB SENTIMENT: <b style="color:#a78bfa;">{web_sentiment:.1f}</b></span>
             </div>
        </div>
    </div>
    """
    st.markdown(threat_html, unsafe_allow_html=True)
    
    # ── 2. TREND GRAPH ──
    # ── 3. TACTICAL INPUT (MOBILE FRIENDLY) ──
    st.markdown("""
        <style>
        div.stButton > button {
            width: 100% !important; height: 55px !important;
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.98)) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-left: 3px solid var(--btn-color) !important;
            border-radius: 10px !important; color: #f8fafc !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            display: flex !important; flex-direction: row !important;
            align-items: center !important; justify-content: center !important; gap: 8px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
        }
        div.stButton > button:hover { 
            transform: translateY(-2px) !important; 
            border-color: var(--btn-color) !important;
            box-shadow: 0 0 20px var(--btn-color)44 !important;
            background: rgba(30, 41, 59, 1) !important;
        }
        div.stButton > button p { margin: 0 !important; font-weight: 950 !important; font-size: 0.7rem !important; letter-spacing: 0.05em; text-transform: uppercase; }
        div.stButton > button span { font-size: 1.2rem !important; margin-bottom: 0px !important; }
        div.stButton > button:disabled { opacity: 0.2 !important; filter: grayscale(1) !important; pointer-events: none !important; }
        /* ── Mobile Grid Overrides for Fear Buttons ── */
        @media (max-width: 768px) {
            div[data-testid="stVerticalBlock"] > div:has(.fear-marker) + div > div[data-testid="stHorizontalBlock"] {
                flex-direction: row !important;
                flex-wrap: wrap !important;
                gap: 0.5rem !important;
            }
            div[data-testid="stVerticalBlock"] > div:has(.fear-marker) + div > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
                width: calc(50% - 0.25rem) !important;
                flex: 1 1 calc(50% - 0.25rem) !important;
                min-width: 0 !important;
            }
            /* Make the 5th (last) button span full width to anchor the grid */
            div[data-testid="stVerticalBlock"] > div:has(.fear-marker) + div > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {
                width: 100% !important;
                flex: 1 1 100% !important;
            }
            /* Compact buttons inside grid */
            div.stButton > button { height: 45px !important; padding: 2px !important; }
            div.stButton > button p { font-size: 0.55rem !important; }
        }
        </style>
        <div style="margin: 1.2rem 0 0.6rem; border-left: 3px solid #38bdf8; padding-left: 10px;">
            <p style='color:#38bdf8; font-size:0.85rem; font-weight:900; margin:0; letter-spacing:0.02em;'>🗣️ TELL US HOW YOU FEEL</p>
            <p style='color:#64748b; font-size:0.6rem; margin:1px 0 0;'>Your input helps recalibrate the community mood in real-time.</p>
        </div>
        <div class="fear-marker" style="display:none;"></div>
        """, unsafe_allow_html=True)

    cols = st.columns(5)
    icons = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴", 5: "💀"}
    for i, level_id in enumerate(range(1, 6)):
        info = FEAR_LEVELS[level_id]
        with cols[i]:
            st.markdown(f'<div style="--btn-color: {info["color"]};">', unsafe_allow_html=True)
            btn_text = f"{icons[level_id]} {info['label'].upper()}"
            if st.button(btn_text, key=f"findex_v4_{level_id}", disabled=is_locked, use_container_width=True):
                _save_fear_vote(level_id, user_id)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    if is_locked:
        hours = lockout_sec // 3600
        mins = (lockout_sec % 3600) // 60
        # If they just voted, show a simpler thank you
        if st.session_state.get("just_voted"):
             st.markdown(
                """
                <div style="background:rgba(34,197,94,0.1); border-left:4px solid #22c55e; padding:0.8rem; margin-top:1rem; border-radius:4px;">
                    <p style="color:#22c55e; font-size:0.75rem; font-weight:900; margin:0;">✓ STATUS UPDATED</p>
                    <p style="color:#94a3b8; font-size:0.6rem; margin:2px 0 0;">Your feedback has been successfully recorded.</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(
                f"""
                <div style="background:rgba(239,68,68,0.1); border-left:4px solid #ef4444; padding:0.8rem; margin-top:1rem; border-radius:4px;">
                    <p style="color:#ef4444; font-size:0.75rem; font-weight:900; margin:0;">🔒 VOTE RECORDED (LOCK ACTIVE)</p>
                    <p style="color:#94a3b8; font-size:0.6rem; margin:2px 0 0;">Next vote available in: <b>{hours}h {mins}m</b>. This prevents multiple votes from one person.</p>
                </div>
                """, unsafe_allow_html=True)
