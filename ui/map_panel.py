"""Terria-Lite 2D Intelligence Console — Professional Tactical Workbench UI."""
from __future__ import annotations

import json
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime

LIVE_FILE = Path("data/outbreak_live.json")

# Compatibility Data
NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "passengers": 27, "crew": 0,  "cases": 3, "deaths": 1},
    {"country": "United Kingdom","code": "GBR", "passengers": 20, "crew": 0,  "cases": 2, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "passengers": 12, "crew": 5,  "cases": 2, "deaths": 1},
    {"country": "Argentina",     "code": "ARG", "passengers": 4,  "crew": 0,  "cases": 4, "deaths": 1},
    {"country": "South Africa",  "code": "ZAF", "passengers": 0,  "crew": 16, "cases": 2, "deaths": 0},
]

def _get_live_state() -> dict:
    if LIVE_FILE.exists():
        try: return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {"confirmed_cases": 5, "ship_status": "Transit"}

def render_map_panel() -> None:
    state = _get_live_state()
    
    # ── CONSOLE HEADER ──
    st.markdown(
        f"""
        <div style='display:flex; justify-content:space-between; align-items:center; background:#0d1b2a; border:1px solid #1b2e45; padding:8px 20px; border-radius:8px 8px 0 0;'>
            <div style="display:flex; align-items:center; gap:15px;">
                <h2 style='margin:0; font-size:0.9rem; letter-spacing:0.12em; color:#ffffff;'>TERRIA_LITE // 2D TACTICAL CONSOLE</h2>
                <span style="color:#00f5ff; font-size:0.6rem; font-weight:900; background:rgba(0,245,255,0.1); padding:2px 8px; border-radius:4px; border:1px solid #00f5ff44;">PLANIMETRIC_MODE</span>
            </div>
            <div style="color:#94a3b8; font-family:monospace; font-size:0.65rem;">MISSION_TIME: {datetime.now().strftime('%H:%M:%S')} UTC</div>
        </div>
        """, unsafe_allow_html=True
    )

    # ── THE TERRIA-LITE 2D CORE ──
    # Uses Leaflet for high-performance 2D tactical mapping
    terria_2d_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            html, body {{ margin: 0; padding: 0; height: 100%; width: 100%; background: #000; font-family: 'Inter', sans-serif; color: white; overflow: hidden; }}
            #main-layout {{ display: flex; height: 100%; width: 100%; }}
            
            /* 1. DATA CATALOG (LEFT) */
            #catalog {{ width: 220px; background: #0a111a; border-right: 1px solid #1b2e45; display: flex; flex-direction: column; }}
            .panel-header {{ padding: 12px; font-size: 10px; font-weight: 900; color: #64748b; text-transform: uppercase; border-bottom: 1px solid #1b2e45; }}
            .catalog-item {{ padding: 10px 15px; font-size: 11px; color: #cbd5e1; border-bottom: 1px solid #111; cursor: pointer; display: flex; justify-content: space-between; }}
            .catalog-item:hover {{ background: #1b2e45; }}
            .badge-active {{ background: #00f5ff; width: 6px; height: 6px; border-radius: 50%; align-self: center; box-shadow: 0 0 5px #00f5ff; }}
            
            /* 2. MAP (CENTER) */
            #map-container {{ flex: 1; position: relative; }}
            #map {{ width: 100%; height: 100%; background: #050505; }}
            
            /* 3. FEATURE INFO (RIGHT) */
            #feature-info {{ width: 260px; background: rgba(10, 17, 26, 0.95); border-left: 1px solid #1b2e45; padding: 15px; display: none; overflow-y: auto; }}
            .info-title {{ color: #00f5ff; font-weight: 900; font-size: 13px; margin-bottom: 10px; }}
            .info-stat {{ background: rgba(255,255,255,0.03); padding: 8px; border-radius: 4px; margin-bottom: 10px; }}
            .stat-label {{ color: #64748b; font-size: 9px; }}
            .stat-val {{ color: #fff; font-size: 14px; font-weight: 900; }}
            
            /* 4. OVERLAYS */
            #timeline {{ position: absolute; bottom: 0; left: 0; right: 0; height: 40px; background: rgba(10, 17, 26, 0.85); border-top: 1px solid #1b2e45; padding: 5px 20px; display: flex; align-items: center; gap: 15px; z-index: 1000; }}
            
            /* Leaflet Customization */
            .leaflet-container {{ background: #050505 !important; }}
            .custom-ring {{
                border: 2px solid white;
                border-radius: 50%;
                background: rgba(255, 77, 77, 0.2);
                box-shadow: 0 0 10px rgba(255, 77, 77, 0.8);
            }}
            .vessel-pulse {{
                border: 2px solid #fbbf24;
                background: #fbbf24;
                border-radius: 50%;
                animation: pulse 1.5s infinite;
            }}
            @keyframes pulse {{ 0% {{ transform: scale(0.5); opacity: 1; }} 100% {{ transform: scale(2); opacity: 0; }} }}
        </style>
    </head>
    <body>
    <div id="main-layout">
        <div id="catalog">
            <div class="panel-header">Data Catalog</div>
            <div class="catalog-item"><span>Tactical Basemap</span><div class="badge-active"></div></div>
            <div class="catalog-item"><span>Outbreak Hotspots</span><div class="badge-active"></div></div>
            <div class="catalog-item"><span>MV Hondius Track</span><div class="badge-active"></div></div>
            <div class="catalog-item" style="opacity: 0.4;"><span>Global Air Traffic</span></div>
            <div class="catalog-item" style="opacity: 0.4;"><span>Port Clearances</span></div>
            
            <div class="panel-header" style="margin-top:auto;">Workbench</div>
            <div style="padding:12px; font-size:10px; color:#475569;">Precision 2D visualization active</div>
        </div>
        
        <div id="map-container">
            <div id="map"></div>
            <div id="timeline">
                <div style="color:#00f5ff; font-weight:900; font-size:9px;">CHRONOLOGY</div>
                <div style="flex:1; height:2px; background:#1b2e45; position:relative;">
                    <div style="position:absolute; left:75%; width:10px; height:10px; background:#00f5ff; border-radius:50%; top:-4px; box-shadow:0 0 8px #00f5ff;"></div>
                </div>
                <div style="color:#64748b; font-size:9px; font-family:monospace;">APR 01 — MAY 10 2026</div>
            </div>
        </div>
        
        <div id="feature-info">
            <div class="info-title" id="info-name">Tactical Feature</div>
            <div class="info-stat">
                <div class="stat-label">SIGNAL STRENGTH</div>
                <div class="stat-val" style="color:#22c55e;">98% / ENCRYPTED</div>
            </div>
            <div class="info-stat">
                <div class="stat-label">DETECTED CASES</div>
                <div class="stat-val" id="info-cases">--</div>
            </div>
            <div style="font-size:11px; line-height:1.4; color:#94a3b8; border-top:1px solid #222; padding-top:10px;" id="info-desc">
                Select a tactical marker for full OSINT situational awareness.
            </div>
        </div>
    </div>

    <script>
        const map = L.map('map', {{
            zoomControl: false,
            attributionControl: false
        }}).setView([10, -20], 2.5);

        // Dark Utilitarian Basemap
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            maxZoom: 19
        }}).addTo(map);

        const hotspots = [
            {{lat: -34.6, lon: -58.38, name: 'BETA_CLUSTER', cases: 4, desc: 'Argentina (Ushuaia) - Primary departure point. High alert in southern shipping lanes.'}},
            {{lat: -26.2, lon: 28.04,  name: 'ALPHA_CLUSTER', cases: 2, desc: 'South Africa (Johannesburg) - Critical crew evacuation signal. Screening active.'}},
            {{lat: 14.93, lon: -23.51, name: 'MV_HONDIUS_CORE', cases: 5, desc: 'Vessel under Cabo Verde military-hold. Quarantine Level 4 strictly enforced.'}}
        ];

        hotspots.forEach(h => {{
            const isShip = h.name.includes('HONDIUS');
            const markerClass = isShip ? 'vessel-pulse' : 'custom-ring';
            const icon = L.divIcon({{
                className: '',
                html: `<div class="${{markerClass}}" style="width:12px; height:12px;"></div>`,
                iconSize: [12, 12]
            }});

            const marker = L.marker([h.lat, h.lon], {{ icon: icon }}).addTo(map);
            marker.on('click', () => {{
                document.getElementById('feature-info').style.display = 'block';
                document.getElementById('info-name').innerText = h.name;
                document.getElementById('info-cases').innerText = h.cases + ' VERIFIED';
                document.getElementById('info-desc').innerText = h.desc;
            }});
        }});

        // Ship Track
        const path = [
            [-54.8, -68.3], [-54.3, -36.5], [-37.1, -12.3], [-15.9, -5.7], [14.93, -23.51]
        ];
        L.polyline(path, {{ color: '#00f5ff', weight: 1, dashArray: '5, 5', opacity: 0.5 }}).addTo(map);

    </script>
    </body>
    </html>
    """
    
    components.html(terria_2d_html, height=650)
    
    st.markdown(
        "<div style='background:#0d1b2a; border:1px solid #1b2e45; border-top:none; padding:8px 20px; border-radius:0 0 8px 8px; text-align:right;'>"
        "<p style='margin:0; font-size:0.5rem; color:#475569; font-family:monospace;'>TACTICAL_ENGINE: LEAFLET_GL // PROJECTION: 2D_PLANIMETRIC // SYNC: ACTIVE</p></div>",
        unsafe_allow_html=True
    )
