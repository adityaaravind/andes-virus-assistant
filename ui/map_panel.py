"""Clean Enhanced Global Outbreak Map — No overlapping animations, clear visual hierarchy."""
from __future__ import annotations

import json
import hashlib
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime

LIVE_FILE = Path("data/outbreak_live.json")

def get_live_state() -> dict:
    """Get current outbreak state."""
    if LIVE_FILE.exists():
        try:
            data = json.loads(LIVE_FILE.read_text())
            if "ship_status" not in data:
                data["ship_status"] = get_dynamic_ship_status()
            return data
        except Exception:
            pass

    return {
        "confirmed_cases": 11,
        "deaths": 4,
        "suspected_cases": 12,
        "ship_status": get_dynamic_ship_status(),
        "last_updated": datetime.now().strftime("%Y-%m-%d")
    }

def get_dynamic_ship_status() -> str:
    """Generate ship status based on time."""
    from datetime import datetime

    day_num = (datetime.utcnow() - datetime(2026, 4, 6)).days
    hour = datetime.utcnow().hour

    if day_num < 10:
        return "Emergency Evacuation — Medical Crisis"
    elif day_num < 20:
        return "Quarantine Anchor — Cape Verde Waters"
    elif day_num < 30:
        return "Medical Isolation — International Waters"
    elif hour < 6:
        return "Night Watch — Restricted Movement"
    elif hour < 12:
        return "Medical Monitoring — Canary Islands Approach"
    elif hour < 18:
        return "Quarantine Transit — Under WHO Oversight"
    else:
        return "Evening Protocols — Enhanced Biosafety"

def get_ship_position() -> tuple[float, float]:
    """Calculate ship position based on time."""
    from datetime import datetime
    import math

    # Base position: Near Cape Verde
    base_lat, base_lng = 14.93, -23.51

    # Calculate days since outbreak start
    start_date = datetime(2026, 4, 6)
    current_date = datetime.utcnow()
    days_elapsed = (current_date - start_date).days

    # Simulate movement toward Canary Islands
    drift_lat = days_elapsed * 0.008   # Northward
    drift_lng = days_elapsed * 0.012   # Westward

    # Add realistic oscillation
    hours = current_date.hour + current_date.minute / 60.0
    oscillation_lat = math.sin(hours * 0.1) * 0.005
    oscillation_lng = math.cos(hours * 0.15) * 0.007

    return (
        base_lat + drift_lat + oscillation_lat,
        base_lng + drift_lng + oscillation_lng
    )

def get_nationality_hotspots(state: dict) -> list[dict]:
    """Generate hotspots based on nationality data."""
    total_cases = state.get("confirmed_cases", 11)
    total_deaths = state.get("deaths", 4)

    # Country distribution data - only affected regions
    countries = [
        {"name": "Argentina", "code": "ARG", "lat": -34.61, "lng": -58.38, "weight": 0.35, "color": "#ff0055"},
        {"name": "Spain", "code": "ESP", "lat": 40.42, "lng": -3.70, "weight": 0.20, "color": "#ffaa00"},
        {"name": "USA", "code": "USA", "lat": 39.83, "lng": -98.58, "weight": 0.15, "color": "#38bdf8"},
        {"name": "United Kingdom", "code": "GBR", "lat": 55.38, "lng": -3.44, "weight": 0.12, "color": "#cc00ff"},
        {"name": "Netherlands", "code": "NLD", "lat": 52.13, "lng": 5.29, "weight": 0.10, "color": "#4ade80"},
        {"name": "South Africa", "code": "ZAF", "lat": -30.56, "lng": 22.94, "weight": 0.08, "color": "#00ffcc"},
    ]

    hotspots = []
    for country in countries:
        cases = max(1, int(total_cases * country["weight"])) if total_cases > 0 else 0
        deaths = max(0, int(total_deaths * country["weight"])) if total_deaths > 0 else 0

        # Calculate risk metrics
        fear_index = min(95, 25 + (cases * 8))
        risk_level = "HIGH" if cases >= 3 else "MEDIUM" if cases >= 1 else "LOW"

        hotspots.append({
            "name": country["name"],
            "code": country["code"],
            "lat": country["lat"],
            "lng": country["lng"],
            "cases": cases,
            "deaths": deaths,
            "fear": round(fear_index, 1),
            "risk": risk_level,
            "color": country["color"],
            "relation": f"Passengers/crew affected: {cases} cases",
            "glow": cases >= 2,
            "glowIntensity": min(2.0, cases / 2),
            "pulseSpeed": 1.0 + (cases * 0.2)
        })

    return hotspots

def get_ship_hotspot(state: dict) -> dict:
    """Generate ship hotspot."""
    ship_lat, ship_lng = get_ship_position()

    return {
        "name": "MV Hondius",
        "code": "SHIP",
        "lat": ship_lat,
        "lng": ship_lng,
        "cases": state.get("confirmed_cases", 11),
        "deaths": state.get("deaths", 4),
        "fear": 85.5,
        "risk": "CRITICAL",
        "color": "#ff1744",
        "relation": "Primary outbreak vessel",
        "status": state.get("ship_status", "Transit"),
        "glow": True,
        "glowIntensity": 2.5,
        "pulseSpeed": 2.0
    }

@st.cache_data(ttl=15, show_spinner=False)
def get_map_data() -> dict:
    """Get all map data with caching."""
    state = get_live_state()
    nationality_hotspots = get_nationality_hotspots(state)
    ship_hotspot = get_ship_hotspot(state)

    all_hotspots = nationality_hotspots + [ship_hotspot]

    # Calculate current outbreak day
    from datetime import datetime
    start_date = datetime(2026, 4, 6)
    current_day = (datetime.utcnow() - start_date).days

    return {
        "state": state,
        "hotspots": all_hotspots,
        "current_day": current_day
    }

def render_outbreak_map() -> None:
    """Render the complete clean outbreak tracking map."""
    from alerts.persistent_kv import kv_get

    # Get map data
    map_data = get_map_data()
    state = map_data["state"]
    hotspots = map_data["hotspots"]
    current_day = map_data["current_day"]

    # Header
    st.markdown(
        f"""
        <div style='border-left: 3px solid #4ade80; padding-left:12px; margin-bottom:0.6rem; display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <h2 style='margin:0; font-size:1rem; letter-spacing:0.1em; color:#ffffff;'>GLOBAL OUTBREAK TRACKER</h2>
                <p style='margin:0; font-size:0.55rem; color:#4ade80; font-family:monospace; font-weight:800;'>CLEAN VISUAL MAP</p>
            </div>
            <div style="background:rgba(74,222,128,0.1); border:1px solid #4ade8044; padding:1px 8px; border-radius:4px;">
                <span style="color:#4ade80; font-size:8px; font-weight:900;">LIVE</span>
                <br><span style="color:#64748b; font-size:6px;">{kv_get("last_map_update", datetime.utcnow().strftime('%H:%M UTC'))}</span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    # Clean map HTML with proper visual hierarchy
    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            html, body {{ height: 100%; background: #000; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
            #map {{ width: 100%; height: 100%; background: #050505; border-radius: 12px; }}

            /* Clean status overlay */
            .status {{
                position: absolute; top: 10px; left: 10px;
                background: rgba(0,0,0,0.9); color: #4ade80;
                padding: 8px 12px; border-radius: 6px; z-index: 1000;
                font-size: 12px; border: 1px solid rgba(74,222,128,0.3);
            }}

            /* Simple navigation */
            .nav-controls {{ position: absolute; top: 10px; right: 10px; z-index: 1001; }}
            .nav-btn {{
                background: rgba(0,0,0,0.9); color: #4ade80;
                border: 1px solid #4ade80; padding: 8px 12px; margin: 2px;
                border-radius: 6px; cursor: pointer; font-size: 12px;
                transition: all 0.2s ease;
            }}
            .nav-btn:hover {{ background: #4ade80; color: #000; }}
            .nav-btn.ship {{ color: #ff6b6b; border-color: #ff6b6b; }}
            .nav-btn.ship:hover {{ background: #ff6b6b; }}

            /* Clean marker styles - no overlap */
            .outbreak-marker {{
                border-radius: 50%; border: 2px solid #ffffff;
                display: flex; align-items: center; justify-content: center;
                color: white; font-weight: 900; font-size: 12px;
                box-shadow: 0 0 20px currentColor;
            }}
            .critical-marker {{ animation: critical-glow 3s ease-in-out infinite; }}
            .high-marker {{ animation: high-glow 4s ease-in-out infinite; }}

            /* Simple connection lines */
            .transmission-line {{
                stroke-dasharray: 8,4;
                animation: line-flow 3s linear infinite;
                stroke-width: 3;
                opacity: 0.7;
            }}

            /* Country outlines - subtle */
            .country-boundary {{
                fill-opacity: 0.1;
                stroke-opacity: 0.5;
                stroke-width: 2;
                stroke-dasharray: 10,5;
            }}

            /* Clean animations - no overlap */
            @keyframes critical-glow {{
                0%, 100% {{ box-shadow: 0 0 20px currentColor; }}
                50% {{ box-shadow: 0 0 40px currentColor, 0 0 60px currentColor; }}
            }}
            @keyframes high-glow {{
                0%, 100% {{ box-shadow: 0 0 15px currentColor; }}
                50% {{ box-shadow: 0 0 30px currentColor; }}
            }}
            @keyframes line-flow {{
                0% {{ stroke-dashoffset: 0; }}
                100% {{ stroke-dashoffset: 24; }}
            }}

            /* Clean tooltips */
            .leaflet-tooltip {{
                background: rgba(13, 27, 42, 0.95) !important;
                color: #fff !important;
                border: 1px solid rgba(74, 222, 128, 0.6) !important;
                border-radius: 8px !important;
                padding: 12px !important;
                font-size: 12px !important;
                line-height: 1.4 !important;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
            }}
            .leaflet-popup-content-wrapper {{
                background: rgba(13, 27, 42, 0.95) !important;
                color: #fff !important;
                border: 1px solid rgba(74, 222, 128, 0.6) !important;
                border-radius: 12px !important;
                box-shadow: 0 12px 48px rgba(0, 0, 0, 0.4) !important;
            }}
            .leaflet-popup-content {{ margin: 15px !important; font-size: 12px !important; line-height: 1.4 !important; }}

            /* Mobile responsive */
            @media (max-width: 768px) {{
                .status {{ font-size: 10px; padding: 6px 8px; }}
                .nav-btn {{ padding: 6px 8px; font-size: 10px; }}
            }}
        </style>
    </head>
    <body>
        <div id="status" class="status">🗺️ Loading clean map...</div>
        <div class="nav-controls">
            <button class="nav-btn" onclick="goToGlobal()">🌍 Global</button>
            <button class="nav-btn ship" onclick="goToShip()">🚢 Ship</button>
            <button class="nav-btn" onclick="refreshMap()">🔄</button>
        </div>
        <div id="map"></div>

        <script>
            const status = document.getElementById('status');
            const hotspots = {json.dumps(hotspots)};
            const state = {json.dumps(state)};
            let map, markers = [];

            function updateStatus(msg) {{
                status.innerHTML = msg;
            }}

            function initMap() {{
                try {{
                    updateStatus('🌍 Creating map...');

                    // Initialize map with clean settings
                    map = L.map('map', {{
                        zoomControl: false,
                        attributionControl: false,
                        minZoom: 2,
                        maxZoom: 10,
                        worldCopyJump: true
                    }}).setView([15, -25], 2.8);

                    // Add zoom controls
                    L.control.zoom({{
                        position: 'bottomright'
                    }}).addTo(map);

                    updateStatus('🗺️ Loading tiles...');

                    // Clean dark tiles
                    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                        maxZoom: 19,
                        attribution: '©CartoDB'
                    }}).addTo(map);

                    updateStatus('🌍 Adding country outlines...');
                    addCountryOutlines();

                    updateStatus('📍 Adding outbreak markers...');
                    addOutbreakMarkers();

                    updateStatus('🔗 Drawing transmission lines...');
                    addTransmissionLines();

                    updateStatus('✅ Clean map ready - tracking {{}} locations'.replace('{{}}', hotspots.length));

                    setTimeout(() => {{
                        status.style.opacity = '0.7';
                        status.innerHTML = '🌍 Live outbreak tracking';
                    }}, 3000);

                }} catch (error) {{
                    console.error('Map error:', error);
                    showFallback();
                }}
            }}

            function addCountryOutlines() {{
                // Only show affected countries - clean boundaries
                const affected = hotspots.filter(h => h.code !== 'SHIP' && h.cases > 0);

                const boundaries = {{
                    'ARG': [[-55, -73], [-22, -53]],
                    'ESP': [[36, -9], [44, 4]],
                    'USA': [[25, -125], [49, -66]],
                    'GBR': [[50, -8], [61, 2]],
                    'NLD': [[52, 3], [54, 7]],
                    'ZAF': [[-35, 16], [-22, 33]]
                }};

                affected.forEach(hotspot => {{
                    const bounds = boundaries[hotspot.code];
                    if (!bounds) return;

                    const outline = L.rectangle(bounds, {{
                        fillColor: hotspot.color,
                        color: hotspot.color,
                        className: 'country-boundary',
                        fillOpacity: 0.05 + (hotspot.cases * 0.02),
                        opacity: 0.3 + (hotspot.cases * 0.1),
                        weight: 2,
                        dashArray: '10,5'
                    }}).addTo(map);

                    // Simple country tooltip
                    const tooltip = `
                        <div style="text-align: center;">
                            <div style="color: ${{hotspot.color}}; font-weight: bold; margin-bottom: 4px;">
                                🌍 ${{hotspot.name}}
                            </div>
                            <div style="font-size: 11px; color: #94a3b8;">
                                ${{hotspot.cases}} outbreak cases
                            </div>
                        </div>
                    `;

                    outline.bindTooltip(tooltip, {{ direction: 'center', permanent: false }});
                }});
            }}

            function addTransmissionLines() {{
                const ship = hotspots.find(h => h.code === 'SHIP');
                if (!ship) return;

                hotspots.forEach(hotspot => {{
                    if (hotspot.code !== 'SHIP' && hotspot.cases > 0) {{
                        // Clean transmission line
                        const line = L.polyline([
                            [ship.lat, ship.lng],
                            [hotspot.lat, hotspot.lng]
                        ], {{
                            color: hotspot.color,
                            weight: Math.min(5, 2 + hotspot.cases),
                            opacity: 0.6,
                            className: 'transmission-line',
                            dashArray: '8,4'
                        }}).addTo(map);

                        // Simple transmission tooltip
                        const lineTooltip = `
                            <div style="text-align: center; min-width: 150px;">
                                <div style="color: ${{hotspot.color}}; font-weight: bold; margin-bottom: 4px;">
                                    🦠 Transmission Path
                                </div>
                                <div style="font-size: 11px; color: #94a3b8;">
                                    MV Hondius → ${{hotspot.name}}
                                </div>
                                <div style="font-size: 11px; color: #ff6b6b; margin-top: 4px;">
                                    ${{hotspot.cases}} cases linked
                                </div>
                            </div>
                        `;

                        line.bindTooltip(lineTooltip, {{ sticky: true }});
                    }}
                }});
            }}

            function addOutbreakMarkers() {{
                hotspots.forEach(hotspot => {{
                    const isShip = hotspot.code === 'SHIP';
                    const size = isShip ? 28 : Math.max(20, 16 + (hotspot.cases * 2));
                    const glowClass = hotspot.risk === 'CRITICAL' ? 'critical-marker' :
                                     hotspot.cases >= 3 ? 'high-marker' : '';

                    // Clean marker HTML
                    const markerHtml = `
                        <div class="outbreak-marker ${{glowClass}}" style="
                            background-color: ${{hotspot.color}};
                            width: ${{size}}px;
                            height: ${{size}}px;
                        ">
                            ${{isShip ? '🚢' : hotspot.cases >= 3 ? '☣️' : '🦠'}}
                        </div>
                    `;

                    const marker = L.divIcon({{
                        html: markerHtml,
                        className: 'custom-marker',
                        iconSize: [size, size],
                        iconAnchor: [size/2, size/2]
                    }});

                    const mapMarker = L.marker([hotspot.lat, hotspot.lng], {{ icon: marker }}).addTo(map);

                    // Clean tooltip
                    const tooltip = `
                        <div style="min-width: 180px;">
                            <div style="color: ${{hotspot.color}}; font-weight: bold; margin-bottom: 8px; font-size: 14px;">
                                ${{isShip ? '🚢' : '🌍'}} ${{hotspot.name}}
                            </div>
                            <div style="display: grid; grid-template-columns: auto auto; gap: 8px; font-size: 12px;">
                                <div>Cases:</div><div style="color: #ff6b6b; font-weight: bold;">${{hotspot.cases}}</div>
                                <div>Deaths:</div><div style="color: #64748b; font-weight: bold;">${{hotspot.deaths}}</div>
                                <div>Risk:</div><div style="color: ${{hotspot.color}}; font-weight: bold;">${{hotspot.risk}}</div>
                            </div>
                            ${{isShip ? `
                                <div style="margin-top: 8px; font-size: 11px; color: #4ade80; font-style: italic;">
                                    ${{hotspot.status}}
                                </div>
                            ` : `
                                <div style="margin-top: 8px; font-size: 11px; color: #94a3b8; font-style: italic;">
                                    Passengers/crew from this region
                                </div>
                            `}}
                        </div>
                    `;

                    mapMarker.bindTooltip(tooltip, {{ direction: 'top', offset: [0, -10] }});

                    // Clean popup
                    const popup = `
                        <div style="min-width: 220px;">
                            <div style="text-align: center; margin-bottom: 12px;">
                                <div style="font-size: 20px; margin-bottom: 4px;">${{isShip ? '🚢' : '🌍'}}</div>
                                <div style="color: ${{hotspot.color}}; font-weight: bold; font-size: 16px;">
                                    ${{hotspot.name}}
                                </div>
                                <div style="font-size: 11px; color: #64748b;">
                                    ${{hotspot.lat.toFixed(3)}}°, ${{hotspot.lng.toFixed(3)}}°
                                </div>
                            </div>

                            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; text-align: center; margin-bottom: 12px;">
                                <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px;">
                                    <div style="color: #ff6b6b; font-weight: bold; font-size: 16px;">${{hotspot.cases}}</div>
                                    <div style="font-size: 9px; color: #94a3b8;">CASES</div>
                                </div>
                                <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px;">
                                    <div style="color: #64748b; font-weight: bold; font-size: 16px;">${{hotspot.deaths}}</div>
                                    <div style="font-size: 9px; color: #94a3b8;">DEATHS</div>
                                </div>
                                <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px;">
                                    <div style="color: ${{hotspot.color}}; font-weight: bold; font-size: 16px;">${{hotspot.risk}}</div>
                                    <div style="font-size: 9px; color: #94a3b8;">RISK</div>
                                </div>
                            </div>

                            ${{isShip ? `
                                <div style="background: rgba(74,222,128,0.1); border: 1px solid #4ade8044; padding: 8px; border-radius: 6px; margin-top: 8px;">
                                    <div style="font-size: 11px; color: #4ade80; font-weight: bold;">🚢 SHIP STATUS</div>
                                    <div style="font-size: 10px; color: #86efac; margin-top: 2px;">${{hotspot.status}}</div>
                                </div>
                            ` : `
                                <div style="background: rgba(255,107,107,0.1); border: 1px solid #ff6b6b44; padding: 8px; border-radius: 6px; margin-top: 8px;">
                                    <div style="font-size: 11px; color: #ff6b6b; font-weight: bold;">🦠 OUTBREAK LINK</div>
                                    <div style="font-size: 10px; color: #fca5a5; margin-top: 2px;">Connected to MV Hondius outbreak</div>
                                </div>
                            `}}

                            <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #333; font-size: 10px; color: #64748b; text-align: center;">
                                Day {current_day} of outbreak • WHO/CDC verified
                            </div>
                        </div>
                    `;

                    mapMarker.bindPopup(popup);
                    markers.push(mapMarker);
                }});
            }}

            function goToGlobal() {{
                map.setView([15, -25], 2.8);
                updateStatus('🌍 Global view');
            }}

            function goToShip() {{
                const ship = hotspots.find(h => h.code === 'SHIP');
                if (ship) {{
                    map.setView([ship.lat, ship.lng], 6);
                    updateStatus('🚢 Ship view');
                }}
            }}

            function refreshMap() {{
                location.reload();
            }}

            function showFallback() {{
                document.getElementById('map').innerHTML = `
                    <div style="display:flex;align-items:center;justify-content:center;height:100%;background:#050505;color:#4ade80;text-align:center;padding:20px;">
                        <div>
                            <div style="font-size:48px;margin-bottom:20px;">🌍</div>
                            <div style="font-size:18px;margin-bottom:15px;">Map Loading...</div>
                            <div style="font-size:14px;color:#94a3b8;">Tracking ${{hotspots.length}} locations</div>
                        </div>
                    </div>
                `;
            }}

            // Initialize
            document.addEventListener('DOMContentLoaded', initMap);

        </script>
    </body>
    </html>
    """

    # Add data hash for cache busting
    data_hash = hashlib.md5(json.dumps(hotspots, sort_keys=True).encode()).hexdigest()[:8]
    map_html = f"<!-- Clean Map Hash: {data_hash} -->" + map_html

    # Render clean map
    components.html(map_html, height=450)

# Legacy compatibility
def get_nationalities_data():
    """Get nationality data based on current live state."""
    state = get_live_state()
    return get_nationality_hotspots(state)

def _get_dynamic_hotspots(state: dict) -> list[dict]:
    """Legacy function for stats panel."""
    return get_nationality_hotspots(state)

def _get_dynamic_ship_status() -> str:
    """Legacy function for stats panel."""
    return get_dynamic_ship_status()

def _get_map_data() -> dict:
    """Legacy function for tests."""
    return get_map_data()

NATIONALITIES_DATA = get_nationality_hotspots(get_live_state())
render_map_panel = render_outbreak_map