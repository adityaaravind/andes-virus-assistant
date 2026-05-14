"""Hope Garden - Garden State Management."""
from __future__ import annotations

from typing import Dict, Tuple
from datetime import datetime, timedelta
import logging


class HopeGardenState:
    """Manages the state of the Hope Garden based on news sentiment and user interactions."""

    def __init__(self):
        self.base_health = 50  # Starting garden health (0-100)
        self.max_health = 100
        self.min_health = 0

        # Growth stages based on health levels
        self.growth_stages = {
            0: {"name": "Barren Soil", "emoji": "🏜️", "description": "Nothing grows here..."},
            10: {"name": "First Seeds", "emoji": "🌱", "description": "Tiny seeds of hope appear"},
            25: {"name": "Green Sprouts", "emoji": "🌿", "description": "Life begins to emerge"},
            40: {"name": "Young Plants", "emoji": "🌾", "description": "Plants grow stronger"},
            60: {"name": "Hope Flowers", "emoji": "🌸🌻", "description": "Beautiful flowers bloom"},
            80: {"name": "Healing Trees", "emoji": "🌳🌲", "description": "Strong trees provide shelter"},
            95: {"name": "Recovery Forest", "emoji": "🌲🌳🌲🌸", "description": "A thriving ecosystem of hope"}
        }

    def get_current_state(self) -> Dict[str, any]:
        """Get current garden state from persistent storage."""
        try:
            from alerts.persistent_kv import kv_get

            # Get stored state or initialize
            stored_state = kv_get("hope_garden_state")

            # Default state
            default_state = {
                "health": self.base_health,
                "care_points": 0,
                "care_points_needed": 0,
                "last_updated": datetime.utcnow().isoformat(),
                "last_sentiment_update": None,
                "total_community_actions": 0,
                "daily_actions": 0,
                "stress_level": 0,
                "needs_care": False
            }

            # Merge stored state with defaults (handles missing keys)
            if stored_state:
                for key, default_value in default_state.items():
                    if key not in stored_state:
                        stored_state[key] = default_value
                state = stored_state
            else:
                state = default_state

            # Reset daily actions if it's a new day
            if state.get("last_updated"):
                last_update = datetime.fromisoformat(state["last_updated"])
                if last_update.date() != datetime.utcnow().date():
                    state["daily_actions"] = 0
                    state["last_updated"] = datetime.utcnow().isoformat()
                    self._save_state(state)

            return state

        except Exception as e:
            logging.error(f"Error getting garden state: {e}")
            return self._get_default_state()

    def _get_default_state(self) -> Dict[str, any]:
        """Get default garden state."""
        return {
            "health": self.base_health,
            "care_points": 0,
            "care_points_needed": 0,
            "last_updated": datetime.utcnow().isoformat(),
            "last_sentiment_update": None,
            "total_community_actions": 0,
            "daily_actions": 0,
            "stress_level": 0,
            "needs_care": False
        }

    def _save_state(self, state: Dict[str, any]) -> None:
        """Save garden state to persistent storage."""
        try:
            from alerts.persistent_kv import kv_set
            state["last_updated"] = datetime.utcnow().isoformat()
            kv_set("hope_garden_state", state)
        except Exception as e:
            logging.error(f"Error saving garden state: {e}")

    def update_from_sentiment(self, sentiment_data: Dict[str, any]) -> Dict[str, any]:
        """Update garden state based on news sentiment analysis.

        Args:
            sentiment_data: Output from sentiment_analyzer.analyze_news_batch()

        Returns:
            Updated garden state
        """
        state = self.get_current_state()

        sentiment_score = sentiment_data.get('overall_sentiment', 0)
        sentiment_type = sentiment_data.get('sentiment_type', 'NEUTRAL')
        confidence = sentiment_data.get('confidence', 0.0)

        # Calculate health change based on sentiment
        # Scale impact by confidence (more confident predictions have bigger impact)
        health_impact = sentiment_score * 10 * confidence

        # Apply health change
        old_health = state["health"]
        new_health = max(self.min_health, min(self.max_health, old_health + health_impact))
        state["health"] = round(new_health, 1)

        # Update stress level based on concerning news
        if sentiment_type == 'CONCERNING':
            stress_increase = confidence * 20  # Max 20 stress points
            state["stress_level"] = min(100, state["stress_level"] + stress_increase)
        elif sentiment_type == 'HOPEFUL':
            stress_decrease = confidence * 15  # Max 15 stress points reduced
            state["stress_level"] = max(0, state["stress_level"] - stress_decrease)

        # Determine if garden needs care
        state["needs_care"] = state["stress_level"] > 50 or state["health"] < 30

        # Calculate care points needed to restore health
        if state["needs_care"]:
            health_deficit = max(0, 50 - state["health"])  # Target minimum healthy level
            stress_excess = max(0, state["stress_level"] - 30)  # Target acceptable stress
            state["care_points_needed"] = int(health_deficit + stress_excess)
        else:
            state["care_points_needed"] = 0
            state["care_points"] = 0  # Reset care points when not needed

        # Store sentiment update info
        state["last_sentiment_update"] = sentiment_data.get('timestamp')
        state["last_sentiment_type"] = sentiment_type
        state["last_sentiment_score"] = sentiment_score

        self._save_state(state)

        logging.info(f"Garden updated: health {old_health:.1f} → {new_health:.1f}, stress {state['stress_level']:.1f}, needs_care {state['needs_care']}")

        return state

    def add_user_care(self, care_type: str, user_id: str = None) -> Dict[str, any]:
        """Add user care action to the garden.

        Args:
            care_type: Type of care ('water', 'sunlight', 'hope', 'fertilizer')
            user_id: Optional user identifier

        Returns:
            Updated garden state with care applied
        """
        state = self.get_current_state()

        # Care point values by type
        care_values = {
            'water': 3,
            'sunlight': 4,
            'hope': 5,
            'fertilizer': 2,
            'healing': 6
        }

        care_points = care_values.get(care_type, 3)

        # Apply care if needed
        if state["needs_care"] and state["care_points_needed"] > 0:
            state["care_points"] = min(state["care_points_needed"], state["care_points"] + care_points)
            state["total_community_actions"] += 1
            state["daily_actions"] += 1

            # Check if enough care has been provided
            if state["care_points"] >= state["care_points_needed"]:
                # Restore garden health
                health_boost = min(20, state["care_points_needed"] / 5)  # Max 20 health boost
                state["health"] = min(self.max_health, state["health"] + health_boost)
                state["stress_level"] = max(0, state["stress_level"] - 15)

                # Reset care system
                state["care_points"] = 0
                state["care_points_needed"] = 0
                state["needs_care"] = False

                logging.info(f"Garden healed! Health boosted by {health_boost}")

        self._save_state(state)
        return state

    def get_garden_display_info(self) -> Dict[str, any]:
        """Get display information for the garden UI."""
        state = self.get_current_state()
        health = state["health"]

        # Find current growth stage
        current_stage_key = 0
        for threshold in sorted(self.growth_stages.keys(), reverse=True):
            if health >= threshold:
                current_stage_key = threshold
                break

        current_stage = self.growth_stages[current_stage_key]

        # Find next stage
        next_stage_key = None
        next_stage = None
        for threshold in sorted(self.growth_stages.keys()):
            if threshold > current_stage_key:
                next_stage_key = threshold
                next_stage = self.growth_stages[threshold]
                break

        # Calculate progress to next stage
        if next_stage_key:
            progress_percent = ((health - current_stage_key) / (next_stage_key - current_stage_key)) * 100
        else:
            progress_percent = 100  # At max stage

        # Garden status message
        if state["needs_care"]:
            if state["stress_level"] > 70:
                status_message = "🥀 Plants are wilting from stress! Urgent care needed!"
                status_color = "#ef4444"
            else:
                status_message = "😟 Garden needs community care to recover"
                status_color = "#f59e0b"
        elif health > 80:
            status_message = "🌟 Garden is thriving! Beautiful and healthy!"
            status_color = "#22c55e"
        elif health > 50:
            status_message = "🌱 Garden is growing well with community support"
            status_color = "#4ade80"
        else:
            status_message = "🌾 Garden is stable but could use more care"
            status_color = "#64748b"

        return {
            "current_stage": current_stage,
            "next_stage": next_stage,
            "health": health,
            "progress_percent": round(progress_percent, 1),
            "needs_care": state["needs_care"],
            "care_points": state["care_points"],
            "care_points_needed": state["care_points_needed"],
            "stress_level": state["stress_level"],
            "status_message": status_message,
            "status_color": status_color,
            "total_community_actions": state["total_community_actions"],
            "daily_actions": state["daily_actions"],
            "last_sentiment_type": state.get("last_sentiment_type"),
            "last_updated": state["last_updated"]
        }


# Singleton instance for use across the app
garden_state = HopeGardenState()