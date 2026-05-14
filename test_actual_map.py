#!/usr/bin/env python3
"""Test the actual map component from map_panel.py"""

import streamlit as st
import streamlit.components.v1 as components
import json
from ui.map_panel import _get_map_data

st.set_page_config(page_title="Actual Map Test", layout="wide")
st.title("🗺️ Actual Map Component Test")

# Get real map data
try:
    map_data = _get_map_data()
    hotspots = map_data["hotspots"]
    intensity = map_data["intensity"]
    current_day = map_data["current_day"]

    st.success(f"✅ Map data loaded: {len(hotspots)} hotspots, day {current_day}")

    # Show debug info
    with st.expander("Debug Info"):
        st.json({
            "hotspots_count": len(hotspots),
            "current_day": current_day,
            "sample_hotspot": hotspots[0] if hotspots else None
        })

    # Minimal working map template
    minimal_map = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            html, body {{ margin: 0; padding: 0; height: 100%; background: #000; }}
            #map {{ width: 100%; height: 100%; }}
            #status {{ position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.8); color: white; padding: 5px; z-index: 1000; }}
        </style>
    </head>
    <body>
        <div id="status">Loading...</div>
        <div id="map"></div>
        <script>
            const status = document.getElementById('status');

            try {{
                status.innerHTML = 'Initializing map...';

                const map = L.map('map').setView([15, -25], 3);
                status.innerHTML = 'Map created...';

                L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                    attribution: '© CartoDB',
                    maxZoom: 19
                }}).addTo(map);
                status.innerHTML = 'Tiles added...';

                const hotspots = {json.dumps(hotspots)};
                status.innerHTML = `Loading ${{hotspots.length}} hotspots...`;

                hotspots.forEach((h, i) => {{
                    const marker = L.marker([h.lat, h.lng]).addTo(map);
                    marker.bindPopup(`
                        <strong>${{h.name}}</strong><br>
                        Cases: ${{h.cases}}<br>
                        Position: ${{h.lat}}, ${{h.lng}}
                    `);

                    if (i === 0) {{
                        marker.openPopup();
                    }}
                }});

                status.innerHTML = `✅ Map loaded with ${{hotspots.length}} markers`;
                setTimeout(() => status.style.opacity = '0.5', 3000);

            }} catch (e) {{
                status.innerHTML = `❌ Error: ${{e.message}}`;
                status.style.background = 'rgba(255,0,0,0.8)';
            }}
        </script>
    </body>
    </html>
    """

    st.subheader("Simplified Map Test")
    components.html(minimal_map, height=400)

except Exception as e:
    st.error(f"❌ Error loading map data: {e}")
    import traceback
    st.code(traceback.format_exc())