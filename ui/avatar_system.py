"""Avatar system for outbreak tracker users."""
from __future__ import annotations

import streamlit as st
from typing import Dict, List

# Themed avatar options for outbreak tracker
AVATAR_OPTIONS = {
    "scientist": {
        "emoji": "👩‍🔬",
        "name": "Scientist",
        "description": "Research professional"
    },
    "doctor": {
        "emoji": "👨‍⚕️",
        "name": "Doctor",
        "description": "Medical practitioner"
    },
    "researcher": {
        "emoji": "🔬",
        "name": "Researcher",
        "description": "Lab researcher"
    },
    "epidemiologist": {
        "emoji": "📊",
        "name": "Epidemiologist",
        "description": "Disease tracker"
    },
    "nurse": {
        "emoji": "👩‍⚕️",
        "name": "Nurse",
        "description": "Healthcare worker"
    },
    "student": {
        "emoji": "🎓",
        "name": "Student",
        "description": "Academic learner"
    },
    "journalist": {
        "emoji": "📰",
        "name": "Journalist",
        "description": "News reporter"
    },
    "analyst": {
        "emoji": "📈",
        "name": "Analyst",
        "description": "Data analyst"
    },
    "tracker": {
        "emoji": "🛰️",
        "name": "Tracker",
        "description": "Outbreak monitor"
    },
    "guardian": {
        "emoji": "🛡️",
        "name": "Guardian",
        "description": "Public safety"
    },
    "explorer": {
        "emoji": "🔍",
        "name": "Explorer",
        "description": "Information seeker"
    },
    "sentinel": {
        "emoji": "⚡",
        "name": "Sentinel",
        "description": "Early warning"
    }
}

def render_avatar_selector(current_avatar: str = "scientist", use_selectbox: bool = False) -> str:
    """
    Render avatar selection grid or selectbox.

    Args:
        current_avatar: Default avatar selection
        use_selectbox: Use selectbox instead of buttons (for forms)

    Returns:
        Selected avatar key
    """
    st.markdown("**Choose Your Avatar:**")

    if use_selectbox:
        # Use selectbox for form compatibility
        avatar_options = {f"{avatar['emoji']} {avatar['name']} - {avatar['description']}": key
                         for key, avatar in AVATAR_OPTIONS.items()}

        # Find current selection for display
        current_display = None
        for display_text, key in avatar_options.items():
            if key == current_avatar:
                current_display = display_text
                break

        if current_display is None:
            current_display = list(avatar_options.keys())[0]  # Default to first option

        selected_display = st.selectbox(
            "Select Avatar:",
            options=list(avatar_options.keys()),
            index=list(avatar_options.keys()).index(current_display) if current_display in avatar_options else 0,
            help="Choose your avatar representation"
        )

        selected_avatar = avatar_options[selected_display]

    else:
        # Use original button grid layout
        cols = st.columns(4)
        selected_avatar = current_avatar

        for i, (key, avatar) in enumerate(AVATAR_OPTIONS.items()):
            col_index = i % 4

            with cols[col_index]:
                # Create avatar button with emoji and name
                if st.button(
                    f"{avatar['emoji']}\n{avatar['name']}",
                    key=f"avatar_{key}",
                    help=avatar['description'],
                    use_container_width=True
                ):
                    selected_avatar = key
                    st.session_state.selected_avatar = key

        # Show current selection
        if 'selected_avatar' in st.session_state:
            selected_avatar = st.session_state.selected_avatar

    # Show current selection preview
    current = AVATAR_OPTIONS[selected_avatar]
    st.markdown(
        f"""
        <div style='background: rgba(0,180,216,0.1); border: 1px solid rgba(0,180,216,0.3);
                    border-radius: 8px; padding: 12px; margin: 8px 0; text-align: center;'>
            <div style='font-size: 2rem; margin-bottom: 8px;'>{current['emoji']}</div>
            <div style='color: #00b4d8; font-weight: 800; font-size: 0.9rem;'>{current['name']}</div>
            <div style='color: #94a3b8; font-size: 0.7rem;'>{current['description']}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    return selected_avatar


def get_avatar_display(avatar_key: str) -> Dict[str, str]:
    """Get avatar display info for a given key."""
    return AVATAR_OPTIONS.get(avatar_key, AVATAR_OPTIONS["scientist"])


def render_user_avatar(avatar_key: str, size: str = "small") -> str:
    """
    Render user avatar for display in UI.

    Args:
        avatar_key: Avatar identifier
        size: "small", "medium", or "large"

    Returns:
        HTML string for avatar display
    """
    avatar = get_avatar_display(avatar_key)

    size_styles = {
        "small": "font-size: 1.2rem; width: 32px; height: 32px;",
        "medium": "font-size: 1.8rem; width: 48px; height: 48px;",
        "large": "font-size: 2.5rem; width: 64px; height: 64px;"
    }

    style = size_styles.get(size, size_styles["small"])

    return f"""
    <div style='{style} display: flex; align-items: center; justify-content: center;
                background: rgba(0,180,216,0.1); border: 1px solid rgba(0,180,216,0.3);
                border-radius: 50%; margin-right: 8px;'
         title='{avatar["name"]} - {avatar["description"]}'>
        {avatar['emoji']}
    </div>
    """


def get_avatar_for_leaderboard(avatar_key: str) -> str:
    """Get emoji for leaderboard display."""
    avatar = get_avatar_display(avatar_key)
    return avatar['emoji']