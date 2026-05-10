"""Cinematic Intelligence Map — dark-mode projection with glowing hotspots and side signals."""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

LIVE_FILE = Path("data/outbreak_live.json")

# Core Telemetry Data
MV_HONDIUS_LAT = 14.93
MV_HONDIUS_LON = -23.51

NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "cases": 2, "deaths": 1},
    {"country": "United Kingdom","code": "GBR", "cases": 1, "deaths": 0},
    {"country": "United States", "code": "USA", "cases": 0, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "cases": 1, "deaths": 1},
    {"country": "Germany",       "code": "DEU", "cases": 0, "deaths": 0},
    {"country": "Philippines",   "code": "PHL", "cases": 2, "deaths": 1},
    {"country": "South Africa",  "code": "ZAF", "cases": 0, "deaths": 0},
    {"country": "Argentina",     "code": "ARG", "cases": 1, "deaths": 0},
]

CASE_LOCATIONS = [
    {
        "lat": -26.2041, "lon": 28.0473,
        "city": "Johannesburg, ZA", "cases": 2, "deaths": 1,
        "label": "HOTSPOT: ZAF_ALPHA",
        "type": "evacuation-site",
    },
    {
        "lat": 14.93, "lon": -23.51,
        "city": "MV HONDIUS (Port Hold)", "cases": 5, "deaths": 2,
        "label": "PRIMARY VECTOR: HONDIUS",
        "type": "active-cluster",
    },
]

def _live_totals() -> dict:
    if LIVE_FILE.exists():
        try:
            return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {}

@st.cache_data(ttl=3600, show_spinner=False)
def build_cinematic_map() -> go.Figure:
    fig = go.Figure()

    # 1. THE GHOST MAP (Choropleth with glowing outlines)
    codes = [d["code"] for d in NATIONALITIES_DATA]
    cases = [d["cases"] for d in NATIONALITIES_DATA]
    
    fig.add_trace(go.Choropleth(
        locations=codes,
        z=cases,
        colorscale=[[0, "#08111e"], [1, "#0077b6"]],
        showscale=False,
        marker=dict(line=dict(color="#00b4d8", width=1)),
        hoverinfo="skip",
    ))

    # 2. GLOWING HOTSPOT RINGS (Pulsing Effect)
    for loc in CASE_LOCATIONS:
        # Subtle Outer Glow
        fig.add_trace(go.Scattergeo(
            lat=[loc["lat"]], lon=[loc["lon"]],
            mode="markers",
            marker=dict(size=40, color="rgba(0, 245, 255, 0.08)", symbol="circle", line=dict(color="#00f5ff", width=1)),
            hoverinfo="skip", showlegend=False
        ))
        # Bright Core
        fig.add_trace(go.Scattergeo(
            lat=[loc["lat"]], lon=[loc["lon"]],
            mode="markers",
            marker=dict(size=12, color="#00f5ff", symbol="circle", line=dict(color="#ffffff", width=2)),
            hovertext=f"<b>{loc['label']}</b><br>{loc['city']}<br>Cases: {loc['cases']}",
            hoverinfo="text",
            name=loc['label']
        ))

    # 3. FATALITY MARKERS (Red Glow)
    death_locs = [loc for loc in CASE_LOCATIONS if loc["deaths"] > 0]
    for loc in death_locs:
        fig.add_trace(go.Scattergeo(
            lat=[loc["lat"]], lon=[loc["lon"]],
            mode="markers",
            marker=dict(size=15, color="#ef4444", symbol="x", line=dict(color="#ffffff", width=1.5)),
            hovertext=f"<b>FATALITY SIGNAL</b><br>{loc['city']}<br>Deaths: {loc['deaths']}",
            hoverinfo="text",
            name="Fatality"
        ))

    # 4. SHIP CROSSHAIR
    fig.add_trace(go.Scattergeo(
        lat=[MV_HONDIUS_LAT], lon=[MV_HONDIUS_LON],
        mode="markers+text",
        marker=dict(size=22, color="#fbbf24", symbol="triangle-up", line=dict(color="#ffffff", width=2)),
        text=["<br>SAT-LOCK: HONDIUS"],
        textfont=dict(family="monospace", color="#fbbf24", size=9),
        hoverinfo="skip"
    ))

    fig.update_geos(
        showcoastlines=True, coastlinecolor="#1b2e45",
        showland=True, landcolor="#0d1b2a",
        showocean=True, oceancolor="#08111e",
        showcountries=True, countrycolor="#1b2e45",
        projection_type="equirectangular",
        bgcolor="rgba(0,0,0,0)",
        resolution=50,
        lataxis=dict(range=[-60, 40]),
        lonaxis=dict(range=[-100, 60])
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=550,
        showlegend=False,
    )
    return fig

def render_map_panel() -> None:
    live = _live_totals()
    total_confirmed = live.get("confirmed_cases", 5)
    
    st.markdown(
        "<div style='border-left: 3px solid #00b4d8; padding-left:15px; margin-bottom:1.5rem;'>"
        "<h2 style='margin:0; font-size:1.1rem !important; letter-spacing:0.1em; color:#ffffff;'>GLOBAL INTELLIGENCE PROJECTION</h2>"
        "<p style='margin:0; font-size:0.65rem; color:#48cae4; font-weight:700;'>REAL-TIME VECTOR TRACKING • SOURCE: WHO_DON_599</p>"
        "</div>",
        unsafe_allow_html=True
    )

    col_map, col_signals = st.columns([3, 1])

    with col_map:
        fig = build_cinematic_map()
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_signals:
        st.markdown(
            "<p style='color:#64748b; font-size:0.6rem; font-weight:900; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:10px;'>📡 LIVE SIGNALS</p>",
            unsafe_allow_html=True
        )
        
        # DYNAMIC SIGNALS: Fetch from live news headlines
        try:
            from ui.news_ticker import fetch_headlines
            headlines = fetch_headlines()
            # Pick 4 highly relevant signals
            display_signals = []
            for art in headlines[:20]:
                text = art.get("title", "").upper()
                source = art.get("source", "OSINT")
                if "WHO" in source: sig_id, color = "WHO_SIGNAL", "#fbbf24"
                elif "Hantavirus" in text or "Andes" in text: sig_id, color = "VECTOR_UPDATE", "#00f5ff"
                else: sig_id, color = "OSINT_SIGNAL", "#94a3b8"
                
                # Format a coordinates-style meta string from source/time
                meta = f"{source} // {datetime.now().strftime('%H:%M')} UTC"
                display_signals.append((sig_id, art.get("title")[:40] + "...", meta, color))
                if len(display_signals) >= 4: break
        except Exception:
            display_signals = [
                ("SIGNAL_ALPHA", "Connection Error", "Re-syncing...", "#ef4444"),
            ]
        
        for name, desc, meta, color in display_signals:
            st.markdown(
                f"""
                <div style="background:rgba(15, 23, 42, 0.6); border-left:2px solid {color}; padding: 8px 12px; border-radius: 4px; margin-bottom: 8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:{color}; font-size:0.55rem; font-weight:900; font-family:monospace;">{name}</span>
                        <span class="live-dot" style="width:4px; height:4px; background:{color}; box-shadow: 0 0 5px {color};"></span>
                    </div>
                    <div style="color:#ffffff; font-size:0.65rem; font-weight:700; margin-top:2px; line-height:1.2;">{desc}</div>
                    <div style="color:#475569; font-size:0.5rem; font-family:monospace; margin-top:2px;">{meta}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown(
            f"<div style='background:rgba(0,180,216,0.05); border:1px solid rgba(0,180,216,0.1); border-radius:6px; padding:10px; margin-top:20px;'>"
            f"<p style='color:#00b4d8; font-size:0.55rem; font-weight:800; margin:0;'>TOTAL DETECTED VECTORS</p>"
            f"<p style='color:#ffffff; font-size:1.4rem; font-weight:950; margin:0; line-height:1;'>{total_confirmed}</p>"
            f"</div>",
            unsafe_allow_html=True
        )

    # Simplified breakdown table
    with st.expander("📊 National Vector Breakdown"):
        rows_html = ""
        for d in sorted(NATIONALITIES_DATA, key=lambda x: x["cases"], reverse=True):
            if d["cases"] > 0:
                rows_html += f"<tr><td style='padding:5px; color:#f8fafc; font-size:0.75rem;'>{d['country']}</td><td style='padding:5px; color:#00f5ff; font-weight:800; text-align:right;'>{d['cases']}</td><td style='padding:5px; color:#ef4444; text-align:right;'>{d['deaths'] or '-'}</td></tr>"
        
        st.markdown(
            f"<table style='width:100%; font-family:monospace; border-collapse:collapse;'>"
            f"<tr style='border-bottom:1px solid #1b2e45;'><th style='text-align:left; color:#64748b; font-size:0.6rem;'>REGION</th><th style='text-align:right; color:#64748b; font-size:0.6rem;'>CASES</th><th style='text-align:right; color:#64748b; font-size:0.6rem;'>FATAL</th></tr>"
            f"{rows_html}</table>",
            unsafe_allow_html=True
        )
