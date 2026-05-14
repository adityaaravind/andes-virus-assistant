"""User management system for outbreak tracker with duplicate validation."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from alerts.persistent_kv import kv_get, kv_set


class UserValidationError(Exception):
    """Custom exception for user validation errors."""
    pass


def is_valid_username(username: str) -> tuple[bool, str]:
    """
    Validate username format and availability.

    Returns:
        (is_valid, error_message)
    """
    if not username:
        return False, "Username cannot be empty"

    if len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(username) > 20:
        return False, "Username cannot exceed 20 characters"

    # Allow only alphanumeric and underscores
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"

    # Check if username is taken
    if is_username_taken(username):
        return False, "Username is already taken"

    return True, ""


def is_username_taken(username: str) -> bool:
    """Check if username already exists (case-insensitive)."""
    users = kv_get("user_profiles", {})

    # Case-insensitive check
    existing_usernames = [u.lower() for u in users.keys()]
    return username.lower() in existing_usernames


def create_user(
    username: str,
    display_name: str,
    email: str = "",
    location: str = "",
    role: str = "public"
) -> dict[str, Any]:
    """
    Create a new user profile with validation.

    Raises:
        UserValidationError: If validation fails

    Returns:
        User profile dict
    """
    # Validate username
    is_valid, error_msg = is_valid_username(username)
    if not is_valid:
        raise UserValidationError(error_msg)

    # Validate display name
    if not display_name or len(display_name.strip()) < 1:
        raise UserValidationError("Display name cannot be empty")

    if len(display_name) > 50:
        raise UserValidationError("Display name cannot exceed 50 characters")

    # Validate email format if provided
    if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        raise UserValidationError("Invalid email format")

    # Create user profile
    now = datetime.utcnow().isoformat()
    user_profile = {
        "username": username,
        "display_name": display_name.strip(),
        "email": email.strip(),
        "location": location.strip(),
        "role": role,
        "created": now,
        "last_active": now,
        "stats": {
            "total_shares": 0,
            "fear_votes": 0,
            "streak_days": 0,
            "badges": ["new_tracker"],
            "predictions": {"correct": 0, "total": 0}
        },
        "preferences": {
            "email_alerts": bool(email),
            "leaderboard_visible": True
        }
    }

    # Save to database
    users = kv_get("user_profiles", {})
    users[username] = user_profile
    kv_set("user_profiles", users)

    return user_profile


def get_user(username: str) -> dict[str, Any] | None:
    """Get user profile by username."""
    users = kv_get("user_profiles", {})
    return users.get(username)


def update_user_stats(username: str, stat_updates: dict[str, Any]) -> bool:
    """Update user statistics."""
    users = kv_get("user_profiles", {})

    if username not in users:
        return False

    # Update last active
    users[username]["last_active"] = datetime.utcnow().isoformat()

    # Update specific stats
    for stat_key, value in stat_updates.items():
        if stat_key in users[username]["stats"]:
            if isinstance(value, dict):
                # Merge dict values (for nested stats like predictions)
                users[username]["stats"][stat_key].update(value)
            else:
                users[username]["stats"][stat_key] = value

    kv_set("user_profiles", users)
    return True


def get_leaderboard(stat_type: str = "total_shares", limit: int = 10) -> list[dict]:
    """
    Get leaderboard sorted by specified stat.

    Args:
        stat_type: 'total_shares', 'fear_votes', 'streak_days', etc.
        limit: Number of users to return
    """
    users = kv_get("user_profiles", {})

    # Filter users who want to be visible on leaderboard
    visible_users = [
        user for user in users.values()
        if user.get("preferences", {}).get("leaderboard_visible", True)
    ]

    # Sort by specified stat
    sorted_users = sorted(
        visible_users,
        key=lambda u: u["stats"].get(stat_type, 0),
        reverse=True
    )

    return sorted_users[:limit]


def get_user_rank(username: str, stat_type: str = "total_shares") -> tuple[int, int]:
    """
    Get user's rank and total user count for specified stat.

    Returns:
        (rank, total_users) - rank is 1-indexed, 0 if user not found
    """
    leaderboard = get_leaderboard(stat_type, limit=1000)  # Get all users

    for i, user in enumerate(leaderboard, 1):
        if user["username"] == username:
            return i, len(leaderboard)

    return 0, len(leaderboard)


def search_users(query: str, limit: int = 10) -> list[dict]:
    """Search users by username or display name."""
    users = kv_get("user_profiles", {})
    query_lower = query.lower()

    matches = []
    for user in users.values():
        if (query_lower in user["username"].lower() or
            query_lower in user["display_name"].lower()):
            matches.append(user)

    return matches[:limit]