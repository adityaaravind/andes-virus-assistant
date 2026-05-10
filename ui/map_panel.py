"""Three-Tile Intelligence Globe — Lightweight high-performance 3D dashboard."""
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
                <h2 style='margin:0; font-size:0.9rem; letter-spacing:0.12em; color:#ffffff;'>THREE_TILE // ORBITAL ARRAY</h2>
                <span style="color:#00f5ff; font-size:0.6rem; font-weight:900; background:rgba(0,245,255,0.1); padding:2px 8px; border-radius:4px; border:1px solid #00f5ff44;">LIGHTWEIGHT_3D</span>
            </div>
            <div style="color:#94a3b8; font-family:monospace; font-size:0.65rem;">MISSION_TIME: {datetime.now().strftime('%H:%M:%S')} UTC</div>
        </div>
        """, unsafe_allow_html=True
    )

    # ── THE THREE-TILE CORE ──
    # Uses Three-Tile for high-performance 3D map tile rendering in Three.js
    three_tile_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>Three-Tile Intel</title>
        <style>
            body {{ margin: 0; padding: 0; background: #000; overflow: hidden; font-family: 'Inter', sans-serif; }}
            #container {{ width: 100%; height: 100vh; position: relative; }}
            #ui-overlay {{
                position: absolute; top: 20px; left: 20px; z-index: 10;
                background: rgba(13, 27, 42, 0.85); border: 1px solid #1b2e45;
                border-radius: 8px; padding: 15px; min-width: 220px; pointer-events: none;
            }}
            .ui-label {{ color: #64748b; font-size: 10px; font-weight: 900; margin-bottom: 5px; }}
            .ui-value {{ color: #ffffff; font-size: 14px; font-weight: 900; margin-bottom: 10px; }}
            .blink-dot {{
                width: 8px; height: 8px; background: #fbbf24; border-radius: 50%;
                display: inline-block; margin-right: 8px;
                box-shadow: 0 0 10px #fbbf24;
                animation: blink 1.5s infinite;
            }}
            @keyframes blink {{ 50% {{ opacity: 0.2; }} }}
        </style>
        <script type="importmap">
            {{
                "imports": {{
                    "three": "https://unpkg.com/three@0.165.0/build/three.module.js",
                    "three/addons/": "https://unpkg.com/three@0.165.0/examples/jsm/",
                    "three-tile": "https://unpkg.com/three-tile@0.7.0/dist/three-tile.module.js"
                }}
            }}
        </script>
    </head>
    <body>
    <div id="container">
        <div id="ui-overlay">
            <div class="ui-label">🛰️ SATELLITE TRACKING</div>
            <div class="ui-value"><span class="blink-dot"></span>MV HONDIUS</div>
            <div style="color:#48cae4; font-size:11px; font-family:monospace;">LAT: 14.93N / LON: 23.51W</div>
            <div style="height:1px; background:rgba(255,255,255,0.1); margin:10px 0;"></div>
            <div class="ui-label">VESSEL STATUS</div>
            <div style="color:#22c55e; font-size:11px; font-weight:900;">{state.get('ship_status', 'In Transit').upper()}</div>
        </div>
    </div>

    <script type="module">
        import * as THREE from 'three';
        import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
        import {{ TileMap }} from 'three-tile';

        // 1. Scene Setup
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 10000);
        const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        document.getElementById('container').appendChild(renderer.domElement);

        // 2. Light Setup
        const ambientLight = new THREE.AmbientLight(0xffffff, 1.5);
        scene.add(ambientLight);

        // 3. Tile Map Setup (Three-Tile)
        // Using CartoDB Dark Matter tiles for the tactical look
        const map = new TileMap({{
            loader: 'https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',
            subdomains: 'abcd',
        }});
        scene.add(map);

        // 4. Hotspots (Using Three.js native objects)
        const hotspots = [
            {{lat: -34.6, lon: -58.38, name: 'BETA_CLUSTER', color: 0xff4d4d}},
            {{lat: -26.2, lon: 28.04,  name: 'ALPHA_CLUSTER', color: 0xff4d4d}},
            {{lat: 14.93, lon: -23.51, name: 'MV_HONDIUS', color: 0xfbbf24}}
        ];

        hotspots.forEach(h => {{
            const geom = new THREE.SphereGeometry(100, 16, 16);
            const mat = new THREE.MeshBasicMaterial({{ color: h.color, transparent: true, opacity: 0.8 }});
            const sphere = new THREE.Mesh(geom, mat);
            
            // Map lat/lon to Three-Tile coordinates (simplistic for this example)
            // Three-Tile handles projection, but for a 3D globe we'd use a sphere model.
            // This example uses a flat 3D plane which three-tile excels at.
            const pos = map.geo2pos(new THREE.Vector3(h.lon, h.lat, 0));
            sphere.position.copy(pos);
            sphere.position.z = 50; // Elevate slightly
            scene.add(sphere);

            // Add glowing ring
            const rGeom = new THREE.RingGeometry(150, 200, 32);
            const rMat = new THREE.MeshBasicMaterial({{ color: h.color, side: THREE.DoubleSide, transparent: true, opacity: 0.4 }});
            const ring = new THREE.Mesh(rGeom, rMat);
            ring.position.copy(pos);
            ring.position.z = 40;
            scene.add(ring);
        }});

        // 5. Controls
        const controls = new OrbitControls(camera, renderer.domElement);
        camera.position.set(0, -1000, 2000);
        controls.update();

        // 6. Render Loop
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();

        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});

    </script>
    </body>
    </html>
    """
    
    components.html(three_tile_html, height=650)
    
    st.markdown(
        "<div style='background:#0d1b2a; border:1px solid #1b2e45; border-top:none; padding:8px 20px; border-radius:0 0 8px 8px; text-align:right;'>"
        "<p style='margin:0; font-size:0.5rem; color:#475569; font-family:monospace;'>ENGINE: THREE_TILE_v0.7 // TACTICAL_3D: ENABLED // OSINT_STREAMS: SYNCED</p></div>",
        unsafe_allow_html=True
    )
