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

CASE_PATTERNS = [
    r"(\d+)\s+confirmed\s+case",
    r"confirmed\s+(\d+)\s+case",
    r"(\d+)\s+total\s+case",
    r"total\s+of\s+(\d+)\s+case",
]

SUSPECTED_PATTERNS = [
    r"(\d+)\s+suspected\s+case",
    r"suspected\s+(\d+)\s+case",
    r"(\d+)\s+(?:passengers?|crew|people).{0,30}(?:infected|positive|ill|sick)",
    r"(?:infected|positive|ill|sick).{0,30}(\d+)\s+(?:passengers?|crew|people)",
]

DEATH_PATTERNS = [
    r"(\d+)\s+death",
    r"(\d+)\s+fatal(?:it)?",
    r"(\d+)\s+(?:have\s+)?died",
    r"killed\s+(\d+)",
    r"(\d+)\s+killed",
]

COUNTRY_PATTERNS = [
    r"(\d+)\s+countr",
    r"(\d+)\s+nationalit",
    r"from\s+(\d+)\s+(?:different\s+)?countr",
]


def _nums(text: str, patterns: list[str], lo: int, hi: int) -> list[int]:
    out = []
    for p in patterns:
        for m in re.finditer(p, text, re.IGNORECASE):
            # Check for percentage symbol immediately after the number to avoid CFR confusion
            start, end = m.span(1)
            if end < len(text) and text[end] == "%":
                continue
            
            for g in m.groups():
                try:
                    n = int(g)
                    if lo <= n <= hi:
                        out.append(n)
                except (ValueError, TypeError):
                    pass
    return out


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
    
    # Filter for high-credibility sources only for numerical extraction
    trusted = [a for a in relevant if a.get("credibility", 0) >= 0.9]
    
    if not trusted:
        logging.info("No high-credibility articles found for case count extraction.")
        return {}

    all_cases, all_deaths, all_countries = [], [], []
    for art in trusted:
        text = (art.get("title", "") + " " + art.get("summary", "")).lower()
        all_cases    += _nums(text, CASE_PATTERNS, 1, 500)
        all_deaths   += _nums(text, DEATH_PATTERNS, 0, 200)
        all_countries += _nums(text, COUNTRY_PATTERNS, 1, 50)

    extracted: dict[str, Any] = {}
    if all_cases:
        extracted["confirmed_cases"] = max(all_cases)
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
        merged["last_updated"]     = datetime.utcnow().strftime("%Y-%m-%d")
        merged["source"]           = "auto-extracted"
        merged["articles_scanned"] = len(relevant)
        LIVE_FILE.parent.mkdir(parents=True, exist_ok=True)
        LIVE_FILE.write_text(json.dumps(merged, indent=2))
        logging.info("Case count live update: %s", {k: merged[k] for k in ("confirmed_cases","deaths","nationalities") if k in merged})

    return extracted if changed else {}
nt live update: %s", {k: merged[k] for k in ("confirmed_cases","deaths","nationalities") if k in merged})

    return extracted if changed else {}
nationalities") if k in merged})

    return extracted if changed else {}
