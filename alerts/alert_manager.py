"""Alert manager — checks thresholds, fires ntfy.sh / email when conditions met."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from alerts.notifier import dispatch, send_ntfy
from alerts.persistent_kv import kv_get, kv_set

HISTORY_FILE = Path("data/alert_history.jsonl")


def load_subscriptions() -> list[dict[str, Any]]:
    return kv_get("subscriptions", [])


def save_subscriptions(subs: list[dict[str, Any]]) -> None:
    kv_set("subscriptions", subs)


def add_subscription(sub: dict[str, Any]) -> None:
    subs = load_subscriptions()
    existing = [s for s in subs if s.get("ntfy_topic") == sub.get("ntfy_topic")
                and s.get("email") == sub.get("email")]
    if existing:
        subs = [sub if (s.get("ntfy_topic") == sub.get("ntfy_topic")
                        and s.get("email") == sub.get("email")) else s
                for s in subs]
    else:
        subs.append(sub)
    save_subscriptions(subs)


def _log_alert(title: str, message: str) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("a") as f:
        f.write(json.dumps({
            "ts": datetime.utcnow().isoformat(),
            "title": title,
            "message": message,
        }) + "\n")


def _load_default_state() -> dict[str, Any]:
    return kv_get("default_alert_state", {})


def _save_default_state(state: dict[str, Any]) -> None:
    kv_set("default_alert_state", state)


def _build_alerts(current: dict[str, Any], last: dict[str, Any],
                  prefs: dict[str, Any] | None) -> list[tuple[str, str, str]]:
    """Build alert list by comparing current vs last known state.

    prefs=None means "all alerts enabled" (used for default topic broadcast).
    """
    all_on = prefs is None

    cur_cases     = current.get("cases", 0)
    cur_deaths    = current.get("deaths", 0)
    cur_countries = current.get("countries", 0)
    cur_risk      = current.get("risk_level", "")
    cur_areas     = set(current.get("areas", []))

    last_cases     = last.get("cases", cur_cases)
    last_deaths    = last.get("deaths", cur_deaths)
    last_countries = last.get("countries", cur_countries)
    last_risk      = last.get("risk_level", cur_risk)
    last_areas     = set(last.get("areas", list(cur_areas)))

    alerts: list[tuple[str, str, str]] = []

    threshold = (prefs or {}).get("case_threshold", 0)
    if threshold and last_cases < threshold <= cur_cases:
        alerts.append((
            f"⚠ Case threshold reached: {cur_cases} confirmed",
            f"Andes virus / MV Hondius outbreak has reached {cur_cases} confirmed cases.\n"
            f"Your alert threshold was set at {threshold}.",
            "warning",
        ))

    if (all_on or (prefs or {}).get("any_case_increase")) and cur_cases > last_cases:
        alerts.append((
            f"🦠 New case confirmed — total now {cur_cases}",
            f"Confirmed cases rose from {last_cases} → {cur_cases}.\nMV Hondius hantavirus outbreak.",
            "warning",
        ))

    if (all_on or (prefs or {}).get("death_increase")) and cur_deaths > last_deaths:
        alerts.append((
            f"💀 New fatality — deaths now {cur_deaths}",
            f"Death toll rose from {last_deaths} → {cur_deaths}.\nMV Hondius outbreak.",
            "critical",
        ))

    if (all_on or (prefs or {}).get("new_country")) and cur_countries > last_countries:
        new = cur_areas - last_areas
        area_str = ", ".join(sorted(new)) if new else f"{cur_countries - last_countries} new"
        alerts.append((
            f"🌍 New area affected: {area_str}",
            f"Outbreak spread. New area(s): {area_str}. Total: {cur_countries} countries.",
            "warning",
        ))

    if (all_on or (prefs or {}).get("risk_level_change")) and cur_risk and cur_risk != last_risk and last_risk:
        level_map = {"LOW": 0, "GUARDED": 1, "ELEVATED": 2, "HIGH": 3, "CRITICAL": 4}
        old_n = level_map.get(last_risk, 0)
        new_n = level_map.get(cur_risk, 0)
        emoji = "🔺" if new_n > old_n else "🔻"
        alerts.append((
            f"{emoji} Risk level: {last_risk} → {cur_risk}",
            f"Pandemic risk updated.\nPrevious: {last_risk}\nCurrent: {cur_risk}",
            "critical" if new_n >= 3 else "warning",
        ))

    return alerts


def _snapshot(current: dict[str, Any]) -> dict[str, Any]:
    return {
        "cases":      current.get("cases", 0),
        "deaths":     current.get("deaths", 0),
        "countries":  current.get("countries", 0),
        "risk_level": current.get("risk_level", ""),
        "areas":      list(current.get("areas", [])),
    }


def check_and_fire(current: dict[str, Any]) -> int:
    """Compare current state vs last known. Fire alerts to default topic + all subscribers. Returns count."""
    default_topic = os.getenv("NTFY_DEFAULT_TOPIC", "HANTAVIRUS")
    fired = 0

    # ── Always check default topic (no subscriber required) ──────────────────
    if default_topic:
        def_last   = _load_default_state()
        def_alerts = _build_alerts(current, def_last, prefs=None)
        for title, msg, lvl in def_alerts:
            send_ntfy(default_topic, title, msg, lvl)
            _log_alert(title, msg)
            fired += 1
        _save_default_state(_snapshot(current))

    # ── Per-subscriber alerts ─────────────────────────────────────────────────
    subs = load_subscriptions()
    updated_subs = []
    for sub in subs:
        last   = sub.get("last_known", {})
        prefs  = sub.get("alerts", {})
        alerts = _build_alerts(current, last, prefs)
        for title, msg, lvl in alerts:
            dispatch(sub, title, msg, lvl)
            if not default_topic:   # avoid double-logging if already logged above
                _log_alert(title, msg)
            fired += 1
        sub["last_known"] = _snapshot(current)
        updated_subs.append(sub)

    if updated_subs:
        save_subscriptions(updated_subs)
    return fired


def get_alert_history(limit: int = 20) -> list[dict[str, Any]]:
    if not HISTORY_FILE.exists():
        return []
    lines = HISTORY_FILE.read_text().strip().splitlines()
    records = []
    for line in reversed(lines[-limit:]):
        try:
            records.append(json.loads(line))
        except Exception:
            continue
    return records
