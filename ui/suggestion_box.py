"""Suggestion box component — project disclaimer and feedback collection."""
from __future__ import annotations

import json
import streamlit as st
from datetime import datetime
from pathlib import Path

FEEDBACK_FILE = Path("data/feedback.jsonl")


def _save_feedback(feedback_type: str, message: str, email: str = "") -> bool:
    """Save feedback to JSON lines file."""
    try:
        FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

        feedback_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": feedback_type,
            "message": message.strip(),
            "email": email.strip(),
        }

        with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(feedback_data) + "\n")

        return True
    except Exception:
        return False


def render_suggestion_box() -> None:
    """Render feedback/suggestion box with interactive form."""
    # Header with project description
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
        '<p style="color:#cbd5e1;font-size:0.85rem;line-height:1.5;margin:0;">'
        'If you encounter any <span style="color:#f59e0b;">bugs</span>, have <span style="color:#10b981;">suggestions for improvement</span>, '
        'or notice <span style="color:#ef4444;">inaccurate information</span>, please let me know! '
        'I\'m committed to fixing issues quickly and keeping this tool as helpful and current as possible.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Interactive feedback form with card styling
    st.markdown(
        '<div style="background:linear-gradient(135deg,rgba(13,27,42,0.95) 0%,rgba(27,46,69,0.95) 100%);'
        'border:1px solid rgba(0,180,216,0.3);border-top:3px solid #00b4d8;'
        'border-radius:12px;padding:1.2rem 1.5rem;margin:1rem 0;">'
        '<h5 style="color:#00b4d8;font-size:1rem;font-weight:600;margin:0 0 1rem;">📝 Submit Feedback Directly</h5>',
        unsafe_allow_html=True,
    )

    with st.form("feedback_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            feedback_type = st.selectbox(
                "Type of feedback:",
                ["Bug Report", "Feature Suggestion", "Data Issue", "General Comment"],
                index=0,
            )

        with col2:
            user_email = st.text_input(
                "Email (optional):",
                placeholder="your.email@example.com",
                help="Leave blank if you prefer to stay anonymous"
            )

        feedback_message = st.text_area(
            "Your message:",
            placeholder="Describe the issue, suggestion, or feedback in detail...",
            height=120,
            help="Please be as specific as possible to help me address your feedback effectively."
        )

        col_left, col_right = st.columns([3, 1])
        with col_right:
            submitted = st.form_submit_button(
                "Submit Feedback",
                use_container_width=True,
                type="primary"
            )

        if submitted:
            if feedback_message.strip():
                success = _save_feedback(feedback_type, feedback_message, user_email)
                if success:
                    st.success(
                        "✅ Thank you for your feedback! I'll review it and address any issues as quickly as possible.",
                        icon="🙏"
                    )
                else:
                    st.error("❌ Sorry, there was an issue saving your feedback. Please try emailing me directly.")
            else:
                st.warning("⚠️ Please enter your feedback message before submitting.")

    # Contact info footer
    st.markdown(
        '<div style="background:rgba(6,182,212,0.1);border:1px solid rgba(6,182,212,0.3);'
        'border-radius:8px;padding:0.8rem;margin:0.5rem 0;">'
        '<p style="color:#06b6d4;font-size:0.8rem;font-weight:600;margin:0 0 0.3rem;">📧 Direct Contact:</p>'
        '<p style="color:#e2e8f0;font-size:0.8rem;margin:0;">adityamedepalli@outlook.com</p>'
        '</div>'
        '</div>',  # Close the main form container
        unsafe_allow_html=True,
    )