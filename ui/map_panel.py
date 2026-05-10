"""High-fidelity 3D Intelligence Globe — Stable Globe.gl implementation with multi-mode telemetry."""
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

# Hotspots mapped to the visual style of the screenshot
HOTSPOT_DATA = [
    {"lat": 40.41, "lng": -3.70,  "cases": 3, "name": "SPAIN_LOCAL", "type": "local"},
    {"lat": 51.50, "lng": -0.12,  "cases": 2, "name": "UK_LOCAL", "type": "local"},
    {"lat": 52.52, "lng": 13.40,  "cases": 2, "name": "GERMANY_LOCAL", "type": "local"},
    {"lat": 52.36, "lng": 4.89,   "cases": 2, "name": "NETHERLANDS_LOCAL", "type": "local"},
    {"lat": 60.47, "lng": 8.46,   "cases": 2, "name": "NORWAY_LOCAL", "type": "local"},
    {"lat": 14.93, "lng": -23.51, "cases": 5, "name": "MV_HONDIUS_CORE", "type": "vessel"},
    {"lat": -34.6, "lng": -58.38, "cases": 4, "name": "ARGENTINA_CORE", "type": "local"},
    {"lat": -26.2, "lng": 28.04,  "cases": 2, "name": "ZA_CLUSTER", "type": "local"},
]

GLOBE_MODES = {
    "Daylight Intelligence": {
        "img": "//unpkg.com/three-globe/example/img/earth-blue-marble.jpg",
        "bg": "#000",
        "atmo": "#ffffff"
    },
    "Night Ops (High-Res)": {
        "img": "//unpkg.com/three-globe/example/img/earth-night.jpg",
        "bg": "#000",
        "atmo": "#00f5ff"
    }
}

def _get_live_state() -> dict:
    if LIVE_FILE.exists():
        try: return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {"confirmed_cases": 5, "ship_status": "Transit"}

def render_map_panel() -> None:
    state = _get_live_state()
    from ui.fear_index import _calculate_fear_average
    fear, _, _, _, _, _ = _calculate_fear_average()

    # ── HEADER & MODE SELECTOR ──
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(
            f"""
            <div style='border-left: 3px solid #22c55e; padding-left:15px; margin-bottom:1rem;'>
                <h2 style='margin:0; font-size:1.1rem; letter-spacing:0.12em; color:#ffffff; text-shadow: 0 0 10px rgba(34,197,94,0.3);'>ORBITAL INTELLIGENCE ARRAY</h2>
                <p style='margin:0; font-size:0.65rem; color:#22c55e; font-family:monospace; font-weight:800;'>SENSOR_LOCK: ACTIVE // LIVE_SYNC: {datetime.now().strftime('%H:%M:%S')} UTC</p>
            </div>
            """, unsafe_allow_html=True
        )
    
    with col_h2:
        selected_mode = st.selectbox("PROJECTION", list(GLOBE_MODES.keys()), label_visibility="collapsed")

    template = GLOBE_MODES[selected_mode]

    # DEFINITIVE TEMPLATE ISOLATION (No f-string)
    globe_template = """
    <head>
      <style> 
        body { margin: 0; background: #000; overflow: hidden; font-family: 'Inter', sans-serif; } 
        
        /* 1. PIXEL-PERFECT MARKERS */
        .ring-marker {
            width: 20px; height: 20px; border-radius: 50%; border: 2px solid #ffffff;
            position: relative; box-shadow: 0 0 15px rgba(255, 77, 77, 0.8);
            display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.5);
        }
        .number-badge {
            position: absolute; top: -8px; right: -8px; background: #ffffff; color: #000;
            border-radius: 50%; width: 14px; height: 14px; font-size: 10px; font-weight: 900;
            display: flex; align-items: center; justify-content: center; box-shadow: 0 0 5px rgba(0,0,0,0.5);
        }
        .vessel-triangle {
            width: 0; height: 0; border-left: 10px solid transparent; border-right: 10px solid transparent;
            border-bottom: 18px solid #22c55e; filter: drop-shadow(0 0 10px #22c55e);
            animation: blinker 1s linear infinite;
        }
        @keyframes blinker { 50% { opacity: 0.2; transform: scale(0.8); } }

        /* TELEMETRY OVERLAY */
        #telemetry-box {
            position: absolute; bottom: 20px; left: 20px;
            background: rgba(15, 23, 42, 0.95); border: 1px solid #22c55e; border-radius: 10px;
            padding: 15px; font-family: monospace; z-index: 100; min-width: 220px;
        }
        .t-header { color: #64748b; font-size: 10px; font-weight: 900; margin-bottom: 5px; }
        .t-vessel { color: #ffffff; font-size: 15px; font-weight: 900; margin-bottom: 5px; }
      </style>
      <script src="//unpkg.com/three"></script>
      <script src="//unpkg.com/globe.gl"></script>
    </head>
    <body>
      <div id="telemetry-box">
          <div class="t-header">🛰️ VESSEL TELEMETRY</div>
          <div class="t-vessel">MV HONDIUS LOCK</div>
          <div style="color:#48cae4; font-size:12px;">LAT: 14.9316° N</div>
          <div style="color:#48cae4; font-size:12px;">LON: 23.5125° W</div>
          <div style="height:1px; background:rgba(255,255,255,0.1); margin:10px 0;"></div>
          <div style="color:#22c55e; font-size:11px; font-weight:900;">STATUS: __STATUS__</div>
      </div>
      
      <div id="globeViz"></div>
      <script>
        const hotspots = __HOTSPOTS__;
        const world = Globe()
          (document.getElementById('globeViz'))
          .globeImageUrl('__IMG__')
          .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
          .showAtmosphere(true)
          .atmosphereColor('__ATMO__')
          .atmosphereDaylightAlpha(0.2)

          // 1. COUNTRY GLOWS (Affected Zones)
          .polygonsData(__GEOJSON__.features)
          .polygonCapColor(d => {
             const code = d.properties.ISO_A3;
             const active = ["ESP", "GBR", "DEU", "NLD", "NOR", "ITA", "ARG", "ZAF", "PHL", "CHL"];
             return active.includes(code) ? 'rgba(74, 18, 18, 0.7)' : 'rgba(0, 0, 0, 0)';
          })
          .polygonStrokeColor(() => 'rgba(255, 255, 255, 0.1)')

          // 2. ROBUST HTML INDICATORS
          .htmlElementsData(hotspots)
          .htmlElement(d => {
            const el = document.createElement('div');
            if (d.type === 'vessel') {
                el.className = 'vessel-triangle';
            } else {
                el.innerHTML = `
                  <div class="ring-marker">
                      <div class="number-badge">${d.cases}</div>
                  </div>
                `;
            }
            return el;
          })

          // 3. HOVER INTELLIGENCE
          .htmlElementTooltip(d => `
            <div style="background: rgba(13, 27, 42, 0.98); border: 1px solid #ffffff33; padding: 12px; border-radius: 8px; font-family: monospace; min-width: 240px; box-shadow: 0 0 25px rgba(0,0,0,0.8);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <b style="color:#ffffff; font-size:12px;">${d.name}</b>
                    <span style="color:#22c55e; font-size:10px; font-weight:800;">LIVE_LOCK</span>
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom:10px;">
                    <div style="background:rgba(255,255,255,0.03); padding:5px; border-radius:4px;">
                        <div style="color:#64748b; font-size:8px;">CASES</div>
                        <div style="color:#ffffff; font-size:14px; font-weight:900;">${d.cases}</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.03); padding:5px; border-radius:4px;">
                        <div style="color:#64748b; font-size:8px;">FEAR_INDEX</div>
                        <div style="color:#fbbf24; font-size:14px; font-weight:900;">__FEAR__/5</div>
                    </div>
                </div>
                <div style="border-top:1px solid rgba(255,255,255,0.1); padding-top:8px;">
                    <div style="color:#00f5ff; font-size:9px; font-weight:900; margin-bottom:2px;">OSINT: MONITORING ACTIVE</div>
                </div>
            </div>
          `);

        world.controls().autoRotate = true;
        world.controls().autoRotateSpeed = 0.5;
        world.pointOfView({ lat: 20, lng: -20, altitude: 2.2 }, 0);
      </script>
    </body>
    """
    
    # Robust GeoJSON Fetch
    import requests
    try:
        geojson = requests.get("https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json").json()
    except: geojson = {"features": []}

    # Manual interpolation
    globe_html = globe_template.replace("__HOTSPOTS__", json.dumps(HOTSPOT_DATA))
    globe_html = globe_html.replace("__GEOJSON__", json.dumps(geojson))
    globe_html = globe_html.replace("__STATUS__", state.get('ship_status', 'Transit').upper())
    globe_html = globe_html.replace("__IMG__", template["img"])
    globe_html = globe_html.replace("__ATMO__", template["atmo"])
    globe_html = globe_html.replace("__FEAR__", f"{fear:.2f}")

    components.html(globe_html, height=750)
    
    st.markdown(
        "<div style='text-align:right; opacity:0.6;'><p style='color:#475569; font-size:0.5rem; font-family:monospace;'>ORBITAL_RECO_SYS v6.8 // ROBUST_ENGINE: ENABLED</p></div>",
        unsafe_allow_html=True
    )
