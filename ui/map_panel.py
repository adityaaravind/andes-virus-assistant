"""3D Intelligence Globe — Professional orbital tracking with robust template isolation."""
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

def _get_live_state() -> dict:
    if LIVE_FILE.exists():
        try: return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {"confirmed_cases": 5, "ship_status": "Transit", "deaths": 3, "nationalities": 23}

def render_map_panel() -> None:
    state = _get_live_state()
    from ui.pandemic_risk import _compute_risk
    risk = _compute_risk(state.get("confirmed_cases", 5), state.get("nationalities", 23))
    from ui.fear_index import _calculate_fear_average
    fear, _, _, _, _, _ = _calculate_fear_average()

    # Dynamic Hotspots
    hotspots = [
        {"lat": -34.60, "lng": -58.38, "size": 0.8, "color": "#fbbf24", "name": "BETA_CLUSTER", "cases": 3, "deaths": 1, "sentiment": "Concerned", "channel": "C5N", "article": "Ministry of Health monitors Ushuaia ports."},
        {"lat": -26.20, "lng": 28.04,  "size": 0.7, "color": "#fbbf24", "name": "ALPHA_CLUSTER", "cases": 2, "deaths": 1, "sentiment": "Alert", "channel": "SABC", "article": "NICD confirms Case 3 remains in isolated ICU."},
        {"lat": 14.93,  "lng": -23.51, "size": 1.4, "color": "#22c55e", "name": "MV_HONDIUS_POS", "cases": state.get("confirmed_cases", 5), "deaths": state.get("deaths", 3), "sentiment": "Critical", "channel": "MARITIME", "article": f"Vessel Status: {state.get('ship_status', 'Active Signal')}."}
    ]

    st.markdown(
        f"""
        <div style='border-left: 3px solid #22c55e; padding-left:15px; margin-bottom:1rem; display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <h2 style='margin:0; font-size:1.1rem; letter-spacing:0.12em; color:#ffffff;'>ORBITAL INTELLIGENCE ARRAY</h2>
                <p style='margin:0; font-size:0.65rem; color:#22c55e; font-family:monospace; font-weight:800;'>SENSOR_LOCK: ACTIVE // SYSTEM_FREQ: 2H // SYNC: {datetime.now().strftime('%H:%M:%S')} UTC</p>
            </div>
            <div style="background:rgba(34,197,94,0.1); border:1px solid #22c55e44; padding:4px 10px; border-radius:4px;">
                <span class="live-dot" style="width:6px; height:6px; background:#22c55e; box-shadow:0 0 10px #22c55e;"></span>
                <span style="color:#22c55e; font-size:0.6rem; font-weight:900; font-family:monospace;">TELEMETRY STABLE</span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    # NO F-STRING HERE: Use standard string to prevent NameError
    globe_template = """
    <head>
      <style> 
        body { margin: 0; background: #000; overflow: hidden; } 
        #telemetry-box {
            position: absolute; bottom: 20px; left: 20px;
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid #22c55e; border-radius: 8px;
            padding: 12px; font-family: monospace; z-index: 100;
            min-width: 220px; backdrop-filter: blur(10px);
        }
        #timeline-container {
            position: absolute; bottom: 20px; right: 20px;
            width: 260px; height: 140px; overflow: hidden;
            background: rgba(0, 0, 0, 0.7);
            border: 1px solid #22c55e33; border-radius: 8px;
            padding: 10px; font-family: monospace; z-index: 100;
        }
        #timeline-scroll {
            display: flex; flex-direction: column; gap: 10px;
            animation: scroll-up 20s linear infinite;
        }
        @keyframes scroll-up { 0% { transform: translateY(100%); } 100% { transform: translateY(-100%); } }
        .tl-item { border-left: 2px solid #22c55e; padding-left: 8px; margin-bottom: 8px; }
        .tl-date { color: #22c55e; font-size: 9px; font-weight: 900; }
        .tl-event { color: #ffffff; font-size: 10px; }
        .t-label { color: #22c55e; font-size: 10px; font-weight: 800; letter-spacing: 1px; }
        .t-value { color: #fff; font-size: 14px; font-weight: 900; }
        .t-coord { color: #48cae4; font-size: 11px; }
        .blink-light { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 8px; animation: blinker 0.8s linear infinite; }
        .vessel-blink { background: #22c55e; box-shadow: 0 0 15px #22c55e; }
        .signal-blink { background: #fbbf24; box-shadow: 0 0 15px #fbbf24; }
        @keyframes blinker { 50% { opacity: 0; } }
      </style>
      <script src="//unpkg.com/three"></script>
      <script src="//unpkg.com/globe.gl"></script>
    </head>
    <body>
      <div id="telemetry-box">
          <div class="t-label">🛰️ VESSEL TELEMETRY</div>
          <div class="t-value" style="margin-bottom:5px;"><span class="blink-light vessel-blink"></span>MV HONDIUS</div>
          <div class="t-coord">LAT: 14.9316° N // LON: 23.5125° W</div>
          <div style="height:1px; background:rgba(255,255,255,0.1); margin:8px 0;"></div>
          <div class="t-label">PANDEMIC_RISK</div>
          <div style="color:#ffffff; font-size:12px; font-weight:900;">__RISK__% // ELEVATED</div>
      </div>
      <div id="timeline-container">
          <div style="color:#22c55e; font-size:8px; font-weight:900; margin-bottom:8px; text-transform:uppercase;">Outbreak Activity Stream</div>
          <div id="timeline-scroll">
              <div class="tl-item"><div class="tl-date">APR 01</div><div class="tl-event">Vessel departure from Ushuaia</div></div>
              <div class="tl-item"><div class="tl-date">APR 06</div><div class="tl-event">Patient Zero: Symptoms detected</div></div>
              <div class="tl-item"><div class="tl-date">APR 11</div><div class="tl-event">First fatality recorded aboard</div></div>
              <div class="tl-item"><div class="tl-date">APR 26</div><div class="tl-event">Case 2 fatality in RSA (Joburg)</div></div>
              <div class="tl-item"><div class="tl-date">MAY 02</div><div class="tl-event">Case 3 confirmed ICU</div></div>
              <div class="tl-item"><div class="tl-date">MAY 04</div><div class="tl-event">Moored under hold (Cabo Verde)</div></div>
              <div class="tl-item"><div class="tl-date">MAY 08</div><div class="tl-event">WHO Releases DON599 SITREP</div></div>
          </div>
      </div>
      <div id="globeViz"></div>
      <script>
        const world = Globe()
          (document.getElementById('globeViz'))
          .globeImageUrl('//unpkg.com/three-globe/example/img/earth-night.jpg')
          .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
          .showAtmosphere(true)
          .atmosphereColor('#22c55e')
          .atmosphereDaylightAlpha(0.2)
          .ringsData(__HOTSPOTS__)
          .ringColor(d => d.color)
          .ringMaxRadius(d => d.size * 8)
          .ringPropagationSpeed(2)
          .ringRepeatPeriod(900)
          .pointsData(__HOTSPOTS__)
          .pointLat('lat')
          .pointLng('lng')
          .pointColor('color')
          .pointAltitude(d => d.size * 0.1)
          .pointRadius(0.8)
          .onPointHover(d => world.controls().autoRotate = !d)
          .pointTooltip(d => `
            <div style="background: rgba(13, 27, 42, 0.95); border: 1px solid ${d.color}; padding: 12px; border-radius: 8px; font-family: monospace; min-width: 250px; box-shadow: 0 0 20px rgba(0,0,0,0.5);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <b style="color:${d.color}; font-size:12px;">${d.name}</b>
                    <span style="color:#22c55e; font-size:10px; font-weight:800;">LOCK: TRUE</span>
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom:10px;">
                    <div style="background:rgba(255,255,255,0.03); padding:5px; border-radius:4px;">
                        <div style="color:#64748b; font-size:8px;">CASES</div>
                        <div style="color:#ffffff; font-size:14px; font-weight:900;">${d.cases}</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.03); padding:5px; border-radius:4px;">
                        <div style="color:#64748b; font-size:8px;">FATAL</div>
                        <div style="color:#ff4d4d; font-size:14px; font-weight:900;">${d.deaths}</div>
                    </div>
                </div>
                <div style="margin-bottom:8px;">
                    <div style="color:#64748b; font-size:8px;">COMMUNITY INTEL</div>
                    <div style="color:#48cae4; font-size:10px;">Sentiment: <b>${d.sentiment}</b> | Fear Index: <b>__FEAR__/5</b></div>
                </div>
                <div style="border-top:1px solid rgba(255,255,255,0.1); padding-top:8px;">
                    <div style="color:#fbbf24; font-size:9px; font-weight:900; margin-bottom:2px;">SOURCE: ${d.channel.toUpperCase()}</div>
                    <div style="color:#94a3b8; font-size:9px; line-height:1.2;">"${d.article}"</div>
                </div>
            </div>
          `);

        world.controls().autoRotate = true;
        world.controls().autoRotateSpeed = 0.5;
        world.pointOfView({ lat: 15, lng: -20, altitude: 2.2 }, 0);
      </script>
    </body>
    """
    
    # Manual interpolation to bypass f-string NameError
    globe_html = globe_template.replace("__HOTSPOTS__", json.dumps(hotspots))
    globe_html = globe_html.replace("__RISK__", f"{risk['overall']:.1f}")
    globe_html = globe_html.replace("__FEAR__", f"{fear:.2f}")

    components.html(globe_html, height=750)
    
    st.markdown(
        "<div style='text-align:right; opacity:0.6;'><p style='color:#475569; font-size:0.5rem; font-family:monospace;'>ORBITAL_RECO_SYS v5.3 // TEMPLATE_ISOLATION: ENABLED</p></div>",
        unsafe_allow_html=True
    )
