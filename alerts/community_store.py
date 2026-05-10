"""Community Intelligence Store — Qdrant-backed persistence for Phase 2."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from alerts.persist_helper import bg_kv_set, get_persisted_value

SENTIMENT_HISTORY_KEY = "community_sentiment_history"
INSIGHTS_FEED_KEY = "community_insights_feed"

MAX_HISTORY_POINTS = 168  # 1 week if hourly
MAX_FEED_ITEMS = 50

def log_sentiment_snapshot(score: float) -> None:
    """Record a point-in-time sentiment score for trend analysis."""
    history = get_persisted_value(SENTIMENT_HISTORY_KEY, [])
    
    # Only snapshot if last one is > 30 mins old to avoid clutter
    now = datetime.utcnow()
    if history:
        try:
            last_ts = datetime.fromisoformat(history[-1]["timestamp"])
            if now - last_ts < timedelta(minutes=30):
                return
        except (ValueError, KeyError, IndexError):
            pass

    history.append({
        "timestamp": now.isoformat(),
        "score": round(score, 2)
    })
    
    # Keep rolling window
    history = history[-MAX_HISTORY_POINTS:]
    bg_kv_set(SENTIMENT_HISTORY_KEY, history)

def add_insight(insight_type: str, content: str, user_id: str = "anon") -> None:
    """Add a new community insight/activity to the live feed."""
    feed = get_persisted_value(INSIGHTS_FEED_KEY, [])
    
    feed.insert(0, {
        "timestamp": datetime.utcnow().isoformat(),
        "type": insight_type, # e.g., 'search', 'alert', 'citation'
        "content": content,
        "user_id": user_id[:8] if user_id else "anon"
    })
    
    # Keep rolling window
    feed = feed[:MAX_FEED_ITEMS]
    bg_kv_set(INSIGHTS_FEED_KEY, feed)

def get_community_data() -> dict[str, Any]:
    """Retrieve all Phase 2 data for UI rendering with fallback defaults."""
    history = get_persisted_value(SENTIMENT_HISTORY_KEY, [])
    feed = get_persisted_value(INSIGHTS_FEED_KEY, [])
    
    # SEED DATA: Ensure chart and feed aren't empty on first load
    if not history:
        now = datetime.utcnow()
        history = [
            {"timestamp": (now - timedelta(days=2)).isoformat(), "score": 2.1},
            {"timestamp": (now - timedelta(days=1)).isoformat(), "score": 2.4},
            {"timestamp": now.isoformat(), "score": 2.2},
        ]

    if not feed:
        feed = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "alert",
                "content": "Phase 2 Intelligence Stream Online",
                "user_id": "SYSTEM"
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                "type": "search",
                "content": "indexed latest WHO situation reports",
                "user_id": "SYSTEM"
            }
        ]
        
    return {
        "history": history,
        "feed": feed
    }
