"""Andes Virus Research Assistant — main Streamlit application."""
from __future__ import annotations

# Must be set before ANY import that touches protobuf/grpc (chromadb, opentelemetry, etc.)
# Fixes crash on Python 3.14 where protobuf C extension is incompatible.
import os
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

import logging
import threading
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv


load_dotenv()

# Pull secrets from Streamlit Cloud when .env is absent (production deploy)
def _load_streamlit_secrets() -> None:
    try:
        for key in ("OPENAI_API_KEY", "CHROMA_PERSIST_DIR", "NEWS_REFRESH_INTERVAL_HOURS",
                    "QDRANT_URL", "QDRANT_API_KEY", "ONESIGNAL_APP_ID", "ONESIGNAL_REST_API_KEY",
                    "NTFY_DEFAULT_TOPIC", "APP_PASSWORD"):
            if not os.getenv(key) and key in st.secrets:
                os.environ[key] = st.secrets[key]
    except Exception:
        pass

_load_streamlit_secrets()


def _ensure_data_dirs() -> None:
    """Create runtime data dirs if missing (needed on Streamlit Cloud cold starts)."""
    for d in ("data", "vectorstore/db"):
        Path(d).mkdir(parents=True, exist_ok=True)


_ensure_data_dirs()

# ---------------------------------------------------------------------------
# Background ingestion scheduler (runs once per process, not per Streamlit
# session — module-level lock prevents duplicate schedulers on hot-reload)
# ---------------------------------------------------------------------------
_SCHEDULER_LOCK = threading.Lock()
_SCHEDULER_STARTED = False


def _run_fast_news_poll() -> None:
    """15-minute job: RSS only → vector store + case count extraction + alert check."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from ingestion.news_scraper import scrape_all_feeds
        from processing.chunker import chunk_documents
        from vectorstore.store import add_documents
        from ingestion.case_count_scraper import extract_and_save
        from alerts.alert_manager import check_and_fire
        from alerts.notifier import send_ntfy

        docs   = scrape_all_feeds()                  # list[dict]
        chunks = chunk_documents(docs)
        if chunks:
            add_documents(chunks)
        st.cache_data.clear()
        logging.info("Fast news poll: %d new chunks", len(chunks))

        # Pass raw article dicts (not Document objects) to case count extractor
        updated = extract_and_save(docs)

        # Fire ntfy + alert checks with latest known data
        try:
            from ui.stats_panel import OUTBREAK_DATA
            from ui.map_panel import NATIONALITIES_DATA
            from ui.pandemic_risk import _compute_risk, _risk_meta
            import json
            from pathlib import Path as _P
            live_file = _P("data/outbreak_live.json")
            live = json.loads(live_file.read_text()) if live_file.exists() else {}
            cases    = live.get("confirmed_cases", OUTBREAK_DATA["confirmed_cases"])
            deaths   = live.get("deaths",          OUTBREAK_DATA["deaths"])
            countries= live.get("nationalities",   OUTBREAK_DATA["nationalities"])
            risk     = _compute_risk(cases, countries)
            _, risk_label, _ = _risk_meta(risk["overall"])
            current = {
                "cases":      cases,
                "deaths":     deaths,
                "countries":  countries,
                "risk_level": risk_label,
                "areas":      [d["country"] for d in NATIONALITIES_DATA if d["cases"] > 0],
            }
            fired = check_and_fire(current)
            if fired:
                logging.info("Fast poll dispatched %d alert(s)", fired)

            # If new relevant articles found but no threshold crossed, send breaking news ping
            topic = os.getenv("NTFY_DEFAULT_TOPIC", "")
            if chunks and topic and not fired:
                send_ntfy(
                    topic,
                    "📰 New Andes Virus Articles Indexed",
                    f"{len(chunks)} new chunks added. Latest data available in the assistant.",
                    "info",
                )
        except Exception:
            logging.exception("Fast poll alert check failed")

    except Exception:
        logging.exception("Fast news poll failed")


def _run_ingestion_job() -> None:
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from scripts.ingest_all import run_ingestion
        run_ingestion()
        st.cache_data.clear()
    except Exception:
        logging.exception("Background ingestion job failed")
    # Check alert thresholds after every ingestion
    try:
        from alerts.alert_manager import check_and_fire
        from ui.stats_panel import OUTBREAK_DATA
        from ui.map_panel import NATIONALITIES_DATA
        from ui.pandemic_risk import _compute_risk, _risk_meta
        risk = _compute_risk(OUTBREAK_DATA["confirmed_cases"], OUTBREAK_DATA["nationalities"])
        _, risk_label, _ = _risk_meta(risk["overall"])
        current = {
            "cases":      OUTBREAK_DATA["confirmed_cases"],
            "deaths":     OUTBREAK_DATA["deaths"],
            "countries":  OUTBREAK_DATA["nationalities"],
            "risk_level": risk_label,
            "areas":      [d["country"] for d in NATIONALITIES_DATA if d["cases"] > 0],
        }
        fired = check_and_fire(current)
        if fired:
            logging.info("Dispatched %d alert(s)", fired)
    except Exception:
        logging.exception("Alert check failed")


def _start_scheduler() -> None:
    global _SCHEDULER_STARTED
    with _SCHEDULER_LOCK:
        if _SCHEDULER_STARTED:
            return
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            interval_hours = int(os.getenv("NEWS_REFRESH_INTERVAL_HOURS", "2"))
            scheduler = BackgroundScheduler(daemon=True)
            scheduler.add_job(
                _run_ingestion_job,
                trigger="interval",
                hours=interval_hours,
                id="auto_ingest",
                max_instances=1,
                coalesce=True,
            )
            scheduler.add_job(
                _run_fast_news_poll,
                trigger="interval",
                minutes=15,
                id="fast_news_poll",
                max_instances=1,
                coalesce=True,
            )
            scheduler.start()
            _SCHEDULER_STARTED = True
            logging.info("Auto-ingestion scheduler started (every %dh)", interval_hours)
        except Exception:
            logging.exception("Failed to start ingestion scheduler")


_start_scheduler()

st.set_page_config(
    page_title="Andes Virus Research Assistant",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "Andes Virus Research Assistant — RAG-powered epidemiology tool.",
    },
)

_CSS_PATH = Path(__file__).parent / "ui" / "styles.css"
if _CSS_PATH.exists():
    st.markdown(f"<style>{_CSS_PATH.read_text()}</style>", unsafe_allow_html=True)

# Google Site Verification (JS Injection into <head>)
st.markdown(
    """
    <script>
        var meta = document.createElement('meta');
        meta.name = "google-site-verification";
        meta.content = "FKa79DavbBQG_9PoGFRcLdArnnibHWi_eF8aRv5vWh4";
        document.getElementsByTagName('head')[0].appendChild(meta);
    </script>
    """,
    unsafe_allow_html=True
)


def _init_rag_chain() -> Any | None:
    if "rag_chain" in st.session_state:
        return st.session_state.rag_chain

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key == "your_key_here":
        st.session_state.rag_chain = None
        return None

    try:
        from rag.chain import build_chain
        chain = build_chain()
        st.session_state.rag_chain = chain
        return chain
    except Exception as exc:
        st.session_state.rag_chain = None
        st.session_state.rag_init_error = str(exc)
        return None


def _check_vectorstore() -> bool:
    try:
        from vectorstore.store import get_stats
        stats = get_stats()
        return stats.get("total_chunks", 0) > 0
    except Exception:
        return False


def _bootstrap_if_empty() -> None:
    """On cold start (Streamlit Cloud) run full ingestion if DB is empty."""
    if st.session_state.get("bootstrap_done"):
        return
    st.session_state["bootstrap_done"] = True
    if _check_vectorstore():
        return
    st.info(
        "**First run — building knowledge base.** "
        "Fetching PubMed, WHO, and live news (~3–5 min). App loads after.",
        icon="⚙️",
    )
    with st.spinner("Ingesting sources… runs once per cold start."):
        try:
            from scripts.ingest_all import run_ingestion
            run_ingestion()
            st.cache_data.clear()
            st.rerun()
        except Exception as exc:
            logging.exception("Bootstrap ingestion failed")
            st.warning(f"Ingestion error: {exc}. App runs with limited RAG.", icon="⚠️")



def _render_header() -> None:
    from ui.author_card import render_author_card
    col_logo, col_title, col_author = st.columns([1, 5, 3])
    with col_logo:
        st.markdown(
            "<div style='font-size:2.8rem;line-height:1;padding-top:0.2rem;'>🧬</div>",
            unsafe_allow_html=True,
        )
    with col_title:
        st.markdown(
            "<h1 style='margin:0;padding:0;font-size:1.6rem;color:#f8fafc;'>"
            "Andes Virus Research Assistant</h1>"
            "<p style='margin:0;color:#94a3b8;font-size:0.85rem;'>"
            "MV Hondius Hantavirus Outbreak · AI-Powered Evidence Review</p>"
            "<div style='margin-top:0.4rem;'>"
            "<span class='outbreak-badge'><span class='dot'></span>OUTBREAK ACTIVE</span>"
            "</div>",
            unsafe_allow_html=True,
        )
    with col_author:
        render_author_card()


def _render_setup_warning() -> None:
    api_key = os.getenv("OPENAI_API_KEY", "")
    has_key = api_key and api_key != "your_key_here"
    has_data = _check_vectorstore()

    if not has_key:
        st.warning(
            "**OpenAI API key not configured.**\n\n"
            "1. Copy `.env.example` → `.env`\n"
            "2. Add your key: `OPENAI_API_KEY=sk-...`\n"
            "3. Restart the app\n\n"
            "Without a key, embeddings fall back to HuggingFace (offline mode).",
            icon="⚙️",
        )

    if not has_data:
        st.info(
            "**Vector store is empty.** Run the ingestion pipeline first:\n\n"
            "```bash\npython scripts/ingest_all.py\n```\n\n"
            "This fetches PubMed abstracts, WHO documents, news, and Wikipedia articles "
            "and stores them for retrieval.",
            icon="📥",
        )


def _render_sidebar(citation_cards_ref: list[dict[str, Any]]) -> None:
    from ui.source_panel import render_source_panel
    from ui.alert_settings import render_alert_settings
    from vectorstore.store import get_stats

    with st.sidebar:
        st.markdown(
            "<h2 style='color:#00b4d8;font-size:1.1rem;margin-bottom:0.5rem;'>"
            "📚 Source Panel</h2>",
            unsafe_allow_html=True,
        )
        render_source_panel(citation_cards_ref)
        st.divider()
        render_alert_settings()

        st.divider()
        st.markdown("#### Vector Store")
        try:
            stats = get_stats()
            st.metric("Chunks indexed", stats.get("total_chunks", 0))
            status = stats.get("status", "unknown")
            color = "#22c55e" if status == "ready" else "#ef4444"
            st.markdown(
                f"<span style='color:{color};font-size:0.8rem;'>● {status.upper()}</span>",
                unsafe_allow_html=True,
            )
        except Exception:
            st.markdown("<span style='color:#ef4444;'>● DB unreachable</span>", unsafe_allow_html=True)

        interval_hours = int(os.getenv("NEWS_REFRESH_INTERVAL_HOURS", "6"))
        st.markdown(
            f"<p style='color:#64748b;font-size:0.72rem;margin-top:0.4rem;'>"
            f"🔄 Full ingest every {interval_hours}h · News every 15 min</p>",
            unsafe_allow_html=True,
        )

        st.divider()
        st.markdown(
            "<p style='color:#64748b;font-size:0.72rem;'>"
            "Data: WHO, CDC, PubMed, Reuters, BBC, Al Jazeera, Wikipedia.<br>"
            "Not medical advice.</p>",
            unsafe_allow_html=True,
        )


def _auth_gate() -> bool:
    """Return True if user is allowed through. Uses APP_PASSWORD env var."""
    password = os.getenv("APP_PASSWORD", "")
    if not password:
        return True  # no password set = open access (local dev)

    if st.session_state.get("authenticated"):
        return True

    st.markdown(
        "<div style='max-width:360px;margin:4rem auto;'>"
        "<h2 style='color:#00b4d8;text-align:center;'>🧬 Andes Virus Assistant</h2>"
        "<p style='color:#94a3b8;text-align:center;font-size:0.85rem;'>Restricted access</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    pwd = st.text_input("Access password", type="password", key="auth_input")
    if st.button("Enter", use_container_width=False):
        if pwd == password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()
    return False


def main() -> None:
    # _auth_gate()  # Disabled for Google verification

    # Auto-refresh page every hour so headlines stay live
    # from streamlit_autorefresh import st_autorefresh
    # st_autorefresh(interval=3600 * 1000, key="hourly_refresh")

    _render_header()
    st.divider()

    # ── WHAT IS THIS? — Introduction Panel ──────────────────────────────────
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("## 🚨 **LIVE OUTBREAK INTELLIGENCE SYSTEM**")
        with col2:
            st.markdown(
                "<div style='background: #f59e0b22; border: 2px solid #f59e0b; border-radius: 12px; padding: 0.5rem 1rem; text-align: center;'>"
                "<p style='color: #f59e0b; font-size: 1.4rem; font-weight: 900; margin: 0; font-family: monospace;'>HANTAVIRUS</p>"
                "<p style='color: #94a3b8; font-size: 0.65rem; margin: 0;'>Andes Virus Strain</p>"
                "</div>",
                unsafe_allow_html=True
            )

    st.error("🦠 **ACTIVE: MV Hondius Hantavirus Outbreak**\n\nThis AI assistant tracks the ongoing Andes virus outbreak linked to the cruise ship MV Hondius. Real-time monitoring of cases, deaths, and geographic spread across multiple countries.")

    col_features, col_usage = st.columns(2)

    with col_features:
        st.success("""
        **🔍 What This Tool Does**
        - Real-time case tracking & mortality analysis
        - AI-powered research assistant (coming soon)
        - Live news monitoring from WHO, CDC, Reuters, BBC
        - Pandemic risk assessment & geographic mapping
        """)

    with col_usage:
        st.info("""
        **💡 How To Use**
        - Scroll down to see live outbreak statistics
        - Ask questions in the research assistant chat (coming soon)
        - Check the map for geographic spread patterns
        - Enable alerts in sidebar for outbreak updates
        """)

    st.warning("⚠️ **NOT MEDICAL ADVICE** • For emergencies contact local health authorities")

    _bootstrap_if_empty()
    _render_setup_warning()

    chain = _init_rag_chain()

    from ui.pandemic_risk import render_pandemic_risk_panel
    from ui.fear_index import render_fear_index
    from ui.news_ticker import render_news_ticker
    from ui.stats_panel import render_stats_panel, render_timeline_chart
    from ui.map_panel import render_map_panel
    from ui.journalist_tools import render_journalist_tools

    # ── PANDEMIC RISK & FEAR INDEX — equal size cards ────────────────────────
    col_risk, col_fear = st.columns([1, 1])
    with col_risk:
        render_pandemic_risk_panel()
    with col_fear:
        render_fear_index()
    st.divider()

    # ── Live news ────────────────────────────────────────────────────────────
    render_news_ticker()
    st.divider()

    # ── Stats + map ──────────────────────────────────────────────────────────
    render_stats_panel()
    render_map_panel()
    render_timeline_chart()
    st.divider()

    # ── Journalist tools ─────────────────────────────────────────────────────
    render_journalist_tools()
    st.divider()

    if "citation_cards" not in st.session_state:
        st.session_state.citation_cards = []

    def update_sources(cards: list[dict[str, Any]]) -> None:
        st.session_state.citation_cards = cards

    _render_sidebar(st.session_state.citation_cards)

    from ui.faq_panel import render_faq_panel
    render_faq_panel(chain)

    from ui.suggestion_box import render_suggestion_box
    render_suggestion_box()

    st.markdown(
        "<div class='app-footer'>"
        "Data sourced from WHO, CDC, PubMed, Reuters, BBC, Al Jazeera, Wikipedia. "
        "Not medical advice. For emergencies contact your local health authority."
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
