"""Cinematic 3D Globe — Globe.gl implementation for robust 3D intelligence."""
from __future__ import annotations

import json
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

LIVE_FILE = Path("data/outbreak_live.json")

# Compatibility Data
NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "passengers": 27, "crew": 0,  "cases": 2, "deaths": 1},
    {"country": "United Kingdom","code": "GBR", "passengers": 20, "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "passengers": 12, "crew": 5,  "cases": 1, "deaths": 1},
    {"country": "Argentina",     "code": "ARG", "passengers": 4,  "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "South Africa",  "code": "ZAF", "passengers": 0,  "crew": 16, "cases": 0, "deaths": 0},
]

HOTSPOTS = [
    {"lat": -34.60, "lng": -58.38, "size": 0.8, "color": "#ff4d4d", "name": "ARGENTINA_CLUSTER"},
    {"lat": -26.20, "lng": 28.04,  "size": 0.6, "color": "#ff4d4d", "name": "ZA_EVAC_SITE"},
    {"lat": 14.93,  "lng": -23.51, "size": 1.2, "color": "#fbbf24", "name": "MV_HONDIUS_POSITION"},
    {"lat": 40.41,  "lng": -3.70,  "size": 0.4, "color": "#ffffff", "name": "ESP_IMPORTED_SIGNAL"},
]

ARCS = [
    {"startLat": -54.8, "startLng": -68.3, "endLat": 14.9, "endLng": -23.5, "color": ["#ff4d4d", "#fbbf24"]}
]

def render_map_panel() -> None:
    st.markdown(
        """
        <div style='border-left: 3px solid #00f5ff; padding-left:15px; margin-bottom:1rem;'>
            <h2 style='margin:0; font-size:1rem; letter-spacing:0.12em; color:#ffffff;'>ORBITAL INTELLIGENCE PROJECTION</h2>
            <p style='margin:0; font-size:0.6rem; color:#00f5ff; font-family:monospace; font-weight:800;'>OSINT ENGINE: GLOBE_GL // SATELLITE_LOCK: ACTIVE</p>
        </div>
        """, unsafe_allow_html=True
    )

    globe_html = f"""
    <head>
      <style> body {{ margin: 0; background: #000; overflow: hidden; }} </style>
      <script src="//unpkg.com/three"></script>
      <script src="//unpkg.com/globe.gl"></script>
    </head>
    <body>
      <div id="globeViz"></div>
      <script>
        const hotspots = {json.dumps(HOTSPOTS)};
        const arcs = {json.dumps(ARCS)};

        const world = Globe()
          (document.getElementById('globeViz'))
          .globeImageUrl('//unpkg.com/three-globe/example/img/earth-night.jpg')
          .bumpImageUrl('//unpkg.com/three-globe/example/img/earth-topology.png')
          .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
          .showAtmosphere(true)
          .atmosphereColor('#00f5ff')
          .atmosphereDaylightAlpha(0.1)
          
          // 1. Hotspots (Pulsing Rings)
          .ringsData(hotspots)
          .ringColor(d => d.color)
          .ringMaxRadius(d => d.size * 5)
          .ringPropagationSpeed(2)
          .ringRepeatPeriod(1000)
          
          // 2. Labels (Detailed Info)
          .labelsData(hotspots)
          .labelLat(d => d.lat)
          .labelLng(d => d.lng)
          .labelText(d => d.name)
          .labelSize(d => d.size * 0.5)
          .labelDotRadius(d => d.size * 0.2)
          .labelColor(d => d.color)
          .labelResolution(2)
          
          // 3. Arcs (Ship Route)
          .arcsData(arcs)
          .arcColor('color')
          .arcDashLength(0.4)
          .arcDashGap(2)
          .arcDashAnimateTime(1500)
          .arcStroke(1.2)
          
          // 4. Interaction
          .onLabelClick(d => window.open(`https://www.google.com/maps?q=${{d.lat}},${{d.lng}}`, '_blank'));

        // High-tech Blinking Vessel Effect
        setInterval(() => {{
            const ship = hotspots.find(h => h.name.includes('HONDIUS'));
            if (ship) {{
                ship.size = (ship.size === 1.2 ? 0.2 : 1.2);
                world.labelsData([...hotspots]);
            }}
        }}, 800);

        // Auto-orbit
        world.controls().autoRotate = true;
        world.controls().autoRotateSpeed = 0.5;
        
        // Initial Camera Focus
        world.pointOfView({{ lat: 10, lng: -20, altitude: 2.0 }}, 0);

      </script>
    </body>
    """
    
    components.html(globe_html, height=650)
    
    st.markdown(
        "<div style='text-align:center; padding:10px;'><p style='color:#475569; font-size:0.55rem; font-family:monospace;'>SENSORS: 3D_ARRAY ACTIVE // DRAG TO ORBIT // SCROLL TO ZOOM</p></div>",
        unsafe_allow_html=True
    )
