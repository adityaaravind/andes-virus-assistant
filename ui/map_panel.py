"""Enhanced Global Outbreak Map — Real-time tracking with all features rebuilt."""
from __future__ import annotations

import json
import hashlib
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime
import random

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

    # Country distribution data
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
        fear_index = min(95, 25 + random.uniform(0, 40) + (cases * 3))
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
    """Render the complete outbreak tracking map."""
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
                <p style='margin:0; font-size:0.55rem; color:#4ade80; font-family:monospace; font-weight:800;'>REAL-TIME MAP & LOCATIONS</p>
            </div>
            <div style="background:rgba(74,222,128,0.1); border:1px solid #4ade8044; padding:1px 8px; border-radius:4px;">
                <span style="color:#4ade80; font-size:8px; font-weight:900;">LIVE SYNC</span>
                <br><span style="color:#64748b; font-size:6px;">{kv_get("last_map_update", datetime.utcnow().strftime('%H:%M UTC'))}</span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    # Enhanced map HTML with all features
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

            /* Status overlay */
            .status {{ position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.9); color: #4ade80; padding: 8px 12px; border-radius: 6px; z-index: 1000; font-size: 12px; max-width: 280px; border: 1px solid rgba(74,222,128,0.3); }}

            /* Navigation controls */
            .nav-controls {{ position: absolute; top: 10px; right: 10px; z-index: 1001; }}
            .nav-btn {{ background: rgba(0,0,0,0.9); color: #4ade80; border: 1px solid #4ade80; padding: 8px 12px; margin: 2px; border-radius: 6px; cursor: pointer; font-size: 12px; transition: all 0.3s; }}
            .nav-btn:hover {{ background: #4ade80; color: #000; transform: scale(1.05); }}
            .nav-btn.ship {{ color: #ff6b6b; border-color: #ff6b6b; }}
            .nav-btn.ship:hover {{ background: #ff6b6b; }}

            /* Marker styles */
            .marker {{ width: 24px; height: 24px; border-radius: 50%; border: 2px solid #ffffff; position: relative; display: flex; align-items: center; justify-content: center; color: white; font-weight: 900; font-size: 10px; }}
            .marker-glow {{ animation: marker-pulse 2s infinite ease-in-out; box-shadow: 0 0 20px currentColor; }}
            .marker-critical {{ animation: critical-pulse 1s infinite ease-in-out; }}
            .marker-badge {{ position: absolute; top: -8px; right: -8px; background: #ffffff; color: #000; border-radius: 50%; width: 16px; height: 16px; font-size: 8px; font-weight: 900; display: flex; align-items: center; justify-content: center; border: 2px solid currentColor; }}

            /* Animations */
            @keyframes marker-pulse {{
                0%, 100% {{ opacity: 1; transform: scale(1); }}
                50% {{ opacity: 0.7; transform: scale(1.1); }}
            }}
            @keyframes critical-pulse {{
                0%, 100% {{ opacity: 1; transform: scale(1); box-shadow: 0 0 15px currentColor; }}
                50% {{ opacity: 0.6; transform: scale(1.2); box-shadow: 0 0 30px currentColor; }}
            }}

            /* Tooltips and popups */
            .leaflet-tooltip {{ background: rgba(13, 27, 42, 0.98) !important; color: #fff !important; border: 1px solid rgba(74, 222, 128, 0.4) !important; border-radius: 8px !important; padding: 12px !important; font-size: 11px !important; }}
            .leaflet-popup-content-wrapper {{ background: rgba(13, 27, 42, 0.98) !important; color: #fff !important; border: 1px solid rgba(74, 222, 128, 0.4) !important; border-radius: 12px !important; }}
            .leaflet-popup-content {{ margin: 15px !important; font-size: 12px !important; line-height: 1.4 !important; }}

            /* Mobile responsive */
            @media (max-width: 768px) {{
                .status {{ font-size: 10px; padding: 6px 8px; max-width: 200px; top: 5px; left: 5px; }}
                .nav-controls {{ top: 5px; right: 5px; }}
                .nav-btn {{ padding: 6px 8px; font-size: 10px; }}
                .leaflet-popup-content-wrapper {{ max-width: 250px !important; }}
                .marker {{ width: 20px; height: 20px; }}
                .marker-badge {{ width: 14px; height: 14px; font-size: 7px; }}
            }}
        </style>
    </head>
    <body>
        <div id="status" class="status">🗺️ Initializing outbreak map...</div>
        <div class="nav-controls">
            <button class="nav-btn" onclick="goToGlobal()" title="Global View">🌍 Global</button>
            <button class="nav-btn ship" onclick="goToShip()" title="Focus Ship">🚢 Ship</button>
            <button class="nav-btn" onclick="refreshMap()" title="Refresh Data">🔄 Refresh</button>
        </div>
        <div id="map"></div>

        <script>
            const status = document.getElementById('status');
            const hotspots = {json.dumps(hotspots)};
            const state = {json.dumps(state)};
            let map, markers = [];

            function updateStatus(msg) {{
                status.innerHTML = msg;
                console.log(msg);
            }}

            function initMap() {{
                try {{
                    updateStatus('🌍 Creating map...');

                    // Initialize map
                    map = L.map('map', {{
                        zoomControl: false,
                        attributionControl: false,
                        minZoom: 2,
                        maxZoom: 12,
                        worldCopyJump: true
                    }}).setView([15, -25], 2.8);

                    // Add zoom controls
                    L.control.zoom({{
                        position: 'bottomright',
                        zoomInTitle: 'Zoom in',
                        zoomOutTitle: 'Zoom out'
                    }}).addTo(map);

                    updateStatus('🗺️ Loading map tiles...');

                    // Add dark theme tiles with fallbacks
                    const tileUrls = [
                        'https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',
                        'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{{z}}/{{x}}/{{y}}{{r}}.png',
                        'https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png'
                    ];

                    let tileLayer = null;
                    for (const url of tileUrls) {{
                        try {{
                            tileLayer = L.tileLayer(url, {{ maxZoom: 19 }}).addTo(map);
                            break;
                        }} catch (e) {{
                            console.warn('Tile layer failed:', e);
                        }}
                    }}

                    updateStatus('📍 Adding outbreak markers...');
                    addHotspotMarkers();

                    updateStatus('✅ Map ready — Tracking {{}} locations'.replace('{{}}', hotspots.length));

                    // Auto-hide status after 3 seconds
                    setTimeout(() => {{
                        status.style.opacity = '0.7';
                        status.innerHTML = '🌍 Live outbreak tracking';
                    }}, 3000);

                }} catch (error) {{
                    console.error('Map initialization failed:', error);
                    showFallback();
                }}
            }}

            function addHotspotMarkers() {{
                hotspots.forEach(hotspot => {{
                    try {{
                        const isShip = hotspot.code === 'SHIP';
                        const riskColor = hotspot.color || '#4ade80';
                        const cases = hotspot.cases || 0;
                        const deaths = hotspot.deaths || 0;

                        // Create custom marker
                        const markerClass = hotspot.glow ?
                            (hotspot.risk === 'CRITICAL' ? 'marker marker-critical' : 'marker marker-glow') :
                            'marker';

                        const markerHtml = `
                            <div class="${{markerClass}}" style="background-color: ${{riskColor}};">
                                ${{isShip ? '🚢' : '🦠'}}
                                ${{cases > 0 ? `<div class="marker-badge">${{cases}}</div>` : ''}}
                            </div>
                        `;

                        // Create marker
                        const marker = L.divIcon({{
                            html: markerHtml,
                            className: 'custom-marker',
                            iconSize: [24, 24],
                            iconAnchor: [12, 12],
                            popupAnchor: [0, -12]
                        }});

                        // Add to map
                        const mapMarker = L.marker([hotspot.lat, hotspot.lng], {{ icon: marker }}).addTo(map);

                        // Tooltip
                        const tooltipContent = `
                            <div>
                                <b style="color:${{riskColor}};">${{isShip ? '🚢' : '🌍'}} ${{hotspot.name}}</b><br>
                                <span style="color:#f87171;">🦠 ${{cases}} cases</span><br>
                                <span style="color:#64748b;">💀 ${{deaths}} deaths</span>
                                ${{hotspot.fear ? `<br><span style="color:#fbbf24;">😰 Fear: ${{hotspot.fear}}%</span>` : ''}}
                            </div>
                        `;
                        mapMarker.bindTooltip(tooltipContent, {{ direction: 'top' }});

                        // Detailed popup
                        const popupContent = `
                            <div style="min-width:200px;">
                                <h3 style="margin:0 0 10px 0; color:${{riskColor}};">${{isShip ? '🚢' : '🌍'}} ${{hotspot.name}}</h3>
                                <div style="margin-bottom:8px;"><b>Status:</b> ${{hotspot.risk || 'MONITORING'}}</div>
                                <div style="margin-bottom:8px;"><b>Confirmed Cases:</b> <span style="color:#f87171;">${{cases}}</span></div>
                                <div style="margin-bottom:8px;"><b>Deaths:</b> <span style="color:#64748b;">${{deaths}}</span></div>
                                ${{hotspot.fear ? `<div style="margin-bottom:8px;"><b>Local Fear Index:</b> <span style="color:#fbbf24;">${{hotspot.fear}}%</span></div>` : ''}}
                                ${{hotspot.status ? `<div style="margin-bottom:8px;"><b>Ship Status:</b> ${{hotspot.status}}</div>` : ''}}
                                <div style="margin-bottom:8px;"><b>Coordinates:</b> ${{hotspot.lat.toFixed(3)}}, ${{hotspot.lng.toFixed(3)}}</div>
                                <div style="font-size:11px; color:#94a3b8; margin-top:10px;">${{hotspot.relation || 'Outbreak location'}}</div>
                            </div>
                        `;
                        mapMarker.bindPopup(popupContent);

                        markers.push(mapMarker);

                    }} catch (error) {{
                        console.warn('Failed to add marker for', hotspot.name, error);
                    }}
                }});
            }}

            function goToGlobal() {{
                map.setView([15, -25], 2.8);
                updateStatus('🌍 Global view');
            }}

            function goToShip() {{
                const shipHotspot = hotspots.find(h => h.code === 'SHIP');
                if (shipHotspot) {{
                    map.setView([shipHotspot.lat, shipHotspot.lng], 6);
                    updateStatus('🚢 Focused on MV Hondius');
                }}
            }}

            function refreshMap() {{
                updateStatus('🔄 Refreshing data...');
                setTimeout(() => {{
                    location.reload();
                }}, 500);
            }}

            function showFallback() {{
                document.getElementById('map').innerHTML = `
                    <div style="display:flex;align-items:center;justify-content:center;height:100%;background:#050505;color:#4ade80;text-align:center;padding:20px;">
                        <div>
                            <div style="font-size:48px;margin-bottom:20px;">🌍</div>
                            <div style="font-size:18px;margin-bottom:15px;">Map temporarily unavailable</div>
                            <div style="font-size:14px;color:#94a3b8;margin-bottom:20px;">Tracking ${{hotspots.length}} outbreak locations</div>
                            <div style="text-align:left;max-height:250px;overflow-y:auto;background:rgba(0,0,0,0.5);padding:15px;border-radius:8px;max-width:400px;">
                                ${{hotspots.slice(0, 8).map(h => `
                                    <div style="margin:8px 0;padding:8px;background:rgba(255,255,255,0.05);border-radius:4px;border-left:3px solid ${{h.color}};">
                                        <strong style="color:${{h.color}};">${{h.name}}</strong><br>
                                        <span style="font-size:11px;color:#94a3b8;">
                                            📍 ${{h.lat.toFixed(2)}}, ${{h.lng.toFixed(2)}} •
                                            🦠 ${{h.cases}} cases •
                                            💀 ${{h.deaths}} deaths
                                        </span>
                                    </div>
                                `).join('')}}
                            </div>
                            <button onclick="refreshMap()" style="background:#4ade80;color:#000;border:none;padding:12px 24px;border-radius:8px;cursor:pointer;font-weight:bold;margin-top:15px;">
                                🔄 Reload Map
                            </button>
                        </div>
                    </div>
                `;
            }}

            // Initialize when page loads
            document.addEventListener('DOMContentLoaded', initMap);

        </script>
    </body>
    </html>
    """

    # Add data hash for cache busting
    data_hash = hashlib.md5(json.dumps(hotspots, sort_keys=True).encode()).hexdigest()[:8]
    map_html = f"<!-- Map Data Hash: {data_hash} -->" + map_html

    # Render map
    components.html(map_html, height=450)

# Legacy compatibility functions for other modules
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

# Legacy constant for backward compatibility
NATIONALITIES_DATA = get_nationality_hotspots(get_live_state())

# Main render function alias for backward compatibility
render_map_panel = render_outbreak_map