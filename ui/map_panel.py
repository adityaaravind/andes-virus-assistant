"""Stable 2D Intelligence Map — High-fidelity tactical tracking with guaranteed visibility."""
from __future__ import annotations

import json
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime

LIVE_FILE = Path("data/outbreak_live.json")

# Core Data Exports for compatibility
NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "cases": 3, "deaths": 1},
    {"country": "United Kingdom","code": "GBR", "cases": 2, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "cases": 2, "deaths": 1},
    {"country": "Argentina",     "code": "ARG", "cases": 4, "deaths": 1},
    {"country": "South Africa",  "code": "ZAF", "cases": 2, "deaths": 0},
]

# Tactical Hotspot Data
HOTSPOT_DATA = [
    {"lat": 40.41, "lng": -3.70,  "cases": 3, "name": "SPAIN_LOCAL", "color": "#fbbf24", "type": "local"},
    {"lat": 51.50, "lng": -0.12,  "cases": 2, "name": "UK_LOCAL", "color": "#fbbf24", "type": "local"},
    {"lat": 52.36, "lng": 4.89,   "cases": 2, "name": "NETHERLANDS_LOCAL", "color": "#fbbf24", "type": "local"},
    {"lat": 14.93, "lng": -23.51, "cases": 5, "name": "MV_HONDIUS_CORE", "color": "#22c55e", "type": "vessel"},
    {"lat": -34.6, "lng": -58.38, "cases": 4, "name": "ARGENTINA_CORE", "color": "#fbbf24", "type": "local"},
    {"lat": -26.2, "lng": 28.04,  "cases": 2, "name": "ZA_CLUSTER", "color": "#fbbf24", "type": "local"},
]

def _get_live_state() -> dict:
    if LIVE_FILE.exists():
        try: return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {"confirmed_cases": 5, "ship_status": "Transit"}

def render_map_panel() -> None:
    state = _get_live_state()
    from ui.fear_index import _calculate_fear_average
    fear, _, _, _, _, _ = _calculate_fear_average()

    st.markdown(
        f"""
        <div style='border-left: 3px solid #22c55e; padding-left:15px; margin-bottom:1rem; display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <h2 style='margin:0; font-size:1.1rem; letter-spacing:0.12em; color:#ffffff;'>TACTICAL INTELLIGENCE PROJECTION</h2>
                <p style='margin:0; font-size:0.65rem; color:#22c55e; font-family:monospace; font-weight:800;'>SENSOR_LOCK: ACQUIRED // MODE: 2D_PLANIMETRIC // SYNC: {datetime.now().strftime('%H:%M:%S')} UTC</p>
            </div>
            <div style="background:rgba(34,197,94,0.1); border:1px solid #22c55e44; padding:4px 10px; border-radius:4px;">
                <span class="live-dot" style="width:6px; height:6px; background:#22c55e; box-shadow:0 0 10px #22c55e;"></span>
                <span style="color:#22c55e; font-size:0.6rem; font-weight:900; font-family:monospace;">SIGNAL: STABLE</span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            html, body {{ margin: 0; padding: 0; height: 100%; background: #000; overflow: hidden; font-family: monospace; }}
            #map {{ width: 100%; height: 100vh; background: #050505; }}
            
            /* High-Intensity Markers */
            .ring-marker {{
                width: 24px; height: 24px; border-radius: 50%; border: 2px solid #ffffff;
                position: relative; display: flex; align-items: center; justify-content: center;
                background: rgba(0,0,0,0.4);
            }}
            .local-ring {{ box-shadow: 0 0 20px #fbbf24, inset 0 0 10px #fbbf24; }}
            .vessel-ring {{ border-color: #22c55e !important; box-shadow: 0 0 25px #22c55e, inset 0 0 15px #22c55e; animation: blinker 1s linear infinite; }}
            
            .badge {{
                position: absolute; top: -10px; right: -10px; background: #ffffff; color: #000;
                border-radius: 50%; width: 16px; height: 16px; font-size: 11px; font-weight: 900;
                display: flex; align-items: center; justify-content: center; border: 1px solid #000;
            }}
            
            @keyframes blinker {{ 50% {{ opacity: 0.3; transform: scale(0.9); }} }}

            /* Telemetry Box */
            #telemetry {{
                position: absolute; bottom: 30px; left: 20px; z-index: 1000;
                background: rgba(15, 23, 42, 0.95); border: 1px solid #22c55e; border-radius: 10px;
                padding: 15px; min-width: 220px; color: white; border-left: 5px solid #22c55e;
            }}
        </style>
    </head>
    <body>
        <div id="telemetry">
            <div style="color:#64748b; font-size:10px; font-weight:900;">🛰️ VESSEL TELEMETRY</div>
            <div style="font-size:16px; font-weight:900; margin:5px 0;">MV HONDIUS LOCK</div>
            <div style="color:#48cae4; font-size:12px;">LAT: 14.9316° N / LON: 23.5125° W</div>
            <div style="height:1px; background:rgba(255,255,255,0.1); margin:10px 0;"></div>
            <div style="color:#22c55e; font-size:11px; font-weight:900;">STATUS: {state.get('ship_status', 'Transit').upper()}</div>
        </div>
        <div id="map"></div>
        <script>
            const map = L.map('map', {{ zoomControl: false, attributionControl: false }}).setView([15, -20], 3);
            
            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{ maxZoom: 19 }}).addTo(map);

            const hotspots = {json.dumps(HOTSPOT_DATA)};
            hotspots.forEach(h => {{
                const ringClass = h.type === 'vessel' ? 'vessel-ring' : 'local-ring';
                const icon = L.divIcon({{
                    className: '',
                    html: `<div class="ring-marker ${{ringClass}}"><div class="badge">${{h.cases}}</div></div>`,
                    iconSize: [24, 24], iconAnchor: [12, 12]
                }});
                
                L.marker([h.lat, h.lng], {{ icon: icon }}).addTo(map)
                 .bindPopup(`<b style="color:${{h.color}};">\${h.name}</b><br/>CASES: \${h.cases}<br/>FEAR_INDEX: {fear:.2f}/5`, {{ className: 'custom-popup' }});
            }});

            // Ship Trajectory
            const path = [[-54.8, -68.3], [-54.3, -36.5], [-37.1, -12.3], [-15.9, -5.7], [14.93, -23.51]];
            L.polyline(path, {{ color: '#00f5ff', weight: 2, dashArray: '8, 8', opacity: 0.6 }}).addTo(map);
        </script>
    </body>
    </html>
    """
    
    components.html(map_html, height=750)
    
    st.markdown(
        "<div style='text-align:right; opacity:0.6;'><p style='color:#475569; font-size:0.5rem; font-family:monospace;'>ENGINE: LEAFLET_TACTICAL // VISIBILITY: 100% // SYNC: LOCKED</p></div>",
        unsafe_allow_html=True
    )
