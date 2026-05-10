"""3D Intelligence Globe — Multi-mode orbital projection with Day/Night switching."""
from __future__ import annotations

import json
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime

LIVE_FILE = Path("data/outbreak_live.json")

# Data Exports for compatibility
NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "passengers": 27, "crew": 0,  "cases": 3, "deaths": 1},
    {"country": "United Kingdom","code": "GBR", "passengers": 20, "crew": 0,  "cases": 2, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "passengers": 12, "crew": 5,  "cases": 2, "deaths": 1},
    {"country": "Argentina",     "code": "ARG", "passengers": 4,  "crew": 0,  "cases": 4, "deaths": 1},
    {"country": "South Africa",  "code": "ZAF", "passengers": 0,  "crew": 16, "cases": 2, "deaths": 0},
]

# Hotspots with robust rendering metadata
HOTSPOT_DATA = [
    {"lat": 40.41, "lng": -3.70,  "cases": 3, "name": "ESP_SIGNAL_ALPHA", "color": "#fbbf24"},
    {"lat": 51.50, "lng": -0.12,  "cases": 2, "name": "GBR_SIGNAL_BETA",  "color": "#fbbf24"},
    {"lat": 52.36, "lng": 4.89,   "cases": 2, "name": "NLD_SIGNAL_GAMMA", "color": "#fbbf24"},
    {"lat": 14.93, "lng": -23.51, "cases": 5, "name": "MV_HONDIUS_CORE",   "color": "#22c55e"},
    {"lat": -34.6, "lng": -58.38, "cases": 4, "name": "ARG_LOCAL_CLUST",  "color": "#fbbf24"},
    {"lat": -26.2, "lng": 28.04,  "cases": 2, "name": "ZAF_LOCAL_CLUST",  "color": "#fbbf24"},
]

GLOBE_TEMPLATES = {
    "Night Ops (High-Res)": {
        "img": "//unpkg.com/three-globe/example/img/earth-night.jpg",
        "bg": "//unpkg.com/three-globe/example/img/night-sky.png",
        "atmo": "#00f5ff"
    },
    "Daylight Intelligence": {
        "img": "//unpkg.com/three-globe/example/img/earth-blue-marble.jpg",
        "bg": "rgba(10, 25, 45, 1)",
        "atmo": "#ffffff"
    },
    "Topological Scan": {
        "img": "//unpkg.com/three-globe/example/img/earth-topology.png",
        "bg": "#000",
        "atmo": "#fbbf24"
    },
    "Satellite Raw": {
        "img": "//unpkg.com/three-globe/example/img/earth-day.jpg",
        "bg": "//unpkg.com/three-globe/example/img/night-sky.png",
        "atmo": "#fff"
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
                <p style='margin:0; font-size:0.65rem; color:#22c55e; font-family:monospace; font-weight:800;'>SENSOR_LOCK: ACTIVE // SYNC: {datetime.now().strftime('%H:%M:%S')} UTC</p>
            </div>
            """, unsafe_allow_html=True
        )
    
    with col_h2:
        selected_mode = st.selectbox("PROJECTION_MODE", list(GLOBE_TEMPLATES.keys()), label_visibility="collapsed")

    template = GLOBE_TEMPLATES[selected_mode]

    globe_html = f"""
    <head>
      <style> 
        body {{ margin: 0; background: #000; overflow: hidden; font-family: monospace; }} 
        #telemetry-box {{
            position: absolute; bottom: 20px; left: 20px;
            background: rgba(15, 23, 42, 0.9); border: 1px solid #22c55e; border-radius: 10px;
            padding: 15px; z-index: 100; min-width: 240px; backdrop-filter: blur(10px);
            box-shadow: 0 0 30px rgba(34, 197, 94, 0.2);
        }}
        .t-header {{ color: #64748b; font-size: 10px; font-weight: 900; margin-bottom: 8px; letter-spacing: 1px; }}
        .t-vessel {{ color: #ffffff; font-size: 15px; font-weight: 900; display: flex; align-items: center; gap: 10px; }}
        .t-coords {{ color: #48cae4; font-size: 12px; margin-top: 4px; }}
        .t-status {{ color: #22c55e; font-size: 11px; font-weight: 900; margin-top: 10px; border-top: 1px solid #222; padding-top: 8px; }}
        .blink-dot {{ width: 10px; height: 10px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 15px #22c55e; animation: blinker 0.8s linear infinite; }}
        @keyframes blinker {{ 50% {{ opacity: 0.1; transform: scale(0.8); }} }}
      </style>
      <script src="//unpkg.com/three"></script>
      <script src="//unpkg.com/globe.gl"></script>
    </head>
    <body>
      <div id="telemetry-box">
          <div class="t-header">🛰️ VESSEL TELEMETRY</div>
          <div class="t-vessel"><div class="blink-dot"></div> MV HONDIUS</div>
          <div class="t-coords">LAT: 14.9316° N // LON: 23.5125° W</div>
          <div class="t-status">STATUS: {state.get('ship_status', 'Transit').upper()}</div>
          <div style="color:#64748b; font-size:9px; margin-top:4px;">PROJECTION: {selected_mode.upper()}</div>
      </div>
      <div id="globeViz"></div>
      <script>
        const hotspots = {json.dumps(HOTSPOT_DATA)};
        const world = Globe()
          (document.getElementById('globeViz'))
          .globeImageUrl('{template["img"]}')
          .backgroundImageUrl('{template["bg"]}')
          .showAtmosphere(true)
          .atmosphereColor('{template["atmo"]}')
          .atmosphereDaylightAlpha(0.3)
          .ringsData(hotspots)
          .ringColor(d => d.color)
          .ringMaxRadius(d => d.lat === 14.93 ? 12 : 8)
          .ringPropagationSpeed(2)
          .ringRepeatPeriod(800)
          .pointsData(hotspots)
          .pointColor('color')
          .pointAltitude(0.1)
          .pointRadius(0.8)
          .labelsData(hotspots)
          .labelText(d => d.cases.toString())
          .labelSize(1.5)
          .labelColor(d => d.color)
          .labelDotRadius(0)
          .pointTooltip(d => `
            <div style="background: rgba(13, 27, 42, 0.95); border: 1px solid ${{d.color}}; padding: 12px; border-radius: 8px; font-family: monospace; min-width: 250px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <b style="color:${{d.color}}; font-size:12px;">\${d.name}</b>
                    <span style="color:#22c55e; font-size:10px; font-weight:800;">LOCK: TRUE</span>
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom:10px;">
                    <div style="background:rgba(255,255,255,0.03); padding:5px; border-radius:4px;">
                        <div style="color:#64748b; font-size:8px;">CASES</div>
                        <div style="color:#ffffff; font-size:14px; font-weight:900;">\${d.cases}</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.03); padding:5px; border-radius:4px;">
                        <div style="color:#64748b; font-size:8px;">FEAR_INDEX</div>
                        <div style="color:#fbbf24; font-size:14px; font-weight:900;">{fear:.2f}/5</div>
                    </div>
                </div>
            </div>
          `);
        world.controls().autoRotate = true;
        world.controls().autoRotateSpeed = 0.5;
        world.pointOfView({{ lat: 20, lng: -20, altitude: 2.2 }}, 0);
      </script>
    </body>
    """
    
    components.html(globe_html, height=750)
    
    st.markdown(
        "<div style='text-align:right; opacity:0.6;'><p style='color:#475569; font-size:0.5rem; font-family:monospace;'>ORBITAL_RECO_SYS v6.5 // MULTI_MODE: ACTIVE</p></div>",
        unsafe_allow_html=True
    )
