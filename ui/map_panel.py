"""Advanced Orbital Intelligence — 3D Globe with live effects and style selection."""
from __future__ import annotations

import json
import pydeck as pdk
import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime
import time

LIVE_FILE = Path("data/outbreak_live.json")

# Data Exports for compatibility
NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "passengers": 27, "crew": 0,  "cases": 2, "deaths": 1},
    {"country": "United Kingdom","code": "GBR", "passengers": 20, "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "passengers": 12, "crew": 5,  "cases": 1, "deaths": 1},
    {"country": "Argentina",     "code": "ARG", "passengers": 4,  "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "South Africa",  "code": "ZAF", "passengers": 0,  "crew": 16, "cases": 0, "deaths": 0},
]

# Hotspots with glow metadata
HOTSPOT_DATA = [
    {"lat": -34.60, "lon": -58.38, "cases": 3, "name": "ARGENTINA_CLUSTER", "color": [255, 0, 0]},
    {"lat": -26.20, "lon": 28.04,  "cases": 2, "name": "ZA_EVAC_SITE", "color": [255, 100, 0]},
    {"lat": 14.93,  "lon": -23.51, "cases": 5, "name": "MV_HONDIUS_CORE", "color": [251, 191, 36]},
    {"lat": 40.41,  "lon": -3.70,  "cases": 2, "name": "ESP_SIGNAL", "color": [255, 255, 255]},
]

MAP_STYLES = {
    "Tactical Ghost": "mapbox://styles/mapbox/dark-v10",
    "Satellite Intel": "mapbox://styles/mapbox/satellite-v9",
    "High-Contrast": "mapbox://styles/mapbox/navigation-night-v1",
    "Minimal Dark": "mapbox://styles/mapbox/light-v10" # Actually darker in deck.gl
}

def _live_totals() -> dict:
    if LIVE_FILE.exists():
        try: return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {}

def render_map_panel() -> None:
    # ── HEADER & STYLE SELECTOR ──
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown(
            """
            <div style='border-left: 3px solid #00f5ff; padding-left:15px;'>
                <h2 style='margin:0; font-size:1rem; letter-spacing:0.1em; color:#ffffff;'>ORBITAL INTELLIGENCE ARRAY</h2>
                <p style='margin:0; font-size:0.6rem; color:#00f5ff; font-family:monospace; font-weight:800;'>LIVE SATELLITE TRACKING // VESSEL LOCK: ACTIVE</p>
            </div>
            """, unsafe_allow_html=True
        )
    
    with col_t2:
        selected_style = st.selectbox("GLOBE STYLE", list(MAP_STYLES.keys()), label_visibility="collapsed")

    # ── DATA PREP ──
    df = pd.DataFrame(HOTSPOT_DATA)
    
    # Simulate a "Blinking" Ship by alternating visibility based on current second
    show_blink = (int(time.time()) % 2) == 0
    ship_data = df[df['name'] == "MV_HONDIUS_CORE"].copy()
    if not show_blink:
        ship_data['color'] = [[251, 191, 36, 50]] # Dimmer when "off"
    else:
        ship_data['color'] = [[251, 191, 36, 255]] # Bright when "on"

    # ── LAYERS ──
    
    # 1. HEATMAP GLOW (For the "Spots Glow" effect)
    glow_layer = pdk.Layer(
        "HeatmapLayer",
        df,
        get_position=["lon", "lat"],
        get_weight="cases",
        radius_pixels=60,
        intensity=0.8,
        threshold=0.05,
        color_range=[
            [0, 245, 255, 0],
            [0, 245, 255, 50],
            [255, 0, 0, 150]
        ]
    )

    # 2. 3D PILLARS (Altitude)
    column_layer = pdk.Layer(
        "ColumnLayer",
        df,
        get_position=["lon", "lat"],
        get_elevation="cases",
        elevation_scale=100000,
        radius=180000,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
    )

    # 3. BLINKING SHIP MARKER
    ship_layer = pdk.Layer(
        "ScatterplotLayer",
        ship_data,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius=300000,
        pickable=False,
    )

    # 4. TRANSIT ARCS
    arc_layer = pdk.Layer(
        "ArcLayer",
        data=[{"from": [-68.3, -54.8], "to": [-23.5, 14.9]}],
        get_source_position="from",
        get_target_position="to",
        get_source_color=[255, 0, 0, 100],
        get_target_color=[0, 245, 255, 255],
        get_width=4,
    )

    # ── VIEW & RENDER ──
    view_state = pdk.ViewState(
        latitude=10, longitude=-20, zoom=1.4, pitch=45, bearing=0
    )

    r = pdk.Deck(
        layers=[glow_layer, column_layer, arc_layer, ship_layer],
        initial_view_state=view_state,
        map_style=MAP_STYLES[selected_style],
        tooltip={
            "html": """
                <div style="background:#0d1b2a; border:1px solid #00f5ff; padding:10px; border-radius:5px; font-family:monospace;">
                    <b style="color:#00f5ff;">{name}</b><br/>
                    <span style="color:white;">DETECTED CASES:</span> <b style="color:#ff4d4d;">{cases}</b><br/>
                    <span style="color:#64748b; font-size:10px;">COORDINATES: {lat}, {lon}</span>
                </div>
            """,
            "style": {"backgroundColor": "transparent", "color": "white"}
        }
    )

    st.pydeck_chart(r, use_container_width=True)
    
    # ── LEGEND ──
    st.markdown(
        """
        <div style="display:flex; gap:20px; margin-top:10px; font-family:monospace; font-size:0.6rem;">
            <div style="color:#ff4d4d;">● LOCAL CLUSTER</div>
            <div style="color:#ffffff;">○ IMPORTED SIGNAL</div>
            <div style="color:#fbbf24;">▲ VESSEL LOCK (BLINKING)</div>
            <div style="margin-left:auto; color:#475569;">USE RIGHT-CLICK TO ROTATE // SCROLL TO ZOOM</div>
        </div>
        """, unsafe_allow_html=True
    )
