"""3D Intelligence Globe — Deck.gl implementation with glowing pillars and arcs."""
from __future__ import annotations

import json
import pydeck as pdk
import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime

LIVE_FILE = Path("data/outbreak_live.json")

# Source: WHO DON599 (2026-DON599) — 147 aboard (88 pass, 59 crew, 23 nationalities)
NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "passengers": 27, "crew": 0,  "cases": 2, "deaths": 1},
    {"country": "United Kingdom","code": "GBR", "passengers": 20, "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "passengers": 12, "crew": 5,  "cases": 1, "deaths": 1},
    {"country": "Argentina",     "code": "ARG", "passengers": 4,  "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "South Africa",  "code": "ZAF", "passengers": 0,  "crew": 16, "cases": 0, "deaths": 0},
    {"country": "United States", "code": "USA", "passengers": 15, "crew": 0,  "cases": 0, "deaths": 0},
    {"country": "Germany",       "code": "DEU", "passengers": 10, "crew": 0,  "cases": 0, "deaths": 0},
    {"country": "Philippines",   "code": "PHL", "passengers": 0,  "crew": 38, "cases": 2, "deaths": 1},
]

# Ship & Case Data
MV_HONDIUS_POS = [14.9, -23.5]
MAP_HOTSPOTS = [
    {"lat": -34.6, "lon": -58.4, "cases": 3, "label": "Argentina", "color": [255, 77, 77]},
    {"lat": -26.2, "lon": 28.0,  "cases": 2, "label": "South Africa", "color": [255, 77, 77]},
    {"lat": 14.9,  "lon": -23.5, "cases": 5, "label": "MV Hondius", "color": [251, 191, 36]},
    {"lat": 40.4,  "lon": -3.7,  "cases": 2, "label": "Spain", "color": [255, 255, 255]},
    {"lat": 51.5,  "lon": -0.1,  "cases": 1, "label": "UK", "color": [255, 255, 255]},
    {"lat": 52.3,  "lon": 4.9,   "cases": 1, "label": "Netherlands", "color": [255, 255, 255]},
]

# Historical Route Arcs
HISTORICAL_ROUTE = [
    {"from": [-54.8, -68.3], "to": [-54.3, -36.5]},
    {"from": [-54.3, -36.5], "to": [-37.1, -12.3]},
    {"from": [-37.1, -12.3], "to": [-15.9, -5.7]},
    {"from": [-15.9, -5.7],  "to": [14.9, -23.5]},
]

def _live_totals() -> dict:
    if LIVE_FILE.exists():
        try: return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {}

def render_map_panel() -> None:
    # ── CUSTOM CSS ──
    st.markdown(
        """
        <style>
        .globe-header {
            display: flex; gap: 20px; background: rgba(0,0,0,0.6); padding: 10px 20px; 
            border-radius: 8px; border: 1px solid #222; margin-bottom: 15px; 
            font-family: monospace; font-size: 0.75rem; color: #94a3b8;
        }
        .sidebar-panel {
            background: rgba(15, 23, 42, 0.8); border: 1px solid #333; 
            border-radius: 10px; padding: 15px; min-height: 520px;
        }
        </style>
        """, unsafe_allow_html=True
    )

    stats = _live_totals()
    
    # 1. TOP METRIC BAR
    st.markdown(
        f"""
        <div class="globe-header">
            <div style="color:white;"><span style="color:#ff4d4d;">●</span> 12 countries detected</div>
            <div>582 signals tracked</div>
            <div style="color:#fbbf24;">⚠ MV HONDIUS · GLOBAL THREAT LEVEL: ELEVATED</div>
            <div style="margin-left:auto;">ORBITAL LOCK: ACTIVE</div>
        </div>
        """, unsafe_allow_html=True
    )

    col_layers, col_globe, col_signals = st.columns([1, 3.5, 1.2])

    with col_layers:
        st.markdown(
            """
            <div class="sidebar-panel">
                <p style="color:#64748b; font-size:0.6rem; font-weight:900; margin-bottom:15px;">TACTICAL LAYERS</p>
                <div style="margin-bottom:15px;"><div style="color:#ff4d4d; font-size:0.75rem; font-weight:700;">● LOCAL INFESTATION</div><div style="color:#475569; font-size:0.6rem;">Pillars indicate case density</div></div>
                <div style="margin-bottom:15px;"><div style="color:white; font-size:0.75rem; font-weight:700;">○ IMPORTED SIGNAL</div><div style="color:#475569; font-size:0.6rem;">Evacuation / Returnee events</div></div>
                <div style="margin-bottom:15px;"><div style="color:#fbbf24; font-size:0.75rem; font-weight:700;">▲ VESSEL TARGET</div><div style="color:#475569; font-size:0.6rem;">MV HONDIUS active position</div></div>
                <div style="margin-top:40px; border-top:1px solid #333; padding-top:15px;">
                    <p style="color:#64748b; font-size:0.6rem; font-weight:900;">3D CONTROLS</p>
                    <div style="color:#94a3b8; font-size:0.6rem;">R-Click: Pitch/Rotate</div>
                    <div style="color:#94a3b8; font-size:0.6rem;">Scroll: Zoom</div>
                </div>
            </div>
            """, unsafe_allow_html=True
        )

    with col_globe:
        # 3D Deck.gl Globe View
        df = pd.DataFrame(MAP_HOTSPOTS)
        
        # Transit Arcs
        arc_data = []
        for r in HISTORICAL_ROUTE:
            arc_data.append({
                "from": [r["from"][1], r["from"][0]],
                "to": [r["to"][1], r["to"][0]],
            })
        df_arcs = pd.DataFrame(arc_data)

        # Layer 1: The Case Pillars
        column_layer = pdk.Layer(
            "ColumnLayer",
            df,
            get_position=["lon", "lat"],
            get_elevation="cases",
            elevation_scale=100000,
            radius=150000,
            get_fill_color="color",
            pickable=True,
            auto_highlight=True,
        )

        # Layer 2: Transit Arcs
        arc_layer = pdk.Layer(
            "ArcLayer",
            df_arcs,
            get_source_position="from",
            get_target_position="to",
            get_source_color=[0, 245, 255, 80],
            get_target_color=[0, 245, 255, 200],
            get_width=2,
        )

        view_state = pdk.ViewState(
            latitude=10,
            longitude=-10,
            zoom=1,
            pitch=45,
            bearing=0
        )

        r = pdk.Deck(
            layers=[column_layer, arc_layer],
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/dark-v10", # Requires no key for basic dark
            tooltip={"text": "{label}\nCases: {cases}"}
        )
        
        st.pydeck_chart(r)

    with col_signals:
        st.markdown(
            """
            <div class="sidebar-panel">
                <p style="color:#fbbf24; font-size:0.6rem; font-weight:800; margin-bottom:10px;">VESSEL TELEMETRY</p>
                <div style="height:420px; overflow-y:auto; font-family:monospace; font-size:0.65rem;">
            """, unsafe_allow_html=True
        )
        
        try:
            from ui.news_ticker import fetch_headlines
            headlines = fetch_headlines()
            for art in headlines[:10]:
                st.markdown(
                    f"""
                    <div style="border-bottom:1px solid #222; padding:8px 0;">
                        <span style="color:#00f5ff; font-weight:900;">SIGNAL</span>
                        <p style="color:#cbd5e1; margin:2px 0;">{art.get('title')[:60]}...</p>
                    </div>
                    """, unsafe_allow_html=True
                )
        except: pass
        
        st.markdown("</div></div>", unsafe_allow_html=True)
