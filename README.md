# 🧬 Andes Virus Research Assistant `v1.1`

**Real-time AI Outbreak Intelligence for the MV Hondius Hantavirus Incident.**

---

## 🚀 Key Features

-   **🤖 AI Research Assistant:** Ask complex questions and get answers cited with original sources (WHO, CDC, PubMed).
-   **🗺️ Live Outbreak Map:** Interactive global tracking of cases by nationality and geographic spread.
-   **📡 Real-Time News Ticker:** Monitored feeds from WHO, CDC, Reuters, and BBC—updated every 15 minutes.
-   **📈 Pandemic Risk & Fear Index:** Blended sentiment analysis from global media and community voting.
-   **📊 Outbreak Analytics:** Detailed statistics on case counts, mortality rates, and source credibility.
-   **🔗 v1.1: Contextual Recommendations:** Leveraging Qdrant's Recommendation API to map related research and bridge data silos.

---

## 🛠️ The Tech Stack

-   **Frontend:** Streamlit (Custom Navy/Teal Design System)
-   **AI Engine:** LangChain + OpenAI GPT-4o-mini
-   **Embeddings:** OpenAI `text-embedding-3-small` (Fallback: HuggingFace `all-MiniLM-L6-v2`)
-   **Vector Database:** Qdrant Cloud (v1.1 with Recommendation Engine) / ChromaDB (Local)
-   **Persistence:** Persistent Analytics & Sentiment tracking via Qdrant Key-Value store.


---

## ⚙️ Quick Start

### 1. Prerequisites
- Python 3.9+
- An OpenAI API Key (for the best AI performance)
- [Optional] A free Qdrant Cloud cluster (for persistent data on Streamlit Cloud)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/adityaaravind/andes-virus-assistant.git
cd andes-virus-assistant

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Copy the example environment file and add your keys:
```bash
cp .env.example .env
# Edit .env and add:
# OPENAI_API_KEY=sk-...
# QDRANT_URL=... (optional)
```

### 4. Ingest Data
Run the ingestion pipeline to build your local knowledge base. This fetches data from PubMed, WHO, Wikipedia, and Live News.
```bash
python scripts/ingest_all.py
```

### 5. Launch
```bash
streamlit run app.py
```

---

## 📚 Data Sources & Credibility

We use a weighted re-ranking algorithm (`similarity_score × credibility_score`) to ensure the most reliable information reaches you first.

| Source Type | Primary Providers | Credibility |
| :--- | :--- | :--- |
| **Official** | WHO, CDC, ECDC, PAHO | **1.0** |
| **Science** | PubMed, The Lancet, ScienceDaily | **0.9** |
| **Top Press** | Reuters, BBC Health, Al Jazeera | **0.75** |
| **General** | Google News, Wikipedia | **0.6** |

---

## 🏗️ Project Architecture

-   `app.py`: Main entry point & background scheduler.
-   `ingestion/`: Scrapers for PubMed, WHO (PDFs), News (RSS), and Wikipedia.
-   `processing/`: Text chunking, metadata tagging, and embedding logic.
-   `rag/`: LangChain implementation, retrieval logic, and citation formatting.
-   `ui/`: Modular Streamlit components (Map, Fear Index, News Ticker, etc.).
-   `vectorstore/`: Abstraction layer for Qdrant and ChromaDB.

---

## ⚠️ Disclaimer
*This tool is for research and informational purposes only. It is not a substitute for professional medical advice. For emergencies, contact your local health authorities.*

---

## 📜 v1.1 Changelog (Active Intelligence Update)

- **Semantic Alerting Engine:** Moves beyond keyword thresholds. Automatically alerts if indexed documents contain high-risk concepts like "human-to-human transmission" or "mutation" using vector similarity.
- **Qdrant Named Vectors:** Implemented dual-vector storage (`summary` vs `detail`). Enables high-level browsing and deep-fact extraction within the same collection.
- **Recommendation API:** Native Qdrant-powered "Related Research" mapping to bridge disparate data sources.
- **Persistent Session Memory:** Conversation context is now indexed in Qdrant, allowing the assistant to maintain deeper context across sessions.
- **Hybrid Search Foundation:** Configured sparse vector support for future keyword+semantic hybrid ranking.
