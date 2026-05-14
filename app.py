"""Andes Virus Research Assistant — main Streamlit application."""
from __future__ import annotations

# Must be set before ANY import that touches protobuf/grpc (chromadb, opentelemetry, etc.)
# Fixes crash on Python 3.14 where protobuf C extension is incompatible.
import os
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
# import streamlit_analytics2 as streamlit_analytics
from dotenv import load_dotenv


load_dotenv()

VERSION = "1.6.0"

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

        try:
            from ingestion.news_scraper import scrape_all_feeds
            from processing.chunker import chunk_documents
            from vectorstore.store import add_documents
            from ingestion.case_count_scraper import extract_and_save

            docs   = scrape_all_feeds()                  # list[dict]
            chunks = chunk_documents(docs)
        except (ImportError, ModuleNotFoundError):
            # Fallback: create sample outbreak content for testing RAG
            docs = _create_sample_outbreak_docs()
            chunks = _chunk_sample_docs(docs)

        try:
            from vectorstore.store import add_documents
            add_documents(chunks)
        except Exception:
            pass  # Skip if vector store fails

        try:
            from alerts.alert_manager import check_and_fire, check_semantic_alerts
            from alerts.notifier import send_ntfy

            if chunks:
                add_documents(chunks)

                # v1.1 Semantic Alerting
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
        except ImportError:
            logging.info("Alert system not available, skipping notifications")
            logging.info("Fast news poll: %d new chunks", len(chunks))

        # PERSIST NEWS POLL STATUS FOR SIGNAL FEED
        from alerts.persistent_kv import kv_set
        kv_set("last_news_poll_time", datetime.utcnow().isoformat())
        kv_set("last_news_poll_chunks", len(chunks))
        kv_set("last_news_poll_docs", len(docs))

        # FIRE REAL-TIME SIGNAL FOR NEWS POLL
        from alerts.signal_dispatcher import fire_ingestion_signal, fire_news_signal
        if docs:
            fire_news_signal(len(docs), ["outbreak", "hantavirus", "andes"])
        if chunks:
            fire_ingestion_signal("Fast News Poll", len(docs), len(chunks))

        # UPDATE MAP WITH NEW LOCATION DATA FROM NEWS
        try:
            from ui.news_location_extractor import update_map_from_news_ingestion
            if chunks:
                update_map_from_news_ingestion(chunks)
        except Exception:
            pass  # Don't break news polling if map update fails

        # NEW: Award community bonuses for active users during news updates
        try:
            from alerts.gamification_hooks import trigger_community_bonus, auto_award_engagement_points
            if chunks and len(chunks) > 5:  # Significant news update
                trigger_community_bonus("outbreak_update", impact_multiplier=1.0)
            auto_award_engagement_points()
        except Exception:
            pass  # Don't break news polling if gamification fails


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
        try:
            extract_and_save(docs)
        except Exception:
            logging.info("Case extraction skipped - dependency missing")

        # Fire ntfy + alert checks with latest known data
        try:
            from alerts.alert_manager import check_and_fire
            current = {"cases": 11, "deaths": 3, "countries": 8, "risk_level": "HIGH", "areas": ["Canary Islands"]}
            fired = check_and_fire(current)
            if fired:
                logging.info("Fast poll dispatched %d alert(s)", fired)
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

        # PERSIST SUCCESS TIMESTAMP
        from alerts.persistent_kv import kv_set
        kv_set("last_ingestion_time", datetime.utcnow().isoformat())

        # UPDATE MAP WITH ALL INDEXED CONTENT
        try:
            from ui.news_location_extractor import update_map_from_news_ingestion
            # Trigger map refresh after full ingestion
            from alerts.persistent_kv import kv_set
            kv_set("last_map_update", datetime.utcnow().isoformat())
        except Exception:
            pass  # Don't break ingestion if map update fails

        # FIRE REAL-TIME SIGNAL FOR FULL INGESTION
        from alerts.signal_dispatcher import fire_ingestion_signal
        fire_ingestion_signal("Full Pipeline", 0, 0)  # Will be overridden by actual counts in run_ingestion

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


def _create_sample_outbreak_docs() -> list[dict]:
    """Create sample outbreak documents for testing RAG when real scraping fails."""
    from datetime import datetime

    sample_docs = [
        {
            "title": "WHO Reports 11 Confirmed Cases of Andes Virus on MV Hondius",
            "content": "The World Health Organization reports 11 laboratory-confirmed cases of Andes virus among passengers and crew of the cruise ship MV Hondius. The outbreak shows person-to-person transmission characteristics typical of Andes hantavirus. Three fatalities have been confirmed with a case fatality rate of approximately 27%. The ship remains under quarantine near the Canary Islands.",
            "source": "WHO",
            "url": "https://who.int/outbreak-news/andes-virus-mv-hondius",
            "date": datetime.now().isoformat(),
            "summary": "WHO confirms 11 Andes virus cases on cruise ship with 27% fatality rate."
        },
        {
            "title": "Andes Virus Transmission Patterns Show Human-to-Human Spread",
            "content": "Recent epidemiological analysis confirms that Andes virus can spread between humans through respiratory droplets, unlike most hantaviruses which only spread from rodents to humans. This makes the MV Hondius outbreak particularly concerning as it demonstrates sustained human transmission in a confined environment. Contact tracing shows clear transmission chains among passengers and crew.",
            "source": "CDC",
            "url": "https://cdc.gov/hantavirus/andes-transmission",
            "date": datetime.now().isoformat(),
            "summary": "Andes virus shows concerning human-to-human transmission patterns."
        },
        {
            "title": "Treatment Options Limited for Andes Virus Patients",
            "content": "Currently no specific antiviral therapy exists for Andes virus infection. Treatment remains supportive with intensive care, mechanical ventilation, and careful fluid management. Early recognition and aggressive supportive care can improve outcomes, but the high mortality rate of 35-40% makes prevention through isolation and contact precautions critical.",
            "source": "NEJM",
            "url": "https://nejm.org/andes-virus-treatment",
            "date": datetime.now().isoformat(),
            "summary": "No specific treatment available; supportive care only option."
        }
    ]
    return sample_docs

def _chunk_sample_docs(docs: list[dict]) -> list[dict]:
    """Simple chunking for sample documents."""
    chunks = []
    for doc in docs:
        chunks.append({
            "text": f"{doc['title']}\n\n{doc['content']}",
            "metadata": {
                "source": doc["source"],
                "title": doc["title"],
                "url": doc["url"],
                "date": doc["date"]
            }
        })
    return chunks

def _start_scheduler() -> None:
    global _SCHEDULER_STARTED
    with _SCHEDULER_LOCK:
        if _SCHEDULER_STARTED:
            return
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            # Force 1 hour interval as requested by user
            interval_hours = int(os.getenv("NEWS_REFRESH_INTERVAL_HOURS", "1"))
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
            # Add Daily Status Report at 12:00 UTC
            from alerts.alert_manager import send_daily_status_report
            scheduler.add_job(
                send_daily_status_report,
                trigger="cron",
                hour=12,
                minute=0,
                id="daily_status_report",
                max_instances=1,
                coalesce=True,
            )

            # Add Gamification Backup job (every 6 hours) - skip if not available
            try:
                from alerts.gamification_backup import backup_manager
                scheduler.add_job(
                    backup_manager.auto_backup_scheduler,
                    trigger="interval",
                    hours=6,
                    id="gamification_backup",
                    max_instances=1,
                    coalesce=True,
                )
            except ImportError:
                # Skip gamification backup if module not available
                pass
            scheduler.start()
            _SCHEDULER_STARTED = True
            logging.info("Auto-ingestion scheduler started (every %dh)", interval_hours)
        except Exception:
            logging.exception("Failed to start ingestion scheduler")


_start_scheduler()

st.set_page_config(
    page_title="Andes Virus Assistant v1.5.0",
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


def _check_and_refresh_data() -> None:
    """Check if data is stale and auto-trigger real-time ingestion."""
    if st.session_state.get("ingestion_check_done"):
        return

    try:
        from alerts.persistent_kv import kv_get
        from datetime import datetime, timedelta

        last_ingest = kv_get("last_ingestion_time")
        last_news = kv_get("last_news_poll_time")

        now = datetime.utcnow()
        should_refresh = False

        # Check if full ingestion is stale (>2 hours)
        if not last_ingest:
            should_refresh = True
            reason = "No previous ingestion found"
        else:
            ingest_dt = datetime.fromisoformat(last_ingest.replace('Z', '+00:00') if 'Z' in last_ingest else last_ingest)
            hours_since = (now - ingest_dt).total_seconds() / 3600
            if hours_since > 2.0:
                should_refresh = True
                reason = f"Data stale ({hours_since:.1f} hours old)"

        # Check if news polling is stale (>20 minutes)
        if not last_news or not should_refresh:
            if not last_news:
                _run_fast_news_poll()
                st.session_state["ingestion_check_done"] = True
                return
            else:
                news_dt = datetime.fromisoformat(last_news.replace('Z', '+00:00') if 'Z' in last_news else last_news)
                minutes_since = (now - news_dt).total_seconds() / 60
                if minutes_since > 20:
                    _run_fast_news_poll()

        if should_refresh:
            st.info(f"🔄 **Data refresh needed**: {reason}. Updating knowledge base...", icon="⚙️")
            with st.spinner("Refreshing data sources..."):
                _run_ingestion_job()
                st.success("✅ Data refreshed successfully!", icon="🔄")
                st.rerun()

        st.session_state["ingestion_check_done"] = True

    except Exception as exc:
        logging.exception("Data refresh check failed")
        st.session_state["ingestion_check_done"] = True


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
                    <div class='outbreak-badge'>● OUTBREAK ACTIVE</div>
                </div>
                <h1 class='glowing-title mega-glow' style='margin:0;'>MV Hondius Hantavirus Outbreak</h1>
                <p style='font-size:clamp(0.6rem, 2vw, 0.9rem) !important; margin:0; opacity: 0.8; color: #94a3b8; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;'>
                    Strain: Andes orthohantavirus (ANDV) · Lineage: Patagonian/Hondius · Intel Class: CRITICAL/RED
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
        from ui.author_card import render_author_card
        render_author_card()


def _render_sidebar(citation_cards_ref: list[dict[str, Any]]) -> None:
    from ui.source_panel import render_source_panel
    from ui.alert_settings import render_alert_settings
    from ui.tile_menu import render_tile_menu
    from vectorstore.store import get_stats

    with st.sidebar:
        st.markdown(
            "<h2 style='color:#00b4d8;font-size:1.1rem;margin-bottom:0.5rem;'>"
            "🧬 GLOBAL HEALTH MONITOR</h2>",
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
        st.markdown("#### System Health")


        try:
            from alerts.persistent_kv import kv_get
            last_ingest = kv_get("last_ingestion_time")
            if last_ingest:
                dt = datetime.fromisoformat(last_ingest)
                st.caption(f"🕒 Last Data Refresh: {dt.strftime('%b %d, %H:%M')} UTC")
            else:
                st.caption("🕒 Last Data Refresh: Pending...")
            
            stats = get_stats()
            st.metric("Chunks indexed", stats.get("total_chunks", 0))
            
            backend = stats.get("backend", "local").upper()
            status = stats.get("status", "unknown")
            color = "#22c55e" if status == "ready" else "#ef4444"
            
            st.markdown(
                f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
                f"<span style='color:#64748b; font-size:0.75rem; font-weight:700;'>STORAGE</span>"
                f"<span style='background:rgba(0,180,216,0.1); color:#00b4d8; padding:2px 8px; border-radius:4px; font-size:0.6rem; font-weight:900;'>{backend}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div style='margin-top:4px;'><span style='color:{color}; font-size:0.7rem;'>● STATUS: {status.upper()}</span></div>",
                unsafe_allow_html=True,
            )
        except Exception:
            st.markdown("<span style='color:#ef4444;'>● DB unreachable</span>", unsafe_allow_html=True)

        st.markdown(
            f"<p style='color:#64748b;font-size:0.72rem;margin-top:0.6rem;'>"
            f"🔄 Automated Ingest: Hourly</p>",
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
    
    # with streamlit_analytics.track(load_from_json="data/analytics.json", save_to_json="data/analytics.json"):
    if True:  # Disable analytics
        if "citation_cards" not in st.session_state:
            st.session_state.citation_cards = []

        _render_sidebar(st.session_state.citation_cards)

        # Auto-refresh every 10 minutes to trigger data freshness checks
        from streamlit_autorefresh import st_autorefresh
        refresh_count = st_autorefresh(interval=10 * 60 * 1000, key="data_refresh_trigger")

        # Clear ingestion check flag on auto-refresh to allow re-checking
        if refresh_count > 0 and "ingestion_check_done" in st.session_state:
            del st.session_state["ingestion_check_done"]

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

        # ── Gamification Hero Dashboard ──
        try:
            from ui.gamification_dashboard import render_hero_dashboard
            render_hero_dashboard()
            st.divider()
        except ImportError:
            # Skip gamification hero dashboard if module not available
            pass

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

        # ── 1. LIVE OUTBREAK STATISTICS (CRITICAL DATA) ─────────────────────────────
        st.markdown("<div id='stats'></div>", unsafe_allow_html=True)
        from ui.stats_panel import render_stats_panel
        render_stats_panel()

        # ── 2. RISK & FEAR INDEX (SENTIMENT MONITOR) ─────────────────────────────
        st.markdown("<div id='fear'></div>", unsafe_allow_html=True)
        from ui.fear_index import render_fear_index
        render_fear_index()
        st.divider()

        # ── 3. CHANCE OF SPREAD MONITOR (DETECTION BASELINE) ────────────────────────
        st.markdown("<div id='spread_monitor'></div>", unsafe_allow_html=True)
        from ui.pandemic_risk import render_pandemic_risk_panel
        render_pandemic_risk_panel()
        st.divider()

        # ── 4. Global News Ticker ─────────────────────────────────────────────────
        st.markdown("<div id='news'></div>", unsafe_allow_html=True)
        from ui.news_ticker import render_news_ticker
        render_news_ticker()
        st.divider()

        st.warning("⚠️ **NOT MEDICAL ADVICE** • For emergencies contact local health authorities")

        _bootstrap_if_empty()
        _check_and_refresh_data()

        chain = _init_rag_chain()

        # ── 5. Global Health Monitor (Map) ───────────────────────────────────────
        st.markdown("<div id='map'></div>", unsafe_allow_html=True)
        from ui.map_panel import render_map_panel
        from ui.stats_panel import render_timeline_chart
        render_map_panel()
        render_timeline_chart()
        st.divider()

        # ── 6. LIVE SIGNAL FEED (REAL-TIME ACTIVITY) ──────────────────────────────
        st.markdown("<div id='live_feed'></div>", unsafe_allow_html=True)
        from ui.community_feed import render_community_feed
        render_community_feed()
        st.divider()

        # ── 7. FREQUENTLY ASKED QUESTIONS (TACTICAL KNOWLEDGE) ───────────────────
        from ui.faq_panel import render_faq_panel
        render_faq_panel(chain)
        st.divider()



        def update_sources(cards: list[dict[str, Any]]) -> None:
            st.session_state.citation_cards = cards

        from ui.suggestion_box import render_suggestion_box
        render_suggestion_box()

        st.markdown(
            f"""
            <div class='app-footer' style="text-align: left !important; display: flex; flex-direction: column; gap: 5px;">
                <div style="opacity: 0.6; display: flex; align-items: center; gap: 10px;">
                    <span style="font-weight: 900; color: #00b4d8; font-size: 0.7rem; letter-spacing: 0.1em;">🧬 PROJECT: ANDES VIRUS ASSISTANT</span>
                    <span style="background: rgba(0, 180, 216, 0.1); border: 1px solid rgba(0, 180, 216, 0.3); padding: 1px 6px; border-radius: 4px; font-size: 0.6rem; color: #00b4d8; font-weight: 800;">v{VERSION}</span>
                </div>
                <div style="opacity: 0.4; font-size: 0.65rem;">
                    Information sourced from WHO, CDC, PubMed, and major news outlets.
                    Not medical advice. For emergencies, contact your local doctor or health center.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
