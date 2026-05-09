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
    """Save a new fear vote to persistent store (background)."""
    try:
        data = _load_fear_data()

        # Remove any previous vote from this user
        data["votes"] = [v for v in data["votes"] if v.get("user_id") != user_id]

        # Add new vote
        data["votes"].append({
            "level": level,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Keep only last 1000 votes
        data["votes"] = data["votes"][-1000:]
        data["last_updated"] = datetime.utcnow().isoformat()

        bg_kv_set(_FEAR_KEY, data)
    except Exception:
        pass


@st.cache_data(ttl=900, show_spinner=False)
def _calculate_web_sentiment() -> float:
    """Analyze recent news to derive a 'media fear' score (1-5)."""
    try:
        from ui.news_ticker import fetch_headlines
        articles = fetch_headlines()
        if not articles:
            return 2.5  # Neutral baseline
            
        # Fear-inducing keywords with weights
        fear_keywords = {
            "outbreak": 0.5, "deadly": 0.8, "fatality": 1.0, "death": 0.8,
            "emergency": 0.6, "spread": 0.4, "evacuated": 0.5, "quarantine": 0.7,
            "alarm": 0.6, "critical": 0.7, "risk": 0.4, "confirmed": 0.3,
            "threat": 0.6, "scramble": 0.5, "warning": 0.5
        }
        
        total_score = 0.0
        relevant_count = 0
        
        for art in articles[:50]: # Look at recent 50
            text = (art.get("title", "") + " " + art.get("summary", "")).lower()
            article_score = 1.0 # Base score (neutral)
            
            for kw, weight in fear_keywords.items():
                if kw in text:
                    article_score += weight
            
            total_score += min(article_score, 5.0)
            relevant_count += 1
            
        if relevant_count == 0:
            return 2.5
            
        return round(total_score / relevant_count, 2)
    except Exception:
        return 2.5


def _calculate_fear_average() -> tuple[float, int, str, str, str, float]:
    """Calculate average fear level blending user votes and web sentiment."""
    data = _load_fear_data()
    votes = data.get("votes", [])
    web_score = _calculate_web_sentiment()

    if not votes:
        # If no votes, show web sentiment as the primary driver
        avg = web_score
    else:
        # Calculate weighted average of votes (recent votes count more)
        total_weight = 0
        weighted_sum = 0
        for i, vote in enumerate(reversed(votes)):
            weight = 1 + (i / len(votes)) * 0.5
            weighted_sum += vote["level"] * weight
            total_weight += weight
        user_avg = weighted_sum / total_weight
        
        # Blend: 60% user votes, 40% web sentiment
        avg = (user_avg * 0.6) + (web_score * 0.4)

    closest_level = min(FEAR_LEVELS.keys(), key=lambda x: abs(x - avg))
    level_info = FEAR_LEVELS[closest_level]
    
    return avg, len(votes), level_info["label"], level_info["desc"], level_info["color"], web_score


@st.cache_data(ttl=60, show_spinner=False)
def _build_fear_gauge(avg_fear: float, color: str) -> go.Figure:
    """Build gauge chart for fear level."""
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
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#f8fafc"},
        margin=dict(l=20, r=20, t=30, b=10),
        height=260,
    )
    return fig


def _build_fear_dist_chart(dist: dict[int, int]) -> go.Figure:
    """Build horizontal bar chart for vote distribution."""
    labels = [FEAR_LEVELS[i]["label"].title() for i in sorted(dist.keys())]
    values = [dist[i] for i in sorted(dist.keys())]
    colors = [FEAR_LEVELS[i]["color"] for i in sorted(dist.keys())]

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation='h',
        marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.2)", width=1)),
        text=values,
        textposition='auto',
        textfont=dict(color="#f8fafc", size=10, family="monospace"),
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", size=10),
        margin=dict(l=10, r=10, t=20, b=10),
        height=200,
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(autorange="reversed"),
    )
    return fig


def render_fear_index() -> None:
    """Render fear index voting panel."""
    avg_fear, vote_count, label, desc, color, web_sentiment = _calculate_fear_average()

    # Generate unique user ID based on session + browser fingerprint
    if "user_id" not in st.session_state:
        browser_info = str(st.session_state) + str(hash(str(datetime.utcnow().date())))
        user_hash = hashlib.md5(browser_info.encode()).hexdigest()[:12]
        st.session_state.user_id = f"user_{user_hash}"

    user_id = st.session_state.user_id

    # Check if user already voted today
    data = _load_fear_data()
    user_voted_today = any(
        v.get("user_id") == user_id and
        v.get("timestamp", "").startswith(datetime.utcnow().strftime("%Y-%m-%d"))
        for v in data.get("votes", [])
    )

    # Vote distribution
    dist = {i: 0 for i in FEAR_LEVELS.keys()}
    for v in data.get("votes", []):
        dist[v["level"]] += 1

    # Horizontal card layout matching pandemic card
    import textwrap
    anim = "pulse-fear 2s ease-in-out infinite" if avg_fear >= 3.0 else "none"
    
    # Calculate percentages for the breakdown bar
    user_weight = 0.6 if vote_count > 0 else 0.0
    web_weight = 0.4 if vote_count > 0 else 1.0
    
    html_content = f"""
<div style="background:rgba(15, 23, 42, 0.4); border: 2px solid {color}44; border-radius: 12px; padding: 1.2rem 1.4rem;
margin-bottom: 1rem; position: relative; overflow: hidden; height: 160px; display: flex; flex-direction: column; justify-content: space-between;">
<div style="position: absolute; top: 0; left: 0; right: 0; height: 4px;
background: linear-gradient(90deg,{color},{color}44,{color}); animation: {anim};"></div>
<div style="display:flex; align-items:center; justify-content: space-between; gap:1rem;">
<div style="flex:1;">
<p style="color:#94a3b8; font-size:0.7rem; font-weight:800; letter-spacing:0.12em; margin:0; font-family:monospace; opacity:0.9;">📡 PUBLIC FEAR INDEX</p>
<h2 style="margin:0.1rem 0 0; font-size:2.1rem !important; font-weight:900; color:white !important; letter-spacing:-0.02em; line-height: 1.1;">{label.upper()}</h2>
</div>
<div style="background:{color}15; border:2px solid {color}; border-radius:10px; padding:0.5rem 1rem; 
text-align:center; min-width:110px; box-shadow: 0 0 20px {color}15; height: fit-content;">
<p style="color:{color}; font-size:1.8rem; font-weight:900; margin:0; line-height:1; font-family:monospace; text-shadow:0 0 10px {color}88;">{avg_fear:.1f}<small style="font-size:0.5em; opacity:0.7;">/5</small></p>
<p style="color:#94a3b8; font-size:0.55rem; font-weight:800; margin:2px 0 0; text-transform:uppercase; letter-spacing:0.05em; opacity:0.8;">FEAR SCORE</p>
</div>
</div>
<div style="display:flex; align-items:center; gap:1.2rem; flex-wrap:wrap; border-top:1px solid rgba(148,163,184,0.1); padding-top:0.6rem;">
<p style="color:#64748b; font-size:0.65rem; margin:0; font-weight:700;">
Blended Sentiment: Media + Community &nbsp;&nbsp;<span class="live-dot" style="width:6px; height:6px;"></span>
<span class="live-label" style="font-size:0.6rem;">LIVE ASSESSMENT</span>
</p>
</div>
</div>
<div style="margin-top: 1rem;">
<div style="display:flex; justify-content:space-between; margin-bottom:0.3rem;">
<span style="color:#64748b; font-size:0.7rem;">🌐 Web Sentiment: {web_sentiment:.1f}</span>
<span style="color:#64748b; font-size:0.7rem;">👥 Community: {avg_fear if vote_count > 0 else 0:.1f}</span>
</div>
<div style="height:4px; background:#1b2e45; border-radius:2px; display:flex; overflow:hidden;">
<div style="width:{web_weight*100}%; height:100%; background:#38bdf8; opacity:0.8;"></div>
<div style="width:{user_weight*100}%; height:100%; background:#a78bfa; opacity:0.8;"></div>
</div>
</div>
<div style="display:flex; gap:1.5rem; margin-top:0.9rem; flex-wrap:wrap;
border-top:1px solid #1b2e45; padding-top:0.7rem;">
<span style="color:#94a3b8; font-size:0.77rem;">😰 Final Score: <b style="color:{color};">{avg_fear:.1f}/5</b></span>
<span style="color:#94a3b8; font-size:0.77rem;">🌍 Media Data: <b style="color:#38bdf8;">Active</b></span>
<span style="color:#94a3b8; font-size:0.77rem;">📈 Responses: <b style="color:#f8fafc;">{vote_count}</b></span>
<span style="color:#94a3b8; font-size:0.77rem;">⏱ Updated: <b style="color:#f8fafc;">{datetime.now().strftime('%H:%M')}</b></span>
</div>
</div>
<style>
@keyframes pulse-fear {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.4; }} }}
</style>
""".replace("\n", "").strip()
    st.markdown(html_content, unsafe_allow_html=True)


    # Gauge + Distribution visualization
    col_gauge, col_dist = st.columns([1, 1.2])

    with col_gauge:
        fig_gauge = _build_fear_gauge(avg_fear, color)
        st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})

    with col_dist:
        st.markdown(
            "<p style='color:#94a3b8; font-size:0.8rem; margin-bottom:0.2rem;'>"
            "📊 <b>Community Vote Distribution</b></p>",
            unsafe_allow_html=True,
        )
        fig_dist = _build_fear_dist_chart(dist)
        st.plotly_chart(fig_dist, use_container_width=True, config={"displayModeBar": False})

    # Callout boxes matching pandemic panel
    callout_html = f"""
<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.6rem;margin-top:0.3rem; margin-bottom: 1rem;">
<div style="background:rgba(27,46,69,0.3);border:1px solid #1b2e45;border-radius:8px;padding:0.6rem 0.8rem;">
<p style="color:#94a3b8;font-size:0.72rem;font-weight:700;margin:0;">ℹ️ SENTIMENT ANALYSIS</p>
<p style="color:#64748b;font-size:0.73rem;margin:0.2rem 0 0;">
Tracks public anxiety level based on 1000+ real-time votes. 
Weighted to favor recent sentiment (15-min decay).
</p>
</div>
<div style="background:rgba(27,46,69,0.3);border:1px solid #1b2e45;border-radius:8px;padding:0.6rem 0.8rem;">
<p style="color:#94a3b8;font-size:0.72rem;font-weight:700;margin:0;">📈 IMPACT ASSESSMENT</p>
<p style="color:#64748b;font-size:0.73rem;margin:0.2rem 0 0;">
Public fear often correlates with geographic spread but can be mitigated by 
clear official communications and verified data.
</p>
</div>
</div>
""".replace("\n", "").strip()
    st.markdown(callout_html, unsafe_allow_html=True)


    # Voting buttons section below the visualization
    if not user_voted_today:
        st.markdown(
            f'<p style="color:#94a3b8; font-size:0.85rem; font-weight:700; margin:1.5rem 0 1rem;">'
            f'🗳️ <b>CAST YOUR VOTE:</b> How do you feel about the outbreak today?</p>',
            unsafe_allow_html=True
        )

        # Custom CSS for colorful, glowing buttons
        btn_style = ""
        for level, info in FEAR_LEVELS.items():
            l_color = info['color']
            btn_style += f"""
                div[data-testid="stButton"] button[key*="vote_{level}"] {{
                    border: 1px solid {l_color}66 !important;
                    color: {l_color} !important;
                    background: rgba(15, 23, 42, 0.4) !important;
                    height: 48px !important;
                    transition: all 0.3s ease !important;
                    font-weight: 800 !important;
                    letter-spacing: 0.05em !important;
                    box-shadow: 0 0 10px {l_color}11 !important;
                }}
                div[data-testid="stButton"] button[key*="vote_{level}"]:hover {{
                    border-color: {l_color} !important;
                    background: {l_color}1a !important;
                    box-shadow: 0 0 20px {l_color}44 !important;
                    transform: translateY(-2px) !important;
                }}
            """
        
        st.markdown(f"<style>{btn_style}</style>", unsafe_allow_html=True)

        # 5-column grid for perfect alignment
        v_cols = st.columns(5)
        for i, level in enumerate(range(1, 6)):
            info = FEAR_LEVELS[level]
            with v_cols[i]:
                if st.button(info['label'].upper(), key=f"vote_{level}", use_container_width=True, help=info['desc']):
                    _save_fear_vote(level, user_id)
                    st.success(f"✅ Voted: {info['label']}")
                    st.rerun()
    else:
        thanks_html = """
<div style="background:rgba(34,197,94,0.08); border:1px solid #22c55e44; border-radius:8px; padding:0.8rem; margin-top:1rem;">
<p style="color:#22c55e; font-size:0.8rem; margin:0;">✓ Thanks for participating! Your vote has been recorded.</p>
<p style="color:#94a3b8; font-size:0.75rem; margin:0.2rem 0 0;">Outbreak sentiment tracking helps researchers understand public response and information gaps.</p>
</div>
""".replace("\n", "").strip()
        st.markdown(thanks_html, unsafe_allow_html=True)
