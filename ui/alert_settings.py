"""Alert subscription UI — OneSignal browser push + email, configurable thresholds."""
from __future__ import annotations

import os
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from alerts.alert_manager import add_subscription, get_alert_history, load_subscriptions
from alerts.notifier import send_onesignal, send_email

ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID", "")


def render_alert_settings() -> None:
    st.markdown(
        '<div style="background:linear-gradient(135deg,rgba(13,27,42,0.95),rgba(27,46,69,0.95));'
        'border:1px solid rgba(239,68,68,0.3);border-top:3px solid #ef4444;border-radius:12px;'
        'padding:1rem 1.2rem;">'
        '<p style="color:#ef4444;font-size:0.95rem;font-weight:700;margin:0 0 0.8rem;letter-spacing:0.04em;">'
        '🔔 OUTBREAK ALERTS</p>',
        unsafe_allow_html=True,
    )

    # ── OneSignal browser push notifications ─────────────────────────────────
    if ONESIGNAL_APP_ID:
        st.markdown(
            f'<div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.3);'
            f'border-radius:8px;padding:0.7rem 0.8rem;margin-bottom:0.7rem;">'
            f'<p style="color:#ef4444;font-size:0.72rem;font-weight:700;margin:0 0 0.3rem;'
            f'text-transform:uppercase;letter-spacing:0.05em;">📡 Browser Push Alerts</p>'
            f'<p style="color:#f1f5f9;font-size:0.78rem;margin:0 0 0.5rem;">'
            f'Get instant outbreak alerts directly in your browser — no app download needed.</p>',
            unsafe_allow_html=True,
        )

        # OneSignal integration
        onesignal_html = f"""
        <script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js" defer></script>
        <script>
          window.OneSignalDeferred = window.OneSignalDeferred || [];
          OneSignalDeferred.push(function(OneSignal) {{
            OneSignal.init({{
              appId: "{ONESIGNAL_APP_ID}",
              safari_web_id: "web.onesignal.auto.{ONESIGNAL_APP_ID}",
              notifyButton: {{
                enable: false
              }}
            }});

            // Custom subscribe button
            window.subscribeToNotifications = function() {{
              OneSignal.showSlidedownPrompt().then(function() {{
                OneSignal.getNotificationPermission().then(function(permission) {{
                  if (permission === 'granted') {{
                    document.getElementById('onesignal-status').innerHTML =
                      '<span style="color:#22c55e;">✅ Subscribed to outbreak alerts!</span>';
                  }}
                }});
              }});
            }};

            // Check current subscription status
            OneSignal.getNotificationPermission().then(function(permission) {{
              const statusEl = document.getElementById('onesignal-status');
              if (permission === 'granted') {{
                statusEl.innerHTML = '<span style="color:#22c55e;">✅ Already subscribed</span>';
              }} else if (permission === 'denied') {{
                statusEl.innerHTML = '<span style="color:#ef4444;">❌ Notifications blocked — please enable in browser settings</span>';
              }} else {{
                statusEl.innerHTML = '<span style="color:#f59e0b;">⏸ Click button below to subscribe</span>';
              }}
            }});
          }});
        </script>
        <div style="text-align:center;margin:0.8rem 0;">
          <button onclick="subscribeToNotifications()" style="
            background:#ef4444;color:#fff;border:none;border-radius:8px;
            padding:0.8rem 1.5rem;font-size:0.9rem;font-weight:700;
            cursor:pointer;transition:all 0.2s ease;">
            🔔 Enable Browser Notifications
          </button>
          <p id="onesignal-status" style="margin:0.5rem 0 0;font-size:0.75rem;color:#94a3b8;">
            Loading subscription status...
          </p>
        </div>
        """

        components.html(onesignal_html, height=150)

        st.markdown(
            f'<p style="color:#475569;font-size:0.65rem;margin:0.4rem 0 0;font-family:monospace;">'
            f'Powered by OneSignal · App ID: {ONESIGNAL_APP_ID[:8]}...</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with st.expander("Configure your alerts", expanded=False):
        st.markdown(
            '<p style="color:#94a3b8;font-size:0.78rem;margin-bottom:0.8rem;">'
            'Get notified via <b style="color:#f8fafc;">ntfy.sh</b> (free push notifications) '
            'or email when outbreak conditions change.</p>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            ntfy_topic = st.text_input(
                "ntfy.sh topic",
                placeholder="e.g. andes-alerts-yourname",
                help="Install ntfy app → subscribe to your topic → get push notifications on any device. Free, no account needed.",
                key="alert_ntfy_topic",
            )
            st.markdown(
                '<p style="color:#475569;font-size:0.68rem;margin-top:-0.4rem;">'
                'Download: <a href="https://ntfy.sh" target="_blank" style="color:#00b4d8;">ntfy.sh</a> '
                '→ subscribe to your topic name above</p>',
                unsafe_allow_html=True,
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
                    st.success("Subscription saved. You'll be notified on next change.")

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
