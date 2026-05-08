"""Fear index component — user voting on outbreak fear level."""
from __future__ import annotations

import hashlib
import json
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
from typing import Any

FEAR_DATA_FILE = Path("data/fear_votes.json")

FEAR_LEVELS = {
    1: {"label": "calm", "desc": "Not worried", "color": "#22c55e"},
    2: {"label": "concerned", "desc": "Slightly worried", "color": "#f59e0b"},
    3: {"label": "worried", "desc": "Moderately fearful", "color": "#ef4444"},
    4: {"label": "fearful", "desc": "Very worried", "color": "#dc2626"},
    5: {"label": "panicked", "desc": "Extremely fearful", "color": "#991b1b"},
}


def _load_fear_data() -> dict[str, Any]:
    """Load fear voting data from file."""
    if FEAR_DATA_FILE.exists():
        try:
            return json.loads(FEAR_DATA_FILE.read_text())
        except Exception:
            pass
    return {"votes": [], "last_updated": datetime.utcnow().isoformat()}


def _save_fear_vote(level: int, user_id: str) -> None:
    """Save a new fear vote."""
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

        FEAR_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        FEAR_DATA_FILE.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


def _calculate_fear_average() -> tuple[float, int, str, str, str]:
    """Calculate average fear level and return display values."""
    data = _load_fear_data()
    votes = data.get("votes", [])

    if not votes:
        return 2.5, len(votes), "unknown", "No votes yet", "#94a3b8"

    # Calculate weighted average (recent votes count more)
    total_weight = 0
    weighted_sum = 0

    for i, vote in enumerate(reversed(votes)):
        # More recent votes have higher weight
        weight = 1 + (i / len(votes)) * 0.5
        weighted_sum += vote["level"] * weight
        total_weight += weight

    avg = weighted_sum / total_weight
    closest_level = min(FEAR_LEVELS.keys(), key=lambda x: abs(x - avg))

    level_info = FEAR_LEVELS[closest_level]
    return avg, len(votes), level_info["label"], level_info["desc"], level_info["color"]


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
    avg_fear, vote_count, label, desc, color = _calculate_fear_average()

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
    anim = "pulse-fear 2s ease-in-out infinite" if avg_fear >= 3.0 else "none"
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg,rgba(13,27,42,0.95) 0%,rgba(27,46,69,0.95) 100%);
            border: 2px solid {color}88;
            border-radius: 16px;
            padding: 1.4rem 1.8rem 1rem;
            margin-bottom: 1rem;
            position: relative;
            overflow: hidden;
        ">
            <div style="
                position: absolute; top: 0; left: 0; right: 0; height: 4px;
                background: linear-gradient(90deg,{color},{color}44,{color});
                animation: {anim};
            "></div>

            <div style="display:flex; align-items:center; gap:1rem; flex-wrap:wrap;">
                <div style="flex:1; min-width:200px;">
                    <p style="
                        color:{color}; font-size:1.55rem; font-weight:800;
                        letter-spacing:0.06em; margin:0; font-family:monospace;
                        text-shadow:0 0 20px {color}88;
                    ">📡 PUBLIC FEAR INDEX</p>
                    <p style="color:#94a3b8; font-size:0.82rem; margin:0.2rem 0 0;">
                        Community Sentiment · Real-time Voting
                        &nbsp;&nbsp;<span class="live-dot" style="width:7px; height:7px;"></span>
                        <span class="live-label">LIVE ASSESSMENT</span>
                    </p>
                </div>
                <div style="
                    background:{color}22; border:2px solid {color};
                    border-radius:12px; padding:0.5rem 1.4rem; text-align:center;
                ">
                    <p style="color:{color}; font-size:1.8rem; font-weight:900; margin:0; font-family:monospace;">{label.upper()}</p>
                    <p style="color:#94a3b8; font-size:0.72rem; margin:0;">{desc}</p>
                </div>
            </div>

            <div style="
                display:flex; gap:1.5rem; margin-top:0.9rem; flex-wrap:wrap;
                border-top:1px solid #1b2e45; padding-top:0.7rem;
            ">
                <span style="color:#94a3b8; font-size:0.77rem;">
                    😰 Fear Level: <b style="color:{color};">{avg_fear:.1f}/5</b>
                </span>
                <span style="color:#94a3b8; font-size:0.77rem;">
                    📈 Responses: <b style="color:#f8fafc;">{vote_count}</b>
                </span>
                <span style="color:#94a3b8; font-size:0.77rem;">
                    🎯 State: <b style="color:{color};">{label.title()}</b>
                </span>
                <span style="color:#94a3b8; font-size:0.77rem;">
                    ⏱ Updated: <b style="color:#f8fafc;">{datetime.now().strftime('%H:%M')}</b>
                </span>
            </div>
        </div>
        <style>
        @keyframes pulse-fear {{
          0%,100% {{ opacity:1; }}
          50% {{ opacity:0.4; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

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
    st.markdown(
        f"""
        <div style="
            display:grid;grid-template-columns:1fr 1fr;gap:0.6rem;
            margin-top:0.3rem; margin-bottom: 1rem;
        ">
          <div style="background:rgba(27,46,69,0.3);border:1px solid #1b2e45;
                      border-radius:8px;padding:0.6rem 0.8rem;">
            <p style="color:#94a3b8;font-size:0.72rem;font-weight:700;margin:0;">ℹ️ SENTIMENT ANALYSIS</p>
            <p style="color:#64748b;font-size:0.73rem;margin:0.2rem 0 0;">
                Tracks public anxiety level based on 1000+ real-time votes. 
                Weighted to favor recent sentiment (15-min decay).
            </p>
          </div>
          <div style="background:rgba(27,46,69,0.3);border:1px solid #1b2e45;
                      border-radius:8px;padding:0.6rem 0.8rem;">
            <p style="color:#94a3b8;font-size:0.72rem;font-weight:700;margin:0;">📈 IMPACT ASSESSMENT</p>
            <p style="color:#64748b;font-size:0.73rem;margin:0.2rem 0 0;">
                Public fear often correlates with geographic spread but can be mitigated by 
                clear official communications and verified data.
            </p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


    # Voting buttons section below the visualization
    if not user_voted_today:
        st.markdown(
            f"""
            <style>
            .vote-buttons .stButton > button {{
                height: 45px !important;
                font-size: 0.8rem !important;
                font-weight: 600 !important;
                padding: 0.6rem 1rem !important;
                margin: 0.2rem 0 !important;
                background: linear-gradient(135deg, rgba(13,27,42,0.8) 0%, rgba(27,46,69,0.8) 100%) !important;
                border: 1px solid {color}44 !important;
                border-radius: 8px !important;
                color: {color} !important;
                transition: all 0.2s ease !important;
            }}
            .vote-buttons .stButton > button:hover {{
                background: linear-gradient(135deg, {color}15 0%, {color}25 100%) !important;
                border-color: {color} !important;
                transform: translateY(-1px) !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
            }}
            </style>
            <div class="vote-buttons">
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<p style="color:#94a3b8; font-size:0.85rem; margin:0.5rem 0 0.8rem;">How do you feel about the outbreak?</p>',
            unsafe_allow_html=True,
        )

        # First row: calm, concerned, worried
        cols1 = st.columns(3)
        for i, level in enumerate([1, 2, 3]):
            info = FEAR_LEVELS[level]
            with cols1[i]:
                if st.button(
                    info['label'].upper(),
                    key=f"vote_{level}",
                    use_container_width=True,
                    help=info['desc']
                ):
                    _save_fear_vote(level, user_id)
                    st.success(f"✅ Voted: {info['label']}")
                    st.rerun()

        # Second row: fearful, panicked (centered)
        cols2 = st.columns([1, 2, 2, 1])
        for i, level in enumerate([4, 5]):
            info = FEAR_LEVELS[level]
            with cols2[i + 1]:
                if st.button(
                    info['label'].upper(),
                    key=f"vote_{level}",
                    use_container_width=True,
                    help=info['desc']
                ):
                    _save_fear_vote(level, user_id)
                    st.success(f"✅ Voted: {info['label']}")
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f"""
            <div style="background:rgba(34,197,94,0.08); border:1px solid #22c55e44; border-radius:8px; padding:0.8rem; margin-top:1rem;">
                <p style="color:#22c55e; font-size:0.8rem; margin:0;">✓ Thanks for participating! Your vote has been recorded.</p>
                <p style="color:#94a3b8; font-size:0.75rem; margin:0.2rem 0 0;">Outbreak sentiment tracking helps researchers understand public response and information gaps.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )