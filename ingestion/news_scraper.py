"""RSS + Google News scraper filtered for hantavirus / Andes / Hondius coverage."""
from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

import feedparser
import requests
from bs4 import BeautifulSoup


# ── Verified working feeds (audited 2026-05-07) ───────────────────────────────
RSS_FEEDS = [
    # Official health authorities
    {"url": "https://www.who.int/rss-feeds/news-english.xml",                                    "source": "WHO",              "credibility": 1.00},
    {"url": "https://www.paho.org/en/rss.xml",                                                   "source": "PAHO",             "credibility": 1.00},
    {"url": "https://www.cidrap.umn.edu/rss.xml",                                                "source": "CIDRAP",           "credibility": 0.95},
    {"url": "https://www.ecdc.europa.eu/en/rss.xml",                                             "source": "ECDC",             "credibility": 0.95},

    # Outbreak-specific
    {"url": "https://outbreaknewstoday.com/feed/",                                               "source": "Outbreak News",    "credibility": 0.88},

    # Peer-reviewed journals
    {"url": "https://www.thelancet.com/rssfeed/lancet_online.xml",                               "source": "The Lancet",       "credibility": 0.97},
    {"url": "https://www.nejm.org/action/showFeed?jc=nejm&type=etoc&feed=rss",                   "source": "NEJM",             "credibility": 0.97},
    {"url": "https://www.nature.com/subjects/infectious-diseases.rss",                           "source": "Nature",           "credibility": 0.95},
    {"url": "https://www.sciencedaily.com/rss/health_medicine/infectious_diseases.xml",          "source": "ScienceDaily",     "credibility": 0.80},

    # News media (BBC works; Reuters RSS removed their public feed)
    {"url": "http://feeds.bbci.co.uk/news/health/rss.xml",                                       "source": "BBC Health",       "credibility": 0.78},
    {"url": "https://www.aljazeera.com/xml/rss/all.xml",                                         "source": "Al Jazeera",       "credibility": 0.72},

    # Google News targeted RSS — highest recall for outbreak-specific coverage
    {"url": "https://news.google.com/rss/search?q=hantavirus&hl=en-US&gl=US&ceid=US:en",         "source": "Google News",      "credibility": 0.65},
    {"url": "https://news.google.com/rss/search?q=%22MV+Hondius%22&hl=en-US&gl=US&ceid=US:en",  "source": "Google News",      "credibility": 0.65},
    {"url": "https://news.google.com/rss/search?q=%22andes+virus%22+outbreak&hl=en-US&gl=US&ceid=US:en", "source": "Google News", "credibility": 0.65},
    {"url": "https://news.google.com/rss/search?q=hantavirus+cruise+ship&hl=en-US&gl=US&ceid=US:en",     "source": "Google News", "credibility": 0.65},
]

FILTER_KEYWORDS = {
    "hantavirus", "hondius", "andes virus", "andes orthohantavirus",
    "hanta", "hps", "hantavirus pulmonary", "orthohantavirus",
    "sin nombre virus", "dobrava", "seoul virus",
    "cruise ship outbreak", "cape verde outbreak",
    "mv hondius", "hantavirus outbreak",
}

TIMEOUT = 20
HEADERS = {"User-Agent": "AndesVirusResearchAssistant/1.0 (research; contact: research@example.org)"}


def scrape_all_feeds() -> list[dict[str, Any]]:
    seen_urls: set[str] = set()
    articles: list[dict[str, Any]] = []
    for feed_config in RSS_FEEDS:
        try:
            articles.extend(_parse_feed(feed_config, seen_urls))
        except Exception:
            continue
    return articles


# Alias used by fast_news_poll in app.py
scrape_all = scrape_all_feeds


def _parse_feed(config: dict[str, str], seen_urls: set[str]) -> list[dict[str, Any]]:
    feed = feedparser.parse(config["url"])
    results: list[dict[str, Any]] = []

    for entry in feed.entries:
        title   = entry.get("title", "")
        url     = entry.get("link", "")
        summary = entry.get("summary", "")
        combined = (title + " " + summary).lower()

        if not _matches_keywords(combined):
            continue
        if url in seen_urls:
            continue

        seen_urls.add(url)
        full_text = _fetch_article_text(url) or summary

        results.append({
            "title":    title,
            "text":     full_text,
            "summary":  summary[:500],
            "url":      url,
            "date":     _parse_date(entry),
            "source":   config["source"],
            "credibility": config.get("credibility", 0.7),
            "type":     "news",
            "url_hash": hashlib.md5(url.encode()).hexdigest(),
        })

    return results


def _matches_keywords(text: str) -> bool:
    return any(kw in text for kw in FILTER_KEYWORDS)


def _parse_date(entry: Any) -> str:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass
    return entry.get("published", "")


def _fetch_article_text(url: str) -> str | None:
    # Skip Google News redirect URLs — summary is sufficient
    if "news.google.com" in url:
        return None
    try:
        resp = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50)
        return text if len(text) > 200 else None
    except Exception:
        return None


if __name__ == "__main__":
    articles = scrape_all_feeds()
    print(f"Found {len(articles)} matching articles")
    for a in articles[:10]:
        print(f"  [{a['source']}] {a['title'][:80]}")
