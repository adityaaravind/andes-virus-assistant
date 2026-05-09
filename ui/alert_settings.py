"""Alert subscription UI — ntfy.sh push notifications + email, configurable thresholds."""
from __future__ import annotations

import os
import random
from typing import Any

import streamlit as st

from alerts.alert_manager import add_subscription, get_alert_history, load_subscriptions
from alerts.notifier import send_ntfy, send_email


# ── Funny Zomato-style Welcome Messages ──
FUNNY_WELCOME_MESSAGES = [
    ("🧼 Hand Wash Protocol", "Wash your hands like you're scrubbing for a million-dollar surgery. We'll handle the data, you handle the soap!"),
    ("🤖 AI vs Virus", "Our AI is currently arguing with the Andes virus. The AI is winning. You're in safe hands!"),
    ("🛡️ Defense Force", "You're now part of the elite Andes Defense Force. First rule: No sharing drinks with rodents. Stay safe!"),
    ("🥤 Hydration Check", "We're tracking the virus so you can focus on tracking your weekend plans. Stay safe and stay hydrated!"),
    ("🦸‍♂️ Superhero Status", "If knowledge is power, you just became a superhero. Your notification shield is now ACTIVATED!"),
    ("🍎 Vitamin Boost", "Eating an apple today? Good. Reading our alerts today? Even better. Let's keep that health score high!"),
    ("🐀 Ratatouille Warning", "Rodents are only cute in movies. In real life, they don't cook, they just bring trouble. Stay alert!"),
    ("🧴 Squeaky Clean", "Your phone is now a hantavirus-free zone. (We can't actually clean your screen, but we're working on it)."),
    ("🍕 Pizza Logic", "Like a good pizza, our alerts are hot, fresh, and delivered right to your lock screen. Stay safe!"),
]


def _send_welcome_ping(topic: str) -> None:
    if not topic:
        return
    title, msg = random.choice(FUNNY_WELCOME_MESSAGES)
    send_ntfy(topic, f"✨ {title}", msg, level="info")


def render_alert_settings() -> None:
    st.markdown(
        '<div style="background:linear-gradient(135deg,rgba(13,27,42,0.95),rgba(27,46,69,0.95));'
        'border:1px solid rgba(239,68,68,0.3);border-top:3px solid #ef4444;border-radius:12px;'
        'padding:1rem 1.2rem;">'
        '<p style="color:#ef4444;font-size:0.95rem;font-weight:700;margin:0 0 0.8rem;letter-spacing:0.04em;">'
        '🔔 OUTBREAK ALERTS</p>',
        unsafe_allow_html=True,
    )

    # ── Direct subscribe button ─────────────────────────────────
    if st.button("📱 Press here for free alerts", use_container_width=True, type="primary"):
        st.session_state.alert_ntfy_topic = "HANTAVIRUS"
        # Auto-save subscription with HANTAVIRUS
        sub = {
            "ntfy_topic": "HANTAVIRUS",
            "email": "",
            "alerts": {
                "any_case_increase": True,
                "death_increase": True,
                "new_country": True,
                "risk_level_change": True,
                "case_threshold": 0,
            },
            "last_known": {},
        }
        add_subscription(sub)
        _send_welcome_ping("HANTAVIRUS")

        st.markdown(
            '<div style="background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.3);'
            'border-radius:8px;padding:0.8rem;margin:0.5rem 0;">'
            '<p style="color:#22c55e;font-size:0.9rem;font-weight:600;margin:0 0 0.4rem;">✅ Subscribed! Check your notifications.</p>'
            '<p style="color:#e2e8f0;font-size:0.75rem;margin:0 0 0.3rem;">We just sent you a welcome ping to <strong>HANTAVIRUS</strong>.</p>'
            '<p style="color:#94a3b8;font-size:0.7rem;margin:0;">'
            'App: <a href="https://ntfy.sh" target="_blank" style="color:#00b4d8;">ntfy.sh</a></p>'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── Custom alerts section ─────────────────────────────────
    st.markdown(
        '<div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.3);'
        'border-radius:8px;padding:0.7rem 0.8rem;margin:0.7rem 0;">'
        '<p style="color:#ef4444;font-size:0.72rem;font-weight:700;margin:0 0 0.3rem;'
        'text-transform:uppercase;letter-spacing:0.05em;">📡 Instant Outbreak Alerts</p>'
        '<p style="color:#f1f5f9;font-size:0.78rem;margin:0 0 0.5rem;">'
        'Get real-time push notifications in your browser. <b>No app or signup required.</b></p>'
        
        '<a href="https://ntfy.sh/HANTAVIRUS" target="_blank" style="display:block;background:#ef4444;color:white;text-align:center;padding:0.6rem;border-radius:8px;text-decoration:none;font-size:0.85rem;font-weight:800;margin-top:0.5rem;box-shadow: 0 4px 15px rgba(239,68,68,0.3);">'
        '🔔 Subscribe in Browser</a>'

        '<p style="color:#cbd5e1;font-size:0.75rem;margin:0.6rem 0 0.4rem;font-weight:600;">'
        'How it works:</p>'
        
        # ── Visual Guide Mockup ──
        '<div style="background:#08111e; border:1px solid rgba(255,255,255,0.1); border-radius:12px; padding:0.8rem; margin:0.5rem 0; position:relative;">'
            '<div style="display:flex; align-items:center; gap:8px; margin-bottom:0.8rem; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:0.4rem;">'
                '<div style="width:10px; height:10px; border-radius:50%; background:#ff5f56;"></div>'
                '<div style="width:10px; height:10px; border-radius:50%; background:#ffbd2e;"></div>'
                '<div style="width:10px; height:10px; border-radius:50%; background:#27c93f;"></div>'
                '<div style="color:#64748b; font-size:0.6rem; font-family:monospace; margin-left:4px;">ntfy.sh/HANTAVIRUS</div>'
            '</div>'
            '<div style="text-align:center; padding:0.5rem 0;">'
                '<div style="display:inline-block; background:#ef4444; color:white; padding:0.4rem 1.2rem; border-radius:20px; font-size:0.75rem; font-weight:800; border:2px solid #ffffff; box-shadow:0 0 15px rgba(239,68,68,0.5); animation: pulse-sub 2s infinite;">'
                    'Click "Subscribe"'
                '</div>'
                '<p style="color:#94a3b8; font-size:0.6rem; margin-top:0.6rem;">Tap the button on the next page</p>'
            '</div>'
        '</div>'
        '<style>@keyframes pulse-sub { 0% { transform:scale(1); } 50% { transform:scale(1.05); } 100% { transform:scale(1); } }</style>'

        '<p style="color:#94a3b8; font-size:0.68rem; line-height:1.4;">'
        'Works on Chrome, Safari (iOS 16.4+), and Android browsers. Your privacy is protected; no personal data is shared.</p></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.3);'
        'border-radius:8px;padding:0.7rem 0.8rem;margin:0.7rem 0;margin-top:0.8rem;padding-top:0.6rem;border-top:1px solid rgba(239,68,68,0.2);">'
        '<p style="color:#94a3b8;font-size:0.65rem;margin:0;">'
        'Prefer an app? Get <b>ntfy</b> on <a href="https://apps.apple.com/app/ntfy/id1622393045" target="_blank" style="color:#00b4d8;">iOS</a> or <a href="https://play.google.com/store/apps/details?id=io.heckel.ntfy" target="_blank" style="color:#00b4d8;">Android</a> and subscribe to <b>HANTAVIRUS</b>.'
        '</p></div>',
        unsafe_allow_html=True
    )

    with st.expander("Advanced alert settings", expanded=False):
        st.markdown(
            '<p style="color:#94a3b8;font-size:0.78rem;margin-bottom:0.8rem;">'
            'Get notified via <b style="color:#f8fafc;">ntfy.sh</b> (free push notifications) '
            'or email when outbreak conditions change.</p>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            ntfy_topic = st.text_input(
                "Custom ntfy.sh topic",
                value="HANTAVIRUS",
                help="Use a custom topic name for private alerts. Leave as HANTAVIRUS for public outbreak alerts.",
                key="alert_ntfy_topic",
            )
        with col2:
            email_addr = st.text_input(
                "Email (optional)",
                placeholder="you@example.com",
                help="Requires SMTP configured in .env (SMTP_HOST, SMTP_USER, SMTP_PASS)",
                key="alert_email",
            )

        st.markdown("**Alert conditions:**")

        ac1, ac2 = st.columns(2)
        with ac1:
            any_case = st.checkbox("Any new case confirmed", value=True, key="al_any_case")
            death_inc = st.checkbox("Death count increases", value=True, key="al_death")
            new_country = st.checkbox("New country affected", value=True, key="al_country")
        with ac2:
            risk_change = st.checkbox("Risk level changes", value=True, key="al_risk")
            threshold_on = st.checkbox("Case count threshold", value=False, key="al_thresh_on")
            if threshold_on:
                threshold_val = st.number_input(
                    "Alert when cases reach:", min_value=1, max_value=10000,
                    value=25, step=5, key="al_thresh_val",
                )
            else:
                threshold_val = 0

        col_save, col_test = st.columns(2)
        with col_save:
            if st.button("💾 Save subscription", use_container_width=True, key="save_alert"):
                if not ntfy_topic and not email_addr:
                    st.error("Enter ntfy.sh topic or email")
                else:
                            sub = {
                        "ntfy_topic": ntfy_topic.strip(),
                        "email": email_addr.strip(),
                        "alerts": {
                            "any_case_increase": any_case,
                            "death_increase":    death_inc,
                            "new_country":       new_country,
                            "risk_level_change": risk_change,
                            "case_threshold":    threshold_val if threshold_on else 0,
                        },
                        "last_known": {},
                    }
                    add_subscription(sub)
                    _send_welcome_ping(ntfy_topic.strip())
                    st.success("Subscription saved. We've sent you a welcome ping!")

        with col_test:
            if st.button("🔔 Test notification", use_container_width=True, key="test_alert"):
                topic = st.session_state.get("alert_ntfy_topic", "").strip()
                email = st.session_state.get("alert_email", "").strip()
                sent = False
                if topic:
                    ok = send_ntfy(
                        topic,
                        "✅ Andes Alert Test",
                        "Your Andes Virus Research Assistant alerts are configured correctly.",
                        level="info",
                    )
                    if ok:
                        st.success("Test notification sent to ntfy.sh!")
                        sent = True
                    else:
                        st.error("ntfy.sh send failed — check topic name")
                if email:
                    ok = send_email(
                        email,
                        "Andes Alert Test",
                        "Your Andes Virus Research Assistant email alerts are configured correctly.",
                    )
                    if ok:
                        st.success("Test email sent!")
                        sent = True
                    else:
                        st.warning("Email failed — check SMTP settings in .env")
                if not topic and not email:
                    st.warning("Enter a topic or email first")

    # ── Active subscriptions ─────────────────────────────────────────────────
    subs = load_subscriptions()
    if subs:
        st.markdown(
            f'<p style="color:#94a3b8;font-size:0.75rem;margin-top:0.5rem;">'
            f'✓ {len(subs)} active subscription(s)</p>',
            unsafe_allow_html=True,
        )

    # ── Recent alerts ────────────────────────────────────────────────────────
    history = get_alert_history(limit=5)
    if history:
        st.markdown(
            '<p style="color:#94a3b8;font-size:0.75rem;margin-top:0.3rem;font-weight:600;">'
            'Recent alerts sent:</p>',
            unsafe_allow_html=True,
        )
        for rec in history:
            ts = rec.get("ts", "")[:16].replace("T", " ")
            st.markdown(
                f'<div style="background:rgba(239,68,68,0.06);border-left:2px solid #ef444466;'
                f'border-radius:4px;padding:0.3rem 0.6rem;margin-bottom:0.25rem;">'
                f'<span style="color:#ef4444;font-size:0.7rem;">{ts}</span> '
                f'<span style="color:#f1f5f9;font-size:0.75rem;">{rec.get("title","")}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)
