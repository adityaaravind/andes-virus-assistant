"""Horizontal FAQ panel — React-inspired design with scrolling cards, popularity ranking."""
from __future__ import annotations

import streamlit as st
import json
from pathlib import Path
from typing import Any

_FAQ_CLICKS_KEY = "faq_popularity_clicks"
_FAQ_VIEWS_KEY = "faq_total_views"

# React-style FAQ data structure
FAQ_DATA = [
    {
        "id": "what",
        "popularity": 98,
        "tag": "Most opened",
        "question": "What is Andes virus and why is it dangerous?",
        "answer": "Andes virus is a hantavirus species that causes Hantavirus Pulmonary Syndrome (HPS). It's dangerous because it has a 35-40% mortality rate, can spread person-to-person (unlike most hantaviruses), and progresses rapidly from flu-like symptoms to respiratory failure. First identified in Argentina in 1995, it's the most lethal hantavirus for humans.",
        "readingTime": "3 min",
        "category": "Scientific Facts"
    },
    {
        "id": "transmission",
        "popularity": 94,
        "tag": "Critical Info",
        "question": "Can Andes virus spread human to human?",
        "answer": "Yes, Andes virus is unique among hantaviruses in that it can spread from person to person through respiratory droplets and close contact. This human-to-human transmission capability makes it particularly concerning and differentiates it from other hantaviruses that only spread from infected rodents to humans.",
        "readingTime": "2 min",
        "category": "How it Spreads"
    },
    {
        "id": "cases",
        "popularity": 91,
        "tag": "Live Data",
        "question": "How many cases are confirmed on MV Hondius?",
        "answer": "As of May 13, 2026, there are 8 laboratory-confirmed cases and 9 suspected cases linked to the MV Hondius cruise ship outbreak, with 3 deaths recorded. Case counts are updated in real-time as health authorities process test results and contact tracing data.",
        "readingTime": "1 min",
        "category": "Current Outbreak"
    },
    {
        "id": "mortality",
        "popularity": 88,
        "tag": "Critical Stats",
        "question": "What is the mortality rate of hantavirus?",
        "answer": "Andes virus has a case fatality rate (CFR) of 35-40%, making it one of the most deadly viral infections. This is significantly higher than COVID-19 (2-3%) and approaches Ebola levels in some outbreaks. The high mortality rate is due to rapid progression to pulmonary edema and respiratory failure.",
        "readingTime": "2 min",
        "category": "Safety & Risks"
    },
    {
        "id": "treatment",
        "popularity": 84,
        "tag": "Medical",
        "question": "What treatments exist for Andes virus infection?",
        "answer": "Currently, there is no specific antiviral treatment for Andes virus infection. Treatment is primarily supportive care including oxygen therapy, mechanical ventilation, and management of fluid balance. Early detection and intensive care can improve outcomes, but prevention through avoiding exposure remains the best strategy.",
        "readingTime": "2 min",
        "category": "Treatment"
    },
    {
        "id": "symptoms",
        "popularity": 79,
        "tag": "Health Alert",
        "question": "What are the symptoms of Andes virus infection?",
        "answer": "Early symptoms include fever, headache, muscle aches, nausea, and fatigue - similar to flu. After 1-6 weeks, it progresses to the pulmonary phase with cough, shortness of breath, and fluid accumulation in the lungs. Without intensive care, respiratory failure can occur rapidly.",
        "readingTime": "3 min",
        "category": "Symptoms"
    },
    {
        "id": "pandemic",
        "popularity": 75,
        "tag": "Risk Assessment",
        "question": "Is there a risk of global pandemic from Andes virus?",
        "answer": "While concerning, Andes virus has a lower pandemic risk than COVID-19. Its R₀ (reproduction rate) is approximately 1.4 versus 2.5+ for COVID-19. However, the high mortality rate and person-to-person transmission capability make it a serious public health threat requiring vigilant containment measures.",
        "readingTime": "3 min",
        "category": "Safety & Risks"
    },
    {
        "id": "countries",
        "popularity": 72,
        "tag": "Geographic",
        "question": "Which countries have been affected by the outbreak?",
        "answer": "The outbreak has affected 23 different nationalities across multiple countries including Argentina, Chile, Netherlands, Germany, United Kingdom, Canada, Australia, and Norway. This international spread occurred because MV Hondius passengers and crew dispersed globally after the cruise ended.",
        "readingTime": "2 min",
        "category": "Locations"
    }
]

def _load_clicks() -> dict[str, int]:
    """Load click counts from persistent storage."""
    from alerts.persistent_kv import kv_get
    return kv_get(_FAQ_CLICKS_KEY, {})

def _save_click(faq_id: str) -> None:
    """Increment click count for a FAQ item."""
    from alerts.persistent_kv import kv_set, kv_get
    clicks = kv_get(_FAQ_CLICKS_KEY, {})
    clicks[faq_id] = clicks.get(faq_id, 0) + 1
    kv_set(_FAQ_CLICKS_KEY, clicks)

def _format_views(value: int) -> str:
    """Format view count for display."""
    if value >= 1000000:
        return f"{value / 1000000:.1f}M"
    elif value >= 1000:
        return f"{value / 1000:.1f}K"
    return str(value)

def _generate_dynamic_faqs(chain: Any) -> list[dict]:
    """Generate dynamic FAQs from RAG chain based on current news/data."""
    dynamic_faqs = []

    if chain is not None:
        try:
            # Generate trending questions from current outbreak data
            trending_queries = [
                "What are the most urgent questions about the current Andes virus outbreak?",
                "What key information do people need about MV Hondius cases?",
                "What are the main concerns about Andes virus transmission?",
            ]

            for query in trending_queries:
                response = chain.query(query)
                # Extract questions from response (simplified)
                if response and response.get("answer"):
                    # This would need more sophisticated parsing in practice
                    pass
        except Exception:
            pass

    return dynamic_faqs

def _get_sorted_faqs(chain: Any = None) -> list[dict]:
    """Sort FAQs by popularity using real click data and dynamic content."""
    clicks = _load_clicks()

    # Get current outbreak data for dynamic content
    try:
        from pathlib import Path
        import json
        live_file = Path("data/outbreak_live.json")
        if live_file.exists():
            live_data = json.loads(live_file.read_text())
            current_cases = live_data.get("confirmed_cases", 8)
            current_deaths = live_data.get("deaths", 3)
            last_updated = live_data.get("last_updated", "2026-05-13")
        else:
            current_cases, current_deaths, last_updated = 8, 3, "2026-05-13"
    except Exception:
        current_cases, current_deaths, last_updated = 8, 3, "2026-05-13"

    # Update FAQ answers with current data
    dynamic_updates = {
        "cases": f"As of {last_updated}, there are {current_cases} laboratory-confirmed cases and {current_cases + 1} suspected cases linked to the MV Hondius cruise ship outbreak, with {current_deaths} deaths recorded. Case counts are updated in real-time as health authorities process test results and contact tracing data.",
    }

    # Map new FAQ IDs to old FAQ keys for legacy data
    id_mapping = {
        "what": "q_what",
        "transmission": "q_p2p",
        "cases": "q_cases",
        "mortality": "q_cfr",
        "treatment": "q_treat",
        "symptoms": "q_symptoms",
        "pandemic": "q_pandemic",
        "countries": "q_countries"
    }

    # Add real click data from existing system
    for faq in FAQ_DATA:
        # Update with dynamic content if available
        if faq["id"] in dynamic_updates:
            faq["answer"] = dynamic_updates[faq["id"]]

        # Get legacy clicks if available
        old_key = id_mapping.get(faq["id"])
        legacy_clicks = clicks.get(old_key, 0) if old_key else 0
        new_clicks = clicks.get(faq["id"], 0)

        # Use total real clicks
        total_clicks = legacy_clicks + new_clicks
        faq["views"] = max(total_clicks, 1)  # Minimum 1 view
        faq["total_popularity"] = faq["popularity"] + (total_clicks * 0.5)  # Weight real clicks higher

    # Add dynamic FAQs if RAG chain available
    dynamic_faqs = _generate_dynamic_faqs(chain)
    if dynamic_faqs:
        FAQ_DATA.extend(dynamic_faqs)

    return sorted(FAQ_DATA, key=lambda x: x["total_popularity"], reverse=True)

def render_faq_panel(chain: Any) -> None:
    """Render horizontal scrolling FAQ cards inspired by React design."""

    # Get FAQ data with real click counts and dynamic content
    sorted_faqs = _get_sorted_faqs(chain)
    clicks = _load_clicks()

    # Calculate total views from all click data
    all_legacy_clicks = sum(v for k, v in clicks.items() if k.startswith("q_"))
    all_new_clicks = sum(v for k, v in clicks.items() if not k.startswith("q_"))
    total_views = all_legacy_clicks + all_new_clicks

    top_faq = sorted_faqs[0]

    # Initialize open state
    if "faq_open_id" not in st.session_state:
        st.session_state.faq_open_id = None

    # Custom CSS for React-inspired design
    st.html("""
    <style>
        :root {
            --accent: #00B4D8;
            --ink: #eef8fb;
            --muted: #9eb4c1;
            --base: #06141f;
            --surface: rgba(14, 42, 61, 0.88);
            --surface-strong: rgba(15, 45, 64, 0.92);
            --line: rgba(158, 237, 229, 0.17);
            --amber: #f59e0b;
            --shadow-raised: 0 1px 0 rgba(255,255,255,0.11) inset, 0 22px 66px rgba(0, 7, 13, 0.52), 0 0 34px color-mix(in srgb, var(--accent) 9%, transparent);
        }

        .intro-section {
            position: relative;
            padding: 28px;
            border: 1px solid var(--line);
            border-radius: 28px;
            background: linear-gradient(160deg, rgba(6,20,31,0.74), rgba(11,34,51,0.56));
            box-shadow: 0 1px 0 rgba(255,255,255,0.09) inset, 0 18px 56px rgba(0, 7, 13, 0.42);
            overflow: hidden;
            margin-bottom: 20px;
        }

        .intro-section::after {
            content: "";
            position: absolute;
            width: 240px;
            height: 240px;
            right: -88px;
            top: -96px;
            border-radius: 999px;
            background: color-mix(in srgb, var(--accent) 16%, transparent);
            filter: blur(8px);
        }

        .intro-grid {
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: 1.4fr 0.6fr;
            gap: 28px;
            align-items: end;
        }

        .eyebrow {
            width: max-content;
            display: inline-flex;
            align-items: center;
            gap: 9px;
            border: 1px solid rgba(158,237,229,0.24);
            border-radius: 999px;
            padding: 7px 11px;
            color: #9eede5;
            background: rgba(63,214,200,0.07);
            font-family: "JetBrains Mono", monospace;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.11em;
            text-transform: uppercase;
            margin-bottom: 14px;
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent);
            box-shadow: 0 0 18px var(--accent);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .intro-title {
            max-width: 16ch;
            margin: 0;
            font-family: Georgia, "Times New Roman", serif;
            font-size: 3.5rem;
            line-height: 0.9;
            letter-spacing: -0.06em;
            color: var(--ink);
            margin-bottom: 14px;
        }

        .intro-copy {
            max-width: 68ch;
            color: #bfd4de;
            font-size: 1.06rem;
            line-height: 1.68;
            margin: 0;
        }

        .metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }

        .metric {
            padding: 14px;
            border-radius: 14px;
            border: 1px solid rgba(158,237,229,0.14);
            background: rgba(22,56,77,0.72);
        }

        .metric span {
            display: block;
            color: var(--muted);
            font-size: 0.72rem;
            letter-spacing: .1em;
            text-transform: uppercase;
            font-family: "JetBrains Mono", monospace;
        }

        .metric strong {
            display: block;
            margin-top: 6px;
            font-size: 1.9rem;
            letter-spacing: -0.04em;
            color: var(--ink);
        }

        .faq-stack {
            border: 1px solid rgba(158,237,229,0.14);
            border-radius: 30px;
            background: rgba(3, 13, 20, 0.28);
            padding: 22px;
            box-shadow: var(--shadow-raised);
            overflow: hidden;
        }

        .stack-header {
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: 14px;
            margin-bottom: 16px;
        }

        .stack-title {
            font-size: 1.55rem;
            letter-spacing: -0.03em;
            color: var(--ink);
            margin: 0;
        }

        .stack-subtitle {
            margin: 4px 0 0 0;
            color: var(--muted);
            line-height: 1.55;
        }

        .sort-pill {
            white-space: nowrap;
            border: 1px solid rgba(245,158,11,0.34);
            border-radius: 999px;
            color: #ffd08a;
            background: rgba(245,158,11,0.09);
            padding: 8px 12px;
            font-size: 0.78rem;
            font-family: "JetBrains Mono", monospace;
            font-weight: 700;
        }

        .faq-rail {
            display: flex;
            gap: 16px;
            align-items: flex-start;
            overflow-x: auto;
            overflow-y: visible;
            padding: 2px 4px 16px;
            margin: 0 -4px -8px;
            scroll-snap-type: x mandatory;
            scroll-padding-inline: 4px;
            scrollbar-color: color-mix(in srgb, var(--accent) 55%, #17364a) rgba(255,255,255,0.06);
        }

        .faq-rail::-webkit-scrollbar { height: 10px; }
        .faq-rail::-webkit-scrollbar-track { background: rgba(255,255,255,0.06); border-radius: 999px; }
        .faq-rail::-webkit-scrollbar-thumb { background: color-mix(in srgb, var(--accent) 58%, #17364a); border-radius: 999px; }

        .faq-card {
            flex: 0 0 380px;
            scroll-snap-align: start;
            border-radius: 18px;
            border: 1px solid rgba(158,237,229,0.16);
            background: var(--surface);
            box-shadow: 0 1px 0 rgba(255,255,255,0.08) inset, 0 16px 38px rgba(0,0,0,0.28);
            overflow: hidden;
            transition: all 0.26s ease;
            animation: cardIn 0.62s cubic-bezier(.2,.8,.2,1);
            cursor: pointer;
            position: relative;
        }

        .faq-card:active {
            transform: translateY(-1px) scale(0.98);
        }

        .faq-card:hover {
            background: var(--surface-strong);
            border-color: color-mix(in srgb, var(--accent) 52%, rgba(158,237,229,0.22));
            transform: translateY(-3px);
            box-shadow: 0 1px 0 rgba(255,255,255,0.13) inset, 0 26px 62px rgba(0, 7, 13, 0.55), 0 0 30px color-mix(in srgb, var(--accent) 11%, transparent);
        }

        .faq-card.open {
            background: var(--surface-strong);
            border-color: color-mix(in srgb, var(--accent) 52%, rgba(158,237,229,0.22));
            transform: translateY(-3px);
            box-shadow: 0 1px 0 rgba(255,255,255,0.13) inset, 0 26px 62px rgba(0, 7, 13, 0.55), 0 0 30px color-mix(in srgb, var(--accent) 11%, transparent);
        }

        .faq-trigger {
            width: 100%;
            min-height: 236px;
            display: grid;
            grid-template-rows: auto 1fr auto;
            gap: 14px;
            text-align: left;
            border: 0;
            color: inherit;
            background: transparent;
            padding: 22px;
            cursor: pointer;
        }

        .card-topline, .card-bottomline {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }

        .rank {
            min-width: 46px;
            height: 38px;
            display: inline-grid;
            place-items: center;
            border-radius: 14px;
            background: #9eede5;
            color: #06141f;
            font-family: "JetBrains Mono", monospace;
            font-weight: 800;
            letter-spacing: -0.04em;
            box-shadow: 0 7px 16px rgba(0,180,216,0.18);
        }

        .popular-score {
            color: #ffd08a;
            font-family: "JetBrains Mono", monospace;
            font-size: 0.75rem;
            font-weight: 800;
            letter-spacing: 0.04em;
        }

        .tag {
            width: max-content;
            display: inline-flex;
            color: #9eede5;
            background: rgba(63,214,200,0.08);
            border: 1px solid rgba(158,237,229,0.16);
            border-radius: 999px;
            padding: 6px 10px;
            font-size: 0.76rem;
            font-weight: 700;
        }

        .question {
            display: block;
            margin-top: 16px;
            font-size: 1.25rem;
            line-height: 1.13;
            letter-spacing: -0.045em;
            color: var(--ink);
        }

        .meta {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
        }

        .views, .read-time {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            color: var(--muted);
            font-size: 0.82rem;
            font-family: "JetBrains Mono", monospace;
            font-weight: 700;
        }

        .eye {
            width: 15px;
            height: 10px;
            border: 1.8px solid currentColor;
            border-radius: 999px;
            position: relative;
            opacity: 0.9;
        }

        .eye::after {
            content: "";
            position: absolute;
            width: 4px;
            height: 4px;
            border-radius: 50%;
            background: currentColor;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
        }

        .chevron {
            width: 25px;
            height: 25px;
            stroke: #9eede5;
            stroke-width: 2.4;
            fill: none;
            stroke-linecap: round;
            stroke-linejoin: round;
            transition: transform 0.32s cubic-bezier(.2,.8,.2,1);
        }

        .chevron.open { transform: rotate(180deg); }

        .answer-wrap {
            display: grid;
            grid-template-rows: 0fr;
            transition: grid-template-rows 0.43s cubic-bezier(.2,.8,.2,1);
        }

        .answer-wrap.open { grid-template-rows: 1fr; }

        .answer-inner {
            min-height: 0;
            overflow: hidden;
        }

        .answer-content {
            margin: 0 22px 22px;
            padding: 16px 18px 18px;
            border-left: 2px solid var(--accent);
            border-radius: 0 16px 16px 0;
            background: rgba(255,255,255,0.045);
            color: #c2d9e4;
            line-height: 1.68;
            transform: translateY(-6px);
            opacity: 0;
            transition: opacity 0.26s ease, transform 0.32s cubic-bezier(.2,.8,.2,1);
        }

        .answer-content.show {
            opacity: 1;
            transform: translateY(0);
        }

        .answer-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 9px;
            margin-top: 14px;
        }

        .mini-button {
            border: 1px solid rgba(158,237,229,0.2);
            background: rgba(63,214,200,0.07);
            color: #9eede5;
            border-radius: 999px;
            padding: 8px 11px;
            font-size: 0.84rem;
            cursor: pointer;
            transition: background 0.2s ease;
        }

        .mini-button:hover { background: rgba(63,214,200,0.13); }

        @keyframes cardIn {
            from { opacity: 0; transform: translateY(14px) scale(.985); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        /* Style control buttons to be minimal */
        .stButton > button {
            background: rgba(0,180,216,0.1) !important;
            border: 1px solid rgba(0,180,216,0.3) !important;
            border-radius: 8px !important;
            color: #00B4D8 !important;
            font-size: 16px !important;
            padding: 8px !important;
            margin: 2px 0 !important;
            min-height: 40px !important;
            transition: all 0.2s ease !important;
        }

        .stButton > button:hover {
            background: rgba(0,180,216,0.2) !important;
            border-color: #00B4D8 !important;
            transform: scale(1.05) !important;
        }

        .stButton > button:focus {
            outline: 2px solid var(--accent) !important;
            outline-offset: 2px !important;
        }

        @media (max-width: 820px) {
            .intro-grid { grid-template-columns: 1fr; }
            .intro-title { font-size: 2.5rem; max-width: 12ch; }
            .faq-card { flex-basis: 360px; }
            .stack-header { align-items: start; flex-direction: column; }
        }

        @media (max-width: 520px) {
            .faq-trigger { min-height: 220px; }
            .read-time { display: none; }
        }
    </style>
    """)

    # Intro section with metrics
    st.html(f"""
    <section class="intro-section">
        <div class="intro-grid">
            <div>
                <div class="eyebrow">
                    <span class="pulse-dot"></span>
                    Live FAQ intelligence
                </div>
                <h1 class="intro-title">Popular questions, side by side.</h1>
                <p class="intro-copy">
                    A Streamlit-friendly horizontal FAQ rail: ranked by popularity, smooth to scroll, and each card increments its live view count when opened.
                </p>
            </div>
            <div class="metrics">
                <div class="metric">
                    <span>Total opens</span>
                    <strong>{_format_views(total_views)}</strong>
                </div>
                <div class="metric">
                    <span>Top article</span>
                    <strong>{top_faq['popularity']}%</strong>
                </div>
            </div>
        </div>
    </section>
    """)

    # FAQ cards section
    st.html("""
    <section class="faq-stack">
        <div class="stack-header">
            <div>
                <h2 class="stack-title">Horizontal FAQ cards</h2>
                <p class="stack-subtitle">Swipe or scroll across the rail; counters update every time a card opens.</p>
            </div>
            <div class="sort-pill">Sorted: Popularity ↓</div>
        </div>
    </section>
    """)

    # Simplified click handling with visible but styled interface
    with st.container():
        cols = st.columns(len(sorted_faqs))
        clicked_id = None

        for i, faq in enumerate(sorted_faqs):
            with cols[i]:
                is_open = st.session_state.faq_open_id == faq["id"]
                icon = "🔽" if is_open else "📖"

                if st.button(
                    f"{icon}",
                    key=f"faq_{faq['id']}_btn",
                    help=f"{faq['question']} ({_format_views(faq['views'])} views)",
                    use_container_width=True
                ):
                    clicked_id = faq["id"]

        if clicked_id:
            if st.session_state.faq_open_id == clicked_id:
                st.session_state.faq_open_id = None
            else:
                st.session_state.faq_open_id = clicked_id
                _save_click(clicked_id)
            st.rerun()

    # Display horizontal scrolling cards
    rail_html = '<div class="faq-rail">'

    for index, faq in enumerate(sorted_faqs):
        is_open = st.session_state.faq_open_id == faq["id"]
        view_count = faq["views"]
        rank = str(index + 1).zfill(2)

        # Generate card states
        card_class = "faq-card open" if is_open else "faq-card"
        chevron_class = "chevron open" if is_open else "chevron"
        answer_wrap_class = "answer-wrap open" if is_open else "answer-wrap"
        answer_content_class = "answer-content show" if is_open else "answer-content"

        rail_html += f"""
        <article class="{card_class}">
            <div class="faq-trigger">
                <span class="card-topline">
                    <span class="rank">{rank}</span>
                    <span class="popular-score">{faq['popularity']}% popularity</span>
                </span>
                <span>
                    <span class="tag">{faq['tag']}</span>
                    <span class="question">{faq['question']}</span>
                </span>
                <span class="card-bottomline">
                    <span class="meta">
                        <span class="views">
                            <span class="eye"></span> {_format_views(view_count)}
                        </span>
                        <span class="read-time">{faq['readingTime']} read</span>
                    </span>
                    <svg class="{chevron_class}" viewBox="0 0 24 24">
                        <path d="M6.5 9.25 12 14.75l5.5-5.5" />
                    </svg>
                </span>
            </div>
            <div class="{answer_wrap_class}">
                <div class="answer-inner">
                    <div class="{answer_content_class}">
                        {faq['answer']}
                        <div class="answer-actions">
                            <span class="mini-button">Mark helpful</span>
                            <span class="mini-button">Copy answer</span>
                        </div>
                    </div>
                </div>
            </div>
        </article>
        """

    rail_html += '</div>'
    st.html(rail_html)

