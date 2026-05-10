"""High-fidelity Vessel Intelligence Map — focuses on MV Hondius tracking and local intelligence."""
from __future__ import annotations

import json
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta

LIVE_FILE = Path("data/outbreak_live.json")

# Ship Intelligence Data
MV_HONDIUS_POS = {"lat": 14.93, "lon": -23.51}
SHIP_SITREP = [
    {"time": "20:45", "event": "Port hold extended by Cabo Verde authorities", "type": "authority"},
    {"time": "18:12", "event": "Medical status: 5 confirmed, 8 suspected (stable)", "type": "medical"},
    {"time": "14:20", "event": "Sat-link established with maritime security", "type": "comm"},
    {"time": "09:10", "event": "Supplies delivered via remote drone drop", "type": "logistics"},
]

# Country Data for Hover (Simplified OSINT)
COUNTRY_INTEL = {
    "ARG": "Major News: Ministry of Health monitors Ushuaia returnees. Hanta-screening mandatory at borders.",
    "ZAF": "Major News: Johannesburg hospital reports Case 3 remains in ICU. Media focus on MV Hondius evacuation.",
    "ESP": "Major News: Canary Island ports on high alert. Tenerife residents voice concerns over port entry.",
    "GBR": "Major News: UKHSA monitors suspected cases from South Africa flight. Low local risk reported.",
}

# The transit route (historical track)
HISTORICAL_ROUTE = [
    {"lat": -54.8, "lon": -68.3}, # Ushuaia
    {"lat": -54.3, "lon": -36.5}, # South Georgia
    {"lat": -37.1, "lon": -12.3}, # Tristan
    {"lat": -15.9, "lon":  -5.7}, # St Helena
    {"lat":  14.9, "lon": -23.5}, # Current
]

def _live_totals() -> dict:
    if LIVE_FILE.exists():
        try: return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {}

@st.cache_data(ttl=3600, show_spinner=False)
def build_vessel_map() -> go.Figure:
    fig = go.Figure()

    # 1. THE DARK BASE (Deep Midnight)
    fig.add_trace(go.Choropleth(
        locations=["ARG", "ZAF", "ESP", "GBR", "NLD", "PHL", "CHL"],
        z=[1] * 7,
        colorscale=[[0, "#1a0505"], [1, "#3d0a0a"]], # Subtle red tint for affected
        showscale=False,
        marker=dict(line=dict(color="#222222", width=0.5)),
        hoverinfo="location+z",
    ))

    # 2. ANIMATED GLOWING TRANSIT LINE
    # We layer multiple lines for a "glow" effect
    lats = [p["lat"] for p in HISTORICAL_ROUTE]
    lons = [p["lon"] for p in HISTORICAL_ROUTE]
    
    # Outer Glow
    fig.add_trace(go.Scattergeo(
        lat=lats, lon=lons, mode="lines",
        line=dict(color="#00f5ff", width=4), opacity=0.1, hoverinfo="skip"
    ))
    # Core Line (Dotted)
    fig.add_trace(go.Scattergeo(
        lat=lats, lon=lons, mode="lines",
        line=dict(color="#00f5ff", width=1.5, dash="dot"),
        hoverinfo="skip"
    ))

    # 3. BLINKING SHIP MARKER (Targetting current pos)
    # Layer 1: Pulse ring
    fig.add_trace(go.Scattergeo(
        lat=[MV_HONDIUS_POS["lat"]], lon=[MV_HONDIUS_POS["lon"]],
        mode="markers",
        marker=dict(size=25, color="rgba(251, 191, 36, 0.2)", line=dict(color="#fbbf24", width=1)),
        hoverinfo="skip"
    ))
    # Layer 2: Core Marker
    fig.add_trace(go.Scattergeo(
        lat=[MV_HONDIUS_POS["lat"]], lon=[MV_HONDIUS_POS["lon"]],
        mode="markers+text",
        marker=dict(size=12, color="#fbbf24", symbol="triangle-up", line=dict(color="#ffffff", width=2)),
        text=["<br>SIGNAL: HONDIUS"],
        textfont=dict(family="monospace", color="#fbbf24", size=10),
        hovertext="<b>MV HONDIUS</b><br>Moored: Cabo Verde<br>Medical Criticality: HIGH",
        hoverinfo="text"
    ))

    # 4. ACTIVE HOTSPOTS (Minimalist Rings)
    hotspots = [
        {"lat": -26.2, "lon": 28.0, "label": "ZA_HOTSPOT"},
        {"lat": -34.6, "lon": -58.4, "label": "ARG_HOTSPOT"}
    ]
    for h in hotspots:
        fig.add_trace(go.Scattergeo(
            lat=[h["lat"]], lon=[h["lon"]], mode="markers",
            marker=dict(size=15, color="rgba(239, 68, 68, 0.4)", line=dict(color="#ef4444", width=1)),
            hovertext=f"HOTSPOT: {h['label']}", hoverinfo="text"
        ))

    fig.update_geos(
        showcoastlines=True, coastlinecolor="#333333",
        showland=True, landcolor="#0a0a0a",
        showocean=True, oceancolor="#050505",
        projection_type="natural earth",
        bgcolor="rgba(0,0,0,0)",
        lataxis=dict(range=[-65, 45]),
        lonaxis=dict(range=[-110, 70])
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=600, showlegend=False,
    )
    return fig

def render_map_panel() -> None:
    # ── BLINKING ANIMATION OVERRIDE ──
    st.markdown(
        """
        <style>
        @keyframes marker-blink { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.3; transform: scale(0.9); } }
        /* Target ship marker layers in Plotly */
        .js-plotly-plot .scattergeo .point:nth-last-child(2) { animation: marker-blink 1s infinite ease-in-out !important; }
        </style>
        """, 
        unsafe_allow_html=True
    )

    # ── TOP METRIC SCROLLER (Replica style) ──
    stats = _live_totals()
    st.markdown(
        f"""
        <div style="display:flex; gap:25px; background:rgba(0,0,0,0.4); padding:10px 20px; border-radius:8px; border:1px solid #333; margin-bottom:15px; font-family:monospace; font-size:0.75rem;">
            <div style="color:#ffffff;"><span style="color:#ff4d4d; margin-right:8px;">●</span> 12 countries</div>
            <div style="color:#94a3b8;">582 signals tracked</div>
            <div style="color:#fbbf24;">⚠ MV HONDIUS · Medical Hold · {stats.get('confirmed_cases', 5)} cases</div>
            <div style="color:#94a3b8; margin-left:auto;">SIGNAL STRENGTH: 98%</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_layers, col_map, col_signals = st.columns([1, 3.5, 1.2])

    with col_layers:
        st.markdown(
            """
            <div style="background:rgba(15, 23, 42, 0.8); border:1px solid #333; border-radius:10px; padding:15px; min-height:500px;">
                <p style="color:#94a3b8; font-size:0.6rem; font-weight:800; margin-bottom:15px;">LAYERS</p>
                <div style="margin-bottom:15px;">
                    <div style="color:#ff4d4d; font-size:0.75rem; font-weight:700;">📈 Now active</div>
                    <div style="color:#64748b; font-size:0.65rem;">12 countries · 582 alerts</div>
                </div>
                <div style="margin-bottom:15px;">
                    <div style="color:#ffffff; font-size:0.75rem; font-weight:700;">● Local case</div>
                    <div style="color:#64748b; font-size:0.65rem;">Confirmed in country</div>
                </div>
                <div style="margin-bottom:15px;">
                    <div style="color:#94a3b8; font-size:0.75rem; font-weight:700;">○ Imported</div>
                    <div style="color:#64748b; font-size:0.65rem;">Infected person present</div>
                </div>
                
                <div style="margin-top:40px; border-top:1px solid #333; padding-top:15px;">
                    <p style="color:#94a3b8; font-size:0.6rem; font-weight:800; margin-bottom:10px;">TACTICAL ASSETS</p>
                    <div style="display:flex; flex-direction:column; gap:8px;">
                        <button style="background:rgba(0,180,216,0.1); border:1px solid #00b4d8; color:#00b4d8; font-size:0.6rem; padding:4px; border-radius:4px; cursor:pointer; text-align:left;">📡 TOGGLE SAT-LINK</button>
                        <button style="background:rgba(255,255,255,0.02); border:1px solid #333; color:#94a3b8; font-size:0.6rem; padding:4px; border-radius:4px; cursor:pointer; text-align:left;">🏥 NEAREST ICUs</button>
                        <button style="background:rgba(255,255,255,0.02); border:1px solid #333; color:#94a3b8; font-size:0.6rem; padding:4px; border-radius:4px; cursor:pointer; text-align:left;">🚁 EVAC ROUTES</button>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_map:
        fig = build_vessel_map()
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="vessel_intel_map")
        
        # OSINT Country Reports (Simulation of Hover functionality)
        st.markdown(
            "<p style='color:#475569; font-size:0.6rem; font-weight:800; margin-top:10px;'>SELECTED REGION OSINT REPORT</p>", 
            unsafe_allow_html=True
        )
        report_cols = st.columns(3)
        for i, (code, text) in enumerate(list(COUNTRY_INTEL.items())[:3]):
            with report_cols[i]:
                st.markdown(f"<div style='background:rgba(0,0,0,0.2); border:1px solid #222; padding:8px; border-radius:4px;'><span style='color:#00b4d8; font-size:0.6rem; font-weight:900;'>{code}</span><p style='color:#94a3b8; font-size:0.65rem; margin:0; line-height:1.2;'>{text}</p></div>", unsafe_allow_html=True)

    with col_signals:
        st.markdown(
            """
            <div style="background:rgba(15, 23, 42, 0.8); border:1px solid #333; border-radius:10px; padding:15px; min-height:500px;">
                <p style="color:#fbbf24; font-size:0.6rem; font-weight:800; margin-bottom:15px; display:flex; align-items:center; gap:5px;">
                    <span class="live-dot" style="background:#fbbf24; width:5px; height:5px;"></span> VESSEL TELEMETRY
                </p>
            """
            , unsafe_allow_html=True
        )
        
        # VESSEL-ONLY SIGNALS
        for sitrep in SHIP_SITREP:
            color = "#fbbf24" if sitrep["type"] == "authority" else "#00f5ff" if sitrep["type"] == "medical" else "#94a3b8"
            st.markdown(
                f"""
                <div style="border-bottom:1px solid #222; padding:10px 0;">
                    <div style="display:flex; justify-content:space-between; font-size:0.55rem; margin-bottom:4px;">
                        <span style="color:{color}; font-weight:900; text-transform:uppercase;">{sitrep['type']}</span>
                        <span style="color:#475569;">{sitrep['time']} UTC</span>
                    </div>
                    <p style="color:#cbd5e1; font-size:0.68rem; margin:0; line-height:1.3; font-family:monospace;">{sitrep['event']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown(
            f"<div style='margin-top:20px; padding:10px; background:rgba(251,191,36,0.05); border:1px solid rgba(251,191,36,0.2); border-radius:6px;'>"
            f"<p style='color:#fbbf24; font-size:0.55rem; font-weight:800; margin:0;'>CARRIER STATUS</p>"
            f"<p style='color:#ffffff; font-size:0.8rem; font-weight:900; margin-top:2px;'>QUARANTINE_LEVEL: 4</p>"
            f"</div>",
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)
