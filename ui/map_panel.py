"""High-fidelity 3D Intelligence Globe — custom JS implementation with geocoding and live effects."""
from __future__ import annotations

import json
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

LIVE_FILE = Path("data/outbreak_live.json")

# Core Telemetry
HOTSPOTS = [
    {"lat": -34.60, "lon": -58.38, "cases": 3, "name": "ARGENTINA_CLUSTER"},
    {"lat": -26.20, "lon": 28.04,  "cases": 2, "name": "ZA_EVAC_SITE"},
    {"lat": 14.93,  "lon": -23.51, "cases": 5, "name": "MV_HONDIUS_MOORED"},
    {"lat": 40.41,  "lon": -3.70,  "cases": 2, "name": "ESP_SIGNAL"},
]

# Compatibility data export
NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "passengers": 27, "crew": 0,  "cases": 2, "deaths": 1},
    {"country": "United Kingdom","code": "GBR", "passengers": 20, "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "passengers": 12, "crew": 5,  "cases": 1, "deaths": 1},
    {"country": "Argentina",     "code": "ARG", "passengers": 4,  "crew": 0,  "cases": 1, "deaths": 0},
]

def render_map_panel() -> None:
    st.markdown(
        """
        <div style='border-left: 3px solid #00f5ff; padding-left:15px; margin-bottom:1.5rem;'>
            <h2 style='margin:0; font-size:1rem; letter-spacing:0.1em; color:#ffffff;'>ORBITAL INTELLIGENCE ARRAY</h2>
            <p style='margin:0; font-size:0.6rem; color:#00f5ff; font-family:monospace; font-weight:800;'>HIGH-FIDELITY 3D TELEMETRY // SEARCH ACTIVE</p>
        </div>
        """, unsafe_allow_html=True
    )

    # Fetch Mapbox Token from Streamlit Secrets (DO NOT HARDCODE FOR SECURITY)
    map_js_token = st.secrets.get("MAPBOX_ACCESS_TOKEN", "PUBLIC_TOKEN_REQUIRED")

    # Use a high-performance 3D Globe via Leaflet + GL (bypassing Mapbox token requirements for free use)
    # This provides a React-like experience with 3D terrain and glowing effects.
    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Intelligence Globe</title>
        <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no">
        <link href="https://api.mapbox.com/mapbox-gl-js/v3.1.2/mapbox-gl.css" rel="stylesheet">
        <script src="https://api.mapbox.com/mapbox-gl-js/v3.1.2/mapbox-gl.js"></script>
        <script src="https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-geocoder/v5.0.0/mapbox-gl-geocoder.min.js"></script>
        <link rel="stylesheet" href="https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-geocoder/v5.0.0/mapbox-gl-geocoder.css" type="text/css">
        <style>
            body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; }}
            #map {{ position: absolute; top: 0; bottom: 0; width: 100%; border-radius: 12px; }}
            .mapboxgl-canvas {{ outline: none; }}
            
            /* Custom Glowing Markers */
            .marker {{
                width: 20px; height: 20px;
                border-radius: 50%; border: 2px solid #ffffff;
                box-shadow: 0 0 15px #00f5ff, inset 0 0 10px #00f5ff;
                cursor: pointer;
            }}
            .ship-marker {{
                width: 25px; height: 25px;
                background: #fbbf24; border-radius: 4px;
                border: 2px solid white;
                animation: blink 1.5s infinite;
                box-shadow: 0 0 20px #fbbf24;
            }}
            @keyframes blink {{
                0% {{ opacity: 1; transform: scale(1); }}
                50% {{ opacity: 0.3; transform: scale(0.8); }}
                100% {{ opacity: 1; transform: scale(1); }}
            }}
            
            /* High-tech Geocoder */
            .mapboxgl-ctrl-geocoder {{
                background-color: rgba(13, 27, 42, 0.9) !important;
                border: 1px solid #00f5ff33 !important;
                color: #fff !important;
                box-shadow: none !important;
            }}
            .mapboxgl-ctrl-geocoder--input {{ color: white !important; font-family: monospace !important; }}
        </style>
    </head>
    <body>
    <div id="map"></div>
    <script>
        mapboxgl.accessToken = '{map_js_token}';
        
        const map = new mapboxgl.Map({{
            container: 'map',
            style: 'mapbox://styles/mapbox/dark-v11',
            center: [-20, 15],
            zoom: 1.5,
            projection: 'globe'
        }});

        map.on('style.load', () => {{
            map.setFog({{
                color: 'rgb(10, 20, 35)', // Lower atmosphere
                'high-color': 'rgb(0, 0, 0)', // Upper atmosphere
                'horizon-blend': 0.1, // Atmosphere thickness
                'space-color': 'rgb(0, 0, 0)', // Background color
                'star-intensity': 0.5 // Background star brightness
            }});
        }});

        // Add Geocoder (Search)
        const geocoder = new MapboxGeocoder({{
            accessToken: mapboxgl.accessToken,
            mapboxgl: mapboxgl,
            marker: false,
            placeholder: 'SEARCH VECTOR LOCATIONS...'
        }});
        map.addControl(geocoder, 'top-right');

        // Hotspots
        const hotspots = {json.dumps(HOTSPOTS)};
        hotspots.forEach(h => {{
            const el = document.createElement('div');
            el.className = h.name.includes('HONDIUS') ? 'ship-marker' : 'marker';
            
            new mapboxgl.Marker(el)
                .setLngLat([h.lon, h.lat])
                .setPopup(new mapboxgl.Popup({{ offset: 25 }})
                    .setHTML('<b>' + h.name + '</b><br>CASES: ' + h.cases))
                .addTo(map);
        }});
    </script>
    </body>
    </html>
    """
    
    components.html(map_html, height=600)
    
    st.markdown(
        "<div style='text-align:center; padding:10px;'><p style='color:#475569; font-size:0.5rem; font-family:monospace;'>ORBITAL SENSORS: 3D PROJECTION ACTIVE // ROTATION ENABLED</p></div>",
        unsafe_allow_html=True
    )
