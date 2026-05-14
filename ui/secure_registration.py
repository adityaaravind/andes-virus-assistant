"""Enhanced registration UI with avatar selection and passkey authentication."""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from alerts.user_manager import (
    create_user,
    get_user,
    UserValidationError,
    get_leaderboard,
    get_user_rank,
    update_user_stats
)
from alerts.passkey_auth import (
    create_registration_challenge,
    create_authentication_challenge,
    store_user_credential,
    verify_user_credential,
    get_user_devices,
    PasskeyAuthError
)
from ui.avatar_system import render_avatar_selector, render_user_avatar, get_avatar_display


def get_current_user() -> dict | None:
    """Get currently logged-in user."""
    if "current_username" in st.session_state:
        return get_user(st.session_state.current_username)
    return None


def render_passkey_registration_form() -> None:
    """Render enhanced registration form with avatar and passkey options."""
    st.markdown("""
        <div style='background: linear-gradient(135deg, rgba(0,180,216,0.1), rgba(168,85,247,0.1));
                    border: 1px solid rgba(0,180,216,0.3); border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;'>
            <h3 style='color: #00b4d8; margin: 0 0 0.5rem 0; font-size: 1rem; display: flex; align-items: center;'>
                🔐 SECURE TRACKER REGISTRATION
            </h3>
            <p style='color: #94a3b8; font-size: 0.75rem; margin: 0;'>
                Choose passwordless passkey authentication or traditional username login
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Authentication method selection
    auth_method = st.radio(
        "**Authentication Method:**",
        ["🔑 Passkey (Recommended)", "👤 Username Only"],
        help="Passkeys use your device's built-in security (fingerprint, face unlock, etc.)"
    )

    with st.form("secure_registration_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            username = st.text_input(
                "Username*",
                placeholder="outbreak_tracker",
                help="3-20 characters, letters, numbers, and underscores only"
            )

        with col2:
            display_name = st.text_input(
                "Display Name*",
                placeholder="Dr. Sarah Chen",
                help="How others will see you in leaderboards"
            )

        # Avatar Selection
        st.markdown("---")
        selected_avatar = render_avatar_selector(use_selectbox=True)

        # Optional Information
        col3, col4 = st.columns(2)

        with col3:
            email = st.text_input(
                "Email (optional)",
                placeholder="alerts@example.com",
                help="For outbreak notifications (optional)"
            )

        with col4:
            location = st.selectbox(
                "Location (optional)",
                ["", "USA", "Canada", "UK", "Spain", "Germany", "France",
                 "Australia", "Japan", "South Korea", "Brazil", "Other"],
                help="For regional comparisons"
            )

        role = st.selectbox(
            "Role",
            ["public", "student", "researcher", "healthcare", "media", "government"],
            help="Your professional background"
        )

        # Passkey information
        if auth_method.startswith("🔑"):
            st.info("""
            **🔐 Passkey Benefits:**
            - No passwords to remember
            - Uses your device's biometric security
            - More secure than traditional passwords
            - Works across all your devices
            - Instant login with fingerprint/face unlock
            """)

        submitted = st.form_submit_button(
            "🚀 CREATE SECURE PROFILE" if auth_method.startswith("🔑") else "📝 CREATE PROFILE",
            use_container_width=True,
            type="primary"
        )

        if submitted:
            if not username or not display_name:
                st.error("Username and display name are required!")
                return

            try:
                # Create user profile
                user = create_user(
                    username=username,
                    display_name=display_name,
                    email=email,
                    location=location,
                    role=role,
                    avatar=selected_avatar
                )

                if auth_method.startswith("🔑"):
                    # Set up passkey registration
                    st.session_state.pending_registration = {
                        "username": username,
                        "user_profile": user
                    }
                    render_passkey_setup(username)
                else:
                    # Traditional username-only registration
                    st.session_state.current_username = username
                    st.success(f"🎉 Welcome to Outbreak Tracker, {display_name}!")
                    st.balloons()
                    st.rerun()

            except UserValidationError as e:
                st.error(f"Registration failed: {e}")


def render_passkey_setup(username: str) -> None:
    """Render passkey setup UI with WebAuthn integration."""
    st.markdown("### 🔐 Set Up Your Passkey")

    try:
        # Generate registration challenge
        challenge_options = create_registration_challenge(username)

        # WebAuthn JavaScript for passkey registration
        webauthn_js = f"""
        <script>
        async function registerPasskey() {{
            try {{
                // Convert challenge from base64
                const challenge = Uint8Array.from(atob('{challenge_options["challenge"]}'), c => c.charCodeAt(0));

                const publicKeyCredentialCreationOptions = {{
                    challenge: challenge,
                    rp: {{
                        name: "Andes Virus Assistant",
                        id: window.location.hostname,
                    }},
                    user: {{
                        id: Uint8Array.from('{username}', c => c.charCodeAt(0)),
                        name: '{username}',
                        displayName: '{username}',
                    }},
                    pubKeyCredParams: [
                        {{alg: -7, type: "public-key"}},
                        {{alg: -257, type: "public-key"}}
                    ],
                    authenticatorSelection: {{
                        authenticatorAttachment: "platform",
                        userVerification: "required",
                    }},
                    timeout: 60000,
                    attestation: "direct"
                }};

                const credential = await navigator.credentials.create({{
                    publicKey: publicKeyCredentialCreationOptions
                }});

                // Convert credential to JSON for Streamlit
                const credentialJSON = {{
                    id: credential.id,
                    rawId: Array.from(new Uint8Array(credential.rawId)),
                    response: {{
                        attestationObject: Array.from(new Uint8Array(credential.response.attestationObject)),
                        clientDataJSON: Array.from(new Uint8Array(credential.response.clientDataJSON)),
                    }},
                    type: credential.type,
                }};

                // Store result for Streamlit to access
                window.passkeyResult = credentialJSON;

                // Show success message
                document.getElementById('passkey-status').innerHTML =
                    '<div style="color: #22c55e; font-weight: bold;">✅ Passkey created successfully!</div>';

                return credentialJSON;

            }} catch (error) {{
                console.error('Passkey registration failed:', error);
                document.getElementById('passkey-status').innerHTML =
                    '<div style="color: #ef4444; font-weight: bold;">❌ Passkey setup failed: ' + error.message + '</div>';
                return null;
            }}
        }}
        </script>

        <div style="text-align: center; padding: 20px;">
            <button onclick="registerPasskey()"
                    style="background: linear-gradient(135deg, #00b4d8, #8b5cf6);
                           color: white; border: none; padding: 12px 24px;
                           border-radius: 8px; font-size: 16px; cursor: pointer;">
                🔐 Set Up Passkey
            </button>
            <div id="passkey-status" style="margin-top: 12px;"></div>
        </div>
        """

        components.html(webauthn_js, height=200)

        # Add manual completion option
        if st.button("✅ Complete Registration (Skip Passkey)", key="skip_passkey"):
            pending = st.session_state.get("pending_registration", {})
            if pending:
                st.session_state.current_username = pending["username"]
                st.success("Registration completed! You can add passkey security later.")
                st.rerun()

    except Exception as e:
        st.error(f"Passkey setup error: {e}")
        st.info("You can complete registration without passkey and add it later.")


def render_passkey_login() -> None:
    """Render passkey login interface."""
    st.markdown("""
        <div style='background: linear-gradient(135deg, rgba(34,197,94,0.1), rgba(168,85,247,0.1));
                    border: 1px solid rgba(34,197,94,0.3); border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;'>
            <h3 style='color: #22c55e; margin: 0 0 0.5rem 0; font-size: 1rem;'>
                🔐 SECURE LOGIN
            </h3>
            <p style='color: #94a3b8; font-size: 0.75rem; margin: 0;'>
                Use your passkey or username to continue tracking
            </p>
        </div>
    """, unsafe_allow_html=True)

    login_method = st.radio(
        "**Login Method:**",
        ["🔑 Passkey", "👤 Username"],
        horizontal=True
    )

    if login_method.startswith("🔑"):
        render_passkey_authentication()
    else:
        render_traditional_login()


def render_passkey_authentication() -> None:
    """Render passkey authentication UI."""
    st.markdown("### 🔐 Authenticate with Passkey")

    if st.button("🔐 Use Passkey", type="primary", use_container_width=True):
        # Trigger passkey authentication
        webauthn_auth_js = """
        <script>
        async function authenticatePasskey() {
            try {
                const publicKeyCredentialRequestOptions = {
                    challenge: new Uint8Array(32), // Will be replaced with real challenge
                    timeout: 60000,
                    userVerification: "required"
                };

                const credential = await navigator.credentials.get({
                    publicKey: publicKeyCredentialRequestOptions
                });

                // Show success
                document.getElementById('auth-status').innerHTML =
                    '<div style="color: #22c55e; font-weight: bold;">✅ Authentication successful!</div>';

            } catch (error) {
                document.getElementById('auth-status').innerHTML =
                    '<div style="color: #ef4444; font-weight: bold;">❌ Authentication failed: ' + error.message + '</div>';
            }
        }

        authenticatePasskey();
        </script>
        <div id="auth-status" style="margin-top: 12px; text-align: center;"></div>
        """

        components.html(webauthn_auth_js, height=100)


def render_traditional_login() -> None:
    """Render traditional username login."""
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")

        submitted = st.form_submit_button("🚀 CONTINUE TRACKING", use_container_width=True)

        if submitted:
            if not username:
                st.error("Please enter your username!")
                return

            user = get_user(username)
            if user:
                st.session_state.current_username = username
                update_user_stats(username, {})  # Update last_active
                st.success(f"Welcome back, {user['display_name']}!")
                st.rerun()
            else:
                st.error("Username not found. Check spelling or register as new user.")


def render_enhanced_user_profile() -> None:
    """Render enhanced user profile with avatar and security options."""
    user = get_current_user()
    if not user:
        return

    avatar_html = render_user_avatar(user.get("avatar", "scientist"), "medium")

    # Profile header with avatar
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, rgba(168,85,247,0.1), rgba(0,180,216,0.1));
                    border: 1px solid rgba(168,85,247,0.3); border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;'>
            <div style='display: flex; align-items: center; gap: 12px;'>
                {avatar_html}
                <div>
                    <h3 style='color: #a855f7; margin: 0; font-size: 1rem;'>
                        {user['display_name']}
                    </h3>
                    <p style='color: #94a3b8; margin: 0; font-size: 0.8rem;'>
                        @{user['username']} • {get_avatar_display(user.get("avatar", "scientist"))["name"]}
                    </p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Stats display
    stats = user["stats"]
    col1, col2, col3 = st.columns(3)

    with col1:
        rank, total = get_user_rank(user['username'], 'total_shares')
        st.metric("🎯 Rank", f"#{rank}" if rank > 0 else "Unranked")

    with col2:
        st.metric("📤 Shares", stats["total_shares"])

    with col3:
        st.metric("🗳️ Votes", stats["fear_votes"])

    # Security settings
    with st.expander("🔐 Security Settings"):
        has_passkey = user.get("preferences", {}).get("use_passkey", False)

        if has_passkey:
            st.success("✅ Passkey authentication enabled")
            devices = get_user_devices(user['username'])
            for device in devices:
                st.caption(f"📱 {device['device']} (Last used: {device['last_used'][:10]})")
        else:
            st.info("🔑 Add passkey for enhanced security")
            if st.button("🔐 Set Up Passkey"):
                render_passkey_setup(user['username'])

    # Quick actions
    col4, col5 = st.columns(2)
    with col4:
        if st.button("📊 View Leaderboard"):
            st.session_state.show_leaderboard = True

    with col5:
        if st.button("🚪 Logout"):
            if "current_username" in st.session_state:
                del st.session_state.current_username
            st.success("Logged out successfully!")
            st.rerun()


def render_enhanced_user_section() -> None:
    """Main enhanced user management section."""
    current_user = get_current_user()

    if current_user:
        render_enhanced_user_profile()
    else:
        # Check if registration was triggered from guest preview
        if st.session_state.get("show_registration", False):
            st.markdown("### 🚀 Guardian Registration")
            render_passkey_registration_form()

            # Clear the trigger
            if st.button("← Back"):
                st.session_state.show_registration = False
                st.rerun()
        else:
            tab1, tab2 = st.tabs(["🔐 Register", "🔑 Login"])

            with tab1:
                render_passkey_registration_form()

            with tab2:
                render_passkey_login()

    # Mini leaderboard with avatars
    if not st.session_state.get("show_leaderboard"):
        with st.expander("🏆 Tracker Leaderboard", expanded=False):
            render_avatar_leaderboard()


def render_avatar_leaderboard() -> None:
    """Render leaderboard with user avatars."""
    leaderboard = get_leaderboard("total_shares", limit=5)
    current_user = get_current_user()

    for i, user in enumerate(leaderboard, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔸"
        avatar_emoji = get_avatar_display(user.get("avatar", "scientist"))["emoji"]

        if current_user and user["username"] == current_user["username"]:
            st.markdown(f"**{emoji} {i}. {avatar_emoji} {user['display_name']}: {user['stats']['total_shares']} shares** ⭐")
        else:
            st.caption(f"{emoji} {i}. {avatar_emoji} {user['display_name']}: {user['stats']['total_shares']} shares")

    if current_user:
        rank, total = get_user_rank(current_user["username"], "total_shares")
        if rank > 5:
            st.caption(f"🎯 Your rank: #{rank} of {total}")