# 🧬 Andes Virus Research Assistant

RAG-powered Streamlit app for journalists, health workers, and the public to query
the MV Hondius hantavirus outbreak with cited, AI-generated answers.

## Stack

- **LLM:** OpenAI GPT-4o-mini (falls back to HuggingFace offline)
- **Embeddings:** OpenAI text-embedding-3-small (fallback: all-MiniLM-L6-v2)
- **Vector store:** ChromaDB (persistent, local)
- **Data sources:** PubMed, WHO PDFs, RSS news, Wikipedia
- **UI:** Streamlit — chat, map, stats, source panel

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=sk-...
```

### 3. Run data ingestion

Fetches PubMed abstracts, WHO documents, news articles, and Wikipedia — chunks,
embeds, and stores everything in ChromaDB.

```bash
python scripts/ingest_all.py
```

Expected output: ~500–2000 chunks indexed depending on data availability.

### 4. Launch the app

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## Architecture

```
andes-virus-assistant/
├── app.py                    # Main Streamlit entry point
├── ingestion/
│   ├── pubmed_scraper.py     # BioPython Entrez API
│   ├── who_scraper.py        # WHO PDF downloader
│   ├── pdf_parser.py         # pdfplumber text extraction
│   ├── news_scraper.py       # RSS feed scraper
│   └── wikipedia_loader.py   # MediaWiki REST API
├── processing/
│   ├── chunker.py            # RecursiveCharacterTextSplitter
│   ├── embedder.py           # OpenAI / HuggingFace embeddings
│   └── metadata_tagger.py    # Credibility scoring
├── vectorstore/
│   └── chroma_store.py       # ChromaDB wrapper
├── rag/
│   ├── chain.py              # LangChain RAG chain
│   ├── retriever.py          # Similarity + credibility re-ranking
│   ├── prompt_templates.py   # System + human prompts
│   └── citation_formatter.py # Source card formatting
├── scripts/
│   └── ingest_all.py         # Full ingestion orchestrator
└── ui/
    ├── chat_panel.py         # Chat interface
    ├── source_panel.py       # Sidebar citation cards
    ├── map_panel.py          # Plotly choropleth map
    ├── stats_panel.py        # Metrics + timeline chart
    └── styles.css            # Navy/teal design system
```

## Credibility scores

| Source | Score |
|--------|-------|
| WHO / CDC | 1.0 |
| PubMed (peer-reviewed) | 0.9 |
| ECDC | 0.9 |
| Reuters / BBC | 0.75 |
| News (general) | 0.7 |
| Wikipedia | 0.6 |

Re-ranking formula: `rerank_score = similarity_score × credibility_score`

## Offline mode

If no `OPENAI_API_KEY` is set, embeddings fall back to `all-MiniLM-L6-v2` via
`sentence-transformers` (runs fully locally). The LLM answer generation requires
an API key — without it, the app shows setup instructions.

## Data refresh

Re-run `python scripts/ingest_all.py` at any time. Already-embedded documents
(checked by URL+content hash) are skipped automatically.
