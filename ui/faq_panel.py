"""FAQ panel — most-asked questions with click-to-expand answers, popularity ranking."""
from __future__ import annotations

import streamlit as st
from alerts.persist_helper import bg_kv_set, get_persisted_value

_FAQ_CLICKS_KEY = "faq_popularity_clicks"

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


def render_faq_panel(chain: Any) -> None:
    questions = _sorted_questions()
    clicks    = _load_clicks()

    st.markdown(
        '<div style="display:flex;align-items:baseline;gap:0.8rem;margin-bottom:0.6rem;">'
        '<h3 style="margin:0;color:#f8fafc;">Frequently Asked Questions</h3>'
        '<span style="color:#64748b;font-size:0.75rem;">Click any card · Auto-ranked by popularity</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Use responsive grid instead of st.columns for better mobile behavior
    faq_html = ""

    for i, item in enumerate(questions):
        key         = item["key"]
        cat         = item["cat"]
        c_border, c_bg = CAT_COLORS.get(cat, ("#94a3b8", "rgba(148,163,184,0.10)"))
        click_count = clicks.get(key, 0)
        answer = STATIC_ANSWERS.get(key, "Answer not available for this question.")

        # Card and expansion logic inside a single markdown block for grid control
        faq_html += (
            f'<div style="background:{c_bg};border:1px solid {c_border}44;border-top:2px solid {c_border};'
            f'border-radius:10px;padding:0.75rem 0.85rem;display:flex;flex-direction:column;gap:0.4rem;">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.4rem;">'
            f'<span style="background:{c_border}22;color:{c_border};font-size:0.62rem;font-weight:700;'
            f'padding:1px 7px;border-radius:10px;text-transform:uppercase;white-space:nowrap;">{cat}</span>'
            f'<span style="color:#475569;font-size:0.65rem;white-space:nowrap;">'
            f'{"🔥 " if click_count > 5 else ""}{click_count} views</span>'
            f'</div>'
            f'<p style="color:#f1f5f9;font-size:0.82rem;font-weight:600;margin:0;line-height:1.35;">'
            f'{item["q"]}</p>'
            f'<details style="margin-top:0.3rem;cursor:pointer;">'
            f'<summary style="color:{c_border};font-size:0.75rem;font-weight:600;outline:none;">Show answer</summary>'
            f'<div style="background:rgba(13,27,42,0.85);border:1px solid {c_border}33;'
            f'border-radius:8px;padding:0.85rem;margin:0.5rem 0;color:#e2e8f0;font-size:0.82rem;line-height:1.6;">'
            f'{answer.replace(chr(10), "<br>")}</div>'
            f'</details>'
            f'</div>'
        )

    st.markdown(
        f'<style>'
        f'.faq-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }}'
        f'@media (max-width: 768px) {{ .faq-grid {{ grid-template-columns: 1fr; }} }}'
        f'</style>'
        f'<div class="faq-grid">{faq_html}</div>',
        unsafe_allow_html=True,
    )
