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
    1: {"label": "CALM", "desc": "Not worried", "color": "#22c55e"},
    2: {"label": "CONCERNED", "desc": "Slightly worried", "color": "#f59e0b"},
    3: {"label": "WORRIED", "desc": "Moderately fearful", "color": "#ef4444"},
    4: {"label": "FEARFUL", "desc": "Very worried", "color": "#dc2626"},
    5: {"label": "PANICKED", "desc": "Extremely fearful", "color": "#991b1b"},
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
        return 2.5, len(votes), "UNKNOWN", "No votes yet", "#94a3b8"

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

    # Compact fear index card
    st.markdown(
        f"""
        <div style="
            background:linear-gradient(135deg,rgba(13,27,42,0.95) 0%,rgba(27,46,69,0.95) 100%);
            border:2px solid {color}88;
            border-radius:12px;
            padding:1rem;
            margin-bottom:0.5rem;
            position:relative;
            overflow:hidden;
        ">
          <div style="
            position:absolute;top:0;left:0;right:0;height:3px;
            background:linear-gradient(90deg,{color},{color}44,{color});
          "></div>

          <div style="text-align:center;margin-bottom:0.8rem;">
            <p style="
                color:{color};font-size:1.2rem;font-weight:800;
                letter-spacing:0.04em;margin:0 0 0.3rem;font-family:monospace;
                text-shadow:0 0 15px {color}88;
              ">😰 FEAR INDEX</p>
            <div style="
              background:{color}22;border:2px solid {color};
              border-radius:8px;padding:0.4rem 0.8rem;display:inline-block;
            ">
              <p style="color:{color};font-size:1.4rem;font-weight:900;margin:0;font-family:monospace;">{label}</p>
              <p style="color:#94a3b8;font-size:0.65rem;margin:0;">{vote_count} votes · {desc}</p>
            </div>
          </div>

          <div style="margin-bottom:0.5rem;">
            <div style="display:flex;align-items:center;gap:0.4rem;">
              <span style="color:#94a3b8;font-size:0.7rem;">Level:</span>
              <div style="flex:1;height:6px;background:#1b2e45;border-radius:3px;position:relative;">
                <div style="width:{avg_fear/5*100}%;height:100%;background:{color};border-radius:3px;"></div>
              </div>
              <span style="color:{color};font-size:0.7rem;font-weight:600;">{avg_fear:.1f}/5</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Compact voting buttons
    if not user_voted_today:
        st.markdown('<p style="color:#94a3b8;font-size:0.75rem;margin:0.3rem 0;">Vote your feeling:</p>', unsafe_allow_html=True)

        # Responsive button grid: 3 top row, 2 bottom row for better mobile layout
        st.markdown("""
        <style>
        .stButton > button {
            height: 32px !important;
            font-size: 0.65rem !important;
            font-weight: 600 !important;
            padding: 0.2rem 0.1rem !important;
            margin: 0.05rem !important;
        }
        @media (max-width: 768px) {
            .stButton > button {
                height: 40px !important;
                font-size: 0.7rem !important;
            }
        }
        </style>
        """, unsafe_allow_html=True)

        # First row: CALM, CONCERNED, WORRIED
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
                    st.success(f"✅ {info['label']}")
                    st.rerun()

        # Second row: FEARFUL, PANICKED (centered)
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
                    st.success(f"✅ {info['label']}")
                    st.rerun()
    else:
        st.markdown(
            '<p style="color:#64748b;font-size:0.7rem;margin:0.3rem 0;">✓ Voted today! Come back tomorrow.</p>',
            unsafe_allow_html=True,
        )