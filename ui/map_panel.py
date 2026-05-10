"""HantavirusMap Pixel-Perfect Replica — High-fidelity 3D Intelligence Projection."""
from __future__ import annotations

import json
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime

LIVE_FILE = Path("data/outbreak_live.json")

# Source: WHO DON599 (2026-DON599) — 147 aboard (88 pass, 59 crew, 23 nationalities)
NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "cases": 3, "deaths": 1},
    {"country": "United Kingdom","code": "GBR", "cases": 2, "deaths": 0},
    {"country": "Germany",       "code": "DEU", "cases": 2, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "cases": 2, "deaths": 1},
    {"country": "Norway",        "code": "NOR", "cases": 2, "deaths": 0},
    {"country": "Italy",         "code": "ITA", "cases": 1, "deaths": 0},
    {"country": "Argentina",     "code": "ARG", "cases": 4, "deaths": 1},
    {"country": "South Africa",  "code": "ZAF", "cases": 2, "deaths": 0},
]

# Hotspots mapped to the visual style of the screenshot
HOTSPOTS = [
    {"lat": 40.41, "lng": -3.70,  "cases": 3, "name": "SPAIN_LOCAL", "type": "local"},
    {"lat": 51.50, "lng": -0.12,  "cases": 2, "name": "UK_LOCAL", "type": "local"},
    {"lat": 52.52, "lng": 13.40,  "cases": 2, "name": "GERMANY_LOCAL", "type": "local"},
    {"lat": 52.36, "lng": 4.89,   "cases": 2, "name": "NETHERLANDS_LOCAL", "type": "local"},
    {"lat": 60.47, "lng": 8.46,   "cases": 2, "name": "NORWAY_LOCAL", "type": "vessel-signal"},
    {"lat": 41.87, "lng": 12.56,  "cases": 1, "name": "ITALY_IMPORTED", "type": "imported"},
    {"lat": 14.93, "lng": -23.51, "cases": 5, "name": "MV_HONDIUS_CORE", "type": "vessel-signal"},
    {"lat": -34.6, "lng": -58.38, "cases": 4, "name": "ARGENTINA_CORE", "type": "local"},
    {"lat": -26.2, "lng": 28.04,  "cases": 2, "name": "ZA_CLUSTER", "type": "local"},
]

def _get_live_state() -> dict:
    if LIVE_FILE.exists():
        try: return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {"confirmed_cases": 5}

def render_map_panel() -> None:
    state = _get_live_state()
    from ui.fear_index import _calculate_fear_average
    fear, _, _, _, _, _ = _calculate_fear_average()

    st.markdown(
        f"""
        <div style='border-left: 3px solid #ff4d4d; padding-left:15px; margin-bottom:1rem; display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <h2 style='margin:0; font-size:1.1rem; letter-spacing:0.12em; color:#ffffff; text-shadow: 0 0 10px rgba(255,77,77,0.3);'>ORBITAL INTELLIGENCE PROJECTION</h2>
                <p style='margin:0; font-size:0.65rem; color:#ff4d4d; font-family:monospace; font-weight:800;'>SENSOR_LOCK: ACTIVE // SYSTEM_FREQ: 2H // SYNC: {datetime.now().strftime('%H:%M:%S')} UTC</p>
            </div>
            <div style="background:rgba(255,77,77,0.1); border:1px solid #ff4d4d44; padding:4px 10px; border-radius:4px;">
                <span class="live-dot" style="width:6px; height:6px; background:#ff4d4d; box-shadow:0 0 10px #ff4d4d;"></span>
                <span style="color:#ff4d4d; font-size:0.6rem; font-weight:900; font-family:monospace;">TACTICAL_OVERLAY_ACTIVE</span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    # NO F-STRING HERE: Use standard string with manual interpolation
    globe_template = """
    <head>
      <style> 
        body { margin: 0; background: #000; overflow: hidden; font-family: 'Inter', sans-serif; } 
        
        /* 1. PIXEL-PERFECT MARKERS FROM SCREENSHOT */
        .ring-marker {
            width: 18px; height: 18px;
            border-radius: 50%;
            border: 2px solid #ffffff;
            position: relative;
            box-shadow: 0 0 15px rgba(255, 77, 77, 0.8), inset 0 0 5px rgba(255, 77, 77, 0.5);
            display: flex; align-items: center; justify-content: center;
        }
        .ring-marker::after {
            content: '';
            position: absolute;
            width: 100%; height: 100%;
            border-radius: 50%;
            border: 1px solid rgba(255,255,255,0.4);
            animation: pulse-ring 2s infinite;
        }
        @keyframes pulse-ring { 0% { transform: scale(1); opacity: 1; } 100% { transform: scale(2.5); opacity: 0; } }

        .number-badge {
            position: absolute; top: -6px; right: -6px;
            background: #ffffff; color: #1a1a1a;
            border-radius: 50%; width: 12px; height: 12px;
            font-size: 8px; font-weight: 900;
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 0 5px rgba(0,0,0,0.5);
        }

        .vessel-triangle {
            width: 0; height: 0;
            border-left: 8px solid transparent;
            border-right: 8px solid transparent;
            border-bottom: 14px solid #fbbf24;
            filter: drop-shadow(0 0 10px #fbbf24);
            animation: blinker 1s linear infinite;
        }
        @keyframes blinker { 50% { opacity: 0.3; } }

        /* TELEMETRY OVERLAY */
        #telemetry-box {
            position: absolute; bottom: 20px; left: 20px;
            background: rgba(15, 23, 42, 0.95); border: 1px solid #333; border-radius: 8px;
            padding: 12px; font-family: monospace; z-index: 100;
            min-width: 200px; backdrop-filter: blur(10px);
        }
        .t-label { color: #64748b; font-size: 9px; font-weight: 900; }
        .t-value { color: #ffffff; font-size: 13px; font-weight: 900; margin-bottom: 5px; }

      </style>
      <script src="//unpkg.com/three"></script>
      <script src="//unpkg.com/globe.gl"></script>
    </head>
    <body>
      <div id="telemetry-box">
          <div class="t-label">LAYERS</div>
          <div style="margin-bottom:10px;">
              <div style="color:#ff4d4d; font-size:11px; font-weight:900;">📈 NOW ACTIVE</div>
              <div style="color:#475569; font-size:9px;">12 COUNTRIES // 582 ALERTS</div>
          </div>
          <div class="t-label">VESSEL TRACKING</div>
          <div class="t-value" style="color:#fbbf24;">MV HONDIUS LOCK</div>
          <div style="color:#22c55e; font-size:10px; font-weight:900;">SIGNAL_STRENGTH: 98%</div>
      </div>
      
      <div id="globeViz"></div>
      <script>
        const hotspots = __HOTSPOTS__;

        const world = Globe()
          (document.getElementById('globeViz'))
          .globeImageUrl('//unpkg.com/three-globe/example/img/earth-night.jpg')
          .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
          .showAtmosphere(true)
          .atmosphereColor('#ff4d4d')
          .atmosphereDaylightAlpha(0.1)

          // 1. COUNTRY GLOWS (Polygons from the screenshot)
          .polygonsData(__GEOJSON__.features)
          .polygonCapColor(d => {
             const code = d.properties.ISO_A3;
             const active = ["ESP", "GBR", "DEU", "NLD", "NOR", "ITA", "ARG", "ZAF", "PHL", "CHL"];
             return active.includes(code) ? 'rgba(74, 18, 18, 0.7)' : 'rgba(0, 0, 0, 0)';
          })
          .polygonSideColor(() => 'rgba(255, 77, 77, 0.05)')
          .polygonStrokeColor(() => 'rgba(255, 255, 255, 0.1)')

          // 2. PIXEL-PERFECT HTML MARKERS
          .htmlElementsData(hotspots)
          .htmlElement(d => {
            const el = document.createElement('div');
            if (d.type === 'vessel-signal') {
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

          // 3. INTERACTIVE TOOLTIP
          .htmlElementTooltip(d => `
            <div style="background: rgba(13, 27, 42, 0.98); border: 1px solid #ffffff33; padding: 12px; border-radius: 8px; font-family: monospace; min-width: 240px; box-shadow: 0 0 25px rgba(0,0,0,0.8);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <b style="color:#ffffff; font-size:12px;">${d.name}</b>
                    <span style="color:#ff4d4d; font-size:10px; font-weight:800;">ACTIVE_OUTBREAK</span>
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom:10px;">
                    <div style="background:rgba(255,255,255,0.03); padding:5px; border-radius:4px;">
                        <div style="color:#64748b; font-size:8px;">DETECTED_CASES</div>
                        <div style="color:#ffffff; font-size:14px; font-weight:900;">${d.cases}</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.03); padding:5px; border-radius:4px;">
                        <div style="color:#64748b; font-size:8px;">FEAR_INDEX</div>
                        <div style="color:#fbbf24; font-size:14px; font-weight:900;">__FEAR__/5</div>
                    </div>
                </div>
                <div style="border-top:1px solid rgba(255,255,255,0.1); padding-top:8px;">
                    <div style="color:#00f5ff; font-size:9px; font-weight:900; margin-bottom:2px;">OSINT_CHANNEL: ${d.channel || 'OFFICIAL'}</div>
                    <div style="color:#94a3b8; font-size:9px; line-height:1.2;">"${d.article || 'Monitoring local transmission signals.'}"</div>
                </div>
            </div>
          `);

        world.controls().autoRotate = true;
        world.controls().autoRotateSpeed = 0.4;
        world.pointOfView({ lat: 20, lng: -10, altitude: 2.5 }, 0);
      </script>
    </body>
    """
    
    # Fetch GeoJSON for country borders
    import requests
    try:
        geojson = requests.get("https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json").json()
    except: geojson = {"features": []}

    # Manual interpolation
    globe_html = globe_template.replace("__HOTSPOTS__", json.dumps(HOTSPOTS))
    globe_html = globe_html.replace("__GEOJSON__", json.dumps(geojson))
    globe_html = globe_html.replace("__FEAR__", f"{fear:.2f}")

    components.html(globe_html, height=750)
    
    st.markdown(
        "<div style='text-align:right; opacity:0.6;'><p style='color:#475569; font-size:0.5rem; font-family:monospace;'>ORBITAL_RECO_SYS v6.0 // REPLICA_AESTHETIC: ENABLED</p></div>",
        unsafe_allow_html=True
    )
