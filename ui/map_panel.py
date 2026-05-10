"""Streamlined Tactical Map — Compact layout with relational intelligence arcs."""
from __future__ import annotations

import json
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime

LIVE_FILE = Path("data/outbreak_live.json")

# Data Exports for compatibility
NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "cases": 3, "deaths": 1},
    {"country": "United Kingdom","code": "GBR", "cases": 2, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "cases": 2, "deaths": 1},
    {"country": "Argentina",     "code": "ARG", "cases": 4, "deaths": 1},
    {"country": "South Africa",  "code": "ZAF", "cases": 2, "deaths": 0},
]

# Relational Hotspot Data (Connected to Vessel)
# vibrant colors associated with regions
RELATIONAL_HOTSPOTS = [
    {
        "lat": -34.60, "lng": -58.38, "cases": 4, "name": "ARGENTINA_CLUSTER", 
        "color": "#ff0055", "relation": "Original Departure Point (APR 01)",
        "intel": "Vessel took on 147 passengers/crew. Patient Zero onset recorded 5 days post-departure."
    },
    {
        "lat": -26.20, "lng": 28.04,  "cases": 2, "name": "SOUTH_AFRICA_SIGNAL", 
        "color": "#00ffcc", "relation": "Emergency Evacuation (APR 26)",
        "intel": "Infected crew members airlifted to Johannesburg ICU. Secondary transmission confirmed in 2 medical staff."
    },
    {
        "lat": 40.41, "lng": -3.70,  "cases": 3, "name": "SPAIN_MONITOR", 
        "color": "#ffaa00", "relation": "Repatriation Link (MAY 05)",
        "intel": "Spanish nationals from MV Hondius returned via air bridge. Mandatory quarantine in Tenerife."
    },
    {
        "lat": 51.50, "lng": -0.12,  "cases": 2, "name": "UK_MONITOR", 
        "color": "#cc00ff", "relation": "Repatriation Link (MAY 06)",
        "intel": "UK passengers isolated upon arrival at Heathrow. Genomic sequencing matches Andes strain."
    },
    {
        "lat": 14.93, "lng": -23.51, "cases": 5, "name": "MV_HONDIUS_CORE", 
        "color": "#22c55e", "relation": "Current Primary Vector",
        "intel": "Vessel moored under Level 4 Quarantine. Sat-link telemetry stable."
    }
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
        <div style='border-left: 3px solid #22c55e; padding-left:15px; margin-bottom:0.8rem; display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <h2 style='margin:0; font-size:0.95rem; letter-spacing:0.1em; color:#ffffff;'>RELATIONAL VECTOR MAP</h2>
                <p style='margin:0; font-size:0.6rem; color:#22c55e; font-family:monospace; font-weight:800;'>VESSEL_RELATION: ACTIVE // LAYOUT: COMPACT // SYNC: {datetime.now().strftime('%H:%M')} UTC</p>
            </div>
            <div style="background:rgba(34,197,94,0.05); border:1px solid #22c55e22; padding:3px 8px; border-radius:4px;">
                <span style="color:#22c55e; font-size:0.55rem; font-weight:900; font-family:monospace;">STABLE LINK</span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    # COMPACT 2D TACTICAL TEMPLATE
    map_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            html, body { margin: 0; padding: 0; height: 100%; background: #000; overflow: hidden; font-family: monospace; }
            #map { width: 100%; height: 100vh; background: #050505; border-radius: 8px; }
            
            .ring-marker {
                width: 20px; height: 20px; border-radius: 50%; border: 2px solid #ffffff;
                position: relative; display: flex; align-items: center; justify-content: center;
                background: rgba(0,0,0,0.6); box-shadow: 0 0 15px rgba(255,255,255,0.3);
            }
            .vessel-ring { border-color: #22c55e !important; box-shadow: 0 0 20px #22c55e; animation: blinker 1s linear infinite; }
            
            .badge {
                position: absolute; top: -8px; right: -8px; background: #ffffff; color: #000;
                border-radius: 50%; width: 14px; height: 14px; font-size: 9px; font-weight: 900;
                display: flex; align-items: center; justify-content: center; border: 1px solid #000;
            }
            
            @keyframes blinker { 50% { opacity: 0.3; transform: scale(0.9); } }

            #telemetry-corner {
                position: absolute; bottom: 20px; left: 15px; z-index: 1000;
                background: rgba(15, 23, 42, 0.9); border: 1px solid #22c55e33; border-radius: 6px;
                padding: 10px; min-width: 180px; color: white; border-left: 3px solid #22c55e;
                pointer-events: none;
            }
            
            .custom-popup .leaflet-popup-content-wrapper {
                background: rgba(10, 17, 26, 0.95); color: #fff; border: 1px solid #333; border-radius: 4px;
            }
            .custom-popup .leaflet-popup-tip { background: #1b2e45; }
        </style>
    </head>
    <body>
        <div id="telemetry-corner">
            <div style="color:#64748b; font-size:8px; font-weight:900;">🛰️ VESSEL POSITION</div>
            <div style="font-size:11px; font-weight:900; color:#22c55e;">14.93°N // 23.51°W</div>
            <div style="color:#475569; font-size:9px; margin-top:2px;">STATUS: __STATUS__</div>
        </div>
        <div id="map"></div>
        <script>
            const map = L.map('map', { zoomControl: false, attributionControl: false }).setView([10, -25], 2.8);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(map);

            const hotspots = __HOTSPOTS__;
            const shipPos = [14.93, -23.51];

            hotspots.forEach(h => {
                const isShip = h.name.includes('HONDIUS');
                const icon = L.divIcon({
                    className: '',
                    html: `<div class="ring-marker ${isShip ? 'vessel-ring' : ''}" style="border-color:${h.color}; box-shadow: 0 0 15px ${h.color};"><div class="badge">${h.cases}</div></div>`,
                    iconSize: [20, 20], iconAnchor: [10, 10]
                });
                
                const marker = L.marker([h.lat, h.lng], { icon: icon }).addTo(map);
                
                // Detailed Intelligence Popup
                marker.bindPopup(`
                    <div style="font-family:monospace; min-width:200px;">
                        <b style="color:${h.color}; font-size:12px;">${h.name}</b><br/>
                        <div style="color:#94a3b8; font-size:10px; margin:5px 0;">${h.relation}</div>
                        <div style="height:1px; background:#333; margin:8px 0;"></div>
                        <div style="font-size:10px; color:#cbd5e1; line-height:1.3;">"${h.intel}"</div>
                        <div style="margin-top:10px; display:flex; justify-content:space-between;">
                            <span style="color:#64748b; font-size:9px;">CASES: <b style="color:#fff;">${h.cases}</b></span>
                            <span style="color:#64748b; font-size:9px;">FEAR: <b style="color:#fbbf24;">__FEAR__/5</b></span>
                        </div>
                    </div>
                `, { className: 'custom-popup' });

                // Connect to Vessel if not the vessel itself
                if (!isShip) {
                    L.polyline([[h.lat, h.lng], shipPos], {
                        color: h.color,
                        weight: 1,
                        dashArray: '4, 6',
                        opacity: 0.4
                    }).addTo(map);
                }
            });
        </script>
    </body>
    </html>
    """

    # Manual Interpolation
    map_html = map_template.replace("__HOTSPOTS__", json.dumps(RELATIONAL_HOTSPOTS))
    map_html = map_html.replace("__STATUS__", state.get('ship_status', 'Transit').upper())
    map_html = map_html.replace("__FEAR__", f"{fear:.2f}")

    # Use a smaller height for the map component
    components.html(map_html, height=520)
    
    st.markdown(
        "<div style='text-align:right; opacity:0.6;'><p style='color:#475569; font-size:0.5rem; font-family:monospace;'>ORBITAL_RECO_SYS v7.5 // RELATIONAL_INTELLIGENCE: ON // COMPACT_VIEW: ON</p></div>",
        unsafe_allow_html=True
    )
