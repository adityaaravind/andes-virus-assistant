"""Integration hooks for gamification with existing app systems."""
from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from alerts.gamification_manager import gamification
from ui.secure_registration import get_current_user


def hook_fear_index_vote(fear_level: float, user_confidence: float = 0.8) -> Dict[str, Any]:
    """
    Hook for when user votes on fear index.

    Args:
        fear_level: Fear level voted (1.0-5.0)
        user_confidence: User's confidence in vote (0.0-1.0)

    Returns:
        Gamification result
    """
    current_user = get_current_user()
    if not current_user:
        return {"success": False, "reason": "User not logged in"}

    try:
        # Calculate impact based on current outbreak severity
        action_data = {
            "vote": fear_level,
            "confidence": user_confidence,
            "fear_level": fear_level,
            "current_fear_level": fear_level  # Pass for context-based impact calc
        }

        result = gamification.process_user_action(
            user_id=current_user["username"],
            action_type="fear_index_vote",
            action_data=action_data
        )

        if result["success"]:
            logging.info(f"User {current_user['username']} voted on fear index, earned {result['impact']} impact")

        return result

    except Exception as e:
        logging.error(f"Error processing fear index vote: {e}")
        return {"success": False, "reason": str(e)}


def hook_content_share(content_type: str, content_id: str, urgency_level: str = "normal") -> Dict[str, Any]:
    """
    Hook for when user shares content.

    Args:
        content_type: Type of content shared ('news', 'alert', 'research')
        content_id: Identifier for the shared content
        urgency_level: Urgency of shared content ('low', 'normal', 'high', 'critical')

    Returns:
        Gamification result
    """
    current_user = get_current_user()
    if not current_user:
        return {"success": False, "reason": "User not logged in"}

    try:
        action_data = {
            "content_type": content_type,
            "content_id": content_id,
            "urgency_level": urgency_level
        }

        result = gamification.process_user_action(
            user_id=current_user["username"],
            action_type="share_update",
            action_data=action_data
        )

        if result["success"]:
            logging.info(f"User {current_user['username']} shared {content_type}, earned {result['impact']} impact")

        return result

    except Exception as e:
        logging.error(f"Error processing content share: {e}")
        return {"success": False, "reason": str(e)}


def hook_daily_checkin() -> Dict[str, Any]:
    """
    Hook for daily check-in action.

    Returns:
        Gamification result
    """
    current_user = get_current_user()
    if not current_user:
        return {"success": False, "reason": "User not logged in"}

    try:
        action_data = {"type": "daily_health_check"}

        result = gamification.process_user_action(
            user_id=current_user["username"],
            action_type="daily_check_in",
            action_data=action_data
        )

        if result["success"]:
            logging.info(f"User {current_user['username']} completed daily check-in, earned {result['impact']} impact")

        return result

    except Exception as e:
        logging.error(f"Error processing daily check-in: {e}")
        return {"success": False, "reason": str(e)}


def hook_prediction_submission(prediction_type: str, prediction_value: Any, actual_value: Any = None) -> Dict[str, Any]:
    """
    Hook for prediction submissions and accuracy tracking.

    Args:
        prediction_type: Type of prediction ('case_count', 'spread_rate', 'risk_level')
        prediction_value: The prediction made
        actual_value: Actual outcome (if known)

    Returns:
        Gamification result
    """
    current_user = get_current_user()
    if not current_user:
        return {"success": False, "reason": "User not logged in"}

    try:
        action_data = {
            "prediction_type": prediction_type,
            "prediction_value": prediction_value,
            "actual_value": actual_value
        }

        # If we have actual value, calculate accuracy
        if actual_value is not None:
            accuracy = calculate_prediction_accuracy(prediction_value, actual_value, prediction_type)
            action_data["accuracy"] = accuracy
            action_type = "accurate_prediction"
        else:
            action_type = "prediction_submission"

        result = gamification.process_user_action(
            user_id=current_user["username"],
            action_type=action_type,
            action_data=action_data
        )

        if result["success"]:
            logging.info(f"User {current_user['username']} submitted prediction, earned {result['impact']} impact")

        return result

    except Exception as e:
        logging.error(f"Error processing prediction: {e}")
        return {"success": False, "reason": str(e)}


def hook_research_contribution(contribution_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hook for research contributions (uploading data, flagging sources, etc.).

    Args:
        contribution_type: Type of contribution ('data_upload', 'source_verification', 'translation')
        data: Additional data about the contribution

    Returns:
        Gamification result
    """
    current_user = get_current_user()
    if not current_user:
        return {"success": False, "reason": "User not logged in"}

    try:
        action_data = {
            "contribution_type": contribution_type,
            **data
        }

        result = gamification.process_user_action(
            user_id=current_user["username"],
            action_type="research_contribution",
            action_data=action_data
        )

        if result["success"]:
            logging.info(f"User {current_user['username']} made research contribution, earned {result['impact']} impact")

        return result

    except Exception as e:
        logging.error(f"Error processing research contribution: {e}")
        return {"success": False, "reason": str(e)}


def hook_user_invitation(invited_username: str) -> Dict[str, Any]:
    """
    Hook for when user successfully invites another user.

    Args:
        invited_username: Username of the invited user

    Returns:
        Gamification result
    """
    current_user = get_current_user()
    if not current_user:
        return {"success": False, "reason": "User not logged in"}

    try:
        action_data = {
            "invited_username": invited_username,
            "invitation_method": "direct"
        }

        result = gamification.process_user_action(
            user_id=current_user["username"],
            action_type="invite_user",
            action_data=action_data
        )

        if result["success"]:
            logging.info(f"User {current_user['username']} invited {invited_username}, earned {result['impact']} impact")

        return result

    except Exception as e:
        logging.error(f"Error processing user invitation: {e}")
        return {"success": False, "reason": str(e)}


def calculate_prediction_accuracy(predicted: Any, actual: Any, prediction_type: str) -> float:
    """
    Calculate prediction accuracy based on type.

    Args:
        predicted: Predicted value
        actual: Actual value
        prediction_type: Type of prediction

    Returns:
        Accuracy score (0.0-1.0)
    """
    try:
        if prediction_type == "case_count":
            # Percentage accuracy for numerical predictions
            if actual == 0:
                return 1.0 if predicted == 0 else 0.0

            percentage_error = abs(predicted - actual) / actual
            accuracy = max(0.0, 1.0 - percentage_error)
            return min(1.0, accuracy)

        elif prediction_type == "risk_level":
            # Categorical accuracy
            return 1.0 if predicted == actual else 0.0

        elif prediction_type == "spread_rate":
            # Range-based accuracy
            if isinstance(predicted, (list, tuple)) and len(predicted) == 2:
                # Range prediction
                low, high = predicted
                return 1.0 if low <= actual <= high else 0.0
            else:
                # Point prediction
                percentage_error = abs(predicted - actual) / max(actual, 1)
                return max(0.0, 1.0 - percentage_error)

        else:
            # Generic similarity
            return 1.0 if predicted == actual else 0.0

    except Exception as e:
        logging.error(f"Error calculating prediction accuracy: {e}")
        return 0.0


def trigger_community_bonus(event_type: str, impact_multiplier: float = 1.0) -> None:
    """
    Trigger community-wide bonuses for major events.

    Args:
        event_type: Type of event ('outbreak_update', 'research_breakthrough', 'crisis_averted')
        impact_multiplier: Multiplier for bonus impact
    """
    try:
        # Get all active users
        leaderboard = gamification.get_leaderboard(limit=1000)

        base_bonus = {
            "outbreak_update": 25,
            "research_breakthrough": 50,
            "crisis_averted": 100
        }.get(event_type, 10)

        bonus = int(base_bonus * impact_multiplier)

        for user_entry in leaderboard:
            try:
                result = gamification.process_user_action(
                    user_id=user_entry["user_id"],
                    action_type="community_bonus",
                    action_data={"event_type": event_type, "bonus": bonus},
                    real_impact=bonus
                )

                if result["success"]:
                    logging.info(f"Community bonus applied to {user_entry['user_id']}: +{bonus} impact")

            except Exception as e:
                logging.error(f"Error applying community bonus to {user_entry['user_id']}: {e}")

        logging.info(f"Community bonus triggered for {event_type}: +{bonus} to {len(leaderboard)} users")

    except Exception as e:
        logging.error(f"Error triggering community bonus: {e}")


def auto_award_engagement_points() -> None:
    """
    Automatically award engagement points based on app usage patterns.
    Called periodically by background tasks.
    """
    try:
        # This could be called from the existing ingestion jobs
        # to award points when news updates are processed, etc.

        # Example: Award points to users who were active when major news broke
        current_user = get_current_user()
        if current_user:
            # User is actively using the app during a news update cycle
            result = gamification.process_user_action(
                user_id=current_user["username"],
                action_type="active_monitoring",
                action_data={"activity_type": "real_time_monitoring"},
                real_impact=5  # Small bonus for being active
            )

            if result["success"]:
                logging.debug(f"Active monitoring bonus awarded to {current_user['username']}")

    except Exception as e:
        logging.error(f"Error awarding engagement points: {e}")


# Integration helper functions
def get_user_gamification_summary(username: str) -> Dict[str, Any]:
    """Get complete gamification summary for a user."""
    try:
        from alerts.user_manager import get_user as get_user_profile
        user = get_user_profile(username)
        if not user:
            return {"error": "User not found"}

        leaderboard = gamification.get_leaderboard(limit=1000)
        user_rank = next((i + 1 for i, entry in enumerate(leaderboard) if entry["user_id"] == username), 0)

        return {
            "username": username,
            "stats": user["stats"],
            "rank": gamification._get_user_rank(user["stats"].get("lives_protected", 0)),
            "global_rank": user_rank,
            "total_users": len(leaderboard)
        }

    except Exception as e:
        logging.error(f"Error getting gamification summary: {e}")
        return {"error": str(e)}


def check_milestone_notifications(username: str) -> List[str]:
    """Check if user has any milestone notifications to display."""
    try:
        from alerts.user_manager import get_user as get_user_profile
        user = get_user_profile(username)
        if not user:
            return []

        notifications = []
        lives_protected = user["stats"].get("lives_protected", 0)

        # Check for recent milestones (last action's impact)
        milestones = [100, 500, 1000, 2500, 5000, 10000]
        for milestone in milestones:
            if (lives_protected >= milestone and
                user["stats"].get("last_milestone_notified", 0) < milestone):
                notifications.append(f"🎉 You've protected {milestone:,}+ lives!")
                # Mark milestone as notified (would need to store this)

        return notifications

    except Exception as e:
        logging.error(f"Error checking milestone notifications: {e}")
        return []