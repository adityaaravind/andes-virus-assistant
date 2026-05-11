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

def log_sentiment_snapshot(user_score: float, web_score: float) -> None:
    """Record dual-stream sentiment scores for trend analysis."""
    history = get_persisted_value(SENTIMENT_HISTORY_KEY, [])
    
    now = datetime.utcnow()
    if history:
        try:
            last_ts = datetime.fromisoformat(history[-1]["timestamp"])
            if now - last_ts < timedelta(minutes=15): # Log more frequently for 'real-time' feel
                return
        except (ValueError, KeyError, IndexError):
            pass

    history.append({
        "timestamp": now.isoformat(),
        "user_score": round(user_score, 2),
        "web_score": round(web_score, 2)
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
            {"timestamp": (now - timedelta(days=2)).isoformat(), "user_score": 1.8, "web_score": 2.2},
            {"timestamp": (now - timedelta(days=1)).isoformat(), "user_score": 2.1, "web_score": 2.5},
            {"timestamp": now.isoformat(), "user_score": 2.0, "web_score": 2.4},
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

def get_trending_topics(limit: int = 5) -> list[tuple[str, int]]:
    """Aggregate search types from the feed to find trending research topics."""
    feed = get_persisted_value(INSIGHTS_FEED_KEY, [])
    counts: dict[str, int] = {}
    for item in feed:
        if item["type"] == "search":
            term = item["content"].replace("queried: ", "").strip().upper()
            if len(term) > 3:
                counts[term] = counts.get(term, 0) + 1
    
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
