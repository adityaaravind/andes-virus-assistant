"""Real-time gamification dashboard UI."""
from __future__ import annotations

import streamlit as st
from datetime import datetime
from typing import Dict, Any, List
from alerts.gamification_manager import gamification
from alerts.user_manager import get_user
from ui.secure_registration import get_current_user


def _get_user_global_rank(username: str) -> int:
    """Get user's global rank on leaderboard."""
    try:
        leaderboard = gamification.get_leaderboard(limit=1000)
        for i, entry in enumerate(leaderboard, 1):
            if entry["user_id"] == username:
                return i
        return len(leaderboard) + 1  # If not found, place at end
    except Exception:
        return 999


def render_hero_dashboard() -> None:
    """Render main hero dashboard with real-time stats."""
    current_user = get_current_user()
    if not current_user:
        render_guest_hero_preview()
        return

    user_stats = current_user["stats"]
    lives_protected = user_stats.get("lives_protected", 0)
    communities_warned = user_stats.get("communities_warned", 0)
    streak_days = user_stats.get("streak_days", 0)
    rank = gamification._get_user_rank(lives_protected)

    # Get global stats for community impact
    global_stats = gamification._get_global_stats()

    # Hero Header Card
    rank_colors = {
        "civilian": "#6b7280",
        "observer": "#3b82f6",
        "tracker": "#8b5cf6",
        "guardian": "#f59e0b",
        "sentinel": "#ef4444",
        "crisis_hero": "#dc2626"
    }

    rank_color = rank_colors.get(rank, "#6b7280")
    rank_display = rank.replace("_", " ").title()

    st.markdown(f"""
        <div style='background: linear-gradient(135deg, rgba({",".join(str(int(rank_color[i:i+2], 16)) for i in (1, 3, 5))}, 0.1), rgba(0,0,0,0.05));
                    border: 2px solid {rank_color}66; border-radius: 16px; padding: 2rem; margin-bottom: 1.5rem;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1);'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                <div style='display: flex; align-items: center; gap: 12px;'>
                    <div style='font-size: 3rem;'>{current_user.get("avatar", "🦸")}</div>
                    <div>
                        <h1 style='margin: 0; color: {rank_color}; font-size: 1.8rem; font-weight: 900;'>
                            {current_user["display_name"]}
                        </h1>
                        <p style='margin: 0; color: {rank_color}; font-size: 1rem; font-weight: 700; text-transform: uppercase;'>
                            🛡️ {rank_display}
                        </p>
                    </div>
                </div>
                <div style='text-align: right;'>
                    <div style='background: {rank_color}22; padding: 8px 16px; border-radius: 8px; border: 1px solid {rank_color}66;'>
                        <p style='margin: 0; color: {rank_color}; font-size: 0.8rem; font-weight: 800;'>GLOBAL RANK</p>
                        <p style='margin: 0; color: {rank_color}; font-size: 1.2rem; font-weight: 900;'>#{_get_user_global_rank(current_user["username"])}</p>
                    </div>
                </div>
            </div>

            <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1rem;'>
                <div style='text-align: center; padding: 1rem; background: rgba(74,222,128,0.1); border-radius: 12px; border: 1px solid rgba(74,222,128,0.3);'>
                    <div style='font-size: 2rem; margin-bottom: 0.5rem;'>🌿</div>
                    <div style='color: #4ade80; font-size: 1.8rem; font-weight: 900; margin-bottom: 0.25rem;'>{lives_protected:,}</div>
                    <div style='color: #4ade80; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;'>Lives Protected</div>
                </div>

                <div style='text-align: center; padding: 1rem; background: rgba(59,130,246,0.1); border-radius: 12px; border: 1px solid rgba(59,130,246,0.3);'>
                    <div style='font-size: 2rem; margin-bottom: 0.5rem;'>🌍</div>
                    <div style='color: #3b82f6; font-size: 1.8rem; font-weight: 900; margin-bottom: 0.25rem;'>{communities_warned:,}</div>
                    <div style='color: #3b82f6; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;'>Communities Warned</div>
                </div>

                <div style='text-align: center; padding: 1rem; background: rgba(245,158,11,0.1); border-radius: 12px; border: 1px solid rgba(245,158,11,0.3);'>
                    <div style='font-size: 2rem; margin-bottom: 0.5rem;'>🔥</div>
                    <div style='color: #f59e0b; font-size: 1.8rem; font-weight: 900; margin-bottom: 0.25rem;'>{streak_days}</div>
                    <div style='color: #f59e0b; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;'>Day Streak</div>
                </div>
            </div>

            {render_rank_progress_bar(lives_protected, rank)}
        </div>
    """, unsafe_allow_html=True)

    # Global Impact Counter
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, rgba(168,85,247,0.1), rgba(0,180,216,0.1));
                    border: 1px solid rgba(168,85,247,0.3); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;'>
            <h3 style='color: #a855f7; margin: 0 0 1rem 0; font-size: 1.2rem; text-align: center;'>
                🌐 GLOBAL CRISIS RESPONSE
            </h3>
            <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; text-align: center;'>
                <div>
                    <div style='color: #a855f7; font-size: 1.5rem; font-weight: 900;'>{global_stats.get("total_lives_protected", 0):,}</div>
                    <div style='color: #a855f7; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;'>Total Lives Protected</div>
                </div>
                <div>
                    <div style='color: #a855f7; font-size: 1.5rem; font-weight: 900;'>{global_stats.get("total_communities_warned", 0):,}</div>
                    <div style='color: #a855f7; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;'>Communities Warned</div>
                </div>
                <div>
                    <div style='color: #a855f7; font-size: 1.5rem; font-weight: 900;'>{global_stats.get("active_guardians_today", 0):,}</div>
                    <div style='color: #a855f7; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;'>Active Guardians</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_rank_progress_bar(lives_protected: int, current_rank: str) -> str:
    """Generate rank progression bar HTML."""
    rank_thresholds = gamification.RANK_THRESHOLDS
    ranks = list(rank_thresholds.keys())

    current_idx = ranks.index(current_rank)

    if current_idx == len(ranks) - 1:  # Max rank
        return f"""
            <div style='background: rgba(220,38,38,0.1); padding: 1rem; border-radius: 8px; border: 1px solid rgba(220,38,38,0.3);'>
                <div style='text-align: center; color: #dc2626; font-weight: 800;'>
                    🏆 MAXIMUM RANK ACHIEVED 🏆
                </div>
            </div>
        """

    next_rank = ranks[current_idx + 1]
    next_threshold = rank_thresholds[next_rank]
    current_threshold = rank_thresholds[current_rank]

    progress = min(100, ((lives_protected - current_threshold) / (next_threshold - current_threshold)) * 100)
    remaining = next_threshold - lives_protected

    return f"""
        <div style='background: rgba(0,0,0,0.1); padding: 1rem; border-radius: 8px;'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                <span style='color: #94a3b8; font-size: 0.8rem; font-weight: 700;'>Progress to {next_rank.replace("_", " ").title()}</span>
                <span style='color: #94a3b8; font-size: 0.8rem; font-weight: 700;'>{remaining:,} lives remaining</span>
            </div>
            <div style='background: rgba(0,0,0,0.2); height: 12px; border-radius: 6px; overflow: hidden;'>
                <div style='background: linear-gradient(90deg, #4ade80, #22c55e); height: 100%; width: {progress}%;
                           transition: width 0.5s ease; box-shadow: 0 0 12px rgba(74,222,128,0.5);'></div>
            </div>
        </div>
    """


def render_guest_hero_preview() -> None:
    """Render preview for non-registered users."""
    # Create card-like container
    with st.container():
        st.markdown("""
            <div style='background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(168,85,247,0.1));
                       border: 2px solid rgba(59,130,246,0.3); border-radius: 16px; padding: 1rem; margin: 1rem 0;'>
        """, unsafe_allow_html=True)

        # Header
        st.markdown("""
            <div style='text-align: center; margin-bottom: 1rem;'>
                <div style='font-size: 3rem; margin-bottom: 0.5rem;'>🦸‍♀️</div>
                <h2 style='color: #3b82f6; margin: 0; font-size: 1.5rem;'>Become a Crisis Guardian</h2>
                <p style='color: #6b7280; margin: 0.5rem 0;'>Join 10,000+ heroes protecting communities worldwide</p>
            </div>
        """, unsafe_allow_html=True)

        # Stats grid using columns
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("🌿 Lives Protected", "150,847", "Today")

        with col2:
            st.metric("🌍 Communities", "2,340", "Warned")

        with col3:
            st.metric("⚡ Active", "1,205", "Guardians")

        # Register button
        st.markdown("<br>", unsafe_allow_html=True)
        col_left, col_center, col_right = st.columns([1, 2, 1])

        with col_center:
            if st.button("🚀 JOIN AS GUARDIAN", type="primary", use_container_width=True):
                # Trigger registration by setting session state
                st.session_state.show_registration = True
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


def render_mission_board() -> None:
    """Render daily mission board with real-time actions."""
    current_user = get_current_user()
    if not current_user:
        return

    st.markdown("""
        <h3 style='color: #f59e0b; margin: 0 0 1rem 0; font-size: 1.2rem;'>
            🎯 DAILY RESCUE MISSIONS
        </h3>
    """, unsafe_allow_html=True)

    # Daily missions
    missions = [
        {
            "id": "daily_check_in",
            "name": "Morning Health Check",
            "description": "Check current outbreak status",
            "reward": 10,
            "icon": "🌅",
            "action_type": "daily_check_in"
        },
        {
            "id": "fear_vote",
            "name": "Assess Risk Level",
            "description": "Vote on current fear index",
            "reward": 25,
            "icon": "📊",
            "action_type": "fear_index_vote"
        },
        {
            "id": "share_update",
            "name": "Share Critical Update",
            "description": "Spread awareness to communities",
            "reward": 50,
            "icon": "📢",
            "action_type": "share_update"
        }
    ]

    for mission in missions:
        col1, col2, col3 = st.columns([1, 4, 2])

        with col1:
            st.markdown(f"<div style='font-size: 2rem; text-align: center;'>{mission['icon']}</div>",
                       unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
                <div>
                    <div style='color: #f59e0b; font-weight: 800; font-size: 1rem;'>{mission['name']}</div>
                    <div style='color: #94a3b8; font-size: 0.8rem;'>{mission['description']}</div>
                    <div style='color: #4ade80; font-size: 0.8rem; font-weight: 700;'>+{mission['reward']} Lives Protected</div>
                </div>
            """, unsafe_allow_html=True)

        with col3:
            # Check if mission can be completed
            can_complete = not gamification._is_action_rate_limited(
                current_user["username"],
                mission["action_type"]
            )

            if can_complete:
                if st.button(f"🚀 Complete", key=f"mission_{mission['id']}", use_container_width=True):
                    complete_mission(mission, current_user["username"])
            else:
                st.markdown("""
                    <div style='background: rgba(107,114,128,0.3); color: #6b7280; padding: 8px;
                               border-radius: 6px; text-align: center; font-size: 0.8rem;'>
                        ✅ Completed
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("---")


def complete_mission(mission: Dict[str, Any], user_id: str) -> None:
    """Complete a mission and update user stats."""
    # Simulate mission completion with real data
    if mission["action_type"] == "daily_check_in":
        action_data = {"type": "health_check"}
    elif mission["action_type"] == "fear_index_vote":
        # Get current fear level from the app
        action_data = {"vote": "moderate", "fear_level": 2.5}
    elif mission["action_type"] == "share_update":
        action_data = {"content_id": "current_outbreak_update", "urgency_level": "high"}
    else:
        action_data = {}

    result = gamification.process_user_action(
        user_id=user_id,
        action_type=mission["action_type"],
        action_data=action_data
    )

    if result["success"]:
        st.success(f"🎉 Mission completed! +{result['impact']} Lives Protected!")
        st.balloons()

        # Check for achievements
        if result["achievements"]:
            for achievement in result["achievements"]:
                st.success(f"🏆 Achievement unlocked: {achievement}!")

        # Force refresh to show updated stats
        st.rerun()
    else:
        st.error(f"Mission failed: {result.get('reason', 'Unknown error')}")


def render_live_leaderboard() -> None:
    """Render real-time leaderboard."""
    st.markdown("""
        <h3 style='color: #dc2626; margin: 0 0 1rem 0; font-size: 1.2rem;'>
            🏆 GLOBAL GUARDIAN LEADERBOARD
        </h3>
    """, unsafe_allow_html=True)

    leaderboard = gamification.get_leaderboard(limit=10)
    current_user = get_current_user()

    for i, entry in enumerate(leaderboard, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔸"

        # Highlight current user
        is_current_user = current_user and entry["user_id"] == current_user["username"]
        bg_color = "rgba(168,85,247,0.2)" if is_current_user else "rgba(0,0,0,0.05)"
        border_color = "rgba(168,85,247,0.5)" if is_current_user else "rgba(148,163,184,0.2)"

        st.markdown(f"""
            <div style='background: {bg_color}; border: 1px solid {border_color};
                       border-radius: 8px; padding: 1rem; margin-bottom: 0.5rem;
                       display: flex; justify-content: space-between; align-items: center;'>
                <div style='display: flex; align-items: center; gap: 12px;'>
                    <span style='font-size: 1.5rem;'>{emoji}</span>
                    <div style='font-size: 1.5rem;'>{entry.get("avatar", "🦸")}</div>
                    <div>
                        <div style='font-weight: 800; color: {"#a855f7" if is_current_user else "#1f2937"};'>
                            {entry["display_name"]} {"(You)" if is_current_user else ""}
                        </div>
                        <div style='font-size: 0.8rem; color: #6b7280; text-transform: uppercase;'>
                            {entry["rank"].replace("_", " ")}
                        </div>
                    </div>
                </div>
                <div style='text-align: right;'>
                    <div style='color: #4ade80; font-weight: 900; font-size: 1.1rem;'>
                        {entry["lives_protected"]:,}
                    </div>
                    <div style='color: #6b7280; font-size: 0.7rem;'>Lives Protected</div>
                </div>
            </div>
        """, unsafe_allow_html=True)


def render_achievement_gallery() -> None:
    """Render user's achievements and badges."""
    current_user = get_current_user()
    if not current_user:
        return

    st.markdown("""
        <h3 style='color: #8b5cf6; margin: 0 0 1rem 0; font-size: 1.2rem;'>
            🏅 ACHIEVEMENTS & BADGES
        </h3>
    """, unsafe_allow_html=True)

    # Sample achievements based on user stats
    user_stats = current_user["stats"]
    lives_protected = user_stats.get("lives_protected", 0)
    streak_days = user_stats.get("streak_days", 0)

    achievements = []

    if lives_protected >= 100:
        achievements.append({"name": "Life Saver", "icon": "🩺", "description": "Protected 100+ lives"})
    if lives_protected >= 1000:
        achievements.append({"name": "Guardian Angel", "icon": "👼", "description": "Protected 1,000+ lives"})
    if streak_days >= 7:
        achievements.append({"name": "Dedicated Guardian", "icon": "🔥", "description": "7-day activity streak"})
    if user_stats.get("communities_warned", 0) >= 10:
        achievements.append({"name": "Community Hero", "icon": "🌍", "description": "Warned 10+ communities"})

    if not achievements:
        st.markdown("""
            <div style='text-align: center; padding: 2rem; color: #6b7280;'>
                <div style='font-size: 3rem; margin-bottom: 1rem;'>🏆</div>
                <p>Complete missions to unlock achievements!</p>
            </div>
        """, unsafe_allow_html=True)
        return

    # Display achievements in grid
    cols = st.columns(min(len(achievements), 3))
    for i, achievement in enumerate(achievements):
        with cols[i % 3]:
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, rgba(139,92,246,0.1), rgba(168,85,247,0.1));
                           border: 1px solid rgba(139,92,246,0.3); border-radius: 12px;
                           padding: 1.5rem; text-align: center; margin-bottom: 1rem;'>
                    <div style='font-size: 3rem; margin-bottom: 0.5rem;'>{achievement["icon"]}</div>
                    <div style='color: #8b5cf6; font-weight: 800; font-size: 1rem; margin-bottom: 0.25rem;'>
                        {achievement["name"]}
                    </div>
                    <div style='color: #6b7280; font-size: 0.8rem;'>
                        {achievement["description"]}
                    </div>
                </div>
            """, unsafe_allow_html=True)