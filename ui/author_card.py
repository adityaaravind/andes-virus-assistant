"""Author profile card — compact top-right widget, purple/violet accent."""
from __future__ import annotations

import streamlit as st
from alerts.persist_helper import bg_kv_set, get_persisted_value


AUTHOR = {
    "name":      "Aditya Aravind Medepalli",
    "role":      "Researcher & Developer",
    "linkedin":  "https://www.linkedin.com/in/aditya-aravind-medepalli/",
    "github":    "https://github.com/adityaaravind",
    "initials":  "AA",
}

_VISITOR_KEY = "analytics_visitor_count"


def _get_visitor_count() -> int:
    """Get current visitor count from persistent store."""
    return get_persisted_value(_VISITOR_KEY, 0)


def _increment_visitor_count() -> int:
    """Increment visitor count and return new total."""
    current = _get_visitor_count()
    new_count = current + 1
    bg_kv_set(_VISITOR_KEY, new_count)
    return new_count


def _track_visitor() -> int:
    """Track unique session visitor and return total count."""
    if st.session_state.get("visitor_counted"):
        return _get_visitor_count()

    st.session_state["visitor_counted"] = True
    return _increment_visitor_count()


def render_author_card() -> None:
    # Track visitor for analytics but don't display
    _track_visitor()

    st.markdown(
        f"""
        <div class="author-card-glow">
            <div style="display:flex; align-items:center; gap: 0.8rem;">
                <div style="width:42px; height:42px; border-radius:50%; flex-shrink:0; 
                    background:linear-gradient(135deg, #0077b5, #00b4d8); 
                    display:flex; align-items:center; justify-content:center; 
                    font-size:1rem; font-weight:950; color:white;
                    box-shadow: 0 0 15px rgba(0, 180, 216, 0.5);">
                    {AUTHOR["initials"]}
                </div>
                <div style="flex:1;">
                    <p style="color:white; font-size:0.9rem; font-weight:950; margin:0; line-height:1.1; text-shadow: 0 0 10px rgba(255,255,255,0.3);">
                        {AUTHOR["name"]}
                    </p>
                    <p style="color:var(--teal); font-size:0.65rem; margin:0; margin-bottom: 6px; font-weight:800; text-transform:uppercase; letter-spacing:0.05em; text-shadow: 0 0 8px rgba(0,180,216,0.4);">
                        {AUTHOR["role"]}
                    </p>
                    <div style="display:flex; gap:8px;">
                        <a href="{AUTHOR["linkedin"]}" target="_blank" class="linkedin-tag" style="font-size:0.55rem;">
                            LinkedIn ↗
                        </a>
                        <a href="{AUTHOR["github"]}" target="_blank" class="linkedin-tag" style="background:#333; box-shadow: 0 0 10px rgba(255,255,255,0.1); font-size:0.55rem;">
                            GitHub ↗
                        </a>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
