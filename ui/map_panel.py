"""Terria-Lite Intelligence Console — Professional Data Workbench UI."""
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

def _get_live_state() -> dict:
    if LIVE_FILE.exists():
        try: return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {"confirmed_cases": 5, "ship_status": "Transit"}

def render_map_panel() -> None:
    state = _get_live_state()
    
    # ── CONSOLE HEADER ──
    st.markdown(
        f"""
        <div style='display:flex; justify-content:space-between; align-items:center; background:#0d1b2a; border:1px solid #1b2e45; padding:8px 20px; border-radius:8px 8px 0 0;'>
            <div style="display:flex; align-items:center; gap:15px;">
                <h2 style='margin:0; font-size:0.9rem; letter-spacing:0.1em; color:#ffffff;'>TERRIA_LITE // INTEL WORKBENCH</h2>
                <span style="color:#22c55e; font-size:0.6rem; font-weight:900; background:rgba(34,197,94,0.1); padding:2px 8px; border-radius:4px; border:1px solid #22c55e44;">v4.2_STABLE</span>
            </div>
            <div style="color:#94a3b8; font-family:monospace; font-size:0.65rem;">MISSION_TIME: {datetime.now().strftime('%H:%M:%S')} UTC</div>
        </div>
        """, unsafe_allow_html=True
    )

    # ── THE TERRIA-LITE CORE ──
    # Implements a 3-panel architecture: [Catalog] [Map] [FeatureInfo]
    terria_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://cesium.com/downloads/cesiumjs/releases/1.114/Build/Cesium/Cesium.js"></script>
        <link href="https://cesium.com/downloads/cesiumjs/releases/1.114/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
        <style>
            html, body {{ margin: 0; padding: 0; height: 100%; width: 100%; background: #000; font-family: 'Inter', sans-serif; color: white; overflow: hidden; }}
            #main-layout {{ display: flex; height: 100%; width: 100%; }}
            
            /* 1. DATA CATALOG (LEFT) */
            #catalog {{ width: 220px; background: #0a111a; border-right: 1px solid #1b2e45; display: flex; flex-direction: column; }}
            .panel-header {{ padding: 12px; font-size: 10px; font-weight: 900; color: #64748b; text-transform: uppercase; border-bottom: 1px solid #1b2e45; }}
            .catalog-item {{ padding: 10px 15px; font-size: 11px; color: #cbd5e1; border-bottom: 1px solid #111; cursor: pointer; display: flex; justify-content: space-between; }}
            .catalog-item:hover {{ background: #1b2e45; }}
            .badge-active {{ background: #22c55e; width: 6px; height: 6px; border-radius: 50%; align-self: center; }}
            
            /* 2. MAP (CENTER) */
            #map-container {{ flex: 1; position: relative; }}
            #cesiumContainer {{ width: 100%; height: 100%; }}
            
            /* 3. FEATURE INFO (RIGHT) */
            #feature-info {{ width: 260px; background: rgba(10, 17, 26, 0.95); border-left: 1px solid #1b2e45; padding: 15px; display: none; overflow-y: auto; }}
            .info-title {{ color: #00f5ff; font-weight: 900; font-size: 13px; margin-bottom: 10px; }}
            .info-stat {{ background: rgba(255,255,255,0.03); padding: 8px; border-radius: 4px; margin-bottom: 10px; }}
            .stat-label {{ color: #64748b; font-size: 9px; }}
            .stat-val {{ color: #fff; font-size: 14px; font-weight: 900; }}
            
            /* 4. WORKBENCH OVERLAYS */
            .map-controls {{ position: absolute; top: 20px; right: 20px; z-index: 10; display: flex; flex-direction: column; gap: 8px; }}
            .ctrl-btn {{ background: rgba(13, 27, 42, 0.9); border: 1px solid #333; color: white; padding: 6px 12px; border-radius: 4px; font-size: 10px; cursor: pointer; }}
            .ctrl-btn:hover {{ border-color: #00f5ff; }}
            
            #timeline {{ position: absolute; bottom: 0; left: 220px; right: 260px; height: 40px; background: rgba(10, 17, 26, 0.8); border-top: 1px solid #1b2e45; padding: 5px 20px; display: flex; align-items: center; gap: 15px; }}
        </style>
    </head>
    <body>
    <div id="main-layout">
        <div id="catalog">
            <div class="panel-header">Tactical Catalog</div>
            <div class="catalog-item"><span>Satellite Imagery</span><div class="badge-active"></div></div>
            <div class="catalog-item"><span>Outbreak Hotspots</span><div class="badge-active"></div></div>
            <div class="catalog-item"><span>Vessel Tracking</span><div class="badge-active"></div></div>
            <div class="catalog-item" style="opacity: 0.4;"><span>Global Terrain</span></div>
            <div class="catalog-item" style="opacity: 0.4;"><span>Population Density</span></div>
            
            <div class="panel-header" style="margin-top:auto;">My Workbench</div>
            <div style="padding:12px; font-size:10px; color:#475569;">3 items active in current view</div>
        </div>
        
        <div id="map-container">
            <div class="map-controls">
                <button class="ctrl-btn" onclick="toggle3D()">2D / 3D</button>
                <button class="ctrl-btn">SATELLITE</button>
            </div>
            <div id="cesiumContainer"></div>
            <div id="timeline">
                <div style="color:#00f5ff; font-weight:900; font-size:9px;">TIMELINE</div>
                <div style="flex:1; height:2px; background:#1b2e45; position:relative;">
                    <div style="position:absolute; left:40%; width:12px; height:12px; background:#00f5ff; border-radius:50%; top:-5px; box-shadow:0 0 10px #00f5ff;"></div>
                </div>
                <div style="color:#64748b; font-size:9px;">APR 01 — MAY 10</div>
            </div>
        </div>
        
        <div id="feature-info">
            <div class="info-title" id="info-name">Feature Report</div>
            <div class="info-stat">
                <div class="stat-label">LOCK STATUS</div>
                <div class="stat-val" style="color:#22c55e;">POSITIVE</div>
            </div>
            <div class="info-stat" id="cases-box">
                <div class="stat-label">DETECTED VECTORS</div>
                <div class="stat-val" id="info-cases">--</div>
            </div>
            <div style="font-size:11px; line-height:1.4; color:#94a3b8; border-top:1px solid #222; padding-top:10px;" id="info-desc">
                Select a signal on the map for deep-field OSINT intelligence.
            </div>
        </div>
    </div>

    <script>
        const viewer = new Cesium.Viewer('cesiumContainer', {{
            imageryProvider: new Cesium.OpenStreetMapImageryProvider({{
                url : 'https://a.tile.openstreetmap.org/'
            }}),
            baseLayerPicker: false, geocoder: false, homeButton: false, infoBox: false, selectionIndicator: true, timeline: false, animation: false,
        }});
        
        viewer.scene.skyBox.show = true;
        viewer.scene.sun.show = false;
        
        const hotspots = [
            {{lat: -34.6, lon: -58.38, name: 'BETA_CLUSTER', cases: 4, desc: 'Argentina (Ushuaia) - Original departure point for MV HONDIUS. Port screening active.'}},
            {{lat: -26.2, lon: 28.04,  name: 'ALPHA_CLUSTER', cases: 2, desc: 'South Africa (Johannesburg) - Critical evacuation site for infected crew.'}},
            {{lat: 14.93, lon: -23.51, name: 'MV_HONDIUS_CORE', cases: 5, desc: 'Primary Vector. Moored in Cabo Verde under military-grade quarantine hold.'}}
        ];

        hotspots.forEach(h => {{
            const color = h.name.includes('HONDIUS') ? Cesium.Color.GOLD : Cesium.Color.RED;
            const entity = viewer.entities.add({{
                position: Cesium.Cartesian3.fromDegrees(h.lon, h.lat),
                point: {{ pixelSize: 10, color: color, outlineColor: Cesium.Color.WHITE, outlineWidth: 2 }},
                name: h.name,
                customData: h
            }});
        }});

        // Handle Feature Info Panel
        const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
        handler.setInputAction(function(movement) {{
            const picked = viewer.scene.pick(movement.position);
            if (Cesium.defined(picked)) {{
                const data = picked.id.customData;
                document.getElementById('feature-info').style.display = 'block';
                document.getElementById('info-name').innerText = data.name;
                document.getElementById('info-cases').innerText = data.cases + ' CONFIRMED';
                document.getElementById('info-desc').innerText = data.desc;
            }} else {{
                document.getElementById('feature-info').style.display = 'none';
            }}
        }}, Cesium.ScreenSpaceEventType.LEFT_CLICK);

        function toggle3D() {{
            if (viewer.scene.mode === Cesium.SceneMode.SCENE3D) {{
                viewer.scene.mode = Cesium.SceneMode.SCENE2D;
            }} else {{
                viewer.scene.mode = Cesium.SceneMode.SCENE3D;
            }}
        }}

        viewer.camera.flyTo({{
            destination: Cesium.Cartesian3.fromDegrees(-20, 10, 15000000.0),
            duration: 0
        }});
    </script>
    </body>
    </html>
    """
    
    components.html(terria_html, height=650)
    
    st.markdown(
        "<div style='background:#0d1b2a; border:1px solid #1b2e45; border-top:none; padding:8px 20px; border-radius:0 0 8px 8px; text-align:right;'>"
        "<p style='margin:0; font-size:0.5rem; color:#475569; font-family:monospace;'>DATA_PROVIDER: TERRIA_LITE_CORE // OSINT_STAGING_MODE: ACTIVE</p></div>",
        unsafe_allow_html=True
    )
