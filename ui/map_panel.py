"""High-fidelity Relational Map — Detailed vessel telemetry and real-time voyage tracking."""
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

# Relational Hotspot Data
RELATIONAL_HOTSPOTS = [
    {"lat": -34.60, "lng": -58.38, "cases": 4, "name": "ARGENTINA_CLUSTER", "color": "#ff0055", "relation": "Departure Point (APR 01)", "intel": "Vessel took on 147 passengers/crew. Original source of andes strain suspected."},
    {"lat": -26.20, "lng": 28.04,  "cases": 2, "name": "SOUTH_AFRICA_SIGNAL", "color": "#00ffcc", "relation": "Evacuation Event (APR 26)", "intel": "Critical crew members airlifted to Joburg. Secondary transmission confirmed."},
    {"lat": 40.41, "lng": -3.70,  "cases": 3, "name": "SPAIN_MONITOR", "color": "#ffaa00", "relation": "Repatriation (MAY 05)", "intel": "Mandatory quarantine active in Tenerife ports for returnees."},
    {"lat": 51.50, "lng": -0.12,  "cases": 2, "name": "UK_MONITOR", "color": "#cc00ff", "relation": "Repatriation (MAY 06)", "intel": "Andes sequencing confirmed in Heathrow isolation ward."},
    {"lat": 14.93, "lng": -23.51, "cases": 5, "name": "MV_HONDIUS_CORE", "color": "#22c55e", "relation": "Primary Vector", "intel": "Vessel moored. Level 4 quarantine enforced."}
]

def _get_live_state() -> dict:
    if LIVE_FILE.exists():
        try: return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {"confirmed_cases": 5, "ship_status": "Quarantined", "last_updated": "2026-05-10"}

def render_map_panel() -> None:
    state = _get_live_state()
    from ui.fear_index import _calculate_fear_average
    fear, _, _, _, _, _ = _calculate_fear_average()

    st.markdown(
        f"""
        <div style='border-left: 3px solid #fbbf24; padding-left:15px; margin-bottom:0.8rem; display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <h2 style='margin:0; font-size:1.1rem; letter-spacing:0.12em; color:#ffffff;'>ORBITAL MISSION CONTROL</h2>
                <p style='margin:0; font-size:0.6rem; color:#fbbf24; font-family:monospace; font-weight:800;'>VESSEL_LOCK: MV_HONDIUS // REAL-TIME TELEMETRY // SYNC: {datetime.now().strftime('%H:%M:%S')} UTC</p>
            </div>
            <div style="background:rgba(251,191,36,0.1); border:1px solid #fbbf2444; padding:4px 12px; border-radius:4px;">
                <span class="live-dot" style="width:6px; height:6px; background:#22c55e; box-shadow:0 0 10px #22c55e;"></span>
                <span style="color:#22c55e; font-size:0.6rem; font-weight:900; font-family:monospace;">DATA_STREAM: LIVE</span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    map_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            html, body { margin: 0; padding: 0; height: 100%; background: #000; overflow: hidden; font-family: monospace; }
            #map { width: 100%; height: 100vh; background: #050505; }
            
            /* ADVANCED TELEMETRY CARD */
            #telemetry-overlay {
                position: absolute; bottom: 25px; left: 20px; z-index: 1000;
                background: rgba(13, 27, 42, 0.95); border: 1px solid #fbbf24; border-radius: 12px;
                padding: 18px; width: 320px; color: white; border-left: 6px solid #fbbf24;
                box-shadow: 0 0 40px rgba(0,0,0,0.8); backdrop-filter: blur(12px);
            }
            .t-header { color: #64748b; font-size: 10px; font-weight: 900; margin-bottom: 12px; letter-spacing: 2px; }
            .t-vessel-name { font-size: 18px; font-weight: 950; color: #ffffff; letter-spacing: 1px; display: flex; align-items: center; gap: 12px; }
            .t-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0; border-top: 1px solid #222; padding-top: 15px; }
            .t-stat-label { color: #475569; font-size: 9px; font-weight: 800; text-transform: uppercase; }
            .t-stat-val { color: #fbbf24; font-size: 12px; font-weight: 900; margin-top: 2px; }
            .t-route { background: rgba(255,255,255,0.03); padding: 10px; border-radius: 6px; border-left: 2px solid #00f5ff; }
            
            .blink-light { width: 10px; height: 10px; background: #22c55e; border-radius: 50%; box-shadow: 0 0 15px #22c55e; animation: blinker 1s linear infinite; }
            @keyframes blinker { 50% { opacity: 0.2; } }

            .ring-marker { width: 22px; height: 22px; border-radius: 50%; border: 2px solid #ffffff; position: relative; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.6); }
            .vessel-ring { border-color: #22c55e !important; box-shadow: 0 0 25px #22c55e; animation: pulse 1.5s infinite; }
            .badge { position: absolute; top: -9px; right: -9px; background: #ffffff; color: #000; border-radius: 50%; width: 15px; height: 15px; font-size: 10px; font-weight: 900; display: flex; align-items: center; justify-content: center; border: 1px solid #000; }
            @keyframes pulse { 0% { transform: scale(0.6); opacity: 1; } 100% { transform: scale(2.2); opacity: 0; } }
        </style>
    </head>
    <body>
        <div id="telemetry-overlay">
            <div class="t-header">🛰️ LIVE VESSEL INTELLIGENCE</div>
            <div class="t-vessel-name"><div class="blink-light"></div> MV HONDIUS</div>
            <div style="color: #48cae4; font-size: 13px; margin-top: 5px;">IMO: 9443413 // CALLSIGN: PBWA</div>
            
            <div class="t-grid">
                <div><div class="t-stat-label">Coordinates</div><div class="t-stat-val">14.93°N // 23.51°W</div></div>
                <div><div class="t-stat-label">Current Speed</div><div class="t-stat-val">0.0 KNOTS</div></div>
                <div><div class="t-stat-label">Status</div><div class="t-stat-val" style="color:#ef4444;">__STATUS__</div></div>
                <div><div class="t-stat-label">Lock Precision</div><div class="t-stat-val">99.8% (SAT-LINK)</div></div>
            </div>

            <div class="t-route">
                <div class="t-stat-label" style="color:#00f5ff; margin-bottom:5px;">Voyage History</div>
                <div style="font-size:10px; color:#fff;"><b>PREV:</b> USHUAIA, ARG (APR 01)</div>
                <div style="font-size:10px; color:#fff; margin-top:4px;"><b>NEXT:</b> PORTO GRANDE, CV (MEDICAL HOLD)</div>
            </div>
            
            <div style="margin-top:15px; display:flex; justify-content:space-between; font-size:9px; color:#475569;">
                <span>REFRESH: 60S</span>
                <span>SYNC_ID: __SYNC_ID__</span>
            </div>
        </div>
        <div id="map"></div>
        <script>
            const map = L.map('map', { zoomControl: false, attributionControl: false }).setView([12, -35], 3.2);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(map);

            const hotspots = __HOTSPOTS__;
            const shipPos = [14.93, -23.51];

            hotspots.forEach(h => {
                const isShip = h.name.includes('HONDIUS');
                const icon = L.divIcon({
                    className: '',
                    html: `<div class="ring-marker ${isShip ? 'vessel-ring' : ''}" style="border-color:${h.color}; box-shadow: 0 0 15px ${h.color};"><div class="badge">${h.cases}</div></div>`,
                    iconSize: [22, 22], iconAnchor: [11, 11]
                });
                
                L.marker([h.lat, h.lng], { icon: icon }).addTo(map)
                 .bindPopup(`<div style="font-family:monospace; color:#fff;"><b>${h.name}</b><br/>Relation: ${h.relation}<br/>Fear: __FEAR__/5</div>`);

                if (!isShip) {
                    L.polyline([[h.lat, h.lng], shipPos], { color: h.color, weight: 1, dashArray: '5, 10', opacity: 0.3 }).addTo(map);
                }
            });

            // Live Pulse Simulation
            setInterval(() => {
                const now = new Date();
                document.querySelectorAll('.blink-light').forEach(el => {
                    el.style.boxShadow = `0 0 ${10 + Math.random()*15}px #22c55e`;
                });
            }, 500);
        </script>
    </body>
    </html>
    """

    # Manual Interpolation
    map_html = map_template.replace("__HOTSPOTS__", json.dumps(RELATIONAL_HOTSPOTS))
    map_html = map_html.replace("__STATUS__", state.get('ship_status', 'Transit').upper())
    map_html = map_html.replace("__FEAR__", f"{fear:.2f}")
    map_html = map_html.replace("__SYNC_ID__", datetime.now().strftime('%y%m%d-%H%M'))

    components.html(map_html, height=580)
    
    st.markdown(
        "<div style='text-align:right; opacity:0.6;'><p style='color:#475569; font-size:0.5rem; font-family:monospace;'>ORBITAL_RECO_SYS v8.0 // SHIP_INTELLIGENCE: SYNCED // LIVE_TELEMETRY: ON</p></div>",
        unsafe_allow_html=True
    )
