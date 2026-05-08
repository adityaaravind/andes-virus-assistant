"""Fear index component — user voting on outbreak fear level."""
from __future__ import annotations

import hashlib
import json
import streamlit as st
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

    # Custom CSS for the fear index card
    st.markdown(
        f"""
        <style>
        .fear-index-card {{
            background: linear-gradient(135deg,rgba(13,27,42,0.95) 0%,rgba(27,46,69,0.95) 100%);
            border: 2px solid {color}88;
            border-radius: 16px;
            padding: 1.4rem 1.8rem;
            margin-bottom: 1rem;
            position: relative;
            overflow: hidden;
        }}
        .fear-index-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg,{color},{color}44,{color});
            border-radius: 16px 16px 0 0;
        }}
        .fear-title {{
            color: {color};
            font-size: 1.55rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            margin: 0 0 0.5rem;
            font-family: monospace;
            text-shadow: 0 0 20px {color}88;
            text-align: center;
        }}
        .fear-subtitle {{
            color: #94a3b8;
            font-size: 0.82rem;
            margin: 0.2rem 0 0.8rem;
            text-align: center;
        }}
        .fear-status-badge {{
            background: {color}22;
            border: 2px solid {color};
            border-radius: 12px;
            padding: 0.5rem 1.4rem;
            display: inline-block;
            margin: 0 auto;
        }}
        .fear-status-label {{
            color: {color};
            font-size: 1.8rem;
            font-weight: 900;
            margin: 0;
            font-family: monospace;
        }}
        .fear-status-desc {{
            color: #94a3b8;
            font-size: 0.72rem;
            margin: 0;
        }}
        .fear-progress {{
            margin: 1rem 0;
        }}
        .fear-progress-bar {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .fear-progress-label {{
            color: #94a3b8;
            font-size: 0.75rem;
        }}
        .fear-progress-track {{
            flex: 1;
            height: 8px;
            background: #1b2e45;
            border-radius: 4px;
            position: relative;
        }}
        .fear-progress-fill {{
            width: {avg_fear/5*100}%;
            height: 100%;
            background: {color};
            border-radius: 4px;
        }}
        .fear-progress-value {{
            color: {color};
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .fear-divider {{
            border-top: 1px solid #1b2e45;
            padding-top: 0.7rem;
        }}
        .fear-question {{
            color: #94a3b8;
            font-size: 0.85rem;
            margin: 0 0 0.8rem;
        }}
        .fear-button-container .stButton > button {{
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
        .fear-button-container .stButton > button:hover {{
            background: linear-gradient(135deg, {color}15 0%, {color}25 100%) !important;
            border-color: {color} !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
        }}
        .fear-thanks {{
            color: #64748b;
            font-size: 0.85rem;
            margin: 0;
            text-align: center;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Main fear index container
    with st.container():
        st.markdown('<div class="fear-index-card">', unsafe_allow_html=True)

        # Header section
        st.markdown(
            f'''
            <div style="padding-top: 0.5rem;">
                <p class="fear-title">😰 PUBLIC FEAR INDEX</p>
                <p class="fear-subtitle">Community sentiment · Real-time voting · {vote_count} total votes</p>
                <div style="text-align: center; margin-bottom: 1rem;">
                    <div class="fear-status-badge">
                        <p class="fear-status-label">{label.upper()}</p>
                        <p class="fear-status-desc">{desc}</p>
                    </div>
                </div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

        # Progress bar
        st.markdown(
            f'''
            <div class="fear-progress">
                <div class="fear-progress-bar">
                    <span class="fear-progress-label">Fear Level:</span>
                    <div class="fear-progress-track">
                        <div class="fear-progress-fill"></div>
                    </div>
                    <span class="fear-progress-value">{avg_fear:.1f}/5</span>
                </div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

        # Question section
        st.markdown(
            '''
            <div class="fear-divider">
                <p class="fear-question">How do you feel about the outbreak?</p>
            </div>
            ''',
            unsafe_allow_html=True,
        )

        # Voting buttons section
        if not user_voted_today:
            st.markdown('<div class="fear-button-container">', unsafe_allow_html=True)

            # First row: calm, concerned, worried
            cols1 = st.columns(3)
            for i, level in enumerate([1, 2, 3]):
                info = FEAR_LEVELS[level]
                with cols1[i]:
                    if st.button(
                        info['label'],
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
                        info['label'],
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
                '<p class="fear-thanks">✓ Thanks for voting! Come back tomorrow to vote again.</p>',
                unsafe_allow_html=True,
            )

        st.markdown('</div>', unsafe_allow_html=True)