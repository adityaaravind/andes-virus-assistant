"""FAQ panel — most-asked questions with click-to-expand answers, popularity ranking."""
from __future__ import annotations

import streamlit as st
import json
from pathlib import Path
from alerts.persist_helper import bg_kv_set, get_persisted_value

_FAQ_CLICKS_KEY = "faq_popularity_clicks"

BASE_QUESTIONS = [
    {"q": "What is Andes virus and why is it dangerous?",         "cat": "Scientific Facts",    "key": "q_what"},
    {"q": "How many cases are confirmed on MV Hondius?",          "cat": "Current Outbreak",   "key": "q_cases"},
    {"q": "Can Andes virus spread human to human?",               "cat": "How it Spreads","key": "q_p2p"},
    {"q": "What is the mortality rate of hantavirus?",            "cat": "Safety & Risks",  "key": "q_cfr"},
    {"q": "What treatments exist for Andes virus infection?",     "cat": "Treatment",  "key": "q_treat"},
    {"q": "Which countries have been affected by the outbreak?",  "cat": "Locations",  "key": "q_countries"},
    {"q": "What is the current status of MV Hondius?",            "cat": "Current Outbreak",   "key": "q_ship"},
    {"q": "How is hantavirus transmitted to humans?",             "cat": "How it Spreads","key": "q_trans"},
    {"q": "What are the symptoms of Andes virus infection?",      "cat": "Symptoms",   "key": "q_symptoms"},
    {"q": "Is there a risk of global pandemic from Andes virus?", "cat": "Safety & Risks",       "key": "q_pandemic"},
    {"q": "What is the difference between HPS and HFRS?",         "cat": "Scientific Facts",    "key": "q_types"},
    {"q": "What precautions are passengers and crew taking?",     "cat": "Official Response",     "key": "q_precautions"},
]

# Static answers based on current outbreak data
STATIC_ANSWERS = {
    "q_what": "Andes virus is a hantavirus species that causes Hantavirus Pulmonary Syndrome (HPS). It's dangerous because it has a 35-40% mortality rate, can spread person-to-person (unlike most hantaviruses), and progresses rapidly from flu-like symptoms to respiratory failure. First identified in Argentina in 1995, it's the most lethal hantavirus for humans.",

    "q_cases": "As of May 8, 2026, there are 5 laboratory-confirmed cases and approximately 4 suspected cases (9 total) linked to the MV Hondius cruise ship outbreak, with 3 deaths recorded. The outbreak is primarily localized to the ship's passengers and crew, with a high case fatality rate reaching up to 50-60%.",

    "q_p2p": "Yes, Andes virus is unique among hantaviruses in that it can spread from person to person through respiratory droplets and close contact. This human-to-human transmission capability makes it particularly concerning and differentiates it from other hantaviruses that only spread from infected rodents to humans.",

    "q_cfr": "Andes virus has a case fatality rate (CFR) of 35-40%, making it one of the most deadly viral infections. This is significantly higher than COVID-19 (2-3%) and even Ebola in some outbreaks. The high mortality rate is due to rapid progression to pulmonary edema and respiratory failure.",

    "q_treat": "Currently, there is no specific antiviral treatment for Andes virus infection. Treatment is primarily supportive care including oxygen therapy, mechanical ventilation, and management of fluid balance. Early detection and intensive care can improve outcomes, but prevention through avoiding exposure remains the best strategy.",

    "q_countries": "The outbreak has affected 8 countries so far: Argentina, Chile, Netherlands, Germany, United Kingdom, Canada, Australia, and Norway. This international spread occurred because MV Hondius passengers and crew dispersed globally after the cruise ended.",

    "q_ship": "MV Hondius has been quarantined and is currently undergoing decontamination procedures. All passengers and crew have been evacuated and are under medical observation. The ship remains docked under strict health authority supervision while investigations continue.",

    "q_trans": "Hantavirus is primarily transmitted through inhalation of aerosolized particles from infected rodent urine, feces, or saliva. However, Andes virus can also spread person-to-person through respiratory droplets, similar to COVID-19 but less efficiently. Close contact with infected individuals poses the highest risk.",

    "q_symptoms": "Early symptoms include fever, headache, muscle aches, nausea, and fatigue - similar to flu. After 1-6 weeks, it progresses to the pulmonary phase with cough, shortness of breath, and fluid accumulation in the lungs. Without intensive care, respiratory failure can occur rapidly.",

    "q_pandemic": "While concerning, Andes virus has a lower pandemic risk than COVID-19. Its R₀ (reproduction rate) is approximately 1.4 versus 2.5+ for COVID-19. However, the high mortality rate and person-to-person transmission capability make it a serious public health threat requiring vigilant containment measures.",

    "q_types": "HPS (Hantavirus Pulmonary Syndrome) primarily affects the lungs and is caused by New World hantaviruses like Andes virus in the Americas. HFRS (Hemorrhagic Fever with Renal Syndrome) affects the kidneys and is caused by Old World hantaviruses in Europe and Asia. Both can be fatal but have different organ targets.",

    "q_precautions": "Passengers and crew are under strict quarantine protocols, regular health monitoring, and PCR testing. Those showing symptoms receive immediate isolation and intensive care. Close contacts are traced and monitored. International health authorities have implemented enhanced screening at ports and airports."
}

CAT_COLORS = {
    "Scientific Facts": ("#3b82f6", "rgba(59,130,246,0.12)"),
    "Current Outbreak": ("#ef4444", "rgba(239,68,68,0.12)"),
    "How it Spreads":   ("#f59e0b", "rgba(245,158,11,0.12)"),
    "Safety & Risks":   ("#ef4444", "rgba(239,68,68,0.10)"),
    "Treatment":        ("#22c55e", "rgba(34,197,94,0.10)"),
    "Locations":        ("#00b4d8", "rgba(0,180,216,0.10)"),
    "Symptoms":         ("#f59e0b", "rgba(245,158,11,0.10)"),
    "Official Response": ("#22c55e", "rgba(34,197,94,0.10)"),
}


def _load_clicks() -> dict[str, int]:
    return get_persisted_value(_FAQ_CLICKS_KEY, {})


def _save_click(key: str) -> None:
    clicks = _load_clicks()
    clicks[key] = clicks.get(key, 0) + 1
    bg_kv_set(_FAQ_CLICKS_KEY, clicks)


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


def _migrate_legacy_clicks() -> None:
    """Merge legacy faq_clicks.json into the new persistent KV store if needed."""
    legacy_path = Path("data/faq_clicks.json")
    if legacy_path.exists():
        try:
            legacy_data = json.loads(legacy_path.read_text())
            current = _load_clicks()
            updated = False
            for k, v in legacy_data.items():
                if k not in current or current[k] < v:
                    current[k] = v
                    updated = True
            if updated:
                bg_kv_set(_FAQ_CLICKS_KEY, current)
        except Exception:
            pass

def render_faq_panel(chain: Any) -> None:
    _migrate_legacy_clicks()
    questions = _sorted_questions()
    clicks    = _load_clicks()

    st.markdown(
        '<div style="display:flex;align-items:baseline;gap:0.8rem;margin-bottom:1.2rem;">'
        '<h3 style="margin:0;color:#f8fafc;font-size:1.4rem;font-weight:900;">COMMON QUESTIONS & ANSWERS</h3>'
        '<span style="color:#64748b;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;">Information Center // Sorted by Popularity</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # FAQ Grid Styles
    st.html("""<style>
.faq-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}
.faq-card {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 1.5rem;
    backdrop-filter: blur(12px);
    position: relative;
    overflow: hidden;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 30px rgba(0,0,0,0.3);
}
.faq-card:hover {
    border-color: var(--accent-color);
    background: rgba(15, 23, 42, 0.9);
    transform: translateY(-4px);
    box-shadow: 0 10px 40px rgba(0,0,0,0.5), 0 0 20px var(--accent-glow);
}
.faq-category {
    font-size: 0.65rem;
    font-weight: 950;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-bottom: 0.8rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: var(--accent-color);
}
.faq-question {
    color: #f8fafc;
    font-size: 1.05rem;
    font-weight: 800;
    line-height: 1.3;
    margin-bottom: 1rem;
    flex-grow: 1;
}
.faq-answer-box {
    margin-top: 1rem;
    padding: 1rem;
    background: rgba(0,0,0,0.3);
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.03);
    color: #94a3b8;
    font-size: 0.9rem;
    line-height: 1.6;
    animation: slideDown 0.3s ease-out;
}
@keyframes slideDown {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}
details summary {
    list-style: none;
    cursor: pointer;
    outline: none;
    color: var(--accent-color);
    font-size: 0.7rem;
    font-weight: 900;
    display: flex;
    align-items: center;
    gap: 8px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    opacity: 0.8;
    transition: opacity 0.2s;
}
details summary:hover { opacity: 1; }
details summary::-webkit-details-marker { display: none; }
details[open] summary { color: #f8fafc; margin-bottom: 0.5rem; }
details[open] summary::before { content: '▼'; font-size: 8px; }
details:not([open]) summary::before { content: '▶'; font-size: 8px; }

.faq-icon {
    font-size: 1.2rem;
    margin-right: 8px;
    opacity: 0.9;
}
</style>""")

    CAT_ICONS = {
        "Scientific Facts": "🧬", "Current Outbreak": "🚨", "How it Spreads": "☣️",
        "Safety & Risks": "☠️", "Treatment": "💊", "Locations": "🗺️",
        "Symptoms": "🌡️", "Official Response": "🛡️",
    }

    faq_html = '<div class="faq-grid">'
    for item in questions:
        key = item["key"]
        cat = item["cat"]
        click_count = clicks.get(key, 0)
        c_border, c_bg = CAT_COLORS.get(cat, ("#94a3b8", "rgba(148,163,184,0.10)"))
        icon = CAT_ICONS.get(cat, "❓")
        answer = STATIC_ANSWERS.get(key, "Strategic response pending...")
        
        # Unique glow for each card
        accent_glow = c_border + "33" # 20% opacity
        
        # Determine popularity badge
        popularity_badge = ""
        if click_count > 140:
            popularity_badge = f'<span style="background:rgba(239,68,68,0.2); color:#f87171; padding:2px 8px; border-radius:6px; font-size:0.55rem; font-weight:950; border:1px solid #f8717144;">MOST VIEWED</span>'
        
        faq_html += f"""<div class="faq-card" style="--accent-color: {c_border}; --accent-glow: {accent_glow};">
<div style="position:absolute; top:0; left:0; width:100%; height:4px; background:linear-gradient(90deg, {c_border}, transparent);"></div>
<div class="faq-category">
<span><span class="faq-icon">{icon}</span>{cat.upper()}</span>
<div style="display:flex; gap:8px; align-items:center;">
{popularity_badge}
<span style="color:#475569; font-size:0.55rem;">{click_count} VIEWS</span>
</div>
</div>
<div class="faq-question">{item['q']}</div>
<details>
<summary>VIEW ANSWER</summary>
<div class="faq-answer-box">
{answer}
</div>
</details>
</div>"""
    
    faq_html += '</div>'
    st.html(faq_html)
