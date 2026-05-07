"""RSS + Google News + GDELT + EuropePMC + NewsAPI/GNews scraper — 2026 hantavirus MV Hondius."""
from __future__ import annotations

import hashlib
import json
import os
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

    # Google News targeted RSS — high recall for outbreak-specific coverage (2026)
    {"url": "https://news.google.com/rss/search?q=hantavirus+2026&hl=en-US&gl=US&ceid=US:en",                "source": "Google News",      "credibility": 0.65},
    {"url": "https://news.google.com/rss/search?q=%22MV+Hondius%22+2026&hl=en-US&gl=US&ceid=US:en",         "source": "Google News",      "credibility": 0.65},
    {"url": "https://news.google.com/rss/search?q=%22andes+virus%22+2026+outbreak&hl=en-US&gl=US&ceid=US:en","source": "Google News",      "credibility": 0.65},
    {"url": "https://news.google.com/rss/search?q=hantavirus+cruise+ship+2026&hl=en-US&gl=US&ceid=US:en",    "source": "Google News",      "credibility": 0.65},
    {"url": "https://news.google.com/rss/search?q=DON599+WHO+hantavirus&hl=en-US&gl=US&ceid=US:en",          "source": "Google News",      "credibility": 0.65},
]

FILTER_KEYWORDS = {
    "hantavirus", "hondius", "andes virus", "andes orthohantavirus",
    "hanta", "hps", "hantavirus pulmonary", "orthohantavirus",
    "mv hondius", "hantavirus outbreak", "don599", "2026-don599",
    "cabo verde hantavirus", "hantavirus cruise",
}

TIMEOUT = 20
HEADERS = {"User-Agent": "AndesVirusResearchAssistant/1.0 (research; contact: research@example.org)"}

# ── 2026-only date filter — reject articles clearly about pre-2026 outbreaks ──
_YEAR_WHITELIST = {"2026", "don599"}
_YEAR_BLACKLIST_TERMS = {"2024", "2023", "2022", "sin nombre", "seoul virus", "dobrava"}


def _is_2026_relevant(text: str) -> bool:
    """Return False if article is clearly about a pre-2026 hantavirus event."""
    lower = text.lower()
    if any(t in lower for t in _YEAR_BLACKLIST_TERMS):
        # Allow if also mentions 2026 or Hondius (comparative coverage)
        if not any(t in lower for t in ("2026", "hondius", "mv hondius", "don599")):
            return False
    return True


def scrape_all_feeds() -> list[dict[str, Any]]:
    seen_urls: set[str] = set()
    articles: list[dict[str, Any]] = []

    for feed_config in RSS_FEEDS:
        try:
            articles.extend(_parse_feed(feed_config, seen_urls))
        except Exception:
            continue

    # GDELT — free, no key, global news intelligence
    try:
        articles.extend(_scrape_gdelt(seen_urls))
    except Exception:
        pass

    # EuropePMC — research papers on hantavirus 2026
    try:
        articles.extend(_scrape_europepmc(seen_urls))
    except Exception:
        pass

    # NewsAPI — requires NEWSAPI_KEY env var
    newsapi_key = os.getenv("NEWSAPI_KEY", "")
    if newsapi_key:
        try:
            articles.extend(_scrape_newsapi(newsapi_key, seen_urls))
        except Exception:
            pass

    # GNews — requires GNEWS_KEY env var
    gnews_key = os.getenv("GNEWS_KEY", "")
    if gnews_key:
        try:
            articles.extend(_scrape_gnews(gnews_key, seen_urls))
        except Exception:
            pass

    # Apply 2026-only filter — drop clearly pre-2026 hantavirus stories
    articles = [a for a in articles if _is_2026_relevant(a.get("title", "") + " " + a.get("summary", ""))]

    return articles


# Alias used by fast_news_poll in app.py
scrape_all = scrape_all_feeds


def _scrape_gdelt(seen_urls: set[str]) -> list[dict[str, Any]]:
    """GDELT v2 doc API — free, no key, global coverage."""
    queries = [
        "hantavirus MV Hondius 2026",
        "andes virus outbreak 2026",
        "hantavirus cruise ship 2026",
    ]
    results: list[dict[str, Any]] = []
    for q in queries:
        url = (
            "https://api.gdeltproject.org/api/v2/doc/doc"
            f"?query={requests.utils.quote(q)}&mode=artlist&format=json&maxrecords=25"
            "&timespan=LAST7DAYS&sort=datedesc"
        )
        try:
            resp = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
            resp.raise_for_status()
            data = resp.json()
            for art in data.get("articles", []):
                art_url = art.get("url", "")
                if not art_url or art_url in seen_urls:
                    continue
                title = art.get("title", "")
                combined = title.lower()
                if not _matches_keywords(combined):
                    continue
                seen_urls.add(art_url)
                results.append({
                    "title":       title,
                    "text":        art.get("seendate", "") + " " + title,
                    "summary":     title,
                    "url":         art_url,
                    "date":        art.get("seendate", "")[:8],
                    "source":      "GDELT",
                    "credibility": 0.60,
                    "type":        "news",
                    "url_hash":    hashlib.md5(art_url.encode()).hexdigest(),
                })
        except Exception:
            continue
    return results


def _scrape_europepmc(seen_urls: set[str]) -> list[dict[str, Any]]:
    """EuropePMC REST API — peer-reviewed hantavirus 2026 papers."""
    url = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        "?query=hantavirus+andes+2026+cruise&format=json&pageSize=20&sort=date+desc"
    )
    resp = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    results: list[dict[str, Any]] = []
    for item in data.get("resultList", {}).get("result", []):
        art_url = f"https://europepmc.org/article/{item.get('source','')}/{item.get('id','')}"
        if art_url in seen_urls:
            continue
        title = item.get("title", "")
        abstract = item.get("abstractText", "") or ""
        if not _matches_keywords((title + " " + abstract).lower()):
            continue
        seen_urls.add(art_url)
        pub_date = item.get("firstPublicationDate", "")
        results.append({
            "title":       title,
            "text":        abstract,
            "summary":     abstract[:500],
            "url":         art_url,
            "date":        pub_date,
            "source":      "EuropePMC",
            "credibility": 0.90,
            "type":        "research",
            "url_hash":    hashlib.md5(art_url.encode()).hexdigest(),
        })
    return results


def _scrape_newsapi(api_key: str, seen_urls: set[str]) -> list[dict[str, Any]]:
    """NewsAPI.org — requires NEWSAPI_KEY env var."""
    queries = [
        "hantavirus 2026 MV Hondius",
        "andes virus outbreak 2026",
    ]
    results: list[dict[str, Any]] = []
    for q in queries:
        url = (
            "https://newsapi.org/v2/everything"
            f"?q={requests.utils.quote(q)}&language=en&sortBy=publishedAt&pageSize=20"
        )
        resp = requests.get(url, timeout=TIMEOUT, headers={**HEADERS, "X-Api-Key": api_key})
        resp.raise_for_status()
        for art in resp.json().get("articles", []):
            art_url = art.get("url", "")
            if not art_url or art_url in seen_urls:
                continue
            title = art.get("title", "") or ""
            desc = art.get("description", "") or ""
            if not _matches_keywords((title + " " + desc).lower()):
                continue
            seen_urls.add(art_url)
            results.append({
                "title":       title,
                "text":        art.get("content", desc),
                "summary":     desc[:500],
                "url":         art_url,
                "date":        (art.get("publishedAt", "") or "")[:10],
                "source":      f"NewsAPI/{art.get('source', {}).get('name', 'Unknown')}",
                "credibility": 0.70,
                "type":        "news",
                "url_hash":    hashlib.md5(art_url.encode()).hexdigest(),
            })
    return results


def _scrape_gnews(api_key: str, seen_urls: set[str]) -> list[dict[str, Any]]:
    """GNews.io — requires GNEWS_KEY env var."""
    url = (
        "https://gnews.io/api/v4/search"
        f"?q=hantavirus+2026&lang=en&sortby=publishedAt&max=20&apikey={api_key}"
    )
    resp = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
    resp.raise_for_status()
    results: list[dict[str, Any]] = []
    for art in resp.json().get("articles", []):
        art_url = art.get("url", "")
        if not art_url or art_url in seen_urls:
            continue
        title = art.get("title", "") or ""
        desc = art.get("description", "") or ""
        if not _matches_keywords((title + " " + desc).lower()):
            continue
        seen_urls.add(art_url)
        results.append({
            "title":       title,
            "text":        art.get("content", desc),
            "summary":     desc[:500],
            "url":         art_url,
            "date":        (art.get("publishedAt", "") or "")[:10],
            "source":      f"GNews/{art.get('source', {}).get('name', 'Unknown')}",
            "credibility": 0.68,
            "type":        "news",
            "url_hash":    hashlib.md5(art_url.encode()).hexdigest(),
        })
    return results


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
