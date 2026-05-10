"""Kepler.gl Inspired 3D Globe — Advanced Deck.gl implementation."""
from __future__ import annotations

import json
import pydeck as pdk
import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime

LIVE_FILE = Path("data/outbreak_live.json")

# Data Exports for compatibility
NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "passengers": 27, "crew": 0,  "cases": 2, "deaths": 1},
    {"country": "United Kingdom","GBR": "GBR", "passengers": 20, "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "passengers": 12, "crew": 5,  "cases": 1, "deaths": 1},
    {"country": "Argentina",     "code": "ARG", "passengers": 4,  "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "South Africa",  "code": "ZAF", "passengers": 0,  "crew": 16, "cases": 0, "deaths": 0},
]

# Kepler-style dense data points (simulating cluster density)
HOTSPOT_POINTS = [
    {"lat": -34.6037, "lon": -58.3816, "intensity": 10}, # Argentina
    {"lat": -34.6100, "lon": -58.3900, "intensity": 5},
    {"lat": -26.2041, "lon": 28.0473,  "intensity": 12}, # South Africa
    {"lat": -26.2100, "lon": 28.0500,  "intensity": 8},
    {"lat": 14.9315,  "lon": -23.5125, "intensity": 20}, # MV Hondius
    {"lat": 14.9350,  "lon": -23.5200, "intensity": 15},
]

# Historical Track for TripLayer/ArcLayer
ROUTE_TRACK = [
    {"path": [[-68.3, -54.8], [-36.5, -54.3], [-12.3, -37.1], [-5.7, -15.9], [-23.5, 14.9]], "color": [0, 245, 255]}
]

def render_map_panel() -> None:
    st.markdown(
        """
        <div style='border-left: 3px solid #ff4d4d; padding-left:15px; margin-bottom:1rem;'>
            <h2 style='margin:0; font-size:1rem; letter-spacing:0.1em; color:#ffffff;'>ORBITAL VECTOR INTELLIGENCE</h2>
            <p style='margin:0; font-size:0.6rem; color:#64748b; font-family:monospace;'>ENHANCED KEPLER_GL PROJECTION // 3D ALTITUDE MAPPING</p>
        </div>
        """, unsafe_allow_html=True
    )

    df_points = pd.DataFrame(HOTSPOT_POINTS)
    df_trips = pd.DataFrame(ROUTE_TRACK)

    # 1. HEXAGON LAYER (Iconic Kepler style for hotspots)
    hexagon_layer = pdk.Layer(
        "HexagonLayer",
        df_points,
        get_position=["lon", "lat"],
        radius=200000,
        elevation_scale=5000,
        elevation_range=[0, 100000],
        pickable=True,
        extruded=True,
        get_fill_color="[255, (1 - intensity/20) * 255, 0, 150]",
        coverage=1,
    )

    # 2. ARC LAYER (Cinematic flight-path feel)
    arc_layer = pdk.Layer(
        "ArcLayer",
        data=[{"from": [-68.3, -54.8], "to": [-23.5, 14.9]}],
        get_source_position="from",
        get_target_position="to",
        get_source_color=[255, 77, 77, 50],
        get_target_color=[0, 245, 255, 200],
        get_width=3,
    )

    # 3. TEXT LAYER (Tactical ID tags)
    text_layer = pdk.Layer(
        "TextLayer",
        data=[{"pos": [-23.5, 14.9], "name": "VESSEL_LOCK: HONDIUS"}],
        get_position="pos",
        get_text="name",
        get_color=[251, 191, 36],
        get_size=16,
        get_alignment_baseline="'bottom'",
    )

    view_state = pdk.ViewState(
        latitude=10, longitude=-20, zoom=1.5, pitch=50, bearing=0
    )

    # Kepler-inspired Dark Theme
    r = pdk.Deck(
        layers=[hexagon_layer, arc_layer, text_layer],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/dark-v10",
        tooltip={"text": "Vector Intensity: {elevationValue}"}
    )

    st.pydeck_chart(r, use_container_width=True)
    
    st.markdown(
        "<div style='text-align:right;'><span style='color:#475569; font-size:0.5rem; font-family:monospace;'>DATA_SOURCE: KEPLER_CORE // ORBITAL_ALTITUDE: 15,000KM</span></div>",
        unsafe_allow_html=True
    )
