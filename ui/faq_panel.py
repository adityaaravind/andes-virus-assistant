"""FAQ panel — most-asked questions with click-to-expand answers, popularity ranking."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

CLICKS_FILE = Path("data/faq_clicks.json")

BASE_QUESTIONS = [
    {"q": "What is Andes virus and why is it dangerous?",         "cat": "Biology",    "key": "q_what"},
    {"q": "How many cases are confirmed on MV Hondius?",          "cat": "Outbreak",   "key": "q_cases"},
    {"q": "Can Andes virus spread human to human?",               "cat": "Transmission","key": "q_p2p"},
    {"q": "What is the mortality rate of hantavirus?",            "cat": "Mortality",  "key": "q_cfr"},
    {"q": "What treatments exist for Andes virus infection?",     "cat": "Treatment",  "key": "q_treat"},
    {"q": "Which countries have been affected by the outbreak?",  "cat": "Geography",  "key": "q_countries"},
    {"q": "What is the current status of MV Hondius?",            "cat": "Outbreak",   "key": "q_ship"},
    {"q": "How is hantavirus transmitted to humans?",             "cat": "Transmission","key": "q_trans"},
    {"q": "What are the symptoms of Andes virus infection?",      "cat": "Symptoms",   "key": "q_symptoms"},
    {"q": "Is there a risk of global pandemic from Andes virus?", "cat": "Risk",       "key": "q_pandemic"},
    {"q": "What is the difference between HPS and HFRS?",         "cat": "Biology",    "key": "q_types"},
    {"q": "What precautions are passengers and crew taking?",     "cat": "Response",   "key": "q_precautions"},
]

CAT_COLORS = {
    "Biology":      ("#3b82f6", "rgba(59,130,246,0.12)"),
    "Outbreak":     ("#ef4444", "rgba(239,68,68,0.12)"),
    "Transmission": ("#f59e0b", "rgba(245,158,11,0.12)"),
    "Mortality":    ("#ef4444", "rgba(239,68,68,0.10)"),
    "Treatment":    ("#22c55e", "rgba(34,197,94,0.10)"),
    "Geography":    ("#00b4d8", "rgba(0,180,216,0.10)"),
    "Symptoms":     ("#f59e0b", "rgba(245,158,11,0.10)"),
    "Risk":         ("#a78bfa", "rgba(167,139,250,0.10)"),
    "Response":     ("#22c55e", "rgba(34,197,94,0.10)"),
}


def _load_clicks() -> dict[str, int]:
    if not CLICKS_FILE.exists():
        return {}
    try:
        return json.loads(CLICKS_FILE.read_text())
    except Exception:
        return {}


def _save_click(key: str) -> None:
    CLICKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    clicks = _load_clicks()
    clicks[key] = clicks.get(key, 0) + 1
    CLICKS_FILE.write_text(json.dumps(clicks))


def _sorted_questions() -> list[dict]:
    clicks = _load_clicks()
    return sorted(BASE_QUESTIONS, key=lambda q: clicks.get(q["key"], 0), reverse=True)


def _pre_fetch_answers(chain: Any, questions: list[dict]) -> None:
    if chain is None:
        return
    cache = st.session_state.setdefault("faq_cache", {})
    for item in questions[:6]:
        if item["key"] not in cache:
            try:
                res = chain.query(item["q"])
                cache[item["key"]] = res.get("answer", "")
            except Exception:
                cache[item["key"]] = ""


def render_faq_panel(chain: Any) -> None:
    if "faq_prefetched" not in st.session_state:
        with st.spinner("Loading common questions…"):
            _pre_fetch_answers(chain, _sorted_questions())
        st.session_state["faq_prefetched"] = True

    questions = _sorted_questions()
    clicks    = _load_clicks()

    st.markdown(
        '<div style="display:flex;align-items:baseline;gap:0.8rem;margin-bottom:0.6rem;">'
        '<h3 style="margin:0;color:#f8fafc;">Frequently Asked Questions</h3>'
        '<span style="color:#64748b;font-size:0.75rem;">Click any card · Auto-ranked by popularity</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Use expanders instead of custom button logic for more reliable functionality
    cols = st.columns(3)

    for i, item in enumerate(questions):
        col = cols[i % 3]
        with col:
            key         = item["key"]
            cat         = item["cat"]
            c_border, c_bg = CAT_COLORS.get(cat, ("#94a3b8", "rgba(148,163,184,0.10)"))
            click_count = clicks.get(key, 0)

            # Card header
            st.markdown(
                f'<div style="background:{c_bg};border:1px solid {c_border}44;border-top:2px solid {c_border};'
                f'border-radius:10px;padding:0.75rem 0.85rem;margin-bottom:0.5rem;">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.4rem;">'
                f'<span style="background:{c_border}22;color:{c_border};font-size:0.62rem;font-weight:700;'
                f'padding:1px 7px;border-radius:10px;text-transform:uppercase;white-space:nowrap;">{cat}</span>'
                f'<span style="color:#475569;font-size:0.65rem;white-space:nowrap;">'
                f'{"🔥 " if click_count > 5 else ""}{click_count} views</span>'
                f'</div>'
                f'<p style="color:#f1f5f9;font-size:0.82rem;font-weight:600;margin:0.4rem 0 0;line-height:1.35;">'
                f'{item["q"]}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Use streamlit expander for reliable click functionality
            with st.expander("Show answer", expanded=False):
                _save_click(key)  # Track clicks when expanded

                cache  = st.session_state.get("faq_cache", {})
                answer = cache.get(key)

                if answer is None:
                    with st.spinner("Fetching answer…"):
                        try:
                            if chain is None:
                                # Force rebuild chain if None
                                from rag.chain import build_chain
                                chain = build_chain()

                            res = chain.query(item["q"])
                            answer = res.get("answer", "No answer available.")

                            # If answer is the generic "insufficient information" message, try to get fallback
                            if "I don't have sufficient information" in answer:
                                from vectorstore.store import similarity_search
                                from processing.embedder import _huggingface_embed

                                # Direct search fallback
                                try:
                                    emb = _huggingface_embed([item["q"]])[0]
                                    results = similarity_search(emb, k=2)
                                    if results:
                                        answer = f"Based on available research:\n\n{results[0].get('text', '')[:400]}..."
                                    else:
                                        answer = "Vector store appears to be empty. Data may need to be reloaded."
                                except Exception:
                                    answer = "Unable to search knowledge base. System may need restart."

                        except Exception as e:
                            answer = f"Error: {e}"
                    st.session_state.setdefault("faq_cache", {})[key] = answer

                st.markdown(
                    f'<div style="background:rgba(13,27,42,0.85);border:1px solid {c_border}33;'
                    f'border-radius:8px;padding:0.85rem;margin:0.5rem 0;">'
                    f'<p style="color:#e2e8f0;font-size:0.82rem;line-height:1.6;margin:0;">'
                    f'{answer.replace(chr(10), "<br>")}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
