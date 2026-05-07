"""PubMed scraper using BioPython Entrez API."""
from __future__ import annotations

import time
from typing import Any

from Bio import Entrez


Entrez.email = "andes-virus-assistant@research.org"

SEARCH_QUERY = (
    '"Andes virus"[Title/Abstract] OR "Andes orthohantavirus"[Title/Abstract] OR '
    '"hantavirus pulmonary syndrome"[Title/Abstract] OR '
    '"hantavirus human-to-human transmission"[Title/Abstract] OR '
    '"MV Hondius"[Title/Abstract] OR '
    '"hantavirus outbreak"[Title/Abstract] OR '
    '"hantavirus cruise ship"[Title/Abstract] OR '
    '"hantavirus 2025"[Title/Abstract]'
)
MAX_RESULTS = 300


def fetch_abstracts(max_results: int = MAX_RESULTS) -> list[dict[str, Any]]:
    search_handle = Entrez.esearch(
        db="pubmed",
        term=SEARCH_QUERY,
        retmax=max_results,
        sort="relevance",
    )
    search_record = Entrez.read(search_handle)
    search_handle.close()

    ids = search_record["IdList"]
    if not ids:
        return []

    fetch_handle = Entrez.efetch(
        db="pubmed",
        id=",".join(ids),
        rettype="xml",
        retmode="xml",
    )
    records = Entrez.read(fetch_handle)
    fetch_handle.close()

    results: list[dict[str, Any]] = []
    for article in records["PubmedArticle"]:
        try:
            medline = article["MedlineCitation"]
            art = medline["Article"]

            title = str(art.get("ArticleTitle", ""))
            abstract_texts = art.get("Abstract", {}).get("AbstractText", [])
            if isinstance(abstract_texts, list):
                abstract = " ".join(str(t) for t in abstract_texts)
            else:
                abstract = str(abstract_texts)

            authors_list = art.get("AuthorList", [])
            authors = "; ".join(
                f"{a.get('LastName', '')} {a.get('ForeName', '')}".strip()
                for a in authors_list
                if "LastName" in a
            )

            pub_date = _extract_date(art)
            doi = _extract_doi(article)
            pmid = str(medline["PMID"])
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

            if abstract:
                results.append({
                    "title": title,
                    "abstract": abstract,
                    "authors": authors,
                    "source": "PubMed",
                    "date": pub_date,
                    "url": url,
                    "doi": doi,
                    "pmid": pmid,
                    "type": "research",
                })
        except (KeyError, AttributeError):
            continue

        time.sleep(0.1)

    return results


def _extract_date(art: dict[str, Any]) -> str:
    try:
        journal = art.get("Journal", {})
        issue = journal.get("JournalIssue", {})
        pub_date = issue.get("PubDate", {})
        year = str(pub_date.get("Year", ""))
        month = str(pub_date.get("Month", ""))
        return f"{year}-{month}" if month else year
    except (KeyError, AttributeError):
        return ""


def _extract_doi(article: dict[str, Any]) -> str:
    try:
        ids = article["PubmedData"]["ArticleIdList"]
        for aid in ids:
            if str(aid.attributes.get("IdType", "")) == "doi":
                return str(aid)
    except (KeyError, AttributeError):
        pass
    return ""


if __name__ == "__main__":
    records = fetch_abstracts(max_results=10)
    print(f"Fetched {len(records)} PubMed records")
    if records:
        print(records[0]["title"])
