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
import streamlit_analytics2 as streamlit_analytics
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


def _restore_analytics_backup() -> None:
    """Restore streamlit-analytics2 data from Qdrant (persistent_kv) to local file."""
    try:
        from alerts.persistent_kv import kv_get
        import json
        analytics_file = Path("data/analytics.json")
        if not analytics_file.exists():
            data = kv_get("analytics_backup")
            if data:
                analytics_file.write_text(json.dumps(data))
                logging.info("Restored streamlit-analytics2 backup from Qdrant")
    except Exception:
        logging.exception("Failed to restore analytics backup")


_ensure_data_dirs()
_restore_analytics_backup()

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
        import gc
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
            
            # v1.1 Semantic Alerting
            from alerts.alert_manager import check_semantic_alerts
            concerns_found = set()
            for c in chunks:
                if "embedding" in c:
                    found = check_semantic_alerts(c["embedding"])
                    concerns_found.update(found)
            
            for concern in concerns_found:
                send_ntfy(
                    os.getenv("NTFY_DEFAULT_TOPIC", "HANTAVIRUS"),
                    "🚨 SEMANTIC ALERT DETECTED",
                    f"Research match found for: {concern}",
                    "critical"
                )
                logging.warning("Semantic alert fired: %s", concern)

        logging.info("Fast news poll: %d new chunks", len(chunks))


        # Backup streamlit-analytics2 to Qdrant & Check size
        try:
            import json
            analytics_file = Path("data/analytics.json")
            if analytics_file.exists():
                # Aggressive 3MB cap for Streamlit Cloud stability
                if analytics_file.stat().st_size > 3 * 1024 * 1024:
                    logging.info("Analytics log > 3MB, clearing local file to save RAM")
                    from alerts.persistent_kv import kv_set
                    data = json.loads(analytics_file.read_text())
                    kv_set("analytics_backup", data)
                    analytics_file.write_text(json.dumps({"counts": {}, "total_views": 0})) # Reset
                    gc.collect()
                else:
                    from alerts.persistent_kv import kv_set
                    data = json.loads(analytics_file.read_text())
                    kv_set("analytics_backup", data)
        except Exception:
            pass

        # Pass raw article dicts (not Document objects) to case count extractor
        extract_and_save(docs)

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
            
        gc.collect() # Force cleanup

    except Exception:
        logging.exception("Fast news poll failed")


def _system_watchdog_cleanup() -> None:
    """Watchdog job to ensure the app stays under 1GB RAM."""
    import gc
    import os
    import psutil
    try:
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / 1024 / 1024
        logging.info("WATCHDOG: Current RAM usage: %.2f MB", mem_mb)
        
        # If we hit 700MB, force aggressive cleanup
        if mem_mb > 700:
            logging.warning("WATCHDOG: High memory detected (%.2f MB). Forcing global cleanup.", mem_mb)
            gc.collect()
            # Clear internal streamlit caches if needed
            st.cache_data.clear()
            st.cache_resource.clear()
    except Exception:
        pass


def _run_ingestion_job() -> None:
    try:
        import sys
        import gc
        sys.path.insert(0, str(Path(__file__).parent))
        from scripts.ingest_all import run_ingestion
        run_ingestion()
        
        # Check alert thresholds after every ingestion
        from alerts.alert_manager import check_and_fire
        from ui.stats_panel import get_outbreak_stats
        from ui.map_panel import NATIONALITIES_DATA
        from ui.pandemic_risk import _compute_risk, _risk_meta
        stats = get_outbreak_stats()
        risk = _compute_risk(stats["confirmed_cases"], stats["nationalities"])
        _, risk_label, _ = _risk_meta(risk["overall"])
        current = {
            "cases":      stats["confirmed_cases"],
            "deaths":     stats["deaths"],
            "countries":  stats["nationalities"],
            "risk_level": risk_label,
            "areas":      [d["country"] for d in NATIONALITIES_DATA if d["cases"] > 0],
        }
        fired = check_and_fire(current)
        if fired:
            logging.info("Dispatched %d alert(s)", fired)
        
        gc.collect() # Force cleanup
    except Exception:
        logging.exception("Background ingestion job failed")


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
            # Add Watchdog job every 30 minutes
            scheduler.add_job(
                _system_watchdog_cleanup,
                trigger="interval",
                minutes=30,
                id="watchdog_cleanup",
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
    page_title="Andes Virus Assistant v1.4.0",
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

# Google Analytics (gtag.js) for Verification
ga_html = """
<script async src="https://www.googletagmanager.com/gtag/js?id=G-Z5Y9BDH9W0"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-Z5Y9BDH9W0');

// Also ensure it is in <head> for Google verification
var script1 = document.createElement('script');
script1.async = true;
script1.src = "https://www.googletagmanager.com/gtag/js?id=G-Z5Y9BDH9W0";
document.getElementsByTagName('head')[0].appendChild(script1);

var script2 = document.createElement('script');
script2.innerHTML = "window.dataLayer = window.dataLayer || []; function gtag(){dataLayer.push(arguments);} gtag('js', new Date()); gtag('config', 'G-Z5Y9BDH9W0');";
document.getElementsByTagName('head')[0].appendChild(script2);
</script>
""".replace("\n", "").strip()
st.markdown(ga_html, unsafe_allow_html=True)


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
            st.rerun()
        except Exception as exc:
            logging.exception("Bootstrap ingestion failed")
            st.warning(f"Ingestion error: {exc}. App runs with limited RAG.", icon="⚠️")



def _render_header() -> None:
    from ui.author_card import render_author_card
    header_col, author_col = st.columns([3, 1])
    
    with header_col:
        st.markdown(
            """
            <div style='display: flex; flex-direction: column; gap: 4px; margin-bottom: 0.5rem;'>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div class='outbreak-badge' style="background: #dc2626 !important; color: white !important; font-size: 0.75rem !important; padding: 2px 10px !important; border-radius: 4px !important; font-weight: 900 !important; letter-spacing: 0.2em !important; animation: pulse-red 2s infinite;">● OUTBREAK ACTIVE</div>
                </div>
                <h1 class='glowing-title mega-glow' style='margin:0; font-size: 2.4rem !important; letter-spacing: -0.02em !important; line-height: 1.1;'>MV Hondius Hantavirus Outbreak</h1>
                <p style='font-size:0.9rem !important; margin:0; opacity: 0.8; color: #94a3b8; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;'>
                    Tactical Intelligence Dashboard · Joint Task Force Operations
                </p>
            </div>
            <style>
            @keyframes pulse-red {
                0% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7); }
                70% { box-shadow: 0 0 0 10px rgba(220, 38, 38, 0); }
                100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    
    with author_col:
        render_author_card()


def _render_sidebar(citation_cards_ref: list[dict[str, Any]]) -> None:
    from ui.source_panel import render_source_panel
    from ui.alert_settings import render_alert_settings
    from ui.tile_menu import render_tile_menu
    from vectorstore.store import get_stats

    with st.sidebar:
        st.markdown(
            "<h2 style='color:#00b4d8;font-size:1.1rem;margin-bottom:0.5rem;'>"
            "🧬 Command Center</h2>",
            unsafe_allow_html=True,
        )
        
        render_tile_menu()
        st.divider()

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

        st.markdown(
            f"<p style='color:#64748b;font-size:0.72rem;margin-top:0.4rem;'>"
            f"🔄 Full ingest every 1h · News every 5 min</p>",
            unsafe_allow_html=True,
        )

        st.divider()
        st.markdown(
            "<p style='color:#64748b;font-size:0.72rem;'>"
            "Data: WHO, CDC, PubMed, Reuters, BBC, Al Jazeera, Wikipedia.<br>"
            "Not medical advice.</p>",
            unsafe_allow_html=True,
        )

def main() -> None:
    import gc
    gc.collect() # Immediate cleanup on reload
    
    with streamlit_analytics.track(load_from_json="data/analytics.json", save_to_json="data/analytics.json"):
        if "citation_cards" not in st.session_state:
            st.session_state.citation_cards = []

        _render_sidebar(st.session_state.citation_cards)

        # REDUCED REFRESH: Every 30 mins instead of 15 to save RAM
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=30 * 60 * 1000, key="stats_refresh")

        # ── Mutation Observer for Forced Gauge Jitter ──
        st.markdown(
            """
            <script>
                function applyJitter() {
                    const needles = document.querySelectorAll('.indicator path.needle, .indicator path.threshold');
                    const numbers = document.querySelectorAll('.indicator text.numbers');
                    
                    const now = Date.now() / 100;
                    
                    needles.forEach(n => {
                        const jitterX = Math.sin(now * 1.5) * 0.5;
                        const jitterY = Math.cos(now * 1.3) * 0.5;
                        const jitterR = Math.sin(now * 1.7) * 0.2;
                        n.style.transform = `translate(${jitterX}px, ${jitterY}px) rotate(${jitterR}deg)`;
                        n.style.transformOrigin = 'center bottom';
                    });
                    
                    numbers.forEach(num => {
                        const jX = Math.cos(now * 2) * 0.3;
                        const jY = Math.sin(now * 2.2) * 0.3;
                        num.style.transform = `translate(${jX}px, ${jY}px)`;
                    });
                    
                    requestAnimationFrame(applyJitter);
                }

                // Start observing the body for Plotly charts
                const observer = new MutationObserver((mutations) => {
                    if (document.querySelector('.js-plotly-plot')) {
                        applyJitter();
                    }
                });
                
                observer.observe(document.body, { childList: true, subtree: true });
                // Initial kickstart
                setTimeout(applyJitter, 2000);
            </script>
            """,
            unsafe_allow_html=True
        )

        # ── Branding & Header ──
        _render_header()

        # ── Sidebar Scroll Guide ──
        st.markdown(
            """
            <div id="scroll-guide" class="sidebar-scroll-guide">
                <div class="scroll-line">
                    <div class="scroll-dot"></div>
                </div>
            </div>
            <script>
                const guide = document.getElementById('scroll-guide');
                let timeout;

                function showGuide() {
                    guide.style.opacity = '1';
                    clearTimeout(timeout);
                    timeout = setTimeout(() => {
                        guide.style.opacity = '0';
                    }, 2500);
                }

                // Show on all major activity
                window.addEventListener('scroll', showGuide);
                window.addEventListener('mousemove', showGuide);
                window.addEventListener('touchstart', showGuide);
                window.addEventListener('keydown', showGuide);
                
                // Show on initial load
                setTimeout(showGuide, 1500);
            </script>
            """,
            unsafe_allow_html=True
        )
        st.divider()

        # ── LIVE STATS (BELOW HEADER) ──
        st.markdown("<div id='stats'></div>", unsafe_allow_html=True)
        from ui.stats_panel import render_stats_panel
        render_stats_panel()

        st.warning("⚠️ **NOT MEDICAL ADVICE** • For emergencies contact local health authorities")

        _bootstrap_if_empty()

        chain = _init_rag_chain()

        from ui.pandemic_risk import render_pandemic_risk_panel
        from ui.fear_index import render_fear_index
        from ui.news_ticker import render_news_ticker
        from ui.stats_panel import render_timeline_chart
        from ui.map_panel import render_map_panel
        from ui.journalist_tools import render_journalist_tools

        # ── PANDEMIC RISK & FEAR INDEX — equal size cards ────────────────────────
        st.markdown("<div id='risk_fear'></div>", unsafe_allow_html=True)
        col_risk, col_fear = st.columns([1, 1])
        with col_risk:
            render_pandemic_risk_panel()
        with col_fear:
            render_fear_index()
        st.divider()

        # ── Live news ────────────────────────────────────────────────────────────
        st.markdown("<div id='news'></div>", unsafe_allow_html=True)
        render_news_ticker()
        st.divider()

        # ── Stats + map ──────────────────────────────────────────────────────────
        st.markdown("<div id='map'></div>", unsafe_allow_html=True)
        render_map_panel()
        render_timeline_chart()
        st.divider()


        # ── Journalist tools ─────────────────────────────────────────────────────
        st.markdown("<div id='journalist'></div>", unsafe_allow_html=True)
        render_journalist_tools()
        st.divider()

        # ── ROADMAP (COMING SOON) ───────────────────────────────────────────────
        st.markdown("<div id='roadmap'></div>", unsafe_allow_html=True)
        st.markdown("### 🚀 Next Intelligence Phases (coming soon)")
        col_road1, col_road2 = st.columns(2)
        with col_road1:
            st.markdown(
                """
                <div class='stat-card' style='border-color: rgba(34, 197, 94, 0.3); min-height: 140px;'>
                    <p class='stat-label glowing-title' style='color:#22c55e; font-size: 0.9rem !important;'>Automated Red-Teaming</p>
                    <p style='color:#94a3b8; font-size:0.75rem; margin-top:0.5rem;'>
                        AI agents stress-test official reports against leaked data to identify informational gaps.
                    </p>
                    <div style='margin-top:auto;'><span class='v11-feature-tag' style='margin-left:0; opacity:0.6;'>PHASE 3</span></div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_road2:
            st.markdown(
                """
                <div class='stat-card' style='border-color: rgba(0, 180, 216, 0.3); min-height: 140px;'>
                    <p class='stat-label glowing-title' style='color:#00b4d8; font-size: 0.9rem !important;'>Interactive Simulations</p>
                    <p style='color:#94a3b8; font-size:0.75rem; margin-top:0.5rem;'>
                        "What If?" Scenario Lab. Adjust viral variables to simulate outbreak progression and response.
                    </p>
                    <div style='margin-top:auto;'><span class='v11-feature-tag' style='margin-left:0; opacity:0.6;'>PHASE 2</span></div>
                </div>
                """,
                unsafe_allow_html=True
            )
        st.divider()

        def update_sources(cards: list[dict[str, Any]]) -> None:
            st.session_state.citation_cards = cards

        from ui.faq_panel import render_faq_panel
        render_faq_panel(chain)

        from ui.suggestion_box import render_suggestion_box
        render_suggestion_box()

        st.markdown(
            f"""
            <div class='app-footer' style="text-align: left !important; display: flex; flex-direction: column; gap: 5px;">
                <div style="opacity: 0.6; display: flex; align-items: center; gap: 10px;">
                    <span style="font-weight: 900; color: #00b4d8; font-size: 0.7rem; letter-spacing: 0.1em;">🧬 SYSTEM: ANDES VIRUS RESEARCH ASSISTANT</span>
                    <span style="background: rgba(0, 180, 216, 0.1); border: 1px solid rgba(0, 180, 216, 0.3); padding: 1px 6px; border-radius: 4px; font-size: 0.6rem; color: #00b4d8; font-weight: 800;">v{VERSION}</span>
                </div>
                <div style="opacity: 0.4; font-size: 0.65rem;">
                    Data sourced from WHO, CDC, PubMed, Reuters, BBC, Al Jazeera, Wikipedia. 
                    Not medical advice. For emergencies contact your local health authority.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
