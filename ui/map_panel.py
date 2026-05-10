"""High-fidelity Vessel Intelligence Map — focuses on MV Hondius tracking and local intelligence."""
from __future__ import annotations

import json
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta

LIVE_FILE = Path("data/outbreak_live.json")

# Source: WHO DON599 (2026-DON599) — 147 aboard (88 pass, 59 crew, 23 nationalities)
NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "passengers": 27, "crew": 0,  "cases": 2, "deaths": 1},
    {"country": "United Kingdom","code": "GBR", "passengers": 20, "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "United States", "code": "USA", "passengers": 15, "crew": 0,  "cases": 0, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "passengers": 12, "crew": 5,  "cases": 1, "deaths": 1},
    {"country": "Germany",       "code": "DEU", "passengers": 10, "crew": 0,  "cases": 0, "deaths": 0},
    {"country": "Philippines",   "code": "PHL", "passengers": 0,  "crew": 38, "cases": 2, "deaths": 1},
    {"country": "South Africa",  "code": "ZAF", "passengers": 0,  "crew": 16, "cases": 0, "deaths": 0},
    {"country": "Argentina",     "code": "ARG", "passengers": 4,  "crew": 0,  "cases": 1, "deaths": 0},
]

# Ship Intelligence Data
MV_HONDIUS_POS = {"lat": 14.93, "lon": -23.51}
SHIP_SITREP = [
    {"time": "20:45", "event": "Port hold extended by Cabo Verde authorities", "type": "authority"},
    {"time": "18:12", "event": "Medical status: 5 confirmed, 8 suspected (stable)", "type": "medical"},
    {"time": "14:20", "event": "Sat-link established with maritime security", "type": "comm"},
    {"time": "09:10", "event": "Supplies delivered via remote drone drop", "type": "logistics"},
    {"time": "07:30", "event": "Morning health check complete - no new onsets", "type": "medical"},
    {"time": "05:00", "event": "External monitoring vessel detected @ 5nm", "type": "security"},
]

# Country Data for Hover (Simplified OSINT)
COUNTRY_INTEL = {
    "ARG": "Ministry of Health monitors returnees from Ushuaia. Hanta-screening mandatory at southern borders.",
    "ZAF": "Case 3 remains in critical ICU condition. NICD confirms limited human-to-human risk in cluster.",
    "ESP": "Canary Island ports on high alert. Tenerife port authority denies entry request for medical hold.",
    "GBR": "UKHSA tracking passengers from secondary transport links. Media reporting focused on cruise security.",
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
        colorscale=[[0, "#0d1b2a"], [1, "#4a1212"]], # Darker, more contrast
        showscale=False,
        marker=dict(line=dict(color="#00b4d8", width=1)), # Glowing teal borders
        hoverinfo="location",
    ))

    # 2. ANIMATED GLOWING TRANSIT LINE
    lats = [p["lat"] for p in HISTORICAL_ROUTE]
    lons = [p["lon"] for p in HISTORICAL_ROUTE]
    
    # Glow Layer 1 (Wide/Faint)
    fig.add_trace(go.Scattergeo(
        lat=lats, lon=lons, mode="lines",
        line=dict(color="#00f5ff", width=8), opacity=0.15, hoverinfo="skip"
    ))
    # Glow Layer 2 (Tight/Bright)
    fig.add_trace(go.Scattergeo(
        lat=lats, lon=lons, mode="lines",
        line=dict(color="#00f5ff", width=2, dash="solid"),
        hoverinfo="skip"
    ))

    # 3. BLINKING SHIP MARKER
    fig.add_trace(go.Scattergeo(
        lat=[MV_HONDIUS_POS["lat"]], lon=[MV_HONDIUS_POS["lon"]],
        mode="markers",
        marker=dict(size=30, color="rgba(251, 191, 36, 0.15)", line=dict(color="#fbbf24", width=1.5)),
        hoverinfo="skip"
    ))
    fig.add_trace(go.Scattergeo(
        lat=[MV_HONDIUS_POS["lat"]], lon=[MV_HONDIUS_POS["lon"]],
        mode="markers+text",
        marker=dict(size=14, color="#fbbf24", symbol="triangle-up", line=dict(color="#ffffff", width=2)),
        text=["<br>VESSEL_SIG: HONDIUS"],
        textfont=dict(family="monospace", color="#fbbf24", size=10),
        hovertext="<b>MV HONDIUS</b><br>Moored: Cabo Verde<br>Signal Level: STABLE",
        hoverinfo="text"
    ))

    # 4. ACTIVE HOTSPOTS (High-Intensity Rings)
    hotspots = [
        {"lat": -26.2, "lon": 28.0, "label": "ALPHA_CLUSTER", "cases": 2},
        {"lat": -34.6, "lon": -58.4, "label": "BETA_CLUSTER", "cases": 3}
    ]
    for h in hotspots:
        fig.add_trace(go.Scattergeo(
            lat=[h["lat"]], lon=[h["lon"]], mode="markers",
            marker=dict(size=22, color="rgba(239, 68, 68, 0.1)", line=dict(color="#ff4d4d", width=2)),
            hoverinfo="skip"
        ))
        fig.add_trace(go.Scattergeo(
            lat=[h["lat"]], lon=[h["lon"]], mode="markers+text",
            marker=dict(size=12, color="#ef4444", line=dict(color="#ffffff", width=1.5)),
            text=[str(h["cases"])],
            textfont=dict(color="#ffffff", size=9),
            hovertext=f"HOTSPOT: {h['label']}", hoverinfo="text"
        ))

    fig.update_geos(
        showcoastlines=True, coastlinecolor="#243b55",
        showland=True, landcolor="#050505",
        showocean=True, oceancolor="#020408",
        projection_type="equirectangular",
        bgcolor="rgba(0,0,0,0)",
        lataxis=dict(range=[-70, 50]),
        lonaxis=dict(range=[-120, 80])
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=600, showlegend=False,
    )
    return fig

def render_map_panel() -> None:
    # ── GLOBAL STYLE OVERRIDES ──
    st.markdown(
        """
        <style>
        @keyframes marker-blink { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.2; transform: scale(0.9); } }
        .js-plotly-plot .scattergeo .point:nth-last-child(2) { animation: marker-blink 1.5s infinite ease-in-out !important; }
        
        .signal-scroll-container {
            height: 380px;
            overflow-y: auto;
            padding-right: 8px;
            margin-top: 10px;
        }
        .signal-scroll-container::-webkit-scrollbar { width: 4px; }
        .signal-scroll-container::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); }
        .signal-scroll-container::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }
        .signal-scroll-container::-webkit-scrollbar-thumb:hover { background: #444; }
        </style>
        """, 
        unsafe_allow_html=True
    )

    # ── TOP METRIC SCROLLER ──
    stats = _live_totals()
    st.markdown(
        f"""<div style="display:flex; gap:25px; background:rgba(0,0,0,0.4); padding:10px 20px; border-radius:8px; border:1px solid #333; margin-bottom:15px; font-family:monospace; font-size:0.75rem;"><div style="color:#ffffff;"><span style="color:#ff4d4d; margin-right:8px;">●</span> 12 countries</div><div style="color:#94a3b8;">582 signals tracked</div><div style="color:#fbbf24;">⚠ MV HONDIUS · Medical Hold · {stats.get('confirmed_cases', 5)} cases</div><div style="color:#94a3b8; margin-left:auto;">SIGNAL STRENGTH: 98%</div></div>""",
        unsafe_allow_html=True
    )

    col_layers, col_map, col_signals = st.columns([1, 3.5, 1.2])

    with col_layers:
        # LEFT: Robust Tactical Layers (Flattened to prevent HTML leak)
        st.markdown(
            f"""
<div style="background:rgba(15, 23, 42, 0.8); border:1px solid #333; border-radius:10px; padding:15px; min-height:500px;">
<p style="color:#94a3b8; font-size:0.6rem; font-weight:800; margin-bottom:15px;">TACTICAL LAYERS</p>
<div style="margin-bottom:15px;"><div style="color:#ff4d4d; font-size:0.75rem; font-weight:700;">📈 Now active</div><div style="color:#64748b; font-size:0.65rem;">12 countries · 582 alerts</div></div>
<div style="margin-bottom:15px;"><div style="color:#ffffff; font-size:0.75rem; font-weight:700;">● Local case</div><div style="color:#64748b; font-size:0.65rem;">Confirmed in country</div></div>
<div style="margin-bottom:15px;"><div style="color:#94a3b8; font-size:0.75rem; font-weight:700;">○ Imported</div><div style="color:#64748b; font-size:0.65rem;">Infected person present</div></div>
<div style="margin-top:40px; border-top:1px solid #333; padding-top:15px;">
<p style="color:#94a3b8; font-size:0.6rem; font-weight:800; margin-bottom:12px;">TACTICAL ASSETS</p>
<div style="display:flex; flex-direction:column; gap:8px;">
<div style="background:rgba(0,180,216,0.08); border:1px solid #00b4d844; color:#00b4d8; font-size:0.65rem; padding:8px; border-radius:4px; font-weight:800;">📡 SAT-LINK: LINKED</div>
<div style="background:rgba(255,255,255,0.03); border:1px solid #333; color:#94a3b8; font-size:0.65rem; padding:8px; border-radius:4px;">🏥 MEDICAL: ACTIVE</div>
<div style="background:rgba(255,255,255,0.03); border:1px solid #333; color:#94a3b8; font-size:0.65rem; padding:8px; border-radius:4px;">🚁 EVAC_ROUTE: READY</div>
</div></div></div>
            """.strip(),
            unsafe_allow_html=True
        )

    with col_map:
        fig = build_vessel_map()
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="vessel_cinematic_map")
        
        # OSINT Reports (Hover Detail Simulation)
        st.markdown("<p style='color:#475569; font-size:0.6rem; font-weight:900; margin:15px 0 5px;'>OSINT REGIONAL INTELLIGENCE REVIEWS</p>", unsafe_allow_html=True)
        rep_cols = st.columns(3)
        for i, (code, text) in enumerate(list(COUNTRY_INTEL.items())[:3]):
            with rep_cols[i]:
                st.markdown(f"<div style='background:rgba(15, 23, 42, 0.4); border:1px solid #1b2e45; padding:10px; border-radius:6px;'><span style='color:#00f5ff; font-size:0.6rem; font-weight:900; font-family:monospace;'>[DETECTED] {code}</span><p style='color:#94a3b8; font-size:0.65rem; margin-top:4px; line-height:1.2;'>{text}</p></div>", unsafe_allow_html=True)

    with col_signals:
        # RIGHT: Scrolled Vessel-Only Telemetry
        st.markdown(
            f"""
<div style="background:rgba(15, 23, 42, 0.8); border:1px solid #333; border-radius:10px; padding:15px; min-height:500px;">
<p style="color:#fbbf24; font-size:0.6rem; font-weight:800; margin-bottom:5px; display:flex; align-items:center; gap:5px;"><span class="live-dot" style="background:#fbbf24; width:5px; height:5px;"></span> VESSEL TELEMETRY</p>
<div class="signal-scroll-container">
            """.strip(), 
            unsafe_allow_html=True
        )
        
        for sitrep in SHIP_SITREP:
            color = "#fbbf24" if sitrep["type"] == "authority" else "#00f5ff" if sitrep["type"] == "medical" else "#94a3b8"
            st.markdown(
                f"""<div style="border-bottom:1px solid #222; padding:10px 0;"><div style="display:flex; justify-content:space-between; font-size:0.55rem; margin-bottom:4px;"><span style="color:{color}; font-weight:900; text-transform:uppercase;">{sitrep['type']}</span><span style="color:#475569;">{sitrep['time']} UTC</span></div><p style="color:#cbd5e1; font-size:0.68rem; margin:0; line-height:1.3; font-family:monospace;">{sitrep['event']}</p></div>""",
                unsafe_allow_html=True
            )
        
        st.markdown(
            f"""
</div><div style='margin-top:20px; padding:12px; background:rgba(251,191,36,0.06); border:1px solid rgba(251,191,36,0.25); border-radius:6px;'><p style='color:#fbbf24; font-size:0.55rem; font-weight:800; margin:0;'>CARRIER STATUS</p><p style='color:#ffffff; font-size:0.8rem; font-weight:950; margin-top:2px;'>QUARANTINE_L4_MOORED</p></div>
</div>
            """.strip(),
            unsafe_allow_html=True
        )
