"""3D Intelligence Globe — High-impact full-screen Deck.gl implementation."""
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
    {"country": "United Kingdom","code": "GBR", "passengers": 20, "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "passengers": 12, "crew": 5,  "cases": 1, "deaths": 1},
    {"country": "Argentina",     "code": "ARG", "passengers": 4,  "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "South Africa",  "code": "ZAF", "passengers": 0,  "crew": 16, "cases": 0, "deaths": 0},
    {"country": "United States", "code": "USA", "passengers": 15, "crew": 0,  "cases": 0, "deaths": 0},
    {"country": "Germany",       "code": "DEU", "passengers": 10, "crew": 0,  "cases": 0, "deaths": 0},
    {"country": "Philippines",   "code": "PHL", "passengers": 0,  "crew": 38, "cases": 2, "deaths": 1},
]

MAP_HOTSPOTS = [
    {"lat": -34.6, "lon": -58.4, "cases": 3, "label": "Argentina", "color": [255, 77, 77]},
    {"lat": -26.2, "lon": 28.0,  "cases": 2, "label": "South Africa", "color": [255, 77, 77]},
    {"lat": 14.9,  "lon": -23.5, "cases": 5, "label": "MV Hondius", "color": [251, 191, 36]},
    {"lat": 40.4,  "lon": -3.7,  "cases": 2, "label": "Spain", "color": [255, 255, 255]},
    {"lat": 51.5,  "lon": -0.1,  "cases": 1, "label": "UK", "color": [255, 255, 255]},
    {"lat": 52.3,  "lon": 4.9,   "cases": 1, "label": "Netherlands", "color": [255, 255, 255]},
]

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
    # ── HEADER & GLOBAL STATS ──
    stats = _live_totals()
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(0,0,0,0.4); padding:10px 20px; border-radius:8px; border:1px solid #222; margin-bottom:15px; font-family:monospace; font-size:0.75rem;">
            <div style="display:flex; gap:25px;">
                <div style="color:#ffffff;"><span style="color:#ff4d4d; margin-right:8px;">●</span> 12 countries detected</div>
                <div style="color:#94a3b8;">582 signals tracked</div>
                <div style="color:#fbbf24;">⚠ MV HONDIUS · GLOBAL THREAT LEVEL: ELEVATED</div>
            </div>
            <div style="color:#22c55e; font-weight:800; letter-spacing:0.1em;">ORBITAL LOCK: ACTIVE</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 3D Deck.gl Globe View (Full Width)
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
        radius=200000,
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
        get_width=3,
    )

    # Layer 3: GeoJson for Land (Fix for map loading issue)
    # Using a high-quality GeoJSON avoids Mapbox tile dependency
    geojson_url = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
    land_layer = pdk.Layer(
        "GeoJsonLayer",
        geojson_url,
        stroked=True,
        filled=True,
        extruded=False,
        get_fill_color=[10, 15, 20, 200],
        get_line_color=[0, 180, 216, 50],
        line_width_min_pixels=1,
    )

    view_state = pdk.ViewState(
        latitude=15,
        longitude=-15,
        zoom=1.2,
        pitch=45,
        bearing=0
    )

    r = pdk.Deck(
        layers=[land_layer, column_layer, arc_layer],
        initial_view_state=view_state,
        map_style=None, # Use the GeoJSON land layer instead of external tiles
        tooltip={"text": "{label}\nCases: {cases}"}
    )
    
    st.pydeck_chart(r, use_container_width=True)

    st.markdown(
        "<div style='text-align:center; padding:10px;'><p style='color:#475569; font-size:0.6rem; font-family:monospace;'>ORBITAL NAVIGATION: Right-Click to Pitch/Rotate · Scroll to Zoom</p></div>",
        unsafe_allow_html=True
    )
