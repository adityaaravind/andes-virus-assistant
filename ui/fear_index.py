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
    """Save a new fear vote to persistent store (Synchronous for reliability)."""
    # FAST REGISTRATION: Update session state immediately
    st.session_state.fear_slider_input = level
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
        
        # --- ROBUST SMALL GRID SELECTOR (v1.4.5) ---
        st.markdown(
            """
            <style>
            /* TARGET STANDARD STREAMLIT BUTTONS */
            div.stButton > button {
                width: 100% !important;
                height: 100px !important;
                background: linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(30, 41, 59, 0.95)) !important;
                backdrop-filter: blur(12px) !important;
                border: 1px solid rgba(255, 255, 255, 0.15) !important;
                border-top: 3px solid var(--btn-color) !important;
                border-radius: 14px !important;
                color: #f8fafc !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                padding: 10px 5px !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 4px !important;
                position: relative !important;
                overflow: hidden !important;
                /* INTENSE PERSISTENT NEON GLOW */
                box-shadow: 0 4px 20px rgba(0,0,0,0.8), 0 0 15px var(--btn-color)44 !important;
            }
            
            /* LABEL FIX: Strict font sizing to prevent wrapping */
            div.stButton > button p {
                margin: 0 !important;
                line-height: 1.1 !important;
                white-space: nowrap !important;
                text-align: center !important;
                font-family: 'Inter', sans-serif !important;
                font-weight: 950 !important;
                font-size: 0.65rem !important;
                letter-spacing: 0.05em !important;
                text-transform: uppercase !important;
                /* INTENSE GLOWING TEXT */
                text-shadow: 0 0 5px var(--btn-color), 0 0 10px var(--btn-color), 0 0 15px var(--btn-color) !important;
            }

            /* EMOJI SIZE */
            div.stButton > button div[data-testid="stMarkdownContainer"] {
                font-size: 1.6rem !important;
                line-height: 1 !important;
            }

            /* MOBILE ADAPTIVE LAYOUT (2-column grid for better thumb reach) */
            @media (max-width: 600px) {
                /* FORCE GRID ON THE PARENT COLUMN CONTAINER WITH HIGHER SPECIFICITY */
                [data-testid="stAppViewContainer"] div[data-testid="stHorizontalBlock"]:has(button[key*="v23_btn_"]) {
                    display: grid !important;
                    grid-template-columns: 1fr 1fr !important;
                    gap: 0.5rem !important;
                    flex-direction: row !important;
                }
                /* Ensure columns don't force 100% width inside the grid */
                [data-testid="stAppViewContainer"] div[data-testid="stHorizontalBlock"]:has(button[key*="v23_btn_"]) > div {
                    width: 100% !important;
                    max-width: 100% !important;
                }
                
                div.stButton > button { 
                    height: 55px !important; 
                    flex-direction: row !important; 
                    gap: 10px !important;
                    justify-content: center !important;
                    padding: 5px 10px !important;
                    border-top: none !important;
                    border-left: 4px solid var(--btn-color) !important;
                    /* ADD INSET GLOW FOR INPUT BUTTON FEEL */
                    box-shadow: inset 0 0 10px var(--btn-color)22, 0 4px 15px rgba(0,0,0,0.6) !important;
                }
                div.stButton > button div[data-testid="stMarkdownContainer"] {
                    font-size: 1.2rem !important;
                }
                div.stButton > button p {
                    font-size: 0.6rem !important;
                    text-align: left !important;
                    letter-spacing: 0.02em !important;
                }
            }
            
            /* INTENSIFIED BACKLIGHT */
            div.stButton > button::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, var(--btn-color)30 0%, transparent 65%);
                opacity: 0.5;
                transition: opacity 0.3s ease;
                z-index: 0;
            }

            div.stButton > button:hover {
                background-color: rgba(30, 41, 59, 1) !important;
                border-color: var(--btn-color) !important;
                transform: translateY(-6px) !important;
                box-shadow: 0 15px 35px var(--btn-color)55, 0 0 25px var(--btn-color)44 !important;
                color: #fff !important;
            }
            
            div.stButton > button:hover::before {
                opacity: 1.0;
            }

            div.stButton > button:active {
                transform: translateY(-2px) scale(0.98) !important;
                box-shadow: 0 5px 15px var(--btn-color)44 !important;
            }
            
            /* DISABLED / VOTED STATE */
            div.stButton > button:disabled {
                opacity: 0.6 !important;
                cursor: not-allowed !important;
                filter: grayscale(0.4) !important;
                border-top-color: rgba(255,255,255,0.1) !important;
                transform: none !important;
                box-shadow: none !important;
            }

            /* BREATHING ANIMATION FOR ACTIVE */
            @keyframes neon-breath {
                0% { box-shadow: 0 0 15px var(--btn-color)33, 0 0 5px var(--btn-color)22; border-color: var(--btn-color); }
                50% { box-shadow: 0 0 40px var(--btn-color)77, 0 0 20px var(--btn-color)44; border-color: #fff; }
                100% { box-shadow: 0 0 15px var(--btn-color)33, 0 0 5px var(--btn-color)22; border-color: var(--btn-color); }
            }
            
            .active-breath > div.stButton > button {
                animation: neon-breath 2s ease-in-out infinite !important;
                border-color: var(--btn-color) !important;
                background: linear-gradient(135deg, var(--btn-color)11, rgba(15, 23, 42, 0.9)) !important;
            }

            </style>
            <div style="margin-bottom: 1.2rem; border-bottom: 1px solid rgba(56,189,248,0.3); padding-bottom: 0.6rem; display:flex; justify-content:space-between; align-items:center;">
                <p style='color:#38bdf8; font-size:0.8rem; font-weight:900; margin:0; letter-spacing:0.15em; text-transform:uppercase; text-shadow: 0 0 10px rgba(56,189,248,0.5);'>📡 TACTICAL SENTIMENT INPUT</p>
                <div style="background:rgba(251,191,36,0.1); border:1px solid #fbbf2444; border-radius:4px; padding:2px 8px;">
                    <p style='color:#fbbf24; font-size:0.5rem; font-weight:950; margin:0; letter-spacing:0.05em;'>LIVE UPLINK</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # The Small Grid: 5 columns
        cols = st.columns(5)
        for i, level_id in enumerate(range(1, 6)):
            info = FEAR_LEVELS[level_id]
            is_active = (level_id == level_int)
            
            with cols[i]:
                # Wrap in a div to pass CSS variable and apply breathing if active
                container_class = "active-breath" if user_voted_today and is_active else ""
                st.markdown(f'<div class="{container_class}" style="--btn-color: {info["color"]};">', unsafe_allow_html=True)
                
                # Use a combined label with emoji and text
                # Note: Streamlit buttons preserve newlines if rendered correctly
                btn_label = f"{icons[level_id]}\n{info['label'].upper()}"
                
                if st.button(btn_label, key=f"v23_btn_{level_id}", disabled=user_voted_today, use_container_width=True):
                    _save_fear_vote(level_id, user_id)
                    st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)

        if user_voted_today:
            st.markdown(
                f"""
                <div style="background:linear-gradient(90deg, rgba(34,197,94,0.1), transparent); border-left:4px solid #22c55e; border-radius:4px; padding:0.8rem; margin-top:1rem; box-shadow: 0 0 20px rgba(34,197,94,0.1);">
                    <p style="color:#22c55e; font-size:0.75rem; font-weight:900; margin:0; letter-spacing:0.05em; text-shadow: 0 0 10px rgba(34,197,94,0.4);">✓ SENTIMENT ANCHORED: {info['label'].upper()} PHASE ACTIVE</p>
                    <p style="color:#94a3b8; font-size:0.6rem; margin:2px 0 0;">Outbreak risk models updated with your local intelligence.</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<p style='color:#00b4d8; font-size:0.7rem; text-align:center; margin-top:1.2rem; font-weight:900; text-transform:uppercase; letter-spacing:0.1em; text-shadow: 0 0 12px rgba(0,180,216,0.8);'>"
                "● Tap to Report Local Sentiment Score"
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
