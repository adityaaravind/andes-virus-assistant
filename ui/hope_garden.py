"""Hope Garden - Community-driven garden game UI."""
from __future__ import annotations

import streamlit as st
from datetime import datetime
from typing import Dict, Any


def render_hope_garden_card() -> None:
    """Render the Hope Garden community game card."""
    try:
        from game.garden_state import garden_state
        from datetime import datetime

        # Auto-refresh every 30 seconds for real-time updates
        import time
        current_time = int(time.time())
        refresh_key = f"garden_refresh_{current_time // 30}"  # Refresh every 30 seconds

        # Get current garden display info
        garden_info = garden_state.get_garden_display_info()

        # Garden header with animations
        st.markdown(
            f"""
            <div class="stat-card hope-garden-card" style='background: linear-gradient(135deg, rgba(74,222,128,0.1), rgba(34,197,94,0.1)); border: 1px solid rgba(74,222,128,0.3); margin-bottom: 1rem;'>
                <div class="mission-header" style='border-left: 3px solid #4ade80; padding-left:12px; margin-bottom:0.8rem; display:flex; justify-content:space-between; align-items:center;'>
                    <div>
                        <h2 style='margin:0; font-size:1rem; letter-spacing:0.1em; color:#ffffff; text-shadow: 0 0 10px rgba(74,222,128,0.5);'>🌱 HOPE GARDEN</h2>
                        <p style='margin:0; font-size:0.55rem; color:#4ade80; font-family:monospace; font-weight:800;'>COMMUNITY HEALING SPACE</p>
                    </div>
                    <div class="live-indicator" style="background:rgba(74,222,128,0.1); border:1px solid #4ade8044; padding:1px 8px; border-radius:4px; animation: pulse-hero 2s infinite;">
                        <span style="color:#4ade80; font-size:8px; font-weight:900;">● LIVE</span>
                        <br><span style="color:#64748b; font-size:6px;">{datetime.utcnow().strftime('%H:%M UTC')}</span>
                    </div>
                </div>

                <style>
                @keyframes garden-grow {{
                    0% {{ transform: scale(1); }}
                    50% {{ transform: scale(1.1); }}
                    100% {{ transform: scale(1); }}
                }}

                @keyframes garden-pulse {{
                    0% {{ box-shadow: 0 0 0 0 rgba(74,222,128,0.7); }}
                    70% {{ box-shadow: 0 0 0 10px rgba(74,222,128,0); }}
                    100% {{ box-shadow: 0 0 0 0 rgba(74,222,128,0); }}
                }}

                @keyframes plant-sway {{
                    0%, 100% {{ transform: rotate(0deg); }}
                    25% {{ transform: rotate(2deg); }}
                    75% {{ transform: rotate(-2deg); }}
                }}

                @keyframes care-glow {{
                    0% {{ box-shadow: 0 0 5px rgba(74,222,128,0.3); }}
                    50% {{ box-shadow: 0 0 20px rgba(74,222,128,0.8); }}
                    100% {{ box-shadow: 0 0 5px rgba(74,222,128,0.3); }}
                }}

                .hope-garden-card {{
                    animation: garden-pulse 3s infinite ease-in-out;
                    backdrop-filter: blur(12px);
                }}

                .garden-stage {{
                    animation: plant-sway 4s infinite ease-in-out;
                }}

                .care-button {{
                    animation: care-glow 2s infinite ease-in-out;
                    transition: all 0.3s ease;
                }}

                .care-button:hover {{
                    transform: translateY(-2px);
                    filter: brightness(1.2);
                }}

                .garden-healthy {{
                    animation: garden-grow 2s infinite ease-in-out;
                }}

                .garden-stressed {{
                    animation: shake 0.5s infinite;
                }}

                @keyframes shake {{
                    0%, 100% {{ transform: translateX(0); }}
                    25% {{ transform: translateX(-2px); }}
                    75% {{ transform: translateX(2px); }}
                }}
                </style>
            """,
            unsafe_allow_html=True
        )

        # Garden visualization and status
        current_stage = garden_info["current_stage"]
        next_stage = garden_info["next_stage"]
        health = garden_info["health"]
        progress = garden_info["progress_percent"]
        needs_care = garden_info["needs_care"]

        # Garden visualization using stat cards layout
        stats_row1 = st.columns(3)
        stats_row2 = st.columns(2)

        # Main garden stage card
        with stats_row1[0]:
            garden_class = "garden-healthy" if health > 70 else "garden-stressed" if needs_care else ""
            st.markdown(
                f"""
                <div class="stat-card garden-stage {garden_class}" style="text-align: center; min-height: 140px;">
                    <div class="stat-value" style="font-size: 3rem; margin-bottom: 0.5rem; animation: plant-sway 4s infinite ease-in-out;">{current_stage["emoji"]}</div>
                    <div class="stat-label" style="color: #4ade80; margin-bottom: 0.3rem;">{current_stage["name"]}</div>
                    <div style="color: #94a3b8; font-size: 0.65rem; line-height: 1.2;">{current_stage["description"]}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Health card with animated meter
        with stats_row1[1]:
            health_color = "#22c55e" if health > 70 else "#f59e0b" if health > 30 else "#ef4444"
            st.markdown(
                f"""
                <div class="stat-card" style="text-align: center;">
                    <div class="stat-value glow-hero" style="color: {health_color};">{health}<span style="font-size: 1.2rem;">%</span></div>
                    <div class="stat-label">Garden Health</div>
                    <div style="background: rgba(0,0,0,0.3); border-radius: 10px; height: 8px; margin-top: 0.5rem;">
                        <div style="background: {health_color}; height: 100%; width: {health}%; border-radius: 10px; transition: width 1s ease; box-shadow: 0 0 10px {health_color};"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Stress level card
        with stats_row1[2]:
            stress_level = garden_info["stress_level"]
            stress_color = "#ef4444" if stress_level > 70 else "#f59e0b" if stress_level > 30 else "#22c55e"
            st.markdown(
                f"""
                <div class="stat-card" style="text-align: center;">
                    <div class="stat-value" style="color: {stress_color};">{stress_level}<span style="font-size: 1.2rem;">%</span></div>
                    <div class="stat-label">Stress Level</div>
                    <div style="background: rgba(0,0,0,0.3); border-radius: 10px; height: 8px; margin-top: 0.5rem;">
                        <div style="background: {stress_color}; height: 100%; width: {stress_level}%; border-radius: 10px; transition: width 1s ease; box-shadow: 0 0 8px {stress_color};"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Progress to next stage card
        with stats_row2[0]:
            if next_stage:
                st.markdown(
                    f"""
                    <div class="stat-card" style="text-align: center;">
                        <div class="stat-value glow-green">{progress:.1f}<span style="font-size: 1.2rem;">%</span></div>
                        <div class="stat-label">Progress to {next_stage['name']}</div>
                        <div style="background: rgba(0,0,0,0.3); border-radius: 10px; height: 8px; margin-top: 0.5rem;">
                            <div style="background: #4ade80; height: 100%; width: {progress}%; border-radius: 10px; transition: width 1s ease; box-shadow: 0 0 10px #4ade80;"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div class="stat-card" style="text-align: center;">
                        <div class="stat-value glow-green">MAX</div>
                        <div class="stat-label">🌟 Peak Growth Achieved</div>
                        <div style="color: #4ade80; font-size: 0.7rem; margin-top: 0.5rem;">Garden has reached maximum stage!</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Community stats card
        with stats_row2[1]:
            st.markdown(
                f"""
                <div class="stat-card" style="text-align: center;">
                    <div class="stat-value glow-green">{garden_info["total_community_actions"]}</div>
                    <div class="stat-label">Total Community Actions</div>
                    <div style="color: #4ade80; font-size: 0.8rem; margin-top: 0.3rem;">Today: {garden_info["daily_actions"]}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Status message bar
        st.markdown(
            f"""
            <div class="stat-card" style="background: linear-gradient(90deg, {garden_info['status_color']}20, rgba(0,0,0,0.1)); border-left: 3px solid {garden_info['status_color']}; text-align: center; margin: 1rem 0;">
                <div style="color: {garden_info['status_color']}; font-size: 0.9rem; font-weight: 700; animation: text-live-shake 3s infinite;">
                    {garden_info['status_message']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Care actions section (only show if garden needs care)
        if needs_care:
            st.markdown("### 🆘 Garden Needs Community Care!")

            # Care progress card
            care_progress = garden_info["care_points"] / max(garden_info["care_points_needed"], 1)
            st.markdown(
                f"""
                <div class="stat-card" style="text-align: center; margin-bottom: 1rem; background: linear-gradient(135deg, rgba(239,68,68,0.1), rgba(220,38,38,0.1)); border: 1px solid rgba(239,68,68,0.3);">
                    <div class="stat-value" style="color: #ef4444;">{garden_info['care_points']}<span style="font-size: 1.2rem;">/{garden_info['care_points_needed']}</span></div>
                    <div class="stat-label">Care Points Progress</div>
                    <div style="background: rgba(0,0,0,0.3); border-radius: 10px; height: 10px; margin-top: 0.5rem;">
                        <div style="background: #ef4444; height: 100%; width: {care_progress * 100}%; border-radius: 10px; transition: width 1s ease; box-shadow: 0 0 15px #ef4444; animation: care-glow 2s infinite;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Care action buttons in stat card style
            care_cols = st.columns(4)

            care_actions = [
                {"emoji": "💧", "name": "Water", "points": "+3", "key": "garden_water", "type": "water", "color": "#3b82f6"},
                {"emoji": "🌞", "name": "Sunlight", "points": "+4", "key": "garden_sunlight", "type": "sunlight", "color": "#f59e0b"},
                {"emoji": "💚", "name": "Hope", "points": "+5", "key": "garden_hope", "type": "hope", "color": "#22c55e"},
                {"emoji": "🌿", "name": "Heal", "points": "+6", "key": "garden_heal", "type": "healing", "color": "#8b5cf6"}
            ]

            for i, action in enumerate(care_actions):
                with care_cols[i]:
                    # Custom button styling with animations
                    button_id = f"care_button_{action['key']}_{current_time // 5}"  # Change every 5 seconds for animation
                    st.markdown(
                        f"""
                        <div class="stat-card care-button" style="
                            text-align: center;
                            cursor: pointer;
                            border: 2px solid {action['color']};
                            background: linear-gradient(135deg, {action['color']}20, rgba(0,0,0,0.1));
                            transition: all 0.3s ease;
                            min-height: 100px;
                            display: flex;
                            flex-direction: column;
                            justify-content: center;
                        " onclick="document.querySelector('button[key=\\'{action['key']}\\']').click();">
                            <div style="font-size: 2rem; margin-bottom: 0.3rem; animation: garden-grow 2s infinite ease-in-out;">{action['emoji']}</div>
                            <div style="color: {action['color']}; font-weight: 800; font-size: 0.8rem;">{action['name']}</div>
                            <div style="color: #94a3b8; font-size: 0.6rem;">{action['points']} care points</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Hidden Streamlit button for functionality
                    if st.button(f"{action['emoji']} {action['name']}", key=action['key'], help=f"Provide {action['name'].lower()} ({action['points']} care points)", type="secondary"):
                        garden_state.add_user_care(action['type'])
                        st.success(f"{action['emoji']} {action['name']} provided! Plants feel better!")
                        st.rerun()

        else:
            # Garden is healthy - show celebration
            if health > 80:
                st.markdown(
                    """
                    <div class="stat-card" style="text-align: center; background: linear-gradient(135deg, rgba(34,197,94,0.2), rgba(74,222,128,0.1)); border: 1px solid rgba(34,197,94,0.4);">
                        <div class="stat-value garden-healthy" style="color: #22c55e;">🌟</div>
                        <div class="stat-label">Garden is thriving thanks to community care!</div>
                        <div style="color: #4ade80; font-size: 0.7rem; margin-top: 0.5rem; animation: text-live-shake 2s infinite;">Keep up the amazing work!</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            elif health > 50:
                st.markdown(
                    """
                    <div class="stat-card" style="text-align: center; background: linear-gradient(135deg, rgba(74,222,128,0.1), rgba(34,197,94,0.1)); border: 1px solid rgba(74,222,128,0.3);">
                        <div class="stat-value" style="color: #4ade80;">🌱</div>
                        <div class="stat-label">Garden is growing well with your support!</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Garden info expander
        with st.expander("🔍 Garden Details", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Garden Status**")
                st.write(f"Health: {health}%")
                st.write(f"Stress Level: {garden_info['stress_level']}%")
                st.write(f"Needs Care: {'Yes' if needs_care else 'No'}")

            with col2:
                st.markdown("**Recent News Impact**")
                last_sentiment = garden_info.get("last_sentiment_type", "Unknown")
                if last_sentiment == "HOPEFUL":
                    st.write("📈 Recent news: Positive")
                elif last_sentiment == "CONCERNING":
                    st.write("📉 Recent news: Concerning")
                else:
                    st.write("📊 Recent news: Neutral")

                if garden_info.get("last_updated"):
                    update_time = datetime.fromisoformat(garden_info["last_updated"])
                    st.caption(f"Last update: {update_time.strftime('%H:%M UTC')}")

        # Auto-refresh indicator
        st.markdown(
            """
            <div style="text-align: center; margin-top: 1rem; opacity: 0.6;">
                <small style="color: #64748b;">🔄 Garden responds automatically to news sentiment • Updated every 15 minutes</small>
            </div>
            """,
            unsafe_allow_html=True
        )

    except Exception as e:
        st.error(f"❌ Hope Garden temporarily unavailable: {str(e)}")
        st.info("🌱 Garden will return shortly. Check back soon!")


def render_garden_debug_info() -> None:
    """Render debug information for the Hope Garden (dev mode only)."""
    if not st.session_state.get("debug_mode", False):
        return

    try:
        from game.garden_state import garden_state
        from game.sentiment_analyzer import sentiment_analyzer

        st.markdown("### 🔧 Garden Debug Info")

        # Current state
        state = garden_state.get_current_state()
        st.json(state)

        # Test sentiment analysis
        if st.button("🧪 Test Sentiment Analysis"):
            test_texts = [
                "3 new deaths reported from the outbreak",
                "Vaccine shows promising results in trials",
                "Scientists continue to monitor the situation"
            ]

            for i, text in enumerate(test_texts):
                result = sentiment_analyzer.analyze_news_chunk(text)
                st.write(f"**Test {i+1}:** {text}")
                st.write(f"Sentiment: {result['sentiment_type']} (score: {result['sentiment_score']})")
                st.write(f"Keywords: {result['keywords_found']}")
                st.write("---")

        # Manual garden updates
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🌱 Simulate Good News"):
                fake_sentiment = {
                    'overall_sentiment': 0.8,
                    'sentiment_type': 'HOPEFUL',
                    'confidence': 0.9,
                    'timestamp': datetime.utcnow().isoformat()
                }
                garden_state.update_from_sentiment(fake_sentiment)
                st.success("Applied good news to garden!")
                st.rerun()

        with col2:
            if st.button("😰 Simulate Bad News"):
                fake_sentiment = {
                    'overall_sentiment': -0.7,
                    'sentiment_type': 'CONCERNING',
                    'confidence': 0.8,
                    'timestamp': datetime.utcnow().isoformat()
                }
                garden_state.update_from_sentiment(fake_sentiment)
                st.warning("Applied bad news to garden!")
                st.rerun()

        with col3:
            if st.button("🔄 Reset Garden"):
                from alerts.persistent_kv import kv_set
                kv_set("hope_garden_state", None)
                st.success("Garden reset!")
                st.rerun()

    except Exception as e:
        st.error(f"Debug error: {e}")