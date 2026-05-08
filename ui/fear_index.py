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
        # More unique ID using browser context
        import hashlib
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

    st.markdown(
        f"""
        <div style="
            background:linear-gradient(135deg,rgba(13,27,42,0.95) 0%,rgba(27,46,69,0.95) 100%);
            border:2px solid {color}88;
            border-radius:16px;
            padding:1.4rem 1.8rem 1rem;
            margin-bottom:1rem;
            position:relative;
            overflow:hidden;
        ">
          <div style="
            position:absolute;top:0;left:0;right:0;height:4px;
            background:linear-gradient(90deg,{color},{color}44,{color});
          "></div>

          <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;">
            <div style="flex:1;min-width:200px;">
              <p style="
                color:{color};font-size:1.55rem;font-weight:800;
                letter-spacing:0.06em;margin:0;font-family:monospace;
                text-shadow:0 0 20px {color}88;
              ">😰 PUBLIC FEAR INDEX</p>
              <p style="color:#94a3b8;font-size:0.82rem;margin:0.2rem 0 0;">
                Community sentiment · Real-time voting · {vote_count} total votes
              </p>
            </div>
            <div style="
              background:{color}22;border:2px solid {color};
              border-radius:12px;padding:0.5rem 1.4rem;text-align:center;
            ">
              <p style="color:{color};font-size:1.8rem;font-weight:900;margin:0;font-family:monospace;">{label}</p>
              <p style="color:#94a3b8;font-size:0.72rem;margin:0;">{desc}</p>
            </div>
          </div>

          <div style="
            margin-top:0.9rem;
            border-top:1px solid #1b2e45;padding-top:0.7rem;
          ">
            <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.8rem;">
              <span style="color:#94a3b8;font-size:0.75rem;">Fear Level:</span>
              <div style="flex:1;height:8px;background:#1b2e45;border-radius:4px;position:relative;">
                <div style="width:{avg_fear/5*100}%;height:100%;background:{color};border-radius:4px;"></div>
              </div>
              <span style="color:{color};font-size:0.75rem;font-weight:600;">{avg_fear:.1f}/5</span>
            </div>
        """)

    if not user_voted_today:
        st.markdown(
            '<p style="color:#94a3b8;font-size:0.78rem;margin:0 0 0.5rem;">How do you feel?</p>',
            unsafe_allow_html=True,
        )

        # Embed voting buttons inside the card with custom HTML
        vote_buttons_html = """
        <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:0.4rem;margin-bottom:0.5rem;">
        """

        for level, info in FEAR_LEVELS.items():
            vote_buttons_html += f"""
            <button onclick="document.getElementById('hidden_vote_{level}').click()"
            style="background:{info['color']}22;border:1px solid {info['color']};
            border-radius:6px;padding:0.3rem 0.2rem;font-size:0.68rem;font-weight:600;
            color:{info['color']};cursor:pointer;min-height:32px;
            transition:all 0.2s ease;text-align:center;"
            onmouseover="this.style.background='{info['color']}44'"
            onmouseout="this.style.background='{info['color']}22'"
            title="{info['desc']}">
                {info['label']}
            </button>
            """

        vote_buttons_html += """
        </div>
        </div>
        </div>
        """

        st.markdown(vote_buttons_html, unsafe_allow_html=True)

        # Hidden Streamlit buttons for actual voting
        cols = st.columns(5)
        for i, (level, info) in enumerate(FEAR_LEVELS.items()):
            with cols[i]:
                if st.button(
                    " ",
                    key=f"hidden_vote_{level}",
                ):
                    _save_fear_vote(level, user_id)
                    st.success(f"✅ Voted: {info['label']}")
                    st.rerun()

        # Hide the Streamlit buttons with CSS
        st.markdown("""
        <style>
        [data-testid="column"]:nth-child(n) button {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)

    else:
        st.markdown(
            '<p style="color:#64748b;font-size:0.72rem;margin:0 0 0.5rem;">✓ Thanks for voting! Come back tomorrow.</p>'
            '</div></div>',
            unsafe_allow_html=True,
        )