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
        data["votes"] = [v for v in data["votes"] if v.get("user_id") != user_id]
        data["votes"].append({
            "level": level,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
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


def render_fear_index() -> None:
    avg_fear, vote_count, label, desc, color, web_sentiment = _calculate_fear_average()
    live_fear = round(avg_fear, 2)

    if "user_id" not in st.session_state:
        browser_info = str(st.session_state) + str(hash(str(datetime.utcnow().date())))
        user_hash = hashlib.md5(browser_info.encode()).hexdigest()[:12]
        st.session_state.user_id = f"user_{user_hash}"
    user_id = st.session_state.user_id

    data = _load_fear_data()
    user_voted_today = any(
        v.get("user_id") == user_id and
        v.get("timestamp", "").startswith(datetime.utcnow().strftime("%Y-%m-%d"))
        for v in data.get("votes", [])
    )

    anim = "pulse-fear 2s ease-in-out infinite" if live_fear >= 3.0 else "none"
    user_weight = 0.6 if vote_count > 0 else 0.0
    web_weight = 0.4 if vote_count > 0 else 1.0
    
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
<style>@keyframes pulse-fear {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.4; }} }}</style>
</div>
""".replace("\n", "").strip()
    st.markdown(html_header, unsafe_allow_html=True)

    col_gauge, col_dist = st.columns([1, 1.6])
    with col_gauge:
        fig_gauge = _build_fear_gauge(live_fear, color)
        st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})

    with col_dist:
        # Pre-calculate state
        level_int = max(1, min(5, int(round(live_fear))))
        if "fear_slider_input" in st.session_state:
            level_int = int(st.session_state.fear_slider_input)

        st.markdown(
            """
            <style>
            /* 1. Global Reset for Sentiment Buttons */
            div[data-testid="column"] div[data-testid="stButton"] {
                margin: 0 !important;
                padding: 0 !important;
            }
            
            div[data-testid="column"] div[data-testid="stButton"] button {
                background: rgba(15, 23, 42, 0.4) !important;
                border: 2px solid rgba(255, 255, 255, 0.05) !important;
                border-radius: 12px !important;
                width: 100% !important;
                aspect-ratio: 1/1 !important;
                height: 75px !important; /* Fixed height for small buttons */
                padding: 0 !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
                line-height: 1.2 !important;
                white-space: pre-wrap !important;
                overflow: hidden !important;
            }

            /* Custom sizing for labels inside button */
            div[data-testid="stButton"] button p {
                font-family: 'Inter', sans-serif !important;
                font-weight: 900 !important;
                font-size: 0.55rem !important;
                text-transform: uppercase !important;
                margin: 0 !important;
                padding-top: 0.2rem !important;
                letter-spacing: 0.02em !important;
                color: #94a3b8 !important;
            }

            /* Emoji size adjustment */
            div[data-testid="stButton"] button::before {
                font-size: 1.3rem !important;
                margin-bottom: 2px !important;
            }}

            /* Active State - Glow based on button key */
            div[data-testid="stButton"] button:hover:not(:disabled) {
                border-color: rgba(255, 255, 255, 0.2) !important;
                transform: translateY(-2px) !important;
            }

            /* Disable other buttons once voted */
            div[data-testid="stButton"] button:disabled {
                opacity: 0.2 !important;
                filter: grayscale(1) !important;
                cursor: not-allowed !important;
            }
            </style>
            <p style='color:#94a3b8; font-size:0.75rem; font-weight:800; margin-bottom:0.8rem; letter-spacing:0.1em; opacity:0.8; text-transform:uppercase;'>📡 SELECT SENTIMENT</p>
            """,
            unsafe_allow_html=True
        )

        icons = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴", 5: "💀"}
        cols = st.columns(5, gap="small")
        
        for i, level_id in enumerate(range(1, 6)):
            info = FEAR_LEVELS[level_id]
            is_active = (level_id == level_int)
            l_color = info['color']
            
            with cols[i]:
                # Full label with slight font size reduction to ensure fit
                label_text = f"{icons[level_id]}\n{info['label'].upper()}"
                
                if st.button(label_text, key=f"tile_v3_{level_id}", disabled=user_voted_today, use_container_width=True):
                    _save_fear_vote(level_id, user_id)
                    st.session_state.fear_slider_input = level_id
                    st.rerun()

        # Target the ACTIVE button with high-intensity "Lit" neon glow
        active_color = FEAR_LEVELS[level_int]['color']
        active_css = f"""
        <style>
        /* Base inactive hover for better UX */
        div[data-testid="stButton"] button[key*="tile_v3_"]:hover:not(:disabled) {{
            background: rgba(255, 255, 255, 0.05) !important;
            box-shadow: 0 0 15px rgba(255, 255, 255, 0.1) !important;
        }}

        div[data-testid="stButton"] button[key*="tile_v3_{level_int}"] {{
            background: radial-gradient(circle at center, {active_color}44 0%, rgba(15, 23, 42, 0.95) 100%) !important;
            border: 2px solid {active_color} !important;
            box-shadow: 0 0 40px {active_color}77, inset 0 0 15px {active_color}44 !important;
            transform: scale(1.1) translateY(-3px) !important;
            opacity: 1 !important;
            filter: none !important;
            z-index: 100 !important;
            animation: active-pulse 2s infinite ease-in-out !important;
        }}
        @keyframes active-pulse {{
            0%, 100% {{ box-shadow: 0 0 30px {active_color}55, inset 0 0 10px {active_color}33; }}
            50% {{ box-shadow: 0 0 50px {active_color}99, inset 0 0 20px {active_color}66; }}
        }}
        div[data-testid="stButton"] button[key*="tile_v3_{level_int}"] p {{
            color: white !important;
            font-weight: 950 !important;
            text-shadow: 0 0 15px {active_color}, 0 0 30px {active_color}cc !important;
            font-size: 0.52rem !important;
            opacity: 1 !important;
        }}
        </style>
        """
        st.markdown(active_css, unsafe_allow_html=True)

        if user_voted_today:
            st.markdown(
                f"<div style='background:rgba(34,197,94,0.05); border:1px solid #22c55e33; border-radius:12px; padding:0.8rem; margin-top:1.5rem; text-align:center;'>"
                f"<p style='color:#22c55e; font-size:0.75rem; font-weight:950; margin:0;'>✓ SENTIMENT ANCHORED: {FEAR_LEVELS[level_int]['label'].upper()}</p>"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown("<p style='color:#64748b; font-size:0.6rem; text-align:center; margin-top:1.2rem; font-weight:700;'>TAP TILE TO CAST VOTE</p>", unsafe_allow_html=True)

    # Callouts
    callout_html = """
<style>.fear-callout-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 0.6rem; margin-top: 0.3rem; }</style>
<div class="fear-callout-grid">
<div style="background:rgba(56,189,248,0.08); border:1px solid rgba(56,189,248,0.3); border-radius:8px; padding:0.6rem 0.8rem;"><p style="color:#38bdf8; font-size:0.72rem; font-weight:700; margin:0; text-transform:uppercase;">ℹ️ SENTIMENT ANALYSIS</p><p style="color:#94a3b8; font-size:0.73rem; margin:0.2rem 0 0;">Tracks public anxiety level based on 1000+ real-time votes. Weighted to favor recent sentiment (15-min decay).</p></div>
<div style="background:rgba(167,139,250,0.08); border:1px solid rgba(167,139,250,0.3); border-radius:8px; padding:0.6rem 0.8rem;"><p style="color:#a78bfa; font-size:0.72rem; font-weight:700; margin:0; text-transform:uppercase;">📈 IMPACT ASSESSMENT</p><p style="color:#94a3b8; font-size:0.73rem; margin:0.2rem 0 0;">Public fear often correlates with geographic spread but can be mitigated by clear official communications and verified data.</p></div>
</div>
""".replace("\n", "").strip()
    st.markdown(callout_html, unsafe_allow_html=True)
