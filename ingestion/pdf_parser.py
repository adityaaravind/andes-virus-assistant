"""Extract and clean text from PDFs using pdfplumber."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pdfplumber


RAW_DIR = Path("data/raw")
HEADER_FOOTER_LINES = 3


def parse_all_pdfs(raw_dir: Path = RAW_DIR) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for pdf_path in raw_dir.rglob("*.pdf"):
        doc = parse_pdf(pdf_path)
        if doc:
            results.append(doc)
    return results


def parse_pdf(path: Path) -> dict[str, Any] | None:
    try:
        with pdfplumber.open(path) as pdf:
            pages_text: list[str] = []
            for page in pdf.pages:
                raw = page.extract_text() or ""
                cleaned = _clean_page(raw)
                if cleaned:
                    pages_text.append(cleaned)

            full_text = "\n\n".join(pages_text)
            if not full_text.strip():
                return None

            source_type = _infer_source_type(path)
            return {
                "text": full_text,
                "filename": path.name,
                "path": str(path),
                "source_type": source_type,
                "date": _extract_date_from_filename(path.name),
                "page_count": len(pdf.pages),
            }
    except Exception:
        return None


def _clean_page(text: str) -> str:
    lines = text.split("\n")
    if len(lines) > HEADER_FOOTER_LINES * 2:
        lines = lines[HEADER_FOOTER_LINES:-HEADER_FOOTER_LINES]

    lines = [l for l in lines if not _is_page_marker(l)]
    text = "\n".join(lines)
    text = re.sub(r"\s{3,}", "  ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _is_page_marker(line: str) -> bool:
    stripped = line.strip()
    if re.match(r"^(page\s*)?\d+(\s*of\s*\d+)?$", stripped, re.IGNORECASE):
        return True
    if re.match(r"^-\s*\d+\s*-$", stripped):
        return True
    return False


def _infer_source_type(path: Path) -> str:
    parts = str(path).lower()
    if "who" in parts:
        return "WHO"
    if "cdc" in parts:
        return "CDC"
    return "PDF"


def _extract_date_from_filename(name: str) -> str:
    match = re.search(r"(\d{4})[-_]?(\d{2})?[-_]?(\d{2})?", name)
    if match:
        parts = [p for p in match.groups() if p]
        return "-".join(parts)
    return ""


if __name__ == "__main__":
    docs = parse_all_pdfs()
    print(f"Parsed {len(docs)} PDFs")
    for d in docs:
        print(f"  {d['filename']}: {len(d['text'])} chars")
