"""Text chunker using LangChain RecursiveCharacterTextSplitter."""
from __future__ import annotations

from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter


CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


def chunk_documents(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    chunks: list[dict[str, Any]] = []
    for doc in documents:
        text = _extract_text(doc)
        if not text:
            continue

        splits = splitter.split_text(text)
        metadata = _extract_metadata(doc)

        for i, chunk_text in enumerate(splits):
            chunk = {
                **metadata,
                "text": chunk_text,
                "chunk_index": i,
                "chunk_total": len(splits),
            }
            chunks.append(chunk)

    return chunks


def _extract_text(doc: dict[str, Any]) -> str:
    return doc.get("text") or doc.get("abstract") or doc.get("summary") or ""


def _extract_metadata(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": doc.get("source", doc.get("source_type", "unknown")),
        "source_type": doc.get("type", doc.get("source_type", "unknown")),
        "title": doc.get("title", doc.get("filename", "")),
        "url": doc.get("url", ""),
        "date": doc.get("date", ""),
        "authors": doc.get("authors", ""),
        "doi": doc.get("doi", ""),
        "filename": doc.get("filename", ""),
    }


if __name__ == "__main__":
    sample_docs = [
        {
            "text": "Andes orthohantavirus is a species of hantavirus. " * 50,
            "source": "Wikipedia",
            "title": "Andes orthohantavirus",
            "url": "https://en.wikipedia.org/wiki/Andes_orthohantavirus",
            "date": "2024-01",
            "type": "encyclopedia",
        }
    ]
    chunks = chunk_documents(sample_docs)
    print(f"Generated {len(chunks)} chunks from {len(sample_docs)} documents")
