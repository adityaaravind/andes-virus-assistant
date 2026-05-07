"""Author profile card — compact top-right widget, purple/violet accent."""
from __future__ import annotations

import streamlit as st


AUTHOR = {
    "name":      "Aditya Aravind Medepalli",
    "role":      "Researcher & Developer",
    "portfolio": "https://adityamedepalli.netlify.app/",
    "linkedin":  "https://www.linkedin.com/in/aditya-aravind-medepalli/",
    "initials":  "AA",
}


def render_author_card() -> None:
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
        f'<div>'
        f'<p style="color:#f8fafc;font-size:0.78rem;font-weight:700;margin:0;line-height:1.2;">'
        f'{AUTHOR["name"]}</p>'
        f'<p style="color:#a78bfa;font-size:0.63rem;margin:0;">{AUTHOR["role"]}</p>'
        f'</div>'
        f'</div>'
        f'<div style="display:flex;gap:0.35rem;">'
        f'<a href="{AUTHOR["portfolio"]}" target="_blank" rel="noopener" style="flex:1;text-align:center;'
        f'background:linear-gradient(135deg,#7c3aed,#a78bfa);'
        f'color:#fff;border-radius:6px;padding:0.28rem 0.4rem;'
        f'font-size:0.63rem;font-weight:700;text-decoration:none;white-space:nowrap;">'
        f'🌐 Portfolio</a>'
        f'<a href="{AUTHOR["linkedin"]}" target="_blank" rel="noopener" style="flex:1;text-align:center;'
        f'background:#0a66c2;color:#fff;border-radius:6px;padding:0.28rem 0.4rem;'
        f'font-size:0.63rem;font-weight:700;text-decoration:none;white-space:nowrap;">'
        f'in LinkedIn</a>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
