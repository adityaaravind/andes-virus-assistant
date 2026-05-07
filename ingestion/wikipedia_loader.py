"""Wikipedia article loader using the MediaWiki REST API."""
from __future__ import annotations

import re
from typing import Any

import requests


WIKI_API = "https://en.wikipedia.org/w/api.php"
TARGET_ARTICLES = [
    "Andes orthohantavirus",
    "Hantavirus",
    "MV Hondius",
    "Hantavirus pulmonary syndrome",
    "Hemorrhagic fever with renal syndrome",
    "Orthohantavirus",
    "Sin Nombre orthohantavirus",
    "Zoonosis",
    "Rodent-borne disease",
    "Cruise ship outbreak",
    "Cape Verde",
    "Patagonia",
]
HEADERS = {"User-Agent": "AndesVirusResearchAssistant/1.0"}
TIMEOUT = 30


def load_wikipedia_articles(
    articles: list[str] = TARGET_ARTICLES,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for title in articles:
        doc = _fetch_article(title)
        if doc:
            results.append(doc)
    return results


def _fetch_article(title: str) -> dict[str, Any] | None:
    params = {
        "action": "query",
        "titles": title,
        "prop": "extracts|info|revisions",
        "exlimit": 1,
        "explaintext": True,
        "exsectionformat": "plain",
        "inprop": "url",
        "rvprop": "timestamp",
        "format": "json",
    }
    try:
        resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        page = next(iter(pages.values()))

        if "missing" in page:
            return None

        extract = page.get("extract", "")
        if not extract:
            return None

        clean_text = _clean_extract(extract)
        timestamp = ""
        if page.get("revisions"):
            timestamp = page["revisions"][0].get("timestamp", "")[:10]

        return {
            "title": page.get("title", title),
            "text": clean_text,
            "url": page.get("fullurl", f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"),
            "source": "Wikipedia",
            "date": timestamp,
            "type": "encyclopedia",
        }
    except (requests.RequestException, KeyError, StopIteration):
        return None


def _clean_extract(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"== See also ==.*", "", text, flags=re.DOTALL)
    text = re.sub(r"== References ==.*", "", text, flags=re.DOTALL)
    text = re.sub(r"== External links ==.*", "", text, flags=re.DOTALL)
    text = re.sub(r"== Notes ==.*", "", text, flags=re.DOTALL)
    return text.strip()


if __name__ == "__main__":
    docs = load_wikipedia_articles()
    print(f"Loaded {len(docs)} Wikipedia articles")
    for d in docs:
        print(f"  {d['title']}: {len(d['text'])} chars")
