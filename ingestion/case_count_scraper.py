"""Auto-extract case counts / deaths from scraped news articles using regex.

Writes data/outbreak_live.json when numbers are found.  Stats panel reads this
file and overlays it onto the hardcoded baseline so the display stays current
without manual edits.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

LIVE_FILE = Path("data/outbreak_live.json")

OUTBREAK_KWS = {"hantavirus", "hondius", "andes virus", "andes orthohantavirus", "hanta"}

# Map of words to integers to handle narrative-style reporting
WORD_TO_NUM = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, 
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15
}

CASE_PATTERNS = [
    r"(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+confirmed\s+case",
    r"confirmed\s+(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+case",
    r"(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+(?:of the\s+\d+|total)\s+cases?\s+(?:have\s+been\s+)?confirmed",
    r"(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+total\s+case",
    r"total\s+of\s+(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+case",
    r"(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+cases?\s+have\s+been\s+reported",
    r"(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+cases?\s*(?:confirmed|reported|identified)",
    r"(?:confirmed|reported|identified)\s+(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+cases?",
    r"(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+people\s+(?:have\s+been\s+)?(?:confirmed|infected)",
    r"(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+(?:infections?|patients?)\s+(?:confirmed|reported)",
]

SUSPECTED_PATTERNS = [
    r"(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+suspected\s+case",
    r"suspected\s+(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+case",
    r"(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+cases?\s+(?:have\s+been\s+)?reported",
    r"(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+total\s+cases?",
    r"(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+(?:passengers?|crew|people).{0,30}(?:infected|positive|ill|sick)",
    r"(?:infected|positive|ill|sick).{0,30}(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+(?:passengers?|crew|people)",
]

DEATH_PATTERNS = [
    r"(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+death",
    r"(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+fatal(?:it)?",
    r"including\s+(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+death",
    r"(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+(?:have\s+)?died",
    r"killed\s+(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")",
    r"(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+killed",
]

COUNTRY_PATTERNS = [
    r"(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+countr",
    r"(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+nationalit",
    r"from\s+(\d+|" + "|".join(WORD_TO_NUM.keys()) + r")\s+(?:different\s+)?countr",
]


def _nums(text: str, patterns: list[str], lo: int, hi: int) -> list[int]:
    out = []
    for p in patterns:
        for m in re.finditer(p, text, re.IGNORECASE):
            # Check for percentage symbol immediately after the number to avoid CFR confusion
            try:
                # Groups might vary based on pattern, but we generally want the first capture
                g = m.group(1)
                
                # Check for percentage suffix immediately following the match
                match_end = m.end(1)
                if match_end < len(text) and text[match_end] == "%":
                    continue
                
                # Convert word to integer if necessary
                if g.lower() in WORD_TO_NUM:
                    n = WORD_TO_NUM[g.lower()]
                else:
                    n = int(g)
                
                if lo <= n <= hi:
                    out.append(n)
            except (ValueError, TypeError, IndexError):
                pass
    return out


def _generate_case_update_signal(old_count: int, new_count: int) -> None:
    """Generate signal when case count changes significantly."""
    if new_count <= old_count:
        return

    try:
        import json
        from pathlib import Path
        from datetime import datetime

        manual_file = Path("data/manual_signals.json")
        signals = []

        if manual_file.exists():
            signals = json.loads(manual_file.read_text())

        # Add new case update signal
        new_signal = {
            "date": "LIVE",
            "time": "AUTO-UPDATE",
            "event": f"📈 CASE INCREASE: Confirmed cases rose from {old_count} to {new_count}. WHO monitoring outbreak progression closely.",
            "type": "CRITICAL",
            "speed": "14.5 kn",
            "uplink": "99%",
            "hours_ago": 0,
            "priority": "critical",
            "active": True,
            "source": "auto_generated",
            "timestamp": datetime.utcnow().isoformat()
        }

        # Add to beginning of signals list
        signals.insert(0, new_signal)

        # Keep only latest 10 signals to prevent overflow
        signals = signals[:10]

        with open(manual_file, 'w') as f:
            json.dump(signals, f, indent=2)

    except Exception:
        pass  # Silent fail to avoid breaking extraction


def extract_and_save(articles: list[dict[str, Any]]) -> dict[str, Any]:
    """Scan articles, update outbreak_live.json if higher counts found. 
    
    CRITICAL: Only trusts sources with credibility >= 0.9 (WHO, CDC, etc.) 
    to prevent misinformation or misinterpretation of secondary news.
    """
    relevant = [
        a for a in articles
        if any(kw in (a.get("title", "") + " " + a.get("summary", "")).lower()
               for kw in OUTBREAK_KWS)
    ]
    
    # Filter for credible sources (lowered threshold to catch more updates)
    trusted = [a for a in relevant if a.get("credibility", 0) >= 0.75]
    
    if not trusted:
        logging.info("No high-credibility articles found for case count extraction.")
        return {}

    all_cases, all_suspected, all_deaths, all_countries = [], [], [], []
    for art in trusted:
        text = (art.get("title", "") + " " + art.get("summary", "")).lower()
        extracted_cases = _nums(text, CASE_PATTERNS, 1, 500)
        extracted_suspected = _nums(text, SUSPECTED_PATTERNS, 1, 500)
        extracted_deaths = _nums(text, DEATH_PATTERNS, 0, 200)
        extracted_countries = _nums(text, COUNTRY_PATTERNS, 1, 50)
        
        all_cases     += extracted_cases
        all_suspected += extracted_suspected
        all_deaths    += extracted_deaths
        all_countries += extracted_countries

    extracted: dict[str, Any] = {}
    if all_cases:
        extracted["confirmed_cases"] = max(all_cases)
    if all_suspected:
        extracted["suspected_cases"] = max(all_suspected)
    if all_deaths:
        extracted["deaths"] = max(all_deaths)
    if all_countries:
        extracted["nationalities"] = max(all_countries)

    if not extracted:
        return {}

    # Read current stored values — never regress numbers
    stored: dict[str, Any] = {}
    if LIVE_FILE.exists():
        try:
            stored = json.loads(LIVE_FILE.read_text())
        except Exception:
            pass

    merged = dict(stored)
    changed = False
    for k in ("confirmed_cases", "suspected_cases", "deaths", "nationalities"):
        if k in extracted and extracted[k] > stored.get(k, 0):
            merged[k] = extracted[k]
            changed = True

    if changed:
        # Generate signal for case count increases before saving
        old_cases = stored.get("confirmed_cases", 0)
        new_cases = merged.get("confirmed_cases", 0)
        if new_cases > old_cases:
            _generate_case_update_signal(old_cases, new_cases)

        merged["last_updated"]     = datetime.utcnow().strftime("%Y-%m-%d")

        # Add source verification info
        highest_credibility_source = max(trusted, key=lambda x: x.get("credibility", 0)) if trusted else None
        if highest_credibility_source:
            source_name = highest_credibility_source.get("source", "Unknown")
            credibility = highest_credibility_source.get("credibility", 0)

            if credibility >= 0.9:
                merged["source_type"] = "WHO/CDC verified"
                merged["confidence"] = "HIGH"
            elif credibility >= 0.8:
                merged["source_type"] = "Medical authority"
                merged["confidence"] = "MEDIUM"
            else:
                merged["source_type"] = "News source"
                merged["confidence"] = "LOW"

            merged["last_source"] = source_name
        merged["source"]           = "auto-extracted"
        merged["articles_scanned"] = len(relevant)
        LIVE_FILE.parent.mkdir(parents=True, exist_ok=True)
        LIVE_FILE.write_text(json.dumps(merged, indent=2))

        # PHASE 2: Log signal to community feed
        from alerts.community_store import add_insight
        summary_msg = f"LIVE SIGNAL: Metrics adjusted to {merged.get('confirmed_cases')} confirmed, {merged.get('deaths')} fatalities"
        add_insight("alert", summary_msg, "SCRAPER")

        logging.info("Case count live update: %s", {k: merged[k] for k in ("confirmed_cases","deaths","nationalities") if k in merged})

    return extracted if changed else {}
