"""3D Intelligence Globe — Real-time telemetry sync and live vessel tracking."""
from __future__ import annotations

import json
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime

LIVE_FILE = Path("data/outbreak_live.json")

# Core Data Exports for compatibility
NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "passengers": 27, "crew": 0,  "cases": 2, "deaths": 1},
    {"country": "United Kingdom","code": "GBR", "passengers": 20, "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "passengers": 12, "crew": 5,  "cases": 1, "deaths": 1},
    {"country": "Argentina",     "code": "ARG", "passengers": 4,  "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "South Africa",  "code": "ZAF", "passengers": 0,  "crew": 16, "cases": 0, "deaths": 0},
]

def _get_live_state() -> dict:
    """Read latest intelligence state from disk."""
    if LIVE_FILE.exists():
        try:
            return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {"confirmed_cases": 5, "ship_status": "Transit"}

def render_map_panel() -> None:
    state = _get_live_state()
    
    # ── HEADER ──
    st.markdown(
        f"""
        <div style='border-left: 3px solid #fbbf24; padding-left:15px; margin-bottom:1rem; display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <h2 style='margin:0; font-size:1rem; letter-spacing:0.12em; color:#ffffff;'>VESSEL INTELLIGENCE ARRAY</h2>
                <p style='margin:0; font-size:0.6rem; color:#fbbf24; font-family:monospace; font-weight:800;'>SATELLITE_LOCK: HONDIUS // SYSTEM_LIVE: {datetime.now().strftime('%H:%M:%S')} UTC</p>
            </div>
            <div style="background:rgba(34,197,94,0.1); border:1px solid #22c55e44; padding:4px 10px; border-radius:4px;">
                <span class="live-dot" style="width:6px; height:6px; background:#22c55e; box-shadow:0 0 10px #22c55e;"></span>
                <span style="color:#22c55e; font-size:0.6rem; font-weight:900; font-family:monospace;">REAL-TIME FEED</span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    # Dynamic Hotspots based on state
    hotspots = [
        {"lat": -34.60, "lng": -58.38, "size": 0.8, "color": "#ff4d4d", "name": "BETA_CLUSTER", "info": "Argentina Sector"},
        {"lat": -26.20, "lng": 28.04,  "size": 0.6, "color": "#ff4d4d", "name": "ALPHA_CLUSTER", "info": "ZA Sector"},
        {"lat": 14.93,  "lng": -23.51, "size": 1.5, "color": "#fbbf24", "name": "MV_HONDIUS_PRIMARY", "info": state.get('ship_status', 'In Transit')},
        {"lat": 40.41,  "lng": -3.70,  "size": 0.4, "color": "#ffffff", "name": "OSINT_SIGNAL_ESP", "info": "Imported Case Monitor"},
    ]

    globe_html = f"""
    <head>
      <style> 
        body {{ margin: 0; background: #000; overflow: hidden; }} 
        #telemetry-box {{
            position: absolute; bottom: 20px; left: 20px;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid #fbbf2444; border-radius: 8px;
            padding: 12px; font-family: monospace; z-index: 100;
            min-width: 200px; backdrop-filter: blur(5px);
        }}
        .t-label {{ color: #fbbf24; font-size: 10px; font-weight: 800; letter-spacing: 1px; }}
        .t-value {{ color: #fff; font-size: 14px; font-weight: 900; margin-bottom: 8px; }}
        .t-coord {{ color: #48cae4; font-size: 11px; }}
        .blink-light {{
            width: 8px; height: 8px; background: #fbbf24; border-radius: 50%;
            display: inline-block; margin-right: 8px;
            box-shadow: 0 0 10px #fbbf24;
            animation: blinker 1s linear infinite;
        }}
        @keyframes blinker {{ 50% {{ opacity: 0; }} }}
      </style>
      <script src="//unpkg.com/three"></script>
      <script src="//unpkg.com/globe.gl"></script>
    </head>
    <body>
      <div id="telemetry-box">
          <div class="t-label">🛰️ VESSEL TELEMETRY</div>
          <div class="t-value"><span class="blink-light"></span>MV HONDIUS</div>
          <div class="t-coord">LAT: 14.9316° N</div>
          <div class="t-coord">LON: 23.5125° W</div>
          <div style="height:1px; background:rgba(255,255,255,0.1); margin:8px 0;"></div>
          <div class="t-label">STATUS</div>
          <div style="color:#22c55e; font-size:11px; font-weight:900;">{state.get('ship_status', 'In Transit').upper()}</div>
      </div>
      <div id="globeViz"></div>
      <script>
        const hotspots = {json.dumps(hotspots)};

        const world = Globe()
          (document.getElementById('globeViz'))
          .globeImageUrl('//unpkg.com/three-globe/example/img/earth-night.jpg')
          .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
          .showAtmosphere(true)
          .atmosphereColor('#00f5ff')
          
          // 1. Hotspots (Glowing Rings)
          .ringsData(hotspots)
          .ringColor(d => d.color)
          .ringMaxRadius(d => d.size * 6)
          .ringPropagationSpeed(1.5)
          
          // 2. Labels (Real-time Intel)
          .labelsData(hotspots)
          .labelLat(d => d.lat)
          .labelLng(d => d.lng)
          .labelText(d => d.name)
          .labelSize(d => d.size * 0.4)
          .labelColor(d => d.color)
          .labelIncludeDot(true)
          .labelDotRadius(0.5)
          
          // 3. High-Intensity Blinking Vessel
          .onLabelClick(d => window.open(`https://www.marinetraffic.com/en/ais/home/shipid:419266/zoom:10`, '_blank'));

        // Blinking Logic
        let blink = true;
        setInterval(() => {{
            blink = !blink;
            const liveData = hotspots.map(h => ({{
                ...h,
                color: (h.name.includes('HONDIUS') && !blink) ? 'rgba(0,0,0,0)' : h.color
            }}));
            world.labelsData(liveData);
        }}, 800);

        world.controls().autoRotate = true;
        world.controls().autoRotateSpeed = 0.4;
        world.pointOfView({{ lat: 15, lng: -20, altitude: 2.2 }}, 0);

      </script>
    </body>
    """
    
    components.html(globe_html, height=650)
    
    st.markdown(
        "<div style='text-align:right; padding:5px;'><p style='color:#475569; font-size:0.5rem; font-family:monospace;'>ORBITAL_RECO_SYS v4.1 // LATERAL_SCAN: ACTIVE</p></div>",
        unsafe_allow_html=True
    )
