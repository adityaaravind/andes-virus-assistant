"""Live news headlines — card grid, color-coded by source, auto-refreshes hourly."""
from __future__ import annotations

from datetime import datetime
from typing import Any

import feedparser
import streamlit as st


RSS_FEEDS = [
    {"url": "https://www.who.int/rss-feeds/news-english.xml",       "source": "WHO",         "tier": "official"},
    {"url": "https://rss.cdc.gov/podcasts/2016/4048.rss",            "source": "CDC",         "tier": "official"},
    {"url": "https://www.ecdc.europa.eu/en/rss.xml",                 "source": "ECDC",        "tier": "official"},
    {"url": "https://feeds.reuters.com/reuters/healthNews",          "source": "Reuters",     "tier": "press"},
    {"url": "http://feeds.bbci.co.uk/news/health/rss.xml",           "source": "BBC Health",  "tier": "press"},
    {"url": "https://www.aljazeera.com/xml/rss/all.xml",             "source": "Al Jazeera",  "tier": "press"},
    {"url": "https://www.sciencedaily.com/rss/health_medicine/infectious_diseases.xml",
                                                                      "source": "ScienceDaily","tier": "science"},
]

FILTER_KEYWORDS = {
    "hantavirus", "hondius", "andes virus", "andes orthohantavirus",
    "hps", "hanta", "hemorrhagic fever with renal",
}

# Visual config per tier
TIER_STYLE = {
    "official": {
        "border":  "#22c55e",
        "bg":      "rgba(34,197,94,0.07)",
        "badge_bg":"rgba(34,197,94,0.18)",
        "badge_fg":"#22c55e",
        "glow":    "rgba(34,197,94,0.15)",
        "icon":    "🏥",
    },
    "press": {
        "border":  "#00b4d8",
        "bg":      "rgba(0,180,216,0.07)",
        "badge_bg":"rgba(0,180,216,0.18)",
        "badge_fg":"#00b4d8",
        "glow":    "rgba(0,180,216,0.15)",
        "icon":    "📰",
    },
    "science": {
        "border":  "#a78bfa",
        "bg":      "rgba(167,139,250,0.07)",
        "badge_bg":"rgba(167,139,250,0.18)",
        "badge_fg":"#a78bfa",
        "glow":    "rgba(167,139,250,0.15)",
        "icon":    "🔬",
    },
}

SOURCE_TIER = {f["source"]: f["tier"] for f in RSS_FEEDS}
SOURCE_CREDIBILITY = {
    "WHO": 1.0, "CDC": 1.0, "ECDC": 0.9,
    "Reuters": 0.75, "BBC Health": 0.75, "Al Jazeera": 0.7,
    "ScienceDaily": 0.8,
}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_headlines(max_per_feed: int = 6) -> list[dict[str, Any]]:
    seen: set[str] = set()
    articles: list[dict[str, Any]] = []

    for feed_cfg in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_cfg["url"])
            for entry in feed.entries[:max_per_feed]:
                title   = entry.get("title", "").strip()
                url     = entry.get("link", "")
                summary = entry.get("summary", "")
                text    = (title + " " + summary).lower()

                if not any(kw in text for kw in FILTER_KEYWORDS):
                    continue
                if url in seen or not title:
                    continue

                seen.add(url)
                articles.append({
                    "title":   title,
                    "url":     url,
                    "source":  feed_cfg["source"],
                    "tier":    feed_cfg["tier"],
                    "date":    _parse_date(entry),
                    "summary": summary[:220] + ("…" if len(summary) > 220 else ""),
                    "credibility": SOURCE_CREDIBILITY.get(feed_cfg["source"], 0.7),
                })
        except Exception:
            continue

    articles.sort(key=lambda a: a["date"], reverse=True)
    return articles


def _parse_date(entry: Any) -> str:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6]).strftime("%b %d, %H:%M UTC")
        except (ValueError, TypeError):
            pass
    return entry.get("published", "—")


def _card_html(art: dict[str, Any]) -> str:
    s = TIER_STYLE[art["tier"]]
    cred_pct = int(art["credibility"] * 100)
    cred_color = "#22c55e" if cred_pct >= 90 else "#f59e0b" if cred_pct >= 70 else "#94a3b8"
    title = art["title"].replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
    summary = art["summary"].replace("<", "&lt;").replace(">", "&gt;")

    # Single-line HTML — prevents Streamlit markdown treating indented lines as code blocks
    return (
        f'<div style="background:{s["bg"]};border:1px solid {s["border"]}44;border-top:3px solid {s["border"]};'
        f'border-radius:10px;padding:0.9rem 1rem;min-height:150px;box-shadow:0 4px 20px {s["glow"]};'
        f'display:flex;flex-direction:column;gap:0.5rem;margin-bottom:0.1rem;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;gap:0.5rem;">'
        f'<span style="background:{s["badge_bg"]};color:{s["badge_fg"]};font-size:0.68rem;font-weight:700;'
        f'letter-spacing:0.06em;padding:2px 8px;border-radius:20px;text-transform:uppercase;white-space:nowrap;">'
        f'{s["icon"]} {art["source"]}</span>'
        f'<span style="color:#475569;font-size:0.68rem;white-space:nowrap;">{art["date"]}</span>'
        f'</div>'
        f'<a href="{art["url"]}" target="_blank" rel="noopener" style="text-decoration:none;'
        f'color:#f1f5f9;font-size:0.87rem;font-weight:600;line-height:1.35;">{title}</a>'
        f'<p style="color:#94a3b8;font-size:0.75rem;line-height:1.4;margin:0;flex:1;">{summary}</p>'
        f'<div style="display:flex;align-items:center;gap:0.4rem;">'
        f'<div style="flex:1;height:3px;background:#1b2e45;border-radius:2px;">'
        f'<div style="width:{cred_pct}%;height:100%;background:{cred_color};border-radius:2px;"></div>'
        f'</div>'
        f'<span style="color:{cred_color};font-size:0.65rem;">{cred_pct}% credibility</span>'
        f'</div>'
        f'</div>'
    )


def render_news_ticker() -> None:
    col_title, col_ts = st.columns([5, 1])
    with col_title:
        st.markdown(
            '<span class="live-dot"></span>'
            '<span class="live-label">LIVE</span>'
            ' <span style="color:#f8fafc;font-size:1.15rem;font-weight:700;"> 📰 Live Outbreak Headlines</span>',
            unsafe_allow_html=True,
        )
    with col_ts:
        st.markdown(
            f"<p style='color:#64748b;font-size:0.72rem;text-align:right;padding-top:0.4rem;'>"
            f"↻ every 15 min<br>{datetime.utcnow().strftime('%H:%M UTC')}</p>",
            unsafe_allow_html=True,
        )

    with st.spinner("Fetching latest headlines…"):
        articles = fetch_headlines()

    if not articles:
        st.info(
            "No live headlines matching outbreak keywords right now. Feeds refresh every hour.",
            icon="📡",
        )
        return

    # Legend row
    st.markdown(
        "<div style='display:flex;gap:1.2rem;margin-bottom:0.6rem;flex-wrap:wrap;'>"
        "<span style='color:#22c55e;font-size:0.75rem;'>🏥 Official (WHO/CDC/ECDC)</span>"
        "<span style='color:#00b4d8;font-size:0.75rem;'>📰 Press (Reuters/BBC/AJ)</span>"
        "<span style='color:#a78bfa;font-size:0.75rem;'>🔬 Science</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    # 3-column card grid
    cols = st.columns(3)
    for i, art in enumerate(articles):
        with cols[i % 3]:
            st.markdown(_card_html(art), unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom:0.7rem;'></div>", unsafe_allow_html=True)
