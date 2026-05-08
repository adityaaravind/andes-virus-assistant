"""Suggestion box component — project disclaimer and feedback collection."""
from __future__ import annotations

import streamlit as st


def render_suggestion_box() -> None:
    """Render feedback/suggestion box with project disclaimer."""
    st.markdown(
        '<div style="background:linear-gradient(135deg,rgba(15,23,42,0.95) 0%,rgba(30,41,59,0.95) 100%);'
        'border:1px solid rgba(148,163,184,0.2);border-left:4px solid #06b6d4;'
        'border-radius:12px;padding:1.2rem 1.5rem;margin:2rem 0 1rem;">'
        '<h4 style="color:#06b6d4;font-size:1.1rem;font-weight:700;margin:0 0 0.8rem;display:flex;align-items:center;gap:0.5rem;">'
        '💬 Project Feedback & Suggestions</h4>'
        '<p style="color:#e2e8f0;font-size:0.9rem;line-height:1.6;margin:0 0 0.8rem;">'
        'This is a <strong style="color:#06b6d4;">side project</strong> created to help people stay informed '
        'and make safer decisions during the ongoing Andes virus outbreak. My goal is to provide accurate, '
        'real-time information without promoting fear or panic — simply to keep everyone better informed.</p>'
        '<p style="color:#cbd5e1;font-size:0.85rem;line-height:1.5;margin:0 0 0.8rem;">'
        'If you encounter any <span style="color:#f59e0b;">bugs</span>, have <span style="color:#10b981;">suggestions for improvement</span>, '
        'or notice <span style="color:#ef4444;">inaccurate information</span>, please let me know! '
        'I\'m committed to fixing issues quickly and keeping this tool as helpful and current as possible.</p>'
        '<div style="background:rgba(6,182,212,0.1);border:1px solid rgba(6,182,212,0.3);'
        'border-radius:8px;padding:0.8rem;margin-top:0.8rem;">'
        '<p style="color:#06b6d4;font-size:0.8rem;font-weight:600;margin:0 0 0.3rem;">📧 Contact for Feedback:</p>'
        '<p style="color:#e2e8f0;font-size:0.8rem;margin:0;">adityamedepalli@outlook.com</p>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )