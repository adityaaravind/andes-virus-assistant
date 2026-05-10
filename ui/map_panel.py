"""3D Intelligence Globe — High-intensity visuals, tactical legends, and scrolling timeline."""
from __future__ import annotations

import json
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime

LIVE_FILE = Path("data/outbreak_live.json")

# Compatibility Data
NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "passengers": 27, "crew": 0,  "cases": 2, "deaths": 1},
    {"country": "United Kingdom","code": "GBR", "passengers": 20, "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "passengers": 12, "crew": 5,  "cases": 1, "deaths": 1},
    {"country": "Argentina",     "code": "ARG", "passengers": 4,  "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "South Africa",  "code": "ZAF", "passengers": 0,  "crew": 16, "cases": 0, "deaths": 0},
]

# Intelligence Clusters
TACTICAL_CLUSTERS = [
    {"id": "ALPHA", "name": "ALPHA_CLUSTER", "loc": "South Africa (Johannesburg)", "status": "Case 3 Evacuation Site", "cases": 2, "color": "#ff4d4d"},
    {"id": "BETA",  "name": "BETA_CLUSTER",  "loc": "Argentina (Ushuaia)", "status": "Original Departure Point", "cases": 3, "color": "#ff4d4d"},
]

# Timeline Milestones
OUTBREAK_TIMELINE = [
    {"date": "APR 01", "event": "MV HONDIUS DEPARTS USHUAIA"},
    {"date": "APR 06", "event": "PATIENT ZERO: FIRST SYMPTOMS DETECTED"},
    {"date": "APR 11", "event": "FIRST FATALITY RECORDED ABOARD"},
    {"date": "APR 26", "event": "CASE 2 FATALITY (SOUTH AFRICA)"},
    {"date": "MAY 02", "event": "CASE 3 CONFIRMED (ICU, JOBURG)"},
    {"date": "MAY 04", "event": "VESSEL MOORED IN CABO VERDE"},
    {"date": "MAY 08", "event": "WHO RELEASES DON599 SITREP"},
]

def _get_live_state() -> dict:
    if LIVE_FILE.exists():
        try: return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {"confirmed_cases": 5, "ship_status": "Transit"}

def render_map_panel() -> None:
    state = _get_live_state()
    
    # ── HEADER ──
    st.markdown(
        f"""
        <div style='border-left: 3px solid #00f5ff; padding-left:15px; margin-bottom:1rem;'>
            <h2 style='margin:0; font-size:1.1rem; letter-spacing:0.1em; color:#ffffff; text-shadow: 0 0 10px rgba(0,245,255,0.5);'>GLOBAL INTELLIGENCE PROJECTION</h2>
            <p style='margin:0; font-size:0.65rem; color:#00f5ff; font-family:monospace; font-weight:800;'>HIGH-INTENSITY SCAN ACTIVE // SYSTEM_LIVE: {datetime.now().strftime('%H:%M:%S')} UTC</p>
        </div>
        """, unsafe_allow_html=True
    )

    # Dynamic Hotspots for the JS side
    hotspots = [
        {"lat": -34.60, "lng": -58.38, "size": 1.2, "color": "#ff4d4d", "name": "BETA_CLUSTER"},
        {"lat": -26.20, "lng": 28.04,  "size": 1.0, "color": "#ff4d4d", "name": "ALPHA_CLUSTER"},
        {"lat": 14.93,  "lng": -23.51, "size": 1.8, "color": "#fbbf24", "name": "MV_HONDIUS_PRIMARY"},
    ]
    
    # Connection Arcs
    arcs = [
        {"startLat": -54.8, "startLng": -68.3, "endLat": 14.9, "endLng": -23.5, "color": ["#ff4d4d", "#00f5ff"]},
        {"startLat": -26.2, "startLng": 28.0,  "endLat": 14.9, "endLng": -23.5, "color": ["#ff4d4d", "#00f5ff"]}
    ]

    globe_html = f"""
    <head>
      <style> 
        body {{ margin: 0; background: #000; overflow: hidden; }} 
        
        /* 1. VESSEL TELEMETRY OVERLAY */
        #telemetry-box {{
            position: absolute; bottom: 20px; left: 20px;
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid #fbbf24; border-radius: 8px;
            padding: 12px; font-family: monospace; z-index: 100;
            min-width: 220px; backdrop-filter: blur(10px);
            box-shadow: 0 0 20px rgba(0,0,0,0.5);
        }}
        
        /* 2. TACTICAL LEGEND OVERLAY */
        #legend-box {{
            position: absolute; top: 20px; left: 20px;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid #ffffff22; border-radius: 6px;
            padding: 10px; font-family: monospace; z-index: 100;
            width: 200px;
        }}
        
        /* 3. SCROLLING TIMELINE OVERLAY */
        #timeline-container {{
            position: absolute; bottom: 20px; right: 20px;
            width: 240px; height: 120px; overflow: hidden;
            background: rgba(0, 0, 0, 0.7);
            border: 1px solid #00f5ff33; border-radius: 8px;
            padding: 10px; font-family: monospace; z-index: 100;
        }}
        #timeline-scroll {{
            display: flex; flex-direction: column; gap: 8px;
            animation: scroll-up 25s linear infinite;
        }}
        @keyframes scroll-up {{ 0% {{ transform: translateY(100%); }} 100% {{ transform: translateY(-100%); }} }}
        
        .t-label {{ color: #fbbf24; font-size: 10px; font-weight: 800; letter-spacing: 1px; }}
        .t-value {{ color: #fff; font-size: 14px; font-weight: 900; }}
        .t-coord {{ color: #48cae4; font-size: 11px; }}
        .timeline-item {{ border-left: 2px solid #00f5ff; padding-left: 8px; }}
        .tl-date {{ color: #00f5ff; font-size: 9px; font-weight: 900; }}
        .tl-event {{ color: #ffffff; font-size: 10px; }}
        
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
      <div id="legend-box">
          <div style="color:#64748b; font-size:9px; font-weight:900; margin-bottom:8px;">TACTICAL IDENTIFIERS</div>
          <div style="margin-bottom:6px;"><span style="color:#ff4d4d; font-weight:900;">ALPHA</span> <span style="color:#94a3b8; font-size:10px;">ZA SECTOR</span></div>
          <div><span style="color:#ff4d4d; font-weight:900;">BETA</span> <span style="color:#94a3b8; font-size:10px;">ARG SECTOR</span></div>
      </div>

      <div id="telemetry-box">
          <div class="t-label">🛰️ VESSEL TELEMETRY</div>
          <div class="t-value" style="margin-bottom:5px;"><span class="blink-light"></span>MV HONDIUS</div>
          <div class="t-coord">28.2916° N // 16.6291° W</div>
          <div style="height:1px; background:rgba(255,255,255,0.1); margin:8px 0;"></div>
          <div class="t-label">STATUS</div>
          <div style="color:#22c55e; font-size:11px; font-weight:900;">{state.get('ship_status', 'In Transit').upper()}</div>
      </div>

      <div id="timeline-container">
          <div style="color:#00f5ff; font-size:8px; font-weight:900; margin-bottom:5px; text-transform:uppercase;">Outbreak Chronology</div>
          <div id="timeline-scroll">
              { "".join([f'<div class="timeline-item"><div class="tl-date">{m["date"]}</div><div class="tl-event">{m["event"]}</div></div>' for m in OUTBREAK_TIMELINE]) }
              { "".join([f'<div class="timeline-item"><div class="tl-date">{m["date"]}</div><div class="tl-event">{m["event"]}</div></div>' for m in OUTBREAK_TIMELINE]) }
          </div>
      </div>

      <div id="globeViz"></div>
      <script>
        const hotspots = {json.dumps(hotspots)};
        const arcs = {json.dumps(arcs)};

        const world = Globe()
          (document.getElementById('globeViz'))
          .globeImageUrl('//unpkg.com/three-globe/example/img/earth-night.jpg')
          .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
          .showAtmosphere(true)
          .atmosphereColor('#00f5ff')
          .atmosphereDaylightAlpha(0.2) // Brighter atmosphere
          
          // 1. Hotspots (High Intensity Pulsing)
          .ringsData(hotspots)
          .ringColor(d => d.color)
          .ringMaxRadius(d => d.size * 8)
          .ringPropagationSpeed(2.5)
          .ringRepeatPeriod(700)
          
          // 2. Tactical Connectors (Dotted Lines)
          .arcsData(arcs)
          .arcColor('color')
          .arcDashLength(0.5)
          .arcDashGap(2)
          .arcDashAnimateTime(2000)
          .arcStroke(1.5)
          
          // 3. Identification Labels
          .labelsData(hotspots)
          .labelLat(d => d.lat)
          .labelLng(d => d.lng)
          .labelText(d => d.name)
          .labelSize(d => d.size * 0.6)
          .labelColor(d => d.color)
          .labelIncludeDot(true)
          .labelDotRadius(0.6)
          .labelResolution(3);

        // LIVE BLINKING LOGIC
        let shipVisible = true;
        setInterval(() => {{
            shipVisible = !shipVisible;
            const updated = hotspots.map(h => ({{
                ...h,
                color: (h.name.includes('HONDIUS') && !shipVisible) ? 'rgba(0,0,0,0)' : h.color
            }}));
            world.labelsData(updated);
        }}, 600);

        world.controls().autoRotate = true;
        world.controls().autoRotateSpeed = 0.5;
        world.pointOfView({{ lat: 10, lng: -20, altitude: 2.0 }}, 0);

      </script>
    </body>
    """
    
    components.html(globe_html, height=700)
    
    st.markdown(
        "<div style='text-align:center; opacity:0.6;'><p style='color:#475569; font-size:0.5rem; font-family:monospace;'>TACTICAL_DISPLAY_MODE: HI_LUM // OSINT_CHRONOLOGY: SYNCED</p></div>",
        unsafe_allow_html=True
    )
