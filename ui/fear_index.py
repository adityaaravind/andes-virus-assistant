"""Fear index component — user voting on outbreak fear level."""
from __future__ import annotations

import hashlib
import json
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
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


def _load_fear_data() -> dict[str, Any]:
    """Load fear voting data from persistent store."""
    data = get_persisted_value(_FEAR_KEY)
    if data:
        return data
    return {"votes": [], "last_updated": datetime.utcnow().isoformat()}


def _save_fear_vote(level: int, user_id: str) -> None:
    """Save a new fear vote to persistent store."""
    # FAST REGISTRATION: Update session state immediately
    st.session_state.user_voted_today = True

    try:
        data = _load_fear_data()
        # Remove existing vote for this user (if any)
        data["votes"] = [v for v in data["votes"] if v.get("user_id") != user_id]
        data["votes"].append({
            "level": level,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
        # Keep only last 2000 votes to prevent file bloat
        data["votes"] = data["votes"][-2000:]
        data["last_updated"] = datetime.utcnow().isoformat()

        # Synchronous save for guaranteed persistence before rerun
        from alerts.persistent_kv import kv_set
        kv_set(_FEAR_KEY, data)
    except Exception as e:
        st.error(f"Persistence error: {str(e)}")


@st.cache_data(ttl=900, show_spinner=False)
def _calculate_web_sentiment() -> float:
    """Analyze recent news to derive a 'media fear' score (1-5)."""
    try:
        from ui.news_ticker import fetch_headlines
        articles = fetch_headlines()
        if not articles:
            return 2.5
        fear_keywords = {
            "outbreak": 0.5, "deadly": 0.8, "fatality": 1.0, "death": 0.8,
            "emergency": 0.6, "spread": 0.4, "evacuated": 0.5, "quarantine": 0.7,
            "alarm": 0.6, "critical": 0.7, "risk": 0.4, "confirmed": 0.3,
            "threat": 0.6, "scramble": 0.5, "warning": 0.5
        }
        total_score = 0.0
        relevant_count = 0
        for art in articles[:50]:
            text = (art.get("title", "") + " " + art.get("summary", "")).lower()
            article_score = 1.0
            for kw, weight in fear_keywords.items():
                if kw in text:
                    article_score += weight
            total_score += min(article_score, 5.0)
            relevant_count += 1
        return round(total_score / relevant_count, 2) if relevant_count > 0 else 2.5
    except Exception:
        return 2.5


def _calculate_fear_average() -> tuple[float, int, str, str, str, float]:
    """Calculate average fear level blending user votes and web sentiment."""
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
        mode="gauge+number",
        value=avg_fear,
        number={"suffix": "/5", "font": {"size": 52, "color": "#f8fafc", "family": "monospace"}},
        gauge={
            "axis": {"range": [1, 5], "tickwidth": 1,
                     "tickcolor": "#475569", "tickfont": {"color": "#94a3b8", "size": 10}},
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": "rgba(27,46,69,0.6)",
            "borderwidth": 0,
            "steps": [
                {"range": [1, 2], "color": "rgba(34,197,94,0.12)"},
                {"range": [2, 3], "color": "rgba(245,158,11,0.12)"},
                {"range": [3, 4], "color": "rgba(239,68,68,0.12)"},
                {"range": [4, 5], "color": "rgba(153,27,27,0.18)"},
            ],
            "threshold": {
                "line": {"color": "#ffffff", "width": 3},
                "thickness": 0.85,
                "value": avg_fear,
            },
        },
        title={"text": "PUBLIC FEAR SCORE", "font": {"size": 13, "color": "#94a3b8", "family": "monospace"}},
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={"color": "#f8fafc"}, margin=dict(l=20, r=20, t=30, b=10), height=280)
    return fig


@st.cache_data(ttl=60, show_spinner=False)
def _build_sentiment_trend(history: list[dict[str, Any]]) -> go.Figure:
    if not history:
        return go.Figure()
    dates = [datetime.fromisoformat(p["timestamp"]) for p in history]
    user_scores = [p.get("user_score", p.get("score", 2.5)) for p in history]
    web_scores = [p.get("web_score", p.get("score", 2.5)) for p in history]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=user_scores, name="User Consensus", mode="lines",
        line=dict(color="#00f5ff", width=4, shape="spline"),
        fill="tozeroy", fillcolor="rgba(0,245,255,0.05)"
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=web_scores, name="Web Sentiment", mode="lines",
        line=dict(color="#a78bfa", width=2, shape="spline", dash="dot")
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=40, t=10, b=10), height=140,
        xaxis=dict(visible=False), yaxis=dict(visible=True, range=[0.5, 5.5]),
        showlegend=False
    )
    return fig


def render_fear_index() -> None:
    avg_fear, vote_count, label, desc, color, web_sentiment = _calculate_fear_average()
    live_fear = round(avg_fear, 2)
    log_sentiment_snapshot(avg_fear, web_sentiment)
    community = get_community_data()

    if "user_id" not in st.session_state:
        browser_info = str(st.session_state) + str(hash(str(datetime.utcnow().date())))
        user_hash = hashlib.md5(browser_info.encode()).hexdigest()[:12]
        st.session_state.user_id = f"user_{user_hash}"
    user_id = st.session_state.user_id

    if "user_voted_today" not in st.session_state:
        data = _load_fear_data()
        st.session_state.user_voted_today = any(
            v.get("user_id") == user_id and
            v.get("timestamp", "").startswith(datetime.utcnow().strftime("%Y-%m-%d"))
            for v in data.get("votes", [])
        )
    user_voted_today = st.session_state.user_voted_today

    html_header = f"""
<div style="background:rgba(15, 23, 42, 0.6); border: 1px solid {color}44; border-radius: 10px; padding: 0.8rem 1.2rem; margin-bottom: 0.8rem; backdrop-filter: blur(10px);">
<div style="display:flex; align-items:center; gap: 1.5rem; flex-wrap:wrap;">
<div style="flex-shrink:0;">
<p style="color:#94a3b8; font-size:0.65rem; font-weight:800; letter-spacing:0.1em; margin:0; font-family:monospace;">📡 FEAR INDEX</p>
<h2 style="margin:0; font-size:1.8rem !important; font-weight:950; color:white !important; letter-spacing:-0.03em;">{label.upper()}</h2>
</div>
<div style="background:{color}15; border:1px solid {color}; border-radius:6px; padding:0.3rem 0.8rem; text-align:center;">
<p style="color:{color}; font-size:1.5rem; font-weight:900; margin:0; font-family:monospace;">{live_fear:.2f}</p>
<p style="color:#94a3b8; font-size:0.5rem; font-weight:800; margin:0; text-transform:uppercase;">SCORE</p>
</div>
</div>
</div>
"""
    st.markdown(html_header, unsafe_allow_html=True)
    
    st.plotly_chart(_build_sentiment_trend(community["history"]), use_container_width=True, config={"displayModeBar": False})

    col_gauge, col_dist = st.columns([1, 1.6])
    with col_gauge:
        st.plotly_chart(_build_fear_gauge(live_fear, color), use_container_width=True, config={"displayModeBar": False})

    with col_dist:
        icons = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴", 5: "💀"}
        slider_options = [FEAR_LEVELS[i]["label"].upper() for i in range(1, 6)]
        
        st.markdown(
            """
            <style>
            div[data-testid="stSelectSlider"] { padding: 1rem 0.5rem !important; }
            .report-btn > div.stButton > button {
                background: linear-gradient(135deg, #00b4d8, #0077b6) !important;
                border: none !important; border-radius: 8px !important;
                height: 45px !important; font-weight: 950 !important;
                box-shadow: 0 4px 15px rgba(0,180,216,0.4) !important;
            }
            </style>
            <div style="margin-bottom: 1rem; border-bottom: 1px solid rgba(56,189,248,0.3); padding-bottom: 0.6rem; display:flex; justify-content:space-between; align-items:center;">
                <p style='color:#38bdf8; font-size:0.8rem; font-weight:900; margin:0; letter-spacing:0.15em;'>📡 TACTICAL SENTIMENT INPUT</p>
            </div>
            """, unsafe_allow_html=True
        )

        if not user_voted_today:
            selected_label = st.select_slider(
                "SELECT CURRENT FEAR LEVEL:",
                options=slider_options,
                value=FEAR_LEVELS[max(1, min(5, int(round(live_fear))))]["label"].upper(),
                key="fear_selector_slider"
            )
            selected_id = [i for i, v in FEAR_LEVELS.items() if v["label"].upper() == selected_label][0]
            st.markdown(f"<div style='text-align:center; margin:1rem 0; color:{FEAR_LEVELS[selected_id]['color']}; font-weight:900; font-size:1.2rem;'>{icons[selected_id]} {selected_label}</div>", unsafe_allow_html=True)
            
            st.markdown('<div class="report-btn">', unsafe_allow_html=True)
            if st.button("REPORT SENTIMENT", use_container_width=True):
                _save_fear_vote(selected_id, user_id)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<div style="background:rgba(34,197,94,0.1); border-left:4px solid #22c55e; border-radius:4px; padding:1.2rem; text-align:center;">'
                '<p style="color:#22c55e; font-size:1rem; font-weight:950; margin:0;">✓ SENTIMENT ANCHORED</p>'
                '</div>', unsafe_allow_html=True
            )
