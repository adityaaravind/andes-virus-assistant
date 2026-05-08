# 🧬 Andes Virus Research Assistant

**Real-time AI Outbreak Intelligence for the MV Hondius Hantavirus Incident.**

The Andes Virus Research Assistant is a RAG-powered (Retrieval-Augmented Generation) dashboard and AI assistant designed to track the ongoing hantavirus outbreak linked to the cruise ship MV Hondius. It provides journalists, health workers, and researchers with cited, evidence-based answers derived from official health reports, peer-reviewed literature, and live news.

---

## 🚀 Key Features

-   **🤖 AI Research Assistant:** Ask complex questions and get answers cited with original sources (WHO, CDC, PubMed).
-   **🗺️ Live Outbreak Map:** Interactive global tracking of cases by nationality and geographic spread.
-   **📡 Real-Time News Ticker:** Monitored feeds from WHO, CDC, Reuters, and BBC—updated every 15 minutes.
-   **📈 Pandemic Risk & Fear Index:** Blended sentiment analysis from global media and community voting.
-   **📊 Outbreak Analytics:** Detailed statistics on case counts, mortality rates, and source credibility.

---

## 🛠️ The Tech Stack

-   **Frontend:** Streamlit (Custom Navy/Teal Design System)
-   **AI Engine:** LangChain + OpenAI GPT-4o-mini
-   **Embeddings:** OpenAI `text-embedding-3-small` (Fallback: HuggingFace `all-MiniLM-L6-v2`)
-   **Vector Database:** Qdrant Cloud (Production) / ChromaDB (Local)
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
