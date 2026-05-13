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

    # ── Direct subscribe button with browser notification ─────────────────────────────────
    st.markdown("""
    <div style="background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.2);border-radius:12px;padding:1rem;margin-bottom:1rem;">
        <p style="color:#ef4444;font-size:0.8rem;font-weight:600;margin:0 0 0.5rem;">
            💡 <b>What to expect:</b> Desktop popup notification will appear outside your browser (usually top-right corner)
        </p>
    </div>

    <div id="notification-container">
        <button id="subscribe-btn" onclick="subscribeToNotifications()"
                style="width:100%;background:#ef4444;color:white;border:none;padding:0.8rem;
                       border-radius:8px;font-size:1rem;font-weight:700;cursor:pointer;
                       box-shadow:0 4px 15px rgba(239,68,68,0.3);">
            📱 Press here for free alerts
        </button>
        <div id="subscription-status" style="margin-top:0.8rem;display:none;"></div>
    </div>

    <script>
    async function subscribeToNotifications() {
        const btn = document.getElementById('subscribe-btn');
        const status = document.getElementById('subscription-status');

        try {
            console.log('Requesting notification permission...');

            // Check browser support first
            if (!('Notification' in window)) {
                throw new Error('Browser does not support desktop notifications');
            }

            // Request notification permission
            const permission = await Notification.requestPermission();
            console.log('Permission result:', permission);

            if (permission === 'granted') {
                console.log('Permission granted, showing welcome notification...');

                // Show immediate welcome notification
                const welcomeMessages = [
                    "Wash your hands like you're scrubbing for a million-dollar surgery. We'll handle the data, you handle the soap!",
                    "Our AI is currently arguing with the Andes virus. The AI is winning. You're in safe hands!",
                    "You're now part of the elite Andes Defense Force. First rule: No sharing drinks with rodents. Stay safe!",
                    "If knowledge is power, you just became a superhero. Your notification shield is now ACTIVATED!"
                ];
                const randomWelcome = welcomeMessages[Math.floor(Math.random() * welcomeMessages.length)];

                try {
                    const notification = new Notification('✨ Welcome to Andes Defense Force!', {
                        body: randomWelcome,
                        icon: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMTMuMDkgOC4yNkwyMCA5TDEzLjA5IDE1Ljc0TDEyIDIyTDEwLjkxITE1Ljc0TDQgOUwxMC45MSA4LjI2TDEyIDJaIiBmaWxsPSIjMjJjNTVlIi8+Cjwvc3ZnPgo=',
                        requireInteraction: true,
                        tag: 'welcome-andes',
                        silent: false
                    });

                    console.log('✅ Welcome notification created and should be visible');

                    // Log when notification is clicked
                    notification.onclick = () => {
                        console.log('Welcome notification clicked');
                        window.focus();
                        notification.close();
                    };

                    notification.onerror = (error) => {
                        console.error('Notification error:', error);
                    };

                    notification.onshow = () => {
                        console.log('Notification is now showing');
                    };

                    notification.onclose = () => {
                        console.log('Notification closed');
                    };

                } catch (notifError) {
                    console.error('❌ Failed to create welcome notification:', notifError);
                    alert('Failed to show welcome notification: ' + notifError.message);
                }

                // Update UI
                btn.innerHTML = '✅ Notifications Active!';
                btn.style.background = '#22c55e';
                btn.disabled = true;

                status.innerHTML = `
                    <div style="background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.3);
                                border-radius:8px;padding:0.8rem;">
                        <p style="color:#22c55e;font-size:0.9rem;font-weight:600;margin:0 0 0.4rem;">
                            ✅ Notifications activated!</p>
                        <p style="color:#e2e8f0;font-size:0.75rem;margin:0 0 0.3rem;">
                            You'll receive instant outbreak alerts in your browser.</p>
                        <p style="color:#94a3b8;font-size:0.7rem;margin:0;">
                            Subscription automatically saved.</p>
                    </div>`;
                status.style.display = 'block';

                // Trigger subscription save by reloading with query param
                console.log('Scheduling page reload to save subscription...');
                setTimeout(() => {
                    const url = new URL(window.location);
                    url.searchParams.set('subscribe_alerts', 'true');
                    console.log('Redirecting to:', url.toString());
                    window.location.href = url.toString();
                }, 1500);

            } else if (permission === 'denied') {
                console.log('❌ Permission denied by user');
                btn.innerHTML = '❌ Blocked';
                btn.style.background = '#ef4444';

                status.innerHTML = `
                    <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);
                                border-radius:8px;padding:0.8rem;">
                        <p style="color:#ef4444;font-size:0.9rem;font-weight:600;margin:0 0 0.4rem;">
                            ❌ Notifications are BLOCKED</p>
                        <p style="color:#e2e8f0;font-size:0.75rem;margin:0 0 0.3rem;">
                            <b>To enable:</b><br>
                            1. Click 🔒 lock icon in address bar<br>
                            2. Set "Notifications" to "Allow"<br>
                            3. Refresh page and try again</p>
                        <p style="color:#94a3b8;font-size:0.7rem;margin:0;">
                            Desktop notifications appear outside browser window.</p>
                    </div>`;
                status.style.display = 'block';

                // Also show alert for immediate feedback
                alert('❌ Notifications BLOCKED!\\n\\nTo enable:\\n1. Click 🔒 in address bar\\n2. Set Notifications to "Allow"\\n3. Refresh and try again');

            } else {
                // Permission prompt dismissed
                btn.innerHTML = '⏳ Permission Required';
                btn.style.background = '#f59e0b';

                status.innerHTML = `
                    <div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);
                                border-radius:8px;padding:0.8rem;">
                        <p style="color:#f59e0b;font-size:0.9rem;font-weight:600;margin:0 0 0.4rem;">
                            ⏳ Permission needed</p>
                        <p style="color:#e2e8f0;font-size:0.75rem;margin:0 0 0.3rem;">
                            Click the button again to enable notifications.</p>
                        <p style="color:#94a3b8;font-size:0.7rem;margin:0;">
                            Browser notifications required for instant alerts.</p>
                    </div>`;
                status.style.display = 'block';
            }

        } catch (error) {
            console.error('Notification subscription failed:', error);
            btn.innerHTML = '❌ Error occurred';
            btn.style.background = '#ef4444';

            status.innerHTML = `
                <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);
                            border-radius:8px;padding:0.8rem;">
                    <p style="color:#ef4444;font-size:0.9rem;font-weight:600;margin:0 0 0.4rem;">
                        ❌ Setup failed</p>
                    <p style="color:#e2e8f0;font-size:0.75rem;margin:0 0 0.3rem;">
                        Browser may not support notifications.</p>
                    <p style="color:#94a3b8;font-size:0.7rem;margin:0;">
                        Try a different browser or device.</p>
                </div>`;
            status.style.display = 'block';
        }
    }

    // Test if notifications are already enabled
    if (Notification.permission === 'granted') {
        const btn = document.getElementById('subscribe-btn');
        btn.innerHTML = '✅ Already Enabled';
        btn.style.background = '#22c55e';
    }
    </script>
    """, unsafe_allow_html=True)

    # Check for query parameter from JavaScript redirect
    try:
        # Use newer API if available, fallback to experimental
        if hasattr(st, 'query_params'):
            subscribe_requested = st.query_params.get('subscribe_alerts') == 'true'
        else:
            query_params = st.experimental_get_query_params()
            subscribe_requested = query_params.get('subscribe_alerts') == ['true']
    except Exception:
        subscribe_requested = False

    if subscribe_requested and not st.session_state.get('auto_subscribed_done', False):
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
        st.session_state.auto_subscribed = True
        st.session_state.auto_subscribed_done = True  # Prevent re-triggering

        # Clear query param and refresh
        st.markdown("""
        <script>
        try {
            const url = new URL(window.location);
            url.searchParams.delete('subscribe_alerts');
            window.history.replaceState({}, '', url.toString());
        } catch (e) {
            // Fallback for URL manipulation issues
            console.log('URL cleanup failed:', e);
        }
        </script>
        """, unsafe_allow_html=True)

    # Show success message if auto-subscription completed
    if st.session_state.get("auto_subscribed", False):
        st.markdown(
            '<div style="background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.3);'
            'border-radius:8px;padding:0.8rem;margin:0.5rem 0;">'
            '<p style="color:#22c55e;font-size:0.9rem;font-weight:600;margin:0 0 0.4rem;">✅ Alerts activated!</p>'
            '<p style="color:#e2e8f0;font-size:0.75rem;margin:0 0 0.3rem;">You\'re now subscribed to outbreak notifications.</p>'
            '<p style="color:#94a3b8;font-size:0.7rem;margin:0;">Welcome notification sent to your browser.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        # Clear the flag
        st.session_state.auto_subscribed = False

    # Handle Streamlit button fallback for when JavaScript is disabled (disabled for analytics compatibility)
    # if st.button("🔄 Fallback: Manual Setup", key="manual_fallback"):
    #     st.session_state.alert_ntfy_topic = "HANTAVIRUS"
    #     sub = {
    #         "ntfy_topic": "HANTAVIRUS",
    #         "email": "",
    #         "alerts": {
    #             "any_case_increase": True,
    #             "death_increase": True,
    #             "new_country": True,
    #             "risk_level_change": True,
    #             "case_threshold": 0,
    #         },
    #         "last_known": {},
    #     }
    #     add_subscription(sub)
        _send_welcome_ping("HANTAVIRUS")

        st.markdown(
            '<div style="background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.3);'
            'border-radius:8px;padding:0.8rem;margin:0.5rem 0;">'
            '<p style="color:#22c55e;font-size:0.9rem;font-weight:600;margin:0 0 0.4rem;">✅ Subscription saved!</p>'
            '<p style="color:#e2e8f0;font-size:0.75rem;margin:0 0 0.3rem;">Visit <a href="https://ntfy.sh/HANTAVIRUS" target="_blank" style="color:#00b4d8;">ntfy.sh/HANTAVIRUS</a> to complete setup.</p>'
            '<p style="color:#94a3b8;font-size:0.7rem;margin:0;">Welcome test notification sent.</p>'
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
        'Get real-time push notifications in your browser. <b>One-click activation above.</b></p>'

        '<p style="color:#cbd5e1;font-size:0.75rem;margin:0.6rem 0 0.4rem;font-weight:600;">'
        'You\'ll receive notifications for:</p>'

        '<div style="background:rgba(239,68,68,0.05);border-radius:8px;padding:0.6rem;margin:0.5rem 0;">'
            '<p style="color:#e2e8f0;font-size:0.7rem;margin:0 0 0.3rem;">🦠 New confirmed cases</p>'
            '<p style="color:#e2e8f0;font-size:0.7rem;margin:0 0 0.3rem;">💀 Death count increases</p>'
            '<p style="color:#e2e8f0;font-size:0.7rem;margin:0 0 0.3rem;">🌍 New countries affected</p>'
            '<p style="color:#e2e8f0;font-size:0.7rem;margin:0 0 0.3rem;">📈 Risk level changes</p>'
            '<p style="color:#e2e8f0;font-size:0.7rem;margin:0;">🧬 Critical research findings</p>'
        '</div>'

        '<p style="color:#94a3b8; font-size:0.68rem; line-height:1.4;">'
        'Works on Chrome, Safari (iOS 16.4+), and Android browsers. Your privacy is protected; no personal data is shared.</p></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.3);'
        'border-radius:8px;padding:0.7rem 0.8rem;margin:0.7rem 0;margin-top:0.8rem;padding-top:0.6rem;border-top:1px solid rgba(239,68,68,0.2);">'
        '<p style="color:#94a3b8;font-size:0.65rem;margin:0;">'
        'Notifications automatically enabled when you click the button above. No manual setup required!'
        '</p></div>',
        unsafe_allow_html=True
    )

    # Add debug section for testing
    if st.button("🧪 Test Browser Notification", key="test_browser_notif"):
        st.markdown("""
        <script>
        async function testBrowserNotification() {
            console.log('Testing browser notification...');

            // Check if browser supports notifications
            if (!('Notification' in window)) {
                alert('❌ This browser does not support desktop notifications');
                return;
            }

            console.log('Current permission state:', Notification.permission);

            // Request permission if not already granted
            let permission = Notification.permission;
            if (permission === 'default') {
                permission = await Notification.requestPermission();
                console.log('Permission after request:', permission);
            }

            if (permission === 'granted') {
                console.log('✅ Permission granted, creating notification...');

                try {
                    const notif = new Notification('🧪 Test Alert', {
                        body: 'SUCCESS! Desktop notifications are working. You should see this popup outside your browser window.',
                        icon: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMTMuMDkgOC4yNkwyMCA5TDEzLjA5IDE1Ljc0TDEyIDIyTDEwLjkxIDE1Ljc0TDQgOUwxMC45MSA4LjI2TDEyIDJaIiBmaWxsPSIjRUY0NDQ0Ii8+Cjwvc3ZnPgo=',
                        requireInteraction: true,
                        tag: 'test-notification'
                    });

                    console.log('✅ Notification created successfully');

                    notif.onclick = function() {
                        console.log('Notification clicked!');
                        window.focus();
                        notif.close();
                    };

                    // Auto-close after 8 seconds
                    setTimeout(() => {
                        notif.close();
                        console.log('Test notification auto-closed');
                    }, 8000);

                    alert('✅ Test notification sent! Check top-right corner of your screen.');

                } catch (error) {
                    console.error('❌ Failed to create notification:', error);
                    alert('❌ Failed to create notification: ' + error.message);
                }

            } else if (permission === 'denied') {
                alert('❌ Notifications are BLOCKED.\\n\\nTo enable:\\n1. Click the 🔒 lock icon in address bar\\n2. Set Notifications to "Allow"\\n3. Refresh page and try again');
            } else {
                alert('❌ Notification permission: ' + permission);
            }
        }

        testBrowserNotification();
        </script>
        """, unsafe_allow_html=True)

    # Test ntfy.sh notifications
    if st.button("🔔 Test NTFY.sh Notification", key="test_ntfy"):
        from alerts.notifier import send_ntfy
        success = send_ntfy(
            "HANTAVIRUS",
            "🧪 Test Alert",
            "This is a test notification from the Andes Virus Assistant. If you see this, ntfy.sh is working!",
            level="info"
        )
        if success:
            st.success("Test notification sent to HANTAVIRUS topic!")
            st.info("Check https://ntfy.sh/HANTAVIRUS to see if it appeared")
        else:
            st.error("Failed to send test notification")

    # Debug: Show current subscriptions
    if st.button("🔍 Show Current Subscriptions", key="debug_subs"):
        subs = load_subscriptions()
        st.json(subs)
        st.info(f"Found {len(subs)} subscription(s)")

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
