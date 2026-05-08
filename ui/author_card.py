"""Author profile card — compact top-right widget, purple/violet accent."""
from __future__ import annotations

import json
import streamlit as st
from pathlib import Path


AUTHOR = {
    "name":      "Aditya Aravind Medepalli",
    "role":      "Researcher & Developer",
    "linkedin":  "https://www.linkedin.com/in/aditya-aravind-medepalli/",
    "initials":  "AA",
}

VISITOR_COUNT_FILE = Path("data/visitor_count.json")


def _get_visitor_count() -> int:
    """Get current visitor count from file."""
    if not VISITOR_COUNT_FILE.exists():
        return 0
    try:
        data = json.loads(VISITOR_COUNT_FILE.read_text())
        return data.get("count", 0)
    except Exception:
        return 0


def _increment_visitor_count() -> int:
    """Increment visitor count and return new total."""
    VISITOR_COUNT_FILE.parent.mkdir(parents=True, exist_ok=True)
    current = _get_visitor_count()
    new_count = current + 1

    try:
        VISITOR_COUNT_FILE.write_text(json.dumps({"count": new_count}))
    except Exception:
        pass  # Fail silently if can't write

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
        f'<div style="background:linear-gradient(135deg,rgba(88,28,135,0.28) 0%,rgba(124,58,237,0.18) 100%);'
        f'border:1px solid rgba(167,139,250,0.35);border-top:3px solid #a78bfa;'
        f'border-radius:10px;padding:0.6rem 0.9rem;">'
        f'<div style="display:flex;align-items:center;gap:0.55rem;margin-bottom:0.45rem;">'
        f'<div style="width:34px;height:34px;border-radius:50%;flex-shrink:0;'
        f'background:linear-gradient(135deg,#7c3aed,#a78bfa);'
        f'display:flex;align-items:center;justify-content:center;'
        f'font-size:0.72rem;font-weight:800;color:#fff;">'
        f'{AUTHOR["initials"]}</div>'
        f'<div style="flex:1;">'
        f'<p style="color:#f8fafc;font-size:0.78rem;font-weight:700;margin:0;line-height:1.2;">'
        f'{AUTHOR["name"]}</p>'
        f'<p style="color:#a78bfa;font-size:0.63rem;margin:0;">{AUTHOR["role"]}</p>'
        f'<a href="{AUTHOR["linkedin"]}" target="_blank" rel="noopener" style="'
        f'color:#0a66c2;font-size:0.6rem;font-weight:600;text-decoration:none;display:inline-block;margin-top:0.2rem;">'
        f'in LinkedIn</a>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
