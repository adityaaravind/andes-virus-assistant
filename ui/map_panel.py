"""High-fidelity 3D Intelligence Globe — Robust markers and automated vessel zoom."""
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

# High-Intensity Hotspot Data
HOTSPOT_DATA = [
    {"lat": 40.41, "lng": -3.70,  "cases": 3, "name": "SPAIN_LOCAL", "color": "#fbbf24", "size": 1.2},
    {"lat": 51.50, "lng": -0.12,  "cases": 2, "name": "UK_LOCAL", "color": "#fbbf24", "size": 1.0},
    {"lat": 52.36, "lng": 4.89,   "cases": 2, "name": "NETHERLANDS_LOCAL", "color": "#fbbf24", "size": 1.0},
    {"lat": 14.93, "lng": -23.51, "cases": 5, "name": "MV_HONDIUS_CORE", "color": "#22c55e", "size": 2.5},
    {"lat": -34.6, "lng": -58.38, "cases": 4, "name": "ARGENTINA_CORE", "color": "#fbbf24", "size": 1.5},
    {"lat": -26.2, "lng": 28.04,  "cases": 2, "name": "ZA_CLUSTER", "color": "#fbbf24", "size": 1.2},
]

SHIP_PATH = [
    {"startLat": -54.8, "startLng": -68.3, "endLat": -54.3, "endLng": -36.5, "color": ["#ff4d4d", "#ff4d4d"]},
    {"startLat": -54.3, "startLng": -36.5, "endLat": -37.1, "endLng": -12.3, "color": ["#ff4d4d", "#ff4d4d"]},
    {"startLat": -37.1, "startLng": -12.3, "endLat": -15.9, "endLng": -5.7,  "color": ["#ff4d4d", "#ff4d4d"]},
    {"startLat": -15.9, "startLng": -5.7,  "endLat": 14.93, "endLng": -23.51, "color": ["#ff4d4d", "#22c55e"]},
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
                <h2 style='margin:0; font-size:1.1rem; letter-spacing:0.12em; color:#ffffff; text-shadow: 0 0 10px rgba(34,197,94,0.3);'>ORBITAL INTELLIGENCE PROJECTION</h2>
                <p style='margin:0; font-size:0.65rem; color:#22c55e; font-family:monospace; font-weight:800;'>VESSEL_LOCK: ACQUIRED // ZOOM_AUTO: ENABLED // SYNC: {datetime.now().strftime('%H:%M:%S')} UTC</p>
            </div>
            <div style="background:rgba(34,197,94,0.1); border:1px solid #22c55e44; padding:4px 10px; border-radius:4px;">
                <span class="live-dot" style="width:6px; height:6px; background:#22c55e; box-shadow:0 0 10px #22c55e;"></span>
                <span style="color:#22c55e; font-size:0.6rem; font-weight:900; font-family:monospace;">TRACKING_LIVE</span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    globe_template = """
    <head>
      <style> 
        body { margin: 0; background: #000; overflow: hidden; font-family: 'Inter', sans-serif; } 
        #telemetry-box {
            position: absolute; bottom: 20px; left: 20px;
            background: rgba(15, 23, 42, 0.95); border: 1px solid #22c55e; border-radius: 10px;
            padding: 15px; z-index: 100; min-width: 220px; backdrop-filter: blur(10px);
        }
        .t-header { color: #64748b; font-size: 10px; font-weight: 900; margin-bottom: 5px; }
        .t-vessel { color: #ffffff; font-size: 15px; font-weight: 900; margin-bottom: 5px; }
        .blink-dot { width: 10px; height: 10px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 15px #22c55e; animation: blinker 0.8s linear infinite; }
        @keyframes blinker { 50% { opacity: 0.1; transform: scale(0.8); } }
      </style>
      <script src="//unpkg.com/three"></script>
      <script src="//unpkg.com/globe.gl"></script>
    </head>
    <body>
      <div id="telemetry-box">
          <div class="t-header">🛰️ VESSEL TELEMETRY</div>
          <div class="t-vessel"><span class="blink-dot"></span> MV HONDIUS LOCK</div>
          <div style="color:#48cae4; font-size:12px; font-family:monospace;">LAT: 14.9316° N // LON: 23.5125° W</div>
          <div style="height:1px; background:rgba(255,255,255,0.1); margin:10px 0;"></div>
          <div style="color:#22c55e; font-size:11px; font-weight:900;">STATUS: __STATUS__</div>
      </div>
      <div id="globeViz"></div>
      <script>
        const hotspots = __HOTSPOTS__;
        const shipPath = __SHIP_PATH__;

        const world = Globe()
          (document.getElementById('globeViz'))
          .globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
          .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
          .showAtmosphere(true)
          .atmosphereColor('#22c55e')
          .atmosphereDaylightAlpha(0.2)

          // 1. ROBUST POINTS (Pillars)
          .pointsData(hotspots)
          .pointLat('lat')
          .pointLng('lng')
          .pointColor('color')
          .pointAltitude(d => d.size * 0.1)
          .pointRadius(0.8)
          
          // 2. ROBUST RINGS (Glow)
          .ringsData(hotspots)
          .ringColor(d => d.color)
          .ringMaxRadius(d => d.size * 5)
          .ringPropagationSpeed(2)
          .ringRepeatPeriod(1000)

          // 3. TRANSIT ARC
          .arcsData(shipPath)
          .arcColor('color')
          .arcDashLength(0.4)
          .arcDashGap(2)
          .arcDashAnimateTime(2000)
          .arcStroke(1.5)

          // 4. HTML BLINKING MARKERS (Ensuring absolute visibility)
          .htmlElementsData(hotspots)
          .htmlElement(d => {
            const el = document.createElement('div');
            el.style.width = '12px';
            el.style.height = '12px';
            el.style.borderRadius = '50%';
            el.style.background = d.color;
            el.style.boxShadow = `0 0 20px ${d.color}`;
            el.style.border = '2px solid white';
            el.className = 'blink-dot';
            if (!d.name.includes('HONDIUS')) el.style.animation = 'none'; // Only vessel blinks high-intensity
            return el;
          })

          .htmlElementTooltip(d => `
            <div style="background: rgba(13, 27, 42, 0.98); border: 1px solid ${d.color}; padding: 12px; border-radius: 8px; font-family: monospace; min-width: 200px;">
                <b style="color:${d.color};">${d.name}</b><br/>
                CASES: ${d.cases}<br/>
                FEAR_INDEX: __FEAR__/5
            </div>
          `);

        world.controls().autoRotate = false; // Disable for precise zoom
        
        // AUTOMATED ZOOM TO VESSEL (Cabo Verde Sector)
        world.pointOfView({ lat: 14.9, lng: -23.5, altitude: 0.8 }, 2000);
      </script>
    </body>
    """
    
    # Manual interpolation
    globe_html = globe_template.replace("__HOTSPOTS__", json.dumps(HOTSPOT_DATA))
    globe_html = globe_html.replace("__SHIP_PATH__", json.dumps(SHIP_PATH))
    globe_html = globe_html.replace("__STATUS__", state.get('ship_status', 'Transit').upper())
    globe_html = globe_html.replace("__FEAR__", f"{fear:.2f}")

    components.html(globe_html, height=750)
    
    st.markdown(
        "<div style='text-align:right; opacity:0.6;'><p style='color:#475569; font-size:0.5rem; font-family:monospace;'>ORBITAL_RECO_SYS v7.0 // AUTO_ZOOM: ON // HI_LUM_MARKERS: ON</p></div>",
        unsafe_allow_html=True
    )
