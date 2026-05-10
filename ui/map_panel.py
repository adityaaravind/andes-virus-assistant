"""HantavirusMap High-Fidelity Clone — dark cinematic projection with layers and signals."""
from __future__ import annotations

import json
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from datetime import datetime

LIVE_FILE = Path("data/outbreak_live.json")

# Authentic HantavirusMap Data (Simulated for Clone)
MAP_HOTSPOTS = [
    {"lat": -34.6, "lon": -58.4, "cases": 3, "label": "Argentina", "type": "local"},
    {"lat": -26.2, "lon": 28.0,  "cases": 2, "label": "South Africa", "type": "local"},
    {"lat": 14.9,  "lon": -23.5, "cases": 5, "label": "MV Hondius", "type": "local"},
    {"lat": 40.4,  "lon": -3.7,  "cases": 2, "label": "Spain", "type": "imported"},
    {"lat": 51.5,  "lon": -0.1,  "cases": 1, "label": "UK", "type": "imported"},
    {"lat": 52.3,  "lon": 4.9,   "cases": 1, "label": "Netherlands", "type": "imported"},
]

NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "passengers": 27, "crew": 0,  "cases": 2, "deaths": 1},
    {"country": "United Kingdom","code": "GBR", "passengers": 20, "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "passengers": 12, "crew": 5,  "cases": 1, "deaths": 1},
    {"country": "Argentina",     "code": "ARG", "passengers": 4,  "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "South Africa",  "code": "ZAF", "passengers": 0,  "crew": 16, "cases": 0, "deaths": 0},
]

def _live_totals() -> dict:
    if LIVE_FILE.exists():
        try: return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {}

@st.cache_data(ttl=3600, show_spinner=False)
def build_replica_map() -> go.Figure:
    fig = go.Figure()

    # 1. THE DARK RED INFECTED BASE
    infected_codes = ["ARG", "ZAF", "ESP", "GBR", "NLD", "PHL", "CHL"]
    fig.add_trace(go.Choropleth(
        locations=infected_codes,
        z=[1] * len(infected_codes),
        colorscale=[[0, "#3a0a0a"], [1, "#3a0a0a"]],
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
            textfont=dict(family="monospace", color=color, size=9),
            hovertext=f"<b>{loc['label']}</b><br>Cases: {loc['cases']}",
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
        showcoastlines=True, coastlinecolor="#222222",
        showland=True, landcolor="#0a0a0a",
        showocean=True, oceancolor="#050505",
        showcountries=True, countrycolor="#1a1a1a",
        projection_type="natural earth",
        bgcolor="rgba(0,0,0,0)",
        resolution=50,
        lataxis=dict(range=[-65, 55]),
        lonaxis=dict(range=[-110, 80])
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=600,
        showlegend=False,
    )
    return fig

def render_map_panel() -> None:
    # ── CUSTOM CSS FOR CLONE UI ──
    st.markdown(
        """
        <style>
        .replica-top-bar {
            display: flex; gap: 20px; background: rgba(0,0,0,0.6); padding: 8px 15px; 
            border-radius: 6px; border: 1px solid #222; margin-bottom: 12px; 
            font-family: monospace; font-size: 0.7rem; color: #94a3b8;
        }
        .replica-sidebar {
            background: rgba(15, 23, 42, 0.9); border: 1px solid #333; 
            border-radius: 8px; padding: 15px; min-height: 520px;
        }
        .signal-scroll {
            height: 400px; overflow-y: auto; padding-right: 5px;
        }
        .signal-scroll::-webkit-scrollbar { width: 3px; }
        .signal-scroll::-webkit-scrollbar-thumb { background: #333; }
        </style>
        """, unsafe_allow_html=True
    )

    # ── 1. TOP METRIC BAR ──
    stats = _live_totals()
    st.markdown(
        f"""
        <div class="replica-top-bar">
            <div style="color:white;"><span style="color:#ff4d4d;">●</span> 12 countries</div>
            <div>582 signals</div>
            <div style="color:#fbbf24;">⚠ MV HONDIUS: {stats.get('confirmed_cases', 5)} cases</div>
            <div style="margin-left:auto;">Updated 3m ago</div>
        </div>
        """, unsafe_allow_html=True
    )

    col_left, col_map, col_right = st.columns([1, 4, 1.2])

    # ── 2. LEFT SIDEBAR (LAYERS) ──
    with col_left:
        st.markdown(
            """
            <div class="replica-sidebar">
                <p style="color:#64748b; font-size:0.55rem; font-weight:900; letter-spacing:0.1em; margin-bottom:12px;">LAYERS</p>
                <div style="margin-bottom:12px;">
                    <div style="color:#ff4d4d; font-size:0.75rem; font-weight:700;">📈 Now active</div>
                    <div style="color:#475569; font-size:0.6rem;">12 countries · 582 recent alerts</div>
                </div>
                <div style="margin-bottom:12px;">
                    <div style="color:white; font-size:0.7rem; font-weight:700;">● Local case</div>
                    <div style="color:#475569; font-size:0.6rem;">Confirmed in country</div>
                </div>
                <div style="margin-bottom:12px;">
                    <div style="color:#94a3b8; font-size:0.7rem; font-weight:700;">○ Imported</div>
                    <div style="color:#475569; font-size:0.6rem;">Infected person present</div>
                </div>
                <div style="margin-top:40px; border-top:1px solid #222; padding-top:10px;">
                    <p style="color:#64748b; font-size:0.55rem; font-weight:900;">TACTICAL ASSETS</p>
                    <div style="color:white; font-size:0.65rem; opacity:0.6; margin-top:5px;">Hospital Networks</div>
                    <div style="color:white; font-size:0.65rem; opacity:0.6; margin-top:5px;">Evacuation Track</div>
                </div>
            </div>
            """, unsafe_allow_html=True
        )

    # ── 3. CENTER MAP ──
    with col_map:
        fig = build_replica_map()
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="hantavirus_clone_map")

    # ── 4. RIGHT SIDEBAR (SIGNALS) ──
    with col_right:
        st.markdown(
            """
            <div class="replica-sidebar">
                <p style="color:#64748b; font-size:0.55rem; font-weight:900; letter-spacing:0.1em; margin-bottom:10px;">RECENT SIGNALS</p>
                <div style="background:#000; border:1px solid #222; border-radius:4px; padding:4px; margin-bottom:12px;">
                    <input type="text" placeholder="Filter Intel..." style="background:transparent; border:none; color:white; font-size:0.6rem; width:100%;">
                </div>
                <div class="signal-scroll">
            """, unsafe_allow_html=True
        )
        
        # Pull live headlines for the clone feed
        try:
            from ui.news_ticker import fetch_headlines
            headlines = fetch_headlines()
            for art in headlines[:12]:
                st.markdown(
                    f"""
                    <div style="border-bottom:1px solid #222; padding:8px 0;">
                        <div style="display:flex; justify-content:space-between; font-size:0.5rem; margin-bottom:3px;">
                            <span style="color:white; font-weight:900; opacity:0.8;">NEWS</span>
                            <span style="color:#475569;">{datetime.now().strftime('%H:%M')} UTC</span>
                        </div>
                        <p style="color:#cbd5e1; font-size:0.65rem; margin:0; line-height:1.2; font-family:monospace;">{art.get('title')[:65]}...</p>
                    </div>
                    """, unsafe_allow_html=True
                )
        except: pass
        
        st.markdown("</div></div>", unsafe_allow_html=True)
