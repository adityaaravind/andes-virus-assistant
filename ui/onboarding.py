"""Guided onboarding for new users — interactive tour sequence."""
from __future__ import annotations

import streamlit as st
from typing import Any


ONBOARDING_STEPS = [
    {
        "title": "Welcome to Andes Assistant",
        "content": "I'm your 🧬 Research Guide. Let me show you how to navigate this outbreak dashboard.",
        "selector": "header",
    },
    {
        "title": "1. Live Stats & Outbreak Status",
        "content": "At the top, you'll see real-time confirmed cases, deaths, and the overall outbreak status. These sync every 15 minutes.",
        "selector": "stats",
    },
    {
        "title": "2. Risk & Fear Assessment",
        "content": "Below the header, the **Pandemic Risk** gauge uses epidemiologic data, while the **Fear Index** tracks public sentiment via real-time voting.",
        "selector": "risk_fear",
    },
    {
        "title": "3. The Global Map",
        "content": "Our interactive map tracks the spread of Andes virus across nationalities. Hover over countries to see specific passenger and crew case counts.",
        "selector": "map",
    },
    {
        "title": "4. Journalist & Sharing Tools",
        "content": "Use the **Share & Download** panel to generate social media cards or export raw CSV case data for reporting.",
        "selector": "journalist",
    },
    {
        "title": "5. RAG Research Assistant",
        "content": "Scroll down to **Ask a Question**. This AI is powered by WHO, PubMed, and latest news. It cites every source it uses.",
        "selector": "chat",
    },
    {
        "title": "6. Alert Subscriptions",
        "content": "Finally, check the **Sidebar** to subscribe to instant push notifications via `ntfy.sh` for critical outbreak updates.",
        "selector": "sidebar",
    },
]


def render_onboarding() -> None:
    """Render the guided onboarding overlay if not completed."""
    if st.session_state.get("onboarding_complete"):
        return

    # Initialize onboarding state
    if "onboarding_step" not in st.session_state:
        st.session_state.onboarding_step = 0

    step_idx = st.session_state.onboarding_step
    
    if step_idx >= len(ONBOARDING_STEPS):
        st.session_state.onboarding_complete = True
        st.rerun()
        return

    step = ONBOARDING_STEPS[step_idx]

    # ── Auto-Scroll Logic ──
    # We use a small JS snippet to find elements based on text or tags since 
    # Streamlit doesn't always provide stable IDs for all widgets.
    scroll_js = ""
    if step["selector"] == "stats":
        scroll_js = "window.scrollTo({top: 0, behavior: 'smooth'});"
    elif step["selector"] == "risk_fear":
        scroll_js = "document.querySelectorAll('h2').forEach(h => { if(h.innerText.includes('PANDEMIC RISK')) h.scrollIntoView({behavior: 'smooth', block: 'center'}); });"
    elif step["selector"] == "map":
        scroll_js = "document.querySelectorAll('h2').forEach(h => { if(h.innerText.includes('NATIONALITY')) h.scrollIntoView({behavior: 'smooth', block: 'center'}); });"
    elif step["selector"] == "journalist":
        scroll_js = "document.querySelectorAll('p').forEach(p => { if(p.innerText.includes('SHARE & DOWNLOAD')) p.scrollIntoView({behavior: 'smooth', block: 'center'}); });"
    elif step["selector"] == "chat":
        scroll_js = "document.querySelectorAll('h3').forEach(h => { if(h.innerText.includes('Ask a Question')) h.scrollIntoView({behavior: 'smooth', block: 'center'}); });"
    elif step["selector"] == "sidebar":
        scroll_js = "window.scrollTo({top: 0, behavior: 'smooth'});" # Sidebar is always visible/at top

    st.markdown(f"<script>{scroll_js}</script>", unsafe_allow_html=True)

    # Overlay / Modal-like UI using a container at the top
    with st.container():
        st.markdown(
            f"""
            <div style="background: rgba(13, 27, 42, 0.98); border: 2px solid #00b4d8; 
            border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; 
            box-shadow: 0 0 40px rgba(0, 180, 216, 0.3); animation: slideIn 0.5s ease-out;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                    <h2 style="color: #00b4d8; margin: 0; font-size: 1.2rem;">🧬 {step['title']}</h2>
                    <span style="color: #64748b; font-size: 0.8rem;">Step {step_idx + 1} of {len(ONBOARDING_STEPS)}</span>
                </div>
                <p style="color: #f8fafc; font-size: 0.95rem; line-height: 1.6;">{step['content']}</p>
                <div style="display: flex; gap: 10px; margin-top: 1.2rem;">
            """,
            unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("Back", key="onboard_back", disabled=step_idx == 0, use_container_width=True):
                st.session_state.onboarding_step -= 1
                st.rerun()
        with col2:
            label = "Next" if step_idx < len(ONBOARDING_STEPS) - 1 else "Finish"
            if st.button(label, key="onboard_next", type="primary", use_container_width=True):
                st.session_state.onboarding_step += 1
                st.rerun()
        with col3:
            if st.button("Skip Tour", key="onboard_skip", help="Dismiss onboarding"):
                st.session_state.onboarding_complete = True
                st.rerun()

        st.markdown("</div></div>", unsafe_allow_html=True)
        st.markdown("<style>@keyframes slideIn { from { transform: translateY(-20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }</style>", unsafe_allow_html=True)
        st.divider()
