"""CesiumJS 3D Intelligence Globe — professional-grade orbital tracking."""
from __future__ import annotations

import json
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

LIVE_FILE = Path("data/outbreak_live.json")

# Core Telemetry
HOTSPOTS = [
    {"lat": -34.60, "lon": -58.38, "cases": 3, "name": "ARGENTINA_CLUSTER", "type": "local"},
    {"lat": -26.20, "lon": 28.04,  "cases": 2, "name": "ZA_EVAC_SITE", "type": "local"},
    {"lat": 14.93,  "lon": -23.51, "cases": 5, "name": "MV_HONDIUS_MOORED", "type": "vessel"},
    {"lat": 40.41,  "lon": -3.70,  "cases": 2, "name": "ESP_SIGNAL", "type": "imported"},
]

# Compatibility data export
NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "passengers": 27, "crew": 0,  "cases": 2, "deaths": 1},
    {"country": "United Kingdom","code": "GBR", "passengers": 20, "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "passengers": 12, "crew": 5,  "cases": 1, "deaths": 1},
    {"country": "Argentina",     "code": "ARG", "passengers": 4,  "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "South Africa",  "code": "ZAF", "passengers": 0,  "crew": 16, "cases": 0, "deaths": 0},
]

def render_map_panel() -> None:
    st.markdown(
        """
        <div style='border-left: 3px solid #ff4d4d; padding-left:15px; margin-bottom:1.5rem;'>
            <h2 style='margin:0; font-size:1rem; letter-spacing:0.1em; color:#ffffff;'>CESIUM ORBITAL PROJECTION</h2>
            <p style='margin:0; font-size:0.6rem; color:#64748b; font-family:monospace; font-weight:800;'>TACTICAL 3D SENSORS // TOKEN-FREE OSINT INTERFACE</p>
        </div>
        """, unsafe_allow_html=True
    )

    cesium_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <script src="https://cesium.com/downloads/cesiumjs/releases/1.114/Build/Cesium/Cesium.js"></script>
        <link href="https://cesium.com/downloads/cesiumjs/releases/1.114/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
        <style>
            html, body, #cesiumContainer {{
                width: 100%; height: 100%; margin: 0; padding: 0; overflow: hidden;
                background-color: #000;
            }}
            .cesium-viewer-bottom {{ display: none !important; }} /* Hide credits for cleaner UI */
            
            /* Custom CSS for Popup */
            .cesium-infoBox {{
                background: rgba(13, 27, 42, 0.9) !important;
                border: 1px solid #00f5ff !important;
                color: white !important;
            }}
        </style>
    </head>
    <body>
    <div id="cesiumContainer"></div>
    <script>
        // Initialize Cesium with an open-source style (No token required for basic imagery)
        const viewer = new Cesium.Viewer('cesiumContainer', {{
            imageryProvider: new Cesium.OpenStreetMapImageryProvider({{
                url : 'https://a.tile.openstreetmap.org/'
            }}),
            baseLayerPicker: false,
            geocoder: true,
            homeButton: false,
            infoBox: true,
            sceneModePicker: true,
            selectionIndicator: true,
            navigationHelpButton: false,
            timeline: false,
            animation: false,
            scene3DOnly: true,
            skyAtmosphere: new Cesium.SkyAtmosphere(),
        }});

        // High-tech styling: Enable stars and black space
        viewer.scene.skyBox.show = true;
        viewer.scene.sun.show = false;
        viewer.scene.moon.show = false;
        
        const hotspots = {json.dumps(HOTSPOTS)};
        
        hotspots.forEach(h => {{
            const color = h.type === 'vessel' ? Cesium.Color.GOLD : (h.type === 'local' ? Cesium.Color.RED : Cesium.Color.WHITE);
            
            // 1. Core Point
            const entity = viewer.entities.add({{
                position: Cesium.Cartesian3.fromDegrees(h.lon, h.lat),
                point: {{
                    pixelSize: h.type === 'vessel' ? 12 : 8,
                    color: color,
                    outlineColor: Cesium.Color.BLACK,
                    outlineWidth: 2,
                    disableDepthTestDistance: Number.POSITIVE_INFINITY // Always on top
                }},
                name: h.name,
                description: '<b>DETECTED CASES:</b> ' + h.cases + '<br/><b>COORDS:</b> ' + h.lat + ', ' + h.lon
            }});

            // 2. Pulse / Glow Ring
            viewer.entities.add({{
                position: Cesium.Cartesian3.fromDegrees(h.lon, h.lat),
                ellipse: {{
                    semiMinorAxis: 150000.0,
                    semiMajorAxis: 150000.0,
                    material: new Cesium.ColorMaterialProperty(color.withAlpha(0.2)),
                    outline: true,
                    outlineColor: color.withAlpha(0.5),
                    height: 0
                }}
            }});

            if (h.type === 'vessel') {{
                // Blinking effect for vessel via JS Interval
                let visible = true;
                setInterval(() => {{
                    visible = !visible;
                    entity.show = visible;
                }}, 800);
            }}
        }});

        // Set initial view
        viewer.camera.flyTo({{
            destination: Cesium.Cartesian3.fromDegrees(-20, 15, 15000000.0),
            duration: 0
        }});
    </script>
    </body>
    </html>
    """
    
    components.html(cesium_html, height=600)
    
    st.markdown(
        "<div style='text-align:center; padding:10px;'><p style='color:#475569; font-size:0.5rem; font-family:monospace;'>ORBITAL ENGINE: CESIUM_CORE // 3D SATELLITE MODE: ENABLED</p></div>",
        unsafe_allow_html=True
    )
