"""Central signal dispatcher — fires real-time notifications for ALL app changes."""
from __future__ import annotations

import os
import logging
from datetime import datetime
from typing import Any
from alerts.notifier import send_ntfy
from alerts.alert_manager import _log_alert


def fire_signal(
    signal_type: str,
    title: str,
    message: str,
    data: dict[str, Any] | None = None,
    level: str = "info"
) -> None:
    """
    Fire real-time signal to all subscribers.

    Args:
        signal_type: Type of change (vote, ingestion, map, news, stats, etc.)
        title: Short signal title
        message: Detailed message
        data: Optional structured data for signal
        level: Notification level (info, warning, critical)
    """
    try:
        topic = os.getenv("NTFY_DEFAULT_TOPIC", "HANTAVIRUS")

        # Add signal type prefix to title
        prefixed_title = f"🔔 {title}"

        # Add timestamp and signal type to message
        timestamp = datetime.utcnow().strftime("%H:%M:%S UTC")
        full_message = f"{message}\n\n📅 {timestamp} | Type: {signal_type.upper()}"

        # Send notification
        success = send_ntfy(topic, prefixed_title, full_message, level)

        if success:
            # Log the signal
            _log_alert(f"SIGNAL[{signal_type}]: {title}", message)
            logging.info(f"Signal fired: {signal_type} - {title}")
        else:
            logging.warning(f"Signal failed: {signal_type} - {title}")

    except Exception as e:
        logging.error(f"Signal dispatch error: {e}")


def fire_ingestion_signal(source: str, docs_count: int, chunks_count: int) -> None:
    """Signal for completed ingestion from any source."""
    fire_signal(
        "ingestion",
        f"Data Refresh: {source}",
        f"Ingestion completed from {source}.\n"
        f"📄 Documents processed: {docs_count}\n"
        f"🔗 Chunks created: {chunks_count}\n"
        f"📊 Knowledge base updated",
        {"source": source, "docs": docs_count, "chunks": chunks_count},
        "info"
    )


def fire_stats_signal(stats: dict[str, Any]) -> None:
    """Signal for outbreak statistics changes."""
    fire_signal(
        "stats",
        f"Outbreak Stats Updated",
        f"📊 CURRENT STATUS:\n"
        f"🦠 Cases: {stats.get('confirmed_cases', 0)}\n"
        f"💀 Deaths: {stats.get('deaths', 0)}\n"
        f"🌍 Countries: {stats.get('nationalities', 0)}\n"
        f"📈 Trend: {stats.get('trend', 'Unknown')}",
        stats,
        "warning"
    )


def fire_map_signal(country: str, cases: int, action: str = "update") -> None:
    """Signal for map/geographic data changes."""
    fire_signal(
        "map",
        f"Geographic Update: {country}",
        f"🗺️ Map data updated for {country}.\n"
        f"🦠 Current cases: {cases}\n"
        f"📍 Action: {action.title()}",
        {"country": country, "cases": cases, "action": action},
        "warning" if cases > 0 else "info"
    )


def fire_news_signal(articles_count: int, keywords: list[str] | None = None) -> None:
    """Signal for new news articles processed."""
    kw_text = f"Keywords: {', '.join(keywords)}" if keywords else "General outbreak news"
    fire_signal(
        "news",
        f"News Update: {articles_count} articles",
        f"📰 Latest news processed.\n"
        f"📄 Articles analyzed: {articles_count}\n"
        f"🔍 {kw_text}\n"
        f"📊 Sentiment analysis updated",
        {"articles": articles_count, "keywords": keywords},
        "info"
    )


def fire_risk_signal(old_risk: str, new_risk: str, score: float) -> None:
    """Signal for pandemic risk level changes."""
    emoji = "🔺" if new_risk > old_risk else "🔻" if new_risk < old_risk else "➡️"
    fire_signal(
        "risk",
        f"Risk Assessment: {new_risk}",
        f"{emoji} Pandemic risk updated.\n"
        f"📊 Previous: {old_risk}\n"
        f"📈 Current: {new_risk}\n"
        f"🎯 Score: {score:.1f}/10",
        {"old_risk": old_risk, "new_risk": new_risk, "score": score},
        "critical" if score >= 7.0 else "warning"
    )


def fire_card_signal(card_type: str, action: str, details: str) -> None:
    """Signal for UI card/component updates."""
    fire_signal(
        "card",
        f"Card Update: {card_type}",
        f"🎛️ UI component updated.\n"
        f"📋 Card: {card_type}\n"
        f"🔄 Action: {action}\n"
        f"💡 {details}",
        {"card_type": card_type, "action": action},
        "info"
    )