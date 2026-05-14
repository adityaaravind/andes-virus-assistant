"""Central signal dispatcher — fires real-time signals to live feed for ALL app changes."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from alerts.community_store import add_insight


def fire_signal(
    signal_type: str,
    content: str,
    user_id: str = "SYSTEM"
) -> None:
    """
    Fire real-time signal to live feed on site.

    Args:
        signal_type: Type of signal ('alert', 'search', 'citation', 'vote', 'ingestion', 'map', 'stats', 'news', 'card')
        content: Signal message content
        user_id: Source of the signal
    """
    try:
        # Add to community feed for immediate display
        add_insight(signal_type, content, user_id)
        logging.info(f"Live signal fired: [{signal_type}] {content[:50]}...")

    except Exception as e:
        logging.error(f"Signal dispatch error: {e}")


def fire_ingestion_signal(source: str, docs_count: int, chunks_count: int) -> None:
    """Signal for completed ingestion from any source."""
    fire_signal(
        "alert",
        f"Data refresh complete: {source} processed {docs_count} docs → {chunks_count} chunks indexed",
        "DATA_PIPELINE"
    )


def fire_stats_signal(stats: dict[str, Any]) -> None:
    """Signal for outbreak statistics changes."""
    cases = stats.get('confirmed_cases', 0)
    deaths = stats.get('deaths', 0)
    countries = stats.get('nationalities', 0)
    trend = stats.get('trend', 'stable')

    fire_signal(
        "alert",
        f"Outbreak stats updated: {cases} cases, {deaths} deaths across {countries} countries - trend: {trend}",
        "STATS_MONITOR"
    )


def fire_map_signal(country: str, cases: int, action: str = "update") -> None:
    """Signal for map/geographic data changes."""
    fire_signal(
        "alert",
        f"Geographic data {action}: {country} now showing {cases} cases on tracking map",
        "MAP_TRACKER"
    )


def fire_hotspot_signal(location: str, cases: int, severity: int, is_glowing: bool = False) -> None:
    """Signal for new glowing hotspots detected from news."""
    severity_levels = ["monitoring", "suspected", "confirmed", "critical"]
    severity_text = severity_levels[min(severity - 1, 3)] if severity > 0 else "unknown"

    glow_text = " ✨ GLOWING HOTSPOT" if is_glowing else ""

    fire_signal(
        "map",
        f"🗺️ {location}: {cases} {severity_text} cases detected{glow_text}",
        "HOTSPOT_DETECTOR"
    )


def fire_connection_signal(source_location: str, target_location: str = "MV Hondius") -> None:
    """Signal for new connection lines drawn on map."""
    fire_signal(
        "map",
        f"📡 Connection established: {source_location} ↔ {target_location}",
        "MAP_CONNECTIONS"
    )


def fire_news_signal(articles_count: int, keywords: list[str] | None = None) -> None:
    """Signal for new news articles processed."""
    kw_text = f" matching {', '.join(keywords[:2])}" if keywords else ""
    fire_signal(
        "citation",
        f"News analysis complete: {articles_count} articles processed{kw_text} - sentiment updated",
        "NEWS_SCRAPER"
    )


def fire_risk_signal(old_risk: str, new_risk: str, score: float) -> None:
    """Signal for pandemic risk level changes."""
    emoji = "🔺" if new_risk > old_risk else "🔻" if new_risk < old_risk else "➡️"
    fire_signal(
        "alert",
        f"{emoji} Risk assessment changed: {old_risk} → {new_risk} (score: {score:.1f}/10)",
        "RISK_CALC"
    )


def fire_card_signal(card_type: str, action: str, details: str) -> None:
    """Signal for UI card/component updates."""
    fire_signal(
        "citation",
        f"{card_type} {action}: {details[:80]}...",
        "UI_SYSTEM"
    )


def fire_vote_signal(level: int, avg_score: float, total_votes: int, label: str) -> None:
    """Signal for fear index vote submissions."""
    fire_signal(
        "search",
        f"Fear index updated: vote level {level}/5 → avg score {avg_score:.1f} ({label}) - {total_votes} total votes",
        "COMMUNITY"
    )