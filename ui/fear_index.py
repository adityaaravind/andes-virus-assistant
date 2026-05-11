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
    data = get_persisted_value(_FEAR_KEY)
    return data if data else {"votes": [], "last_updated": datetime.utcnow().isoformat()}

def _save_fear_vote(level: int, user_id: str) -> None:
    st.session_state.user_voted_today = True
    try:
        data = _load_fear_data()
        data["votes"] = [v for v in data["votes"] if v.get("user_id") != user_id]
        data["votes"].append({
            "level": level,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
        data["votes"] = data["votes"][-2000:]
        data["last_updated"] = datetime.utcnow().isoformat()
        from alerts.persistent_kv import kv_set
        kv_set(_FEAR_KEY, data)
    except Exception: pass

def _calculate_web_sentiment() -> float:
    try:
        from ui.news_ticker import fetch_headlines
        articles = fetch_headlines()
        if not articles: return 2.5
        score = 1.0
        # Simple sentiment logic
        text = " ".join([a['title'] for a in articles[:10]]).lower()
        if "death" in text or "fatality" in text: score += 1.5
        if "outbreak" in text or "emergency" in text: score += 1.0
        return min(5.0, score + (len(articles) * 0.05))
    except Exception: return 2.5

def _calculate_fear_average() -> tuple[float, int, str, str, str, float]:
    data = _load_fear_data()
    votes = data.get("votes", [])
    web_score = _calculate_web_sentiment()
    if not votes: avg = web_score
    else:
        user_avg = sum(v["level"] for v in votes) / len(votes)
        avg = (user_avg * 0.6) + (web_score * 0.4)
    closest = min(FEAR_LEVELS.keys(), key=lambda x: abs(x - avg))
    info = FEAR_LEVELS[closest]
    return avg, len(votes), info["label"], info["desc"], info["color"], web_score

@st.cache_data(ttl=60, show_spinner=False)
def _build_fear_gauge(avg_fear: float, color: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=avg_fear,
        number={"suffix": "/5", "font": {"size": 40, "color": "#f8fafc"}},
        gauge={"axis": {"range": [1, 5]}, "bar": {"color": color}, "bgcolor": "rgba(0,0,0,0.2)"}
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=180, margin=dict(l=10, r=10, t=10, b=10))
    return fig

@st.cache_data(ttl=60, show_spinner=False)
def _build_sentiment_trend(history: list[dict[str, Any]]) -> go.Figure:
    if not history: return go.Figure()
    dates = [datetime.fromisoformat(p["timestamp"]) for p in history]
    scores = [p.get("score", 2.5) for p in history]
    fig = go.Figure(go.Scatter(x=dates, y=scores, mode="lines", line=dict(color="#00f5ff", width=3, shape="spline"), fill="tozeroy"))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=100, margin=dict(l=10, r=10, t=5, b=5), xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig

def render_fear_index() -> None:
    avg_fear, vote_count, label, desc, color, web_sentiment = _calculate_fear_average()
    log_sentiment_snapshot(avg_fear, web_sentiment)
    community = get_community_data()

    if "user_id" not in st.session_state:
        st.session_state.user_id = f"user_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
    
    if "user_voted_today" not in st.session_state:
        data = _load_fear_data()
        st.session_state.user_voted_today = any(v.get("user_id") == st.session_state.user_id and v.get("timestamp", "").startswith(datetime.utcnow().strftime("%Y-%m-%d")) for v in data.get("votes", []))

    st.markdown(f"""
        <div style="background:rgba(15,23,42,0.6); border-radius:12px; padding:1.2rem; border-left:4px solid {color}; margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div><p style="color:#94a3b8; font-size:0.7rem; font-weight:800; margin:0;">FEAR INDEX</p>
                <h2 style="margin:0; font-size:1.6rem; color:white;">{label.upper()}</h2></div>
                <div style="text-align:right;"><p style="color:{color}; font-size:1.8rem; font-weight:900; margin:0;">{avg_fear:.2f}</p></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1: st.plotly_chart(_build_fear_gauge(avg_fear, color), use_container_width=True, config={"displayModeBar": False})
    with col2: st.plotly_chart(_build_sentiment_trend(community["history"]), use_container_width=True, config={"displayModeBar": False})

    # --- TACTICAL SEGMENTED SELECTOR (v1.6.0) ---
    st.markdown("""
        <style>
        .stSelectSlider [data-testid="stMarkdownContainer"] p { font-size: 0.6rem !important; font-weight: 800 !important; color: #64748b !important; }
        div[data-testid="stSelectSlider"] { padding-top: 0 !important; }
        </style>
        <div style="margin-top: 1rem; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 1rem;">
            <p style='color:#00b4d8; font-size:0.75rem; font-weight:950; text-transform:uppercase; letter-spacing:0.15em; margin-bottom: 0.2rem;'>🚨 YOUR INPUT NEEDED: HOW SAFE DO YOU FEEL?</p>
            <p style='color:#94a3b8; font-size:0.6rem; margin-bottom: 1rem;'>Select your local anxiety level below. Your participation calibrates global risk intelligence.</p>
        </div>
    """, unsafe_allow_html=True)

    if not st.session_state.user_voted_today:
        options = ["CALM", "CONCERNED", "WORRIED", "FEARFUL", "PANICKED"]
        icons = ["🟢", "🟡", "🟠", "🔴", "💀"]
        
        # Use a more compact select_slider
        selected = st.select_slider(
            "SELECT LEVEL",
            options=options,
            value=options[max(0, min(4, int(round(avg_fear))-1))],
            label_visibility="collapsed",
            key="fear_selector_final"
        )
        
        # Mapping back to ID
        selected_id = options.index(selected) + 1
        
        # Dynamic Color/Icon feedback
        info = FEAR_LEVELS[selected_id]
        st.markdown(f"<div style='text-align:center; padding:10px; border-radius:8px; background:{info['color']}15; border:1px solid {info['color']}44; color:{info['color']}; font-weight:900; font-size:0.9rem;'>{icons[selected_id-1]} {selected} LEVEL SELECTED</div>", unsafe_allow_html=True)
        
        # The user wants "easier to just select". We still need a trigger in Streamlit or it will vote on every slide.
        # However, I can make the button smaller and more like a "SUBMIT DATA" toggle.
        if st.button("CONFIRM & LOG REPORT", use_container_width=True, type="primary"):
            _save_fear_vote(selected_id, st.session_state.user_id)
            st.rerun()
    else:
        st.success("SENTIMENT ANCHORED")
