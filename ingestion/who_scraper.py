"""WHO situation report scraper — downloads hantavirus PDFs."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


WHO_BASE = "https://www.who.int"
WHO_DISEASE_URL = "https://www.who.int/emergencies/disease-outbreak-news"
KEYWORDS = {"hantavirus", "hondius", "andes virus", "andes orthohantavirus"}
SAVE_DIR = Path("data/raw/who")
TIMEOUT = 30
HEADERS = {"User-Agent": "AndesVirusResearchAssistant/1.0"}


def download_who_pdfs(save_dir: Path = SAVE_DIR) -> list[dict[str, Any]]:
    save_dir.mkdir(parents=True, exist_ok=True)
    pdf_links = _find_pdf_links()
    downloaded: list[dict[str, Any]] = []

    for item in pdf_links:
        filename = _safe_filename(item["url"])
        dest = save_dir / filename
        if dest.exists():
            downloaded.append({**item, "path": str(dest), "status": "cached"})
            continue

        try:
            resp = requests.get(item["url"], timeout=TIMEOUT, headers=HEADERS)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
            downloaded.append({**item, "path": str(dest), "status": "downloaded"})
        except requests.RequestException as exc:
            downloaded.append({**item, "path": "", "status": f"error: {exc}"})

    return downloaded


def _find_pdf_links() -> list[dict[str, str]]:
    links: list[dict[str, str]] = []

    candidate_pages = [
        WHO_DISEASE_URL,
        # WHO DON599 — confirmed 2026 hantavirus MV Hondius outbreak report
        "https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON599",
        "https://www.who.int/news-room/fact-sheets/detail/hantavirus-pulmonary-syndrome",
        # WHO OData outbreaks API (may populate as outbreak progresses)
        "https://www.who.int/api/news/outbreaks",
        # Broader search pages for any recent DON reports
        "https://www.who.int/emergencies/disease-outbreak-news?sf_Status=Active",
        "https://www.who.int/csr/don/en/",
    ]

    for page_url in candidate_pages:
        try:
            resp = requests.get(page_url, timeout=TIMEOUT, headers=HEADERS)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            _extract_from_soup(soup, page_url, links)
        except requests.RequestException:
            continue

    return _deduplicate(links)


def _extract_from_soup(
    soup: BeautifulSoup, base_url: str, links: list[dict[str, str]]
) -> None:
    for tag in soup.find_all("a", href=True):
        href: str = tag["href"]
        text = tag.get_text(strip=True).lower()
        combined = (href + " " + text).lower()

        if any(kw in combined for kw in KEYWORDS):
            full_url = href if href.startswith("http") else urljoin(WHO_BASE, href)
            if href.endswith(".pdf"):
                links.append({"url": full_url, "title": tag.get_text(strip=True)})
            elif not href.endswith((".jpg", ".png", ".gif")):
                links.extend(_find_pdfs_on_page(full_url))


def _find_pdfs_on_page(url: str) -> list[dict[str, str]]:
    try:
        resp = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        return [
            {"url": urljoin(WHO_BASE, a["href"]), "title": a.get_text(strip=True)}
            for a in soup.find_all("a", href=True)
            if a["href"].endswith(".pdf")
        ]
    except requests.RequestException:
        return []


def _deduplicate(links: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for item in links:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)
    return unique


def _safe_filename(url: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", url.split("/")[-1])
    return name if name.endswith(".pdf") else name + ".pdf"


if __name__ == "__main__":
    results = download_who_pdfs()
    print(f"Processed {len(results)} WHO documents")
    for r in results:
        print(f"  {r['status']}: {r.get('path', r['url'])}")
