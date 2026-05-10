"""High-fidelity HantavirusMap replica — dark cinematic projection with layers and signals."""
from __future__ import annotations

import json
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from datetime import datetime

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

# Data from WHO/Dashboard baseline
MAP_HOTSPOTS = [
    {"lat": -34.6, "lon": -58.4, "cases": 3, "label": "Argentina", "type": "local"},
    {"lat": -26.2, "lon": 28.0,  "cases": 2, "label": "South Africa", "type": "local"},
    {"lat": 14.9,  "lon": -23.5, "cases": 5, "label": "MV Hondius", "type": "local"},
    {"lat": 40.4,  "lon": -3.7,  "cases": 2, "label": "Spain", "type": "imported"},
    {"lat": 51.5,  "lon": -0.1,  "cases": 1, "label": "UK", "type": "imported"},
    {"lat": 52.3,  "lon": 4.9,   "cases": 1, "label": "Netherlands", "type": "imported"},
]

def _live_totals() -> dict:
    if LIVE_FILE.exists():
        try: return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {}

@st.cache_data(ttl=3600, show_spinner=False)
def build_replica_map() -> go.Figure:
    fig = go.Figure()

    # 1. THE DARK RED BASE (Choropleth for infected zones)
    # Countries with cases get a dark red fill, others stay black
    infected_codes = ["ARG", "ZAF", "ESP", "GBR", "NLD", "PHL", "CHL"]
    fig.add_trace(go.Choropleth(
        locations=infected_codes,
        z=[1] * len(infected_codes),
        colorscale=[[0, "#4a1212"], [1, "#4a1212"]],
        showscale=False,
        marker=dict(line=dict(color="#1a1a1a", width=0.5)),
        hoverinfo="skip",
    ))

    # 2. GLOWING RING MARKERS (White rings with inner numbers)
    for loc in MAP_HOTSPOTS:
        color = "#ff4d4d" if loc["type"] == "local" else "#ffffff"
        # The Glow Ring
        fig.add_trace(go.Scattergeo(
            lat=[loc["lat"]], lon=[loc["lon"]],
            mode="markers",
            marker=dict(size=25, color=f"{color}", opacity=0.2, symbol="circle", line=dict(color=color, width=1)),
            hoverinfo="skip", showlegend=False
        ))
        # The Core Number
        fig.add_trace(go.Scattergeo(
            lat=[loc["lat"]], lon=[loc["lon"]],
            mode="markers+text",
            marker=dict(size=14, color="#1a1a1a", line=dict(color=color, width=2)),
            text=[str(loc["cases"])],
            textfont=dict(family="Inter, sans-serif", color=color, size=9),
            hovertext=f"<b>{loc['label']}</b><br>Cases: {loc['cases']}<br>Type: {loc['type'].upper()}",
            hoverinfo="text"
        ))

    # 3. SHIP ROUTE (Dotted red line)
    route_lat = [-54.8, -15.9, 14.9]
    route_lon = [-68.3, -5.7, -23.5]
    fig.add_trace(go.Scattergeo(
        lat=route_lat, lon=route_lon,
        mode="lines",
        line=dict(color="#ff4d4d", width=1, dash="dot"),
        hoverinfo="skip"
    ))

    fig.update_geos(
        showcoastlines=True, coastlinecolor="#333333",
        showland=True, landcolor="#111111",
        showocean=True, oceancolor="#0a0a0a",
        showcountries=True, countrycolor="#222222",
        projection_type="natural earth",
        bgcolor="rgba(0,0,0,0)",
        resolution=50,
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=600,
        showlegend=False,
    )
    return fig

def render_map_panel() -> None:
    # ── TOP METRIC SCROLLER (Replica style) ──
    stats = _live_totals()
    st.markdown(
        f"""
        <div style="display:flex; gap:25px; background:rgba(0,0,0,0.4); padding:10px 20px; border-radius:8px; border:1px solid #333; margin-bottom:15px; font-family:monospace; font-size:0.75rem;">
            <div style="color:#ffffff;"><span style="color:#ff4d4d; margin-right:8px;">●</span> 12 countries</div>
            <div style="color:#94a3b8;">582 signals</div>
            <div style="color:#fbbf24;">⚠ MV HONDIUS · 3 deaths · {stats.get('confirmed_cases', 5)} cases</div>
            <div style="color:#94a3b8; margin-left:auto;">Updated 7m ago</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_layers, col_map, col_signals = st.columns([1, 3.5, 1])

    with col_layers:
        st.markdown(
            """
            <div style="background:rgba(15, 23, 42, 0.8); border:1px solid #333; border-radius:10px; padding:15px; min-height:500px;">
                <p style="color:#94a3b8; font-size:0.6rem; font-weight:800; margin-bottom:15px;">LAYERS</p>
                <div style="margin-bottom:12px;">
                    <div style="color:#ff4d4d; font-size:0.75rem; font-weight:700;">📈 Now active</div>
                    <div style="color:#64748b; font-size:0.65rem;">12 countries · 582 recent alerts</div>
                </div>
                <div style="margin-bottom:12px;">
                    <div style="color:#ffffff; font-size:0.75rem; font-weight:700;">● Local case</div>
                    <div style="color:#64748b; font-size:0.65rem;">Outbreak confirmed in country</div>
                </div>
                <div style="margin-bottom:12px;">
                    <div style="color:#94a3b8; font-size:0.75rem; font-weight:700;">○ Imported</div>
                    <div style="color:#64748b; font-size:0.65rem;">Infected person present</div>
                </div>
                <div style="margin-top:40px; border-top:1px solid #333; pt-15px;">
                    <p style="color:#94a3b8; font-size:0.6rem; font-weight:800;">ADD CONTEXT</p>
                    <div style="color:#ffffff; font-size:0.7rem; opacity:0.6; margin-top:5px;">Endemic regions</div>
                    <div style="color:#ffffff; font-size:0.7rem; opacity:0.6; margin-top:5px;">Historical cases</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_map:
        fig = build_replica_map()
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="hanta_replica_map")

    with col_signals:
        st.markdown(
            """
            <div style="background:rgba(15, 23, 42, 0.8); border:1px solid #333; border-radius:10px; padding:15px; min-height:500px;">
                <p style="color:#94a3b8; font-size:0.6rem; font-weight:800; margin-bottom:10px;">RECENT SIGNALS</p>
                <div style="background:rgba(0,0,0,0.3); border:1px solid #222; padding:5px; border-radius:4px; margin-bottom:15px;">
                    <input type="text" placeholder="Search news..." style="background:transparent; border:none; color:white; font-size:0.7rem; width:100%;">
                </div>
            """
            , unsafe_allow_html=True
        )
        
        # Pull real headlines for the replica feed
        try:
            from ui.news_ticker import fetch_headlines
            headlines = fetch_headlines()
            for art in headlines[:5]:
                st.markdown(
                    f"""
                    <div style="border-bottom:1px solid #222; padding:10px 0;">
                        <div style="display:flex; justify-content:space-between; font-size:0.55rem; margin-bottom:4px;">
                            <span style="color:#ffffff; font-weight:900;">NEWS</span>
                            <span style="color:#64748b;">1h ago</span>
                        </div>
                        <p style="color:#cbd5e1; font-size:0.65rem; margin:0; line-height:1.2;">{art.get('title')[:60]}...</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        except: pass
        
        st.markdown("</div>", unsafe_allow_html=True)
