"""Real-time gamification system for outbreak tracker."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from alerts.persistent_kv import kv_get, kv_set
from alerts.user_manager import get_user, update_user_stats


class GameificationManager:
    """Manages real-time gamification mechanics."""

    # Action impact calculations
    ACTION_IMPACTS = {
        "fear_index_vote": 15,
        "share_update": 50,
        "accurate_prediction": 100,
        "daily_check_in": 10,
        "invite_user": 200,
        "research_contribution": 75
    }

    # Achievement thresholds
    RANK_THRESHOLDS = {
        "civilian": 0,
        "observer": 50,
        "tracker": 200,
        "guardian": 500,
        "sentinel": 1000,
        "crisis_hero": 2500
    }

    def __init__(self):
        self.global_stats_key = "game_global_stats"
        self.leaderboard_key = "game_leaderboard"
        self.actions_key = "game_user_actions"

    def process_user_action(
        self,
        user_id: str,
        action_type: str,
        action_data: Dict[str, Any],
        real_impact: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Process user action and calculate real-time impact.

        Args:
            user_id: User identifier
            action_type: Type of action performed
            action_data: Additional data about the action
            real_impact: Override impact calculation with real data

        Returns:
            Action result with impact calculated
        """
        try:
            # Calculate impact based on real data if available
            if real_impact is not None:
                impact = int(real_impact)
            else:
                impact = self._calculate_action_impact(action_type, action_data)

            # Verify action is meaningful (not just clicking for points)
            if not self._validate_action(user_id, action_type, action_data):
                return {"success": False, "reason": "Action not validated"}

            # Update user stats immediately
            user_update = self._update_user_stats(user_id, action_type, impact)

            # Update global counters
            self._update_global_stats(action_type, impact)

            # Check for achievements/rank changes
            achievements = self._check_achievements(user_id, user_update["stats"])

            # Log action for analysis
            self._log_user_action(user_id, action_type, action_data, impact)

            # Update leaderboards
            self._update_leaderboard(user_id, user_update["stats"])

            return {
                "success": True,
                "impact": impact,
                "new_total": user_update["stats"]["lives_protected"],
                "achievements": achievements,
                "rank": self._get_user_rank(user_update["stats"]["lives_protected"]),
                "global_impact": self._get_global_stats()
            }

        except Exception as e:
            logging.error(f"Error processing user action: {e}")
            return {"success": False, "reason": str(e)}

    def _calculate_action_impact(self, action_type: str, action_data: Dict[str, Any]) -> int:
        """Calculate impact based on action type and context."""
        base_impact = self.ACTION_IMPACTS.get(action_type, 10)

        # Adjust impact based on action context
        if action_type == "fear_index_vote":
            # Higher impact for votes during active outbreaks
            current_fear_level = action_data.get("current_fear_level", 2.0)
            if current_fear_level > 3.0:
                base_impact *= 2

        elif action_type == "share_update":
            # Higher impact for sharing verified/critical news
            if action_data.get("urgency_level") == "critical":
                base_impact *= 1.5

        elif action_type == "accurate_prediction":
            # Scale by accuracy percentage
            accuracy = action_data.get("accuracy", 0.5)
            base_impact = int(base_impact * (accuracy * 2))

        return base_impact

    def _validate_action(self, user_id: str, action_type: str, action_data: Dict[str, Any]) -> bool:
        """Validate that action is meaningful and not spam."""

        # Check for rate limiting
        if self._is_action_rate_limited(user_id, action_type):
            return False

        # Validate action has real backing data
        if action_type == "fear_index_vote":
            # Must have actual fear index data to vote on
            return action_data.get("fear_level") is not None

        elif action_type == "share_update":
            # Must have actual content to share
            return action_data.get("content_id") is not None

        elif action_type == "daily_check_in":
            # Only one check-in per day
            last_checkin = self._get_last_action_time(user_id, "daily_check_in")
            if last_checkin:
                last_date = datetime.fromisoformat(last_checkin).date()
                today = datetime.utcnow().date()
                return last_date < today

        return True

    def _is_action_rate_limited(self, user_id: str, action_type: str) -> bool:
        """Check if user is rate limited for this action type."""
        rate_limits = {
            "fear_index_vote": timedelta(hours=1),  # Max 1 vote per hour
            "share_update": timedelta(minutes=10),   # Max 1 share per 10 min
            "daily_check_in": timedelta(hours=23),   # Once per day
        }

        if action_type not in rate_limits:
            return False

        last_action = self._get_last_action_time(user_id, action_type)
        if not last_action:
            return False

        time_since = datetime.utcnow() - datetime.fromisoformat(last_action)
        return time_since < rate_limits[action_type]

    def _update_user_stats(self, user_id: str, action_type: str, impact: int) -> Dict[str, Any]:
        """Update user statistics with new impact."""
        user = get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Ensure user stats have all required keys
        if "stats" not in user:
            user["stats"] = {}

        current_lives_protected = user["stats"].get("lives_protected", 0)

        # Update specific stats based on action
        stats_updates = {"lives_protected": current_lives_protected + impact}

        if action_type == "share_update":
            stats_updates["communities_warned"] = user["stats"].get("communities_warned", 0) + 1
        elif action_type == "research_contribution":
            stats_updates["research_contributions"] = user["stats"].get("research_contributions", 0) + 1
        elif action_type == "accurate_prediction":
            pred_stats = user["stats"].get("predictions", {"correct": 0, "total": 0})
            pred_stats["correct"] += 1
            pred_stats["total"] += 1
            stats_updates["predictions"] = pred_stats
            stats_updates["prediction_accuracy"] = pred_stats["correct"] / pred_stats["total"]

        # Update daily streak
        if action_type == "daily_check_in":
            stats_updates["streak_days"] = self._calculate_streak(user_id)

        # Apply updates
        update_user_stats(user_id, stats_updates)

        # Return updated user data
        updated_user = get_user(user_id)
        return {"user": updated_user, "stats": updated_user["stats"]}

    def _update_global_stats(self, action_type: str, impact: int) -> None:
        """Update global game statistics."""
        global_stats = kv_get(self.global_stats_key, {
            "total_lives_protected": 0,
            "total_communities_warned": 0,
            "active_guardians_today": 0,
            "last_updated": datetime.utcnow().isoformat()
        })

        # Ensure all required keys exist
        if "total_lives_protected" not in global_stats:
            global_stats["total_lives_protected"] = 0
        if "total_communities_warned" not in global_stats:
            global_stats["total_communities_warned"] = 0
        if "active_guardians_today" not in global_stats:
            global_stats["active_guardians_today"] = 0

        global_stats["total_lives_protected"] += impact
        global_stats["last_updated"] = datetime.utcnow().isoformat()

        if action_type == "share_update":
            global_stats["total_communities_warned"] += 1

        # Update active guardians count (users active in last 24h)
        global_stats["active_guardians_today"] = self._count_active_guardians()

        kv_set(self.global_stats_key, global_stats)

    def _check_achievements(self, user_id: str, user_stats: Dict[str, Any]) -> List[str]:
        """Check for new achievements and rank changes."""
        achievements = []
        lives_protected = user_stats.get("lives_protected", 0)

        # Check rank advancement
        current_rank = self._get_user_rank(lives_protected)
        user = get_user(user_id)
        previous_rank = user.get("game_rank", "civilian")

        if current_rank != previous_rank:
            # Rank up!
            achievements.append(f"rank_up_{current_rank}")
            update_user_stats(user_id, {"game_rank": current_rank})

        # Check milestone achievements
        milestones = [100, 500, 1000, 2500, 5000, 10000]
        for milestone in milestones:
            if (lives_protected >= milestone and
                user_stats.get("lives_protected", 0) - self.ACTION_IMPACTS.get("daily_check_in", 10) < milestone):
                achievements.append(f"milestone_{milestone}")

        # Check streak achievements
        streak = user_stats.get("streak_days", 0)
        if streak in [7, 30, 100] and streak > user.get("max_streak", 0):
            achievements.append(f"streak_{streak}")
            update_user_stats(user_id, {"max_streak": streak})

        return achievements

    def _get_user_rank(self, lives_protected: int) -> str:
        """Get user rank based on lives protected."""
        for rank, threshold in reversed(list(self.RANK_THRESHOLDS.items())):
            if lives_protected >= threshold:
                return rank
        return "civilian"

    def _update_leaderboard(self, user_id: str, user_stats: Dict[str, Any]) -> None:
        """Update real-time leaderboard."""
        leaderboard = kv_get(self.leaderboard_key, {})

        leaderboard[user_id] = {
            "lives_protected": user_stats.get("lives_protected", 0),
            "communities_warned": user_stats.get("communities_warned", 0),
            "last_updated": datetime.utcnow().isoformat()
        }

        kv_set(self.leaderboard_key, leaderboard)

    def get_leaderboard(self, limit: int = 10, timeframe: str = "all_time") -> List[Dict[str, Any]]:
        """Get current leaderboard with user details."""
        leaderboard_data = kv_get(self.leaderboard_key, {})

        # Get user details for leaderboard entries
        leaderboard = []
        for user_id, stats in leaderboard_data.items():
            user = get_user(user_id)
            if user:
                leaderboard.append({
                    "user_id": user_id,
                    "username": user["username"],
                    "display_name": user["display_name"],
                    "avatar": user.get("avatar", "observer"),
                    "lives_protected": stats["lives_protected"],
                    "communities_warned": stats["communities_warned"],
                    "rank": self._get_user_rank(stats["lives_protected"])
                })

        # Sort by lives protected
        leaderboard.sort(key=lambda x: x["lives_protected"], reverse=True)

        return leaderboard[:limit]

    def _get_global_stats(self) -> Dict[str, Any]:
        """Get current global game statistics."""
        return kv_get(self.global_stats_key, {
            "total_lives_protected": 0,
            "total_communities_warned": 0,
            "active_guardians_today": 0,
            "last_updated": datetime.utcnow().isoformat()
        })

    def _log_user_action(self, user_id: str, action_type: str, action_data: Dict[str, Any], impact: int) -> None:
        """Log user action for analytics and recovery."""
        actions = kv_get(self.actions_key, [])

        action_log = {
            "action_id": f"{user_id}_{datetime.utcnow().isoformat()}",
            "user_id": user_id,
            "action_type": action_type,
            "action_data": action_data,
            "impact": impact,
            "timestamp": datetime.utcnow().isoformat()
        }

        actions.append(action_log)

        # Keep only last 10,000 actions for performance
        actions = actions[-10000:]

        kv_set(self.actions_key, actions)

    def _get_last_action_time(self, user_id: str, action_type: str) -> Optional[str]:
        """Get timestamp of user's last action of specific type."""
        actions = kv_get(self.actions_key, [])

        user_actions = [a for a in actions if a["user_id"] == user_id and a["action_type"] == action_type]
        if user_actions:
            return user_actions[-1]["timestamp"]
        return None

    def _calculate_streak(self, user_id: str) -> int:
        """Calculate current daily streak for user."""
        actions = kv_get(self.actions_key, [])
        checkin_actions = [a for a in actions if a["user_id"] == user_id and a["action_type"] == "daily_check_in"]

        if not checkin_actions:
            return 1

        # Sort by timestamp
        checkin_actions.sort(key=lambda x: x["timestamp"], reverse=True)

        streak = 1
        current_date = datetime.utcnow().date()

        for action in checkin_actions[1:]:  # Skip today's check-in
            action_date = datetime.fromisoformat(action["timestamp"]).date()
            expected_date = current_date - timedelta(days=streak)

            if action_date == expected_date:
                streak += 1
                current_date = action_date
            else:
                break

        return streak

    def _count_active_guardians(self) -> int:
        """Count users active in last 24 hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        actions = kv_get(self.actions_key, [])

        active_users = set()
        for action in actions:
            if datetime.fromisoformat(action["timestamp"]) > cutoff_time:
                active_users.add(action["user_id"])

        return len(active_users)

    def backup_user_data(self) -> Dict[str, Any]:
        """Create backup of all gamification data for recovery."""
        return {
            "global_stats": kv_get(self.global_stats_key, {}),
            "leaderboard": kv_get(self.leaderboard_key, {}),
            "user_actions": kv_get(self.actions_key, []),
            "backup_timestamp": datetime.utcnow().isoformat()
        }

    def restore_user_data(self, backup_data: Dict[str, Any]) -> bool:
        """Restore gamification data from backup."""
        try:
            if "global_stats" in backup_data:
                kv_set(self.global_stats_key, backup_data["global_stats"])
            if "leaderboard" in backup_data:
                kv_set(self.leaderboard_key, backup_data["leaderboard"])
            if "user_actions" in backup_data:
                kv_set(self.actions_key, backup_data["user_actions"])
            return True
        except Exception as e:
            logging.error(f"Error restoring user data: {e}")
            return False


# Global instance
gamification = GameificationManager()