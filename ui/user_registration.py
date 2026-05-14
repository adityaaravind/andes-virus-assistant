"""User registration and profile management UI."""
from __future__ import annotations

import streamlit as st
from datetime import datetime
from alerts.user_manager import (
    create_user,
    get_user,
    UserValidationError,
    get_leaderboard,
    get_user_rank,
    update_user_stats
)


def get_current_user() -> dict | None:
    """Get currently logged-in user."""
    if "current_username" in st.session_state:
        return get_user(st.session_state.current_username)
    return None


def login_user(username: str) -> bool:
    """Log in user by username."""
    user = get_user(username)
    if user:
        st.session_state.current_username = username
        # Update last active time
        update_user_stats(username, {})  # This updates last_active
        return True
    return False


def logout_user():
    """Log out current user."""
    if "current_username" in st.session_state:
        del st.session_state.current_username


def render_registration_form() -> None:
    """Render registration form for new users."""
    st.markdown("""
        <div style='background: rgba(0,180,216,0.05); border: 1px solid rgba(0,180,216,0.2);
                    border-radius: 8px; padding: 1rem; margin-bottom: 1rem;'>
            <h3 style='color: #00b4d8; margin: 0 0 0.5rem 0; font-size: 0.9rem;'>
                👤 JOIN OUTBREAK TRACKER
            </h3>
        </div>
    """, unsafe_allow_html=True)

    with st.form("registration_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            username = st.text_input(
                "Username*",
                placeholder="tracker123",
                help="3-20 characters, letters, numbers, and underscores only"
            )

        with col2:
            display_name = st.text_input(
                "Display Name*",
                placeholder="Dr. Smith",
                help="How others will see you in leaderboards"
            )

        email = st.text_input(
            "Email (optional)",
            placeholder="alerts@example.com",
            help="For outbreak notifications (optional)"
        )

        col3, col4 = st.columns(2)

        with col3:
            location = st.selectbox(
                "Location (optional)",
                ["", "USA", "Canada", "UK", "Spain", "Germany", "France", "Australia", "Other"],
                help="For regional comparisons"
            )

        with col4:
            role = st.selectbox(
                "Role",
                ["public", "student", "researcher", "healthcare", "media"],
                help="Your professional background"
            )

        submitted = st.form_submit_button(
            "🔬 START TRACKING",
            use_container_width=True,
            type="primary"
        )

        if submitted:
            if not username or not display_name:
                st.error("Username and display name are required!")
                return

            try:
                user = create_user(
                    username=username,
                    display_name=display_name,
                    email=email,
                    location=location,
                    role=role
                )

                # Auto-login the new user
                login_user(username)

                st.success(f"Welcome to Outbreak Tracker, {display_name}!")
                st.balloons()
                st.rerun()

            except UserValidationError as e:
                st.error(f"Registration failed: {e}")


def render_login_form() -> None:
    """Render simple login form for existing users."""
    st.markdown("""
        <div style='background: rgba(34,197,94,0.05); border: 1px solid rgba(34,197,94,0.2);
                    border-radius: 8px; padding: 1rem; margin-bottom: 1rem;'>
            <h3 style='color: #22c55e; margin: 0 0 0.5rem 0; font-size: 0.9rem;'>
                🔑 EXISTING TRACKER LOGIN
            </h3>
        </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input(
            "Username",
            placeholder="Enter your username"
        )

        submitted = st.form_submit_button(
            "🚀 CONTINUE TRACKING",
            use_container_width=True
        )

        if submitted:
            if not username:
                st.error("Please enter your username!")
                return

            if login_user(username):
                user = get_current_user()
                st.success(f"Welcome back, {user['display_name']}!")
                st.rerun()
            else:
                st.error("Username not found. Check spelling or register as new user.")


def render_user_profile() -> None:
    """Render current user's profile and stats."""
    user = get_current_user()
    if not user:
        return

    # Profile header
    st.markdown(f"""
        <div style='background: rgba(168,85,247,0.05); border: 1px solid rgba(168,85,247,0.2);
                    border-radius: 8px; padding: 1rem; margin-bottom: 1rem;'>
            <h3 style='color: #a855f7; margin: 0 0 0.5rem 0; font-size: 0.9rem;'>
                👤 TRACKER PROFILE
            </h3>
            <p style='color: #f1f5f9; margin: 0; font-size: 0.8rem;'>
                <strong>{user['display_name']}</strong> (@{user['username']})
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Stats display
    stats = user["stats"]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "🎯 Rank",
            f"#{get_user_rank(user['username'], 'total_shares')[0]}",
            help="Your position in share leaderboard"
        )

    with col2:
        st.metric(
            "📤 Shares",
            stats["total_shares"],
            help="Total intel reports shared"
        )

    with col3:
        st.metric(
            "🗳️ Votes",
            stats["fear_votes"],
            help="Fear index votes cast"
        )

    # Badges
    if stats.get("badges"):
        st.markdown("**🏆 Badges:**")
        badge_text = " ".join([f"🎖️ {badge.replace('_', ' ').title()}" for badge in stats["badges"]])
        st.caption(badge_text)

    # Quick actions
    col4, col5 = st.columns(2)

    with col4:
        if st.button("📊 View Leaderboard", key="view_leaderboard"):
            st.session_state.show_leaderboard = True

    with col5:
        if st.button("🚪 Logout", key="logout_user"):
            logout_user()
            st.success("Logged out successfully!")
            st.rerun()


def render_mini_leaderboard() -> None:
    """Render compact leaderboard for sidebar."""
    st.markdown("#### 🏆 Top Trackers")

    leaderboard = get_leaderboard("total_shares", limit=5)
    current_user = get_current_user()

    for i, user in enumerate(leaderboard, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔸"

        # Highlight current user
        if current_user and user["username"] == current_user["username"]:
            st.markdown(f"**{emoji} {i}. {user['display_name']}: {user['stats']['total_shares']} shares** ⭐")
        else:
            st.caption(f"{emoji} {i}. {user['display_name']}: {user['stats']['total_shares']} shares")

    # Show current user rank if not in top 5
    if current_user:
        rank, total = get_user_rank(current_user["username"], "total_shares")
        if rank > 5:
            st.caption(f"🎯 Your rank: #{rank} of {total}")


def render_user_section() -> None:
    """Main user management section for sidebar."""
    current_user = get_current_user()

    if current_user:
        # Show user profile
        render_user_profile()

        # Show leaderboard if requested
        if st.session_state.get("show_leaderboard"):
            render_mini_leaderboard()
            if st.button("❌ Hide Leaderboard"):
                st.session_state.show_leaderboard = False
                st.rerun()

    else:
        # Show registration/login options
        tab1, tab2 = st.tabs(["👤 Register", "🔑 Login"])

        with tab1:
            render_registration_form()

        with tab2:
            render_login_form()

    # Always show mini leaderboard at bottom
    if not st.session_state.get("show_leaderboard"):
        with st.expander("🏆 Quick Leaderboard", expanded=False):
            render_mini_leaderboard()