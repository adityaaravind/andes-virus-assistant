"""Extract location and case information from indexed news chunks for real-time map updates."""
from __future__ import annotations

import re
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta


# Country/location patterns for extraction
LOCATION_PATTERNS = {
    "argentina": {"lat": -34.6037, "lon": -58.3816, "code": "ARG"},
    "spain": {"lat": 40.4168, "lon": -3.7038, "code": "ESP"},
    "usa": {"lat": 39.8283, "lon": -98.5795, "code": "USA"},
    "united states": {"lat": 39.8283, "lon": -98.5795, "code": "USA"},
    "united kingdom": {"lat": 55.3781, "lon": -3.4360, "code": "GBR"},
    "uk": {"lat": 55.3781, "lon": -3.4360, "code": "GBR"},
    "netherlands": {"lat": 52.1326, "lon": 5.2913, "code": "NLD"},
    "south africa": {"lat": -30.5595, "lon": 22.9375, "code": "ZAF"},
    "canary islands": {"lat": 28.1, "lon": -15.4, "code": "ESP"},
    "tenerife": {"lat": 28.2916, "lon": -16.6291, "code": "ESP"},
    "cape verde": {"lat": 16.5388, "lon": -24.0132, "code": "CPV"},
    "cabo verde": {"lat": 16.5388, "lon": -24.0132, "code": "CPV"},
    "chile": {"lat": -35.6751, "lon": -71.5430, "code": "CHL"},
    "brazil": {"lat": -14.2350, "lon": -51.9253, "code": "BRA"},
    "peru": {"lat": -9.1900, "lon": -75.0152, "code": "PER"},
    "bolivia": {"lat": -16.2902, "lon": -63.5887, "code": "BOL"},
    "patagonia": {"lat": -41.8106, "lon": -68.9063, "code": "ARG"},
}

# Case number extraction patterns
CASE_PATTERNS = [
    r"(\d+)\s*(?:new\s+)?(?:confirmed|suspected|probable)\s*cases?",
    r"(\d+)\s*cases?\s*(?:confirmed|suspected|reported)",
    r"(\d+)\s*(?:additional\s+)?patients?",
    r"(\d+)\s*infected",
    r"(\d+)\s*positive",
    r"total\s*(?:of\s+)?(\d+)\s*cases?",
    r"(\d+)\s*deaths?",
    r"(\d+)\s*fatalities",
]

# Severity keywords
SEVERITY_KEYWORDS = {
    "critical": 4,
    "severe": 3,
    "confirmed": 3,
    "outbreak": 3,
    "suspected": 2,
    "possible": 1,
    "monitoring": 1,
}


def extract_locations_from_chunk(chunk_text: str, chunk_metadata: dict = None) -> List[Dict]:
    """
    Extract location and case information from a news chunk.

    Args:
        chunk_text: The text content of the chunk
        chunk_metadata: Optional metadata about the chunk

    Returns:
        List of location data dictionaries with lat, lon, cases, severity, etc.
    """
    locations = []
    text_lower = chunk_text.lower()

    # Find mentioned locations
    mentioned_locations = []
    for location_name, coords in LOCATION_PATTERNS.items():
        if location_name in text_lower:
            mentioned_locations.append((location_name, coords))

    if not mentioned_locations:
        return locations

    # Extract case numbers
    case_numbers = []
    for pattern in CASE_PATTERNS:
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            try:
                num = int(match.group(1))
                if 1 <= num <= 10000:  # Reasonable case range
                    case_numbers.append(num)
            except (ValueError, IndexError):
                continue

    # Calculate severity
    severity = 1
    for keyword, weight in SEVERITY_KEYWORDS.items():
        if keyword in text_lower:
            severity = max(severity, weight)

    # Create location entries
    for location_name, coords in mentioned_locations:
        # Use the highest case number found, or 1 as minimum
        cases = max(case_numbers) if case_numbers else 1

        location_data = {
            "name": location_name.title(),
            "lat": coords["lat"],
            "lon": coords["lon"],
            "code": coords["code"],
            "cases": cases,
            "severity": severity,
            "glow_intensity": min(severity * 25, 100),
            "timestamp": datetime.utcnow().isoformat(),
            "source_text": chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text,
            "metadata": chunk_metadata or {},
        }

        locations.append(location_data)

    return locations


def get_dynamic_map_hotspots() -> List[Dict]:
    """
    Get dynamic map hotspots based on recently indexed news chunks.

    Returns:
        List of hotspot dictionaries for map rendering
    """
    try:
        from vectorstore.store import similarity_search
        from alerts.persistent_kv import kv_get

        # Search for recent hantavirus/outbreak content
        recent_chunks = []
        search_terms = [
            "hantavirus cases",
            "outbreak suspected",
            "confirmed patients",
            "mv hondius",
            "andes virus",
        ]

        for term in search_terms:
            try:
                results = similarity_search(term, k=10)
                recent_chunks.extend(results)
            except Exception:
                continue

        # Extract locations from all chunks
        all_locations = []
        seen_locations = set()

        for chunk in recent_chunks:
            if isinstance(chunk, dict) and "text" in chunk:
                locations = extract_locations_from_chunk(
                    chunk["text"],
                    chunk.get("metadata", {})
                )

                for loc in locations:
                    # Avoid duplicates based on location name
                    loc_key = f"{loc['name']}_{loc['code']}"
                    if loc_key not in seen_locations:
                        seen_locations.add(loc_key)
                        all_locations.append(loc)

        # Convert to map hotspot format
        hotspots = []
        for i, loc in enumerate(all_locations):
            hotspot = {
                "id": f"news_hotspot_{i}",
                "name": f"{loc['name']} - {loc['cases']} cases",
                "lat": loc["lat"],
                "lon": loc["lon"],
                "intensity": loc["glow_intensity"],
                "radius": max(15, loc["cases"] * 2),
                "color": _get_severity_color(loc["severity"]),
                "pulseSpeed": max(0.5, 3.0 / loc["severity"]),
                "cases": loc["cases"],
                "severity": loc["severity"],
                "timestamp": loc["timestamp"],
                "source": "news_analysis",
                "connectToShip": True,  # Always connect to MV Hondius
            }
            hotspots.append(hotspot)

        # Add MV Hondius position
        ship_hotspot = {
            "id": "mv_hondius",
            "name": "MV Hondius - Primary Outbreak Site",
            "lat": 28.5, "lon": -15.0,  # Near Canary Islands
            "intensity": 100,
            "radius": 25,
            "color": "#dc2626",  # Red for primary outbreak
            "pulseSpeed": 1.0,
            "cases": _get_total_outbreak_cases(),
            "severity": 4,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "ship_tracking",
            "connectToShip": False,  # This IS the ship
        }
        hotspots.insert(0, ship_hotspot)

        return hotspots

    except Exception as e:
        # Fallback to empty list if extraction fails
        return []


def _get_severity_color(severity: int) -> str:
    """Get color code based on severity level."""
    colors = {
        1: "#fbbf24",  # Yellow - monitoring
        2: "#f59e0b",  # Orange - suspected
        3: "#dc2626",  # Red - confirmed
        4: "#b91c1c",  # Dark red - critical
    }
    return colors.get(severity, "#64748b")


def _get_total_outbreak_cases() -> int:
    """Get total outbreak cases from stats."""
    try:
        from ui.stats_panel import get_outbreak_stats
        stats = get_outbreak_stats()
        return stats.get("confirmed_cases", 8)
    except Exception:
        return 8


def update_map_from_news_ingestion(new_chunks: List[Dict]) -> None:
    """
    Trigger map update after news ingestion.

    Args:
        new_chunks: List of newly ingested chunks
    """
    try:
        from alerts.signal_dispatcher import fire_signal

        # Extract locations from new chunks
        new_locations = []
        for chunk in new_chunks:
            if isinstance(chunk, dict) and "text" in chunk:
                locations = extract_locations_from_chunk(
                    chunk["text"],
                    chunk.get("metadata", {})
                )
                new_locations.extend(locations)

        if new_locations:
            # Fire detailed signals for each new location
            from alerts.signal_dispatcher import fire_hotspot_signal, fire_connection_signal

            for loc in new_locations:
                is_glowing = loc["glow_intensity"] > 50

                fire_hotspot_signal(
                    loc["name"],
                    loc["cases"],
                    loc["severity"],
                    is_glowing
                )

                # Signal connection line if this location connects to ship
                if loc.get("connectToShip", False):
                    fire_connection_signal(loc["name"], "MV Hondius")

            # Fire summary signal
            location_names = [loc["name"] for loc in new_locations]
            total_cases = sum(loc["cases"] for loc in new_locations)
            high_severity = [loc for loc in new_locations if loc["severity"] >= 3]

            if high_severity:
                fire_signal(
                    "alert",
                    f"🚨 HIGH-SEVERITY LOCATIONS: {len(high_severity)} critical/confirmed hotspots added to map",
                    "THREAT_MONITOR"
                )

            fire_signal(
                "map",
                f"📡 Map updated: {len(new_locations)} new locations, {total_cases} total cases tracked",
                "NEWS_ANALYZER"
            )

            # Store update timestamp for map refresh
            from alerts.persistent_kv import kv_set
            kv_set("last_map_update", datetime.utcnow().isoformat())

    except Exception as e:
        # Don't break news ingestion if map update fails
        pass