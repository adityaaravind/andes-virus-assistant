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
    """Save a new fear vote to persistent store (background)."""
    # FAST REGISTRATION: Update session state immediately before background IO
    st.session_state.fear_slider_input = level
    st.session_state.user_voted_today = True
    
    try:
        data = _load_fear_data()
        data["votes"] = [v for v in data["votes"] if v.get("user_id") != user_id]
        data["votes"].append({
            "level": level,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
        data["votes"] = data["votes"][-1000:]
        data["last_updated"] = datetime.utcnow().isoformat()
        # Fire and forget
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
    """Advanced dual-stream sentiment tracker with glowing neon aesthetics."""
    if not history:
        return go.Figure()
        
    dates = [datetime.fromisoformat(p["timestamp"]) for p in history]
    
    # Handle both old single-score data and new dual-score data
    user_scores = [p.get("user_score", p.get("score", 2.5)) for p in history]
    web_scores = [p.get("web_score", p.get("score", 2.5)) for p in history]

    fig = go.Figure()

    # 1. USER CONSENSUS (Glowing Cyan)
    fig.add_trace(go.Scatter(
        x=dates, y=user_scores,
        name="User Consensus",
        mode="lines",
        line=dict(color="#00f5ff", width=4, shape="spline"),
        fill="tozeroy",
        fillcolor="rgba(0,245,255,0.05)",
        hovertemplate="User: %{y:.2f}<extra></extra>"
    ))

    # 2. WEB SENTIMENT (Neon Purple)
    fig.add_trace(go.Scatter(
        x=dates, y=web_scores,
        name="Web Sentiment",
        mode="lines",
        line=dict(color="#a78bfa", width=2, shape="spline", dash="dot"),
        hovertemplate="Web: %{y:.2f}<extra></extra>"
    ))
    
    # 3. LIVE INDICATOR (Green dot at current point)
    if dates:
        fig.add_trace(go.Scatter(
            x=[dates[-1]], y=[user_scores[-1]],
            mode="markers+text",
            marker=dict(color="#22c55e", size=10, line=dict(color="#ffffff", width=2)),
            text=[" LIVE"],
            textposition="middle right",
            textfont=dict(color="#22c55e", size=10, family="monospace"),
            showlegend=False
        ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=40, t=10, b=10),
        height=140,
        xaxis=dict(visible=False, showgrid=False),
        yaxis=dict(
            visible=True, range=[0.5, 5.5], showgrid=True, gridcolor="rgba(255,255,255,0.05)",
            tickmode="array", tickvals=[1, 3, 5], ticktext=["CALM", "WARN", "CRIT"],
            tickfont=dict(color="#475569", size=8)
        ),
        showlegend=False,
        hovermode="x unified"
    )
    return fig


def render_fear_index() -> None:
    avg_fear, vote_count, label, desc, color, web_sentiment = _calculate_fear_average()
    live_fear = round(avg_fear, 2)
    
    # PHASE 2: Log current dual-stream state
    log_sentiment_snapshot(avg_fear, web_sentiment)
    community = get_community_data()

    if "user_id" not in st.session_state:
        browser_info = str(st.session_state) + str(hash(str(datetime.utcnow().date())))
        user_hash = hashlib.md5(browser_info.encode()).hexdigest()[:12]
        st.session_state.user_id = f"user_{user_hash}"
    user_id = st.session_state.user_id

    # OPTIMIZED CHECK: Prioritize session state over disk read
    if "user_voted_today" not in st.session_state:
        data = _load_fear_data()
        st.session_state.user_voted_today = any(
            v.get("user_id") == user_id and
            v.get("timestamp", "").startswith(datetime.utcnow().strftime("%Y-%m-%d"))
            for v in data.get("votes", [])
        )
    user_voted_today = st.session_state.user_voted_today

    anim = "pulse-fear 2s ease-in-out infinite" if live_fear >= 3.0 else "none"
    
    html_header = f"""
<div style="background:rgba(15, 23, 42, 0.6); border: 1px solid {color}44; border-radius: 10px; padding: 0.8rem 1.2rem;
margin-bottom: 0.8rem; position: relative; overflow: hidden; min-height: 120px; display: flex; flex-direction: column; justify-content: space-between; backdrop-filter: blur(10px);">
<div style="position: absolute; top: 0; left: 0; right: 0; height: 3px;
background: linear-gradient(90deg,{color},{color}44,{color}); animation: {anim};"></div>
<div style="display:flex; align-items:center; gap: 1.5rem; flex-wrap:wrap;">
<div style="flex-shrink:0;">
<p style="color:#94a3b8; font-size:0.65rem; font-weight:800; letter-spacing:0.1em; margin:0; font-family:monospace; opacity:0.8;">📡 FEAR INDEX</p>
<h2 style="margin:0; font-size:1.8rem !important; font-weight:950; color:white !important; letter-spacing:-0.03em; line-height: 1;">{label.upper()}</h2>
</div>
<div style="background:{color}15; border:1px solid {color}; border-radius:6px; padding:0.3rem 0.8rem; 
text-align:center; min-width:90px; box-shadow: 0 0 15px {color}15; height: fit-content;">
<p style="color:{color}; font-size:1.5rem; font-weight:900; margin:0; line-height:1; font-family:monospace; text-shadow:0 0 8px {color}88;">{live_fear:.2f}<small style="font-size:0.5em; opacity:0.7;">/5</small></p>
<p style="color:#94a3b8; font-size:0.5rem; font-weight:800; margin:0; text-transform:uppercase; opacity:0.8;">SCORE</p>
</div>
</div>
<div style="display:flex; gap:0.9rem; flex-wrap:wrap; border-top:1px solid rgba(255,255,255,0.05); padding-top:0.4rem;">
<span style="color:#94a3b8; font-size:0.6rem;">🌐 Web: <b style="color:white;">{web_sentiment:.1f}</b></span>
<span style="color:#94a3b8; font-size:0.6rem;">👥 User: <b style="color:white;">{avg_fear:.1f}</b></span>
<span style="color:#94a3b8; font-size:0.6rem;">📈 Votes: <b style="color:white;">{vote_count}</b></span>
<span style="color:#64748b; font-size:0.6rem; font-weight:700; text-transform:uppercase;">Live <span class="live-dot" style="width:5px; height:5px; margin-left:3px;"></span></span>
</div>
<div style="margin-top: 0.8rem; margin-bottom: -0.5rem; opacity: 0.8;">
    <p style="color:#64748b; font-size:0.5rem; font-weight:800; margin:0 0 2px 0; text-transform:uppercase; letter-spacing:0.05em;">7-Day Sentiment Velocity</p>
</div>
</div>
""".replace("\n", "").strip()
    st.markdown(html_header, unsafe_allow_html=True)
    
    # Sparkline chart (Phase 2)
    fig_trend = _build_sentiment_trend(community["history"])
    st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})

    col_gauge, col_dist = st.columns([1, 1.6])
    with col_gauge:
        fig_gauge = _build_fear_gauge(live_fear, color)
        st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})

    with col_dist:
        level_int = max(1, min(5, int(round(live_fear))))
        if "fear_slider_input" in st.session_state:
            level_int = int(st.session_state.fear_slider_input)

        icons = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴", 5: "💀"}
        
        st.markdown(
            """
            <style>
            /* 1. ANIMATIONS */
            @keyframes tile-glow {
                0% { box-shadow: 0 0 5px rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.1); }
                50% { box-shadow: 0 0 20px rgba(56,189,248,0.15); border-color: rgba(56,189,248,0.3); }
                100% { box-shadow: 0 0 5px rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.1); }
            }
            @keyframes text-blink {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.7; transform: scale(0.98); }
            }
            @keyframes pulse-active {
                0% { box-shadow: 0 0 10px var(--t-color)44; }
                50% { box-shadow: 0 0 30px var(--t-color)88; }
                100% { box-shadow: 0 0 10px var(--t-color)44; }
            }

            /* 2. LAYOUT RESET */
            div[data-testid="stHorizontalBlock"] {
                display: flex !important;
                flex-wrap: wrap !important;
                justify-content: space-between !important;
                gap: 10px !important;
            }

            div[data-testid="column"] {
                flex: 1 1 18% !important;
                min-width: 0 !important;
                position: relative;
                height: 90px !important;
            }

            /* 3. TACTICAL BUTTONS */
            .premium-tile {
                background: linear-gradient(135deg, rgba(15, 23, 42, 0.8), rgba(30, 41, 59, 0.8));
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                width: 100%;
                height: 100%;
                position: absolute;
                top: 0;
                left: 0;
                pointer-events: none;
                z-index: 1;
                animation: tile-glow 3s ease-in-out infinite;
            }

            .premium-tile.active {
                background: radial-gradient(circle at center, var(--t-color)44 0%, rgba(15, 23, 42, 0.98) 100%) !important;
                border: 2px solid var(--t-color) !important;
                animation: pulse-active 2s ease-in-out infinite !important;
                transform: translateY(-4px);
                z-index: 2;
            }

            .premium-tile.disabled { opacity: 0.2; filter: grayscale(0.8); animation: none; }
            
            .tile-icon { 
                font-size: 1.8rem; 
                margin-bottom: 4px;
                filter: drop-shadow(0 0 8px rgba(255,255,255,0.3));
            }
            .tile-label { 
                font-family: 'Inter', sans-serif; 
                font-weight: 900; 
                font-size: 0.6rem; 
                text-transform: uppercase; 
                color: #ffffff; 
                letter-spacing: 0.1em;
                text-shadow: 0 0 10px rgba(255,255,255,0.2);
            }

            /* 4. INVISIBLE BUTTON OVERLAY */
            div[data-testid="stButton"] { 
                height: 90px !important; 
                margin: 0 !important;
                position: absolute !important;
                top: 0 !important;
                left: 0 !important;
                width: 100% !important;
                z-index: 10 !important;
            }
            div[data-testid="stButton"] button {
                background: transparent !important;
                border: none !important;
                height: 90px !important;
                width: 100% !important;
                color: transparent !important;
                border-radius: 12px !important;
            }
            
            /* REACTIVE FEEDBACK */
            div[data-testid="stButton"] button:hover + .premium-tile {
                background: rgba(255,255,255,0.12) !important;
                border-color: #38bdf8 !important;
                transform: translateY(-6px);
                box-shadow: 0 10px 30px rgba(56,189,248,0.2);
            }
            div[data-testid="stButton"] button:active + .premium-tile {
                transform: scale(0.92) translateY(0);
                background: rgba(56,189,248,0.2) !important;
            }

            /* 5. MOBILE OVERRIDE */
            @media (max-width: 600px) {
                div[data-testid="stHorizontalBlock"] { flex-direction: column !important; gap: 12px !important; }
                div[data-testid="column"] { flex: 1 1 100% !important; height: 70px !important; width: 100% !important; }
                .premium-tile { 
                    flex-direction: row !important; 
                    height: 70px !important; 
                    justify-content: flex-start !important;
                    padding: 0 25px !important;
                    gap: 20px;
                    animation: tile-glow 2s ease-in-out infinite;
                }
                div[data-testid="stButton"] { height: 70px !important; }
                div[data-testid="stButton"] button { height: 70px !important; }
                .tile-icon { font-size: 2rem; margin: 0; }
                .tile-label { font-size: 0.9rem; letter-spacing: 0.2em; }
                .premium-tile.active { transform: scale(1.02) !important; }
            }
            </style>
            <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:1.5rem; border-bottom:2px solid rgba(56,189,248,0.2); padding-bottom:0.8rem;">
                <p style='color:#38bdf8; font-size:0.75rem; font-weight:900; margin:0; letter-spacing:0.15em; text-transform:uppercase; text-shadow:0 0 10px rgba(56,189,248,0.5);'>📡 SENTIMENT INPUT</p>
                <p style='color:#fbbf24; font-size:0.6rem; font-weight:950; margin:0; letter-spacing:0.08em; animation: text-blink 1.5s ease-in-out infinite; text-shadow:0 0 12px rgba(251,191,36,0.6);'>● ACTION REQUIRED: ANALYZE & SUBMIT</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        cols = st.columns(5)
        for i, level_id in enumerate(range(1, 6)):
            info = FEAR_LEVELS[level_id]
            is_active = (level_id == level_int)
            with cols[i]:
                # THE FIX: Put button BEFORE tile in DOM so we can use '+' selector for hover effects
                if st.button(" ", key=f"v16_btn_{level_id}", disabled=user_voted_today):
                    _save_fear_vote(level_id, user_id)
                    st.rerun()
                st.markdown(f'<div class="premium-tile {"active" if is_active else ""} {"disabled" if user_voted_today and not is_active else ""}" style="--t-color: {info["color"]};"><span class="tile-icon">{icons[level_id]}</span><span class="tile-label">{info["label"].upper()}</span></div>', unsafe_allow_html=True)

        if user_voted_today:
            st.markdown(f"<div style='background:rgba(34,197,94,0.05); border:1px solid #22c55e33; border-radius:10px; padding:0.8rem; margin-top:1rem; text-align:center;'><p style='color:#22c55e; font-size:0.75rem; font-weight:950; margin:0;'>✓ SENTIMENT ANCHORED</p></div>", unsafe_allow_html=True)
        else:
            st.markdown(
                "<p style='color:#38bdf8; font-size:0.55rem; text-align:center; margin-top:1rem; font-weight:950; letter-spacing:0.03em; text-shadow: 0 0 10px rgba(56,189,248,0.4);'>"
                "⚡ TAP TILE TO VOTE — CRITICAL FOR RISK MODELING"
                "</p>", 
                unsafe_allow_html=True
            )

    callout_html = """
<style>.fear-callout-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 0.6rem; margin-top: 0.3rem; }</style>
<div class="fear-callout-grid">
<div style="background:rgba(56,189,248,0.08); border:1px solid rgba(56,189,248,0.3); border-radius:8px; padding:0.6rem 0.8rem;"><p style="color:#38bdf8; font-size:0.72rem; font-weight:700; margin:0; text-transform:uppercase;">ℹ️ SENTIMENT ANALYSIS</p><p style="color:#94a3b8; font-size:0.73rem; margin:0.2rem 0 0;">Tracks public anxiety level based on 1000+ real-time votes. Weighted to favor recent sentiment (15-min decay).</p></div>
<div style="background:rgba(167,139,250,0.08); border:1px solid rgba(167,139,250,0.3); border-radius:8px; padding:0.6rem 0.8rem;"><p style="color:#a78bfa; font-size:0.72rem; font-weight:700; margin:0; text-transform:uppercase;">📈 IMPACT ASSESSMENT</p><p style="color:#94a3b8; font-size:0.73rem; margin:0.2rem 0 0;">Public fear often correlates with geographic spread but can be mitigated by clear official communications and verified data.</p></div>
</div>
""".replace("\n", "").strip()
    st.markdown(callout_html, unsafe_allow_html=True)
