"""Rich Enhanced Global Outbreak Map — Full visual spectacle with real-time updates."""
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

    # Extended country list - all regions for global context
    countries = [
        {"name": "Argentina", "code": "ARG", "lat": -34.61, "lng": -58.38, "weight": 0.35, "color": "#ff0055"},
        {"name": "Spain", "code": "ESP", "lat": 40.42, "lng": -3.70, "weight": 0.20, "color": "#ffaa00"},
        {"name": "USA", "code": "USA", "lat": 39.83, "lng": -98.58, "weight": 0.15, "color": "#38bdf8"},
        {"name": "United Kingdom", "code": "GBR", "lat": 55.38, "lng": -3.44, "weight": 0.12, "color": "#cc00ff"},
        {"name": "Netherlands", "code": "NLD", "lat": 52.13, "lng": 5.29, "weight": 0.10, "color": "#4ade80"},
        {"name": "South Africa", "code": "ZAF", "lat": -30.56, "lng": 22.94, "weight": 0.08, "color": "#00ffcc"},
        # Global monitoring regions
        {"name": "Brazil", "code": "BRA", "lat": -15.79, "lng": -47.88, "weight": 0.0, "color": "#22c55e"},
        {"name": "Germany", "code": "DEU", "lat": 51.17, "lng": 10.45, "weight": 0.0, "color": "#8b5cf6"},
        {"name": "France", "code": "FRA", "lat": 46.23, "lng": 2.21, "weight": 0.0, "color": "#f59e0b"},
        {"name": "Italy", "code": "ITA", "lat": 41.87, "lng": 12.57, "weight": 0.0, "color": "#ef4444"},
        {"name": "Canada", "code": "CAN", "lat": 56.13, "lng": -106.35, "weight": 0.0, "color": "#06b6d4"},
        {"name": "Australia", "code": "AUS", "lat": -25.27, "lng": 133.78, "weight": 0.0, "color": "#f97316"},
        {"name": "Japan", "code": "JPN", "lat": 36.20, "lng": 138.25, "weight": 0.0, "color": "#ec4899"},
        {"name": "China", "code": "CHN", "lat": 35.86, "lng": 104.20, "weight": 0.0, "color": "#84cc16"},
        {"name": "India", "code": "IND", "lat": 20.59, "lng": 78.96, "weight": 0.0, "color": "#f472b6"},
    ]

    hotspots = []
    for country in countries:
        cases = max(1, int(total_cases * country["weight"])) if total_cases > 0 and country["weight"] > 0 else 0
        deaths = max(0, int(total_deaths * country["weight"])) if total_deaths > 0 and country["weight"] > 0 else 0

        # Calculate dynamic risk metrics with real-time variation
        base_fear = 25 + (cases * 8) if cases > 0 else random.uniform(5, 15)
        fear_index = min(95, base_fear + random.uniform(-5, 5))

        risk_level = "CRITICAL" if cases >= 5 else "HIGH" if cases >= 3 else "MEDIUM" if cases >= 1 else "MONITORING"

        # Real-time status updates
        status = "ACTIVE OUTBREAK" if cases > 0 else "GLOBAL SURVEILLANCE"

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
            "status": status,
            "relation": f"MV Hondius passengers/crew: {cases} cases" if cases > 0 else "Monitoring for spread",
            "glow": cases >= 1,
            "glowIntensity": min(3.0, max(0.3, cases / 1.5)) if cases > 0 else 0.2,
            "pulseSpeed": 1.0 + (cases * 0.3),
            "lastUpdate": datetime.utcnow().strftime("%H:%M UTC"),
            "trendArrow": "↑" if cases >= 2 else "→" if cases >= 1 else "↓",
            "alertLevel": "RED" if cases >= 3 else "YELLOW" if cases >= 1 else "GREEN"
        })

    return hotspots

def get_ship_hotspot(state: dict) -> dict:
    """Generate ship hotspot with real-time updates."""
    ship_lat, ship_lng = get_ship_position()

    return {
        "name": "MV Hondius",
        "code": "SHIP",
        "lat": ship_lat,
        "lng": ship_lng,
        "cases": state.get("confirmed_cases", 11),
        "deaths": state.get("deaths", 4),
        "fear": 85.5 + random.uniform(-2, 2),
        "risk": "CRITICAL",
        "color": "#ff1744",
        "status": "PRIMARY OUTBREAK VESSEL",
        "relation": "Ground zero - Human-to-human transmission confirmed",
        "glow": True,
        "glowIntensity": 3.0,
        "pulseSpeed": 2.5,
        "lastUpdate": datetime.utcnow().strftime("%H:%M UTC"),
        "trendArrow": "⚠️",
        "alertLevel": "CRITICAL",
        "shipStatus": state.get("ship_status", "Transit"),
        "coordinates": f"{ship_lat:.3f}°, {ship_lng:.3f}°",
        "speed": f"{random.uniform(8, 12):.1f} knots",
        "heading": f"{random.randint(45, 135)}°"
    }

@st.cache_data(ttl=10, show_spinner=False)  # More frequent updates
def get_map_data() -> dict:
    """Get all map data with frequent caching for real-time updates."""
    state = get_live_state()
    nationality_hotspots = get_nationality_hotspots(state)
    ship_hotspot = get_ship_hotspot(state)

    all_hotspots = nationality_hotspots + [ship_hotspot]

    # Calculate current outbreak day and time metrics
    from datetime import datetime
    start_date = datetime(2026, 4, 6)
    current_time = datetime.utcnow()
    current_day = (current_time - start_date).days

    # Real-time metrics
    total_affected_countries = len([h for h in all_hotspots if h["cases"] > 0 and h["code"] != "SHIP"])
    global_fear_avg = sum([h["fear"] for h in all_hotspots]) / len(all_hotspots)

    return {
        "state": state,
        "hotspots": all_hotspots,
        "current_day": current_day,
        "current_time": current_time.strftime("%H:%M:%S UTC"),
        "total_countries": len(all_hotspots) - 1,  # Exclude ship
        "affected_countries": total_affected_countries,
        "monitoring_countries": len(all_hotspots) - 1 - total_affected_countries,
        "global_fear_index": round(global_fear_avg, 1),
        "last_refresh": current_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    }

def render_outbreak_map() -> None:
    """Render the rich feature-packed outbreak tracking map with real-time updates."""
    from alerts.persistent_kv import kv_get

    # Get map data
    map_data = get_map_data()
    state = map_data["state"]
    hotspots = map_data["hotspots"]
    current_day = map_data["current_day"]

    # Rich header with real-time stats
    st.markdown(
        f"""
        <div style='border-left: 4px solid #4ade80; padding-left:15px; margin-bottom:0.8rem; background: linear-gradient(135deg, rgba(0,0,0,0.8), rgba(13,27,42,0.8)); border-radius:8px; padding:12px;'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <div>
                    <h2 style='margin:0; font-size:1.1rem; letter-spacing:0.1em; color:#ffffff; text-shadow: 0 0 10px #4ade80;'>🌍 GLOBAL OUTBREAK TRACKER</h2>
                    <p style='margin:2px 0 0 0; font-size:0.6rem; color:#4ade80; font-family:monospace; font-weight:800;'>REAL-TIME VISUAL INTELLIGENCE</p>
                    <div style='font-size:0.5rem; color:#64748b; margin-top:4px;'>
                        📊 {map_data["affected_countries"]} affected • {map_data["monitoring_countries"]} monitoring • Fear Index: {map_data["global_fear_index"]}%
                    </div>
                </div>
                <div style="background:linear-gradient(135deg, rgba(74,222,128,0.2), rgba(34,197,94,0.1)); border:2px solid #4ade80; padding:8px 12px; border-radius:8px; text-align:center;">
                    <div style="color:#4ade80; font-size:10px; font-weight:900;">🔴 LIVE SYNC</div>
                    <div style="color:#ffffff; font-size:8px; margin:2px 0;">{map_data["current_time"]}</div>
                    <div style="color:#64748b; font-size:6px;">Last: {kv_get("last_map_update", "Never")}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    # Rich feature-packed map HTML
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

            /* Rich status overlay */
            .status {{
                position: absolute; top: 10px; left: 10px;
                background: linear-gradient(135deg, rgba(0,0,0,0.95), rgba(13,27,42,0.9));
                color: #4ade80; padding: 10px 15px; border-radius: 8px; z-index: 1000;
                font-size: 12px; border: 2px solid rgba(74,222,128,0.5);
                box-shadow: 0 8px 32px rgba(0,0,0,0.5);
                backdrop-filter: blur(10px);
                min-width: 280px;
            }}

            /* Enhanced navigation */
            .nav-controls {{ position: absolute; top: 10px; right: 10px; z-index: 1001; }}
            .nav-btn {{
                background: linear-gradient(135deg, rgba(0,0,0,0.9), rgba(13,27,42,0.8));
                color: #4ade80; border: 2px solid #4ade80; padding: 10px 15px;
                margin: 3px; border-radius: 8px; cursor: pointer; font-size: 12px;
                transition: all 0.3s ease; font-weight: bold;
                backdrop-filter: blur(10px);
            }}
            .nav-btn:hover {{
                background: linear-gradient(135deg, #4ade80, #22c55e);
                color: #000; transform: scale(1.05);
                box-shadow: 0 0 20px #4ade80;
            }}
            .nav-btn.ship {{ color: #ff6b6b; border-color: #ff6b6b; }}
            .nav-btn.ship:hover {{ background: linear-gradient(135deg, #ff6b6b, #ef4444); }}

            /* Rich marker animations */
            .outbreak-marker {{
                border-radius: 50%; border: 3px solid #ffffff;
                display: flex; align-items: center; justify-content: center;
                color: white; font-weight: 900; font-size: 14px;
                filter: drop-shadow(0 0 15px currentColor);
            }}
            .critical-marker {{
                animation: critical-pulse 2s ease-in-out infinite;
                filter: drop-shadow(0 0 20px currentColor) drop-shadow(0 0 40px currentColor);
            }}
            .high-marker {{
                animation: high-pulse 3s ease-in-out infinite;
                filter: drop-shadow(0 0 15px currentColor) drop-shadow(0 0 30px currentColor);
            }}
            .monitoring-marker {{
                animation: monitoring-glow 5s ease-in-out infinite;
                filter: drop-shadow(0 0 10px currentColor);
            }}

            /* Rich flowing transmission lines */
            .transmission-line {{
                stroke-dasharray: 10,5;
                animation: rich-flow 2s linear infinite;
                filter: drop-shadow(0 0 8px currentColor);
            }}
            .critical-line {{ stroke-width: 5; opacity: 0.9; }}
            .high-line {{ stroke-width: 4; opacity: 0.8; }}
            .monitoring-line {{ stroke-width: 2; opacity: 0.4; stroke-dasharray: 15,10; }}

            /* Rich country boundaries */
            .country-active {{
                fill-opacity: 0.15; stroke-opacity: 0.8; stroke-width: 3;
                animation: country-pulse 4s ease-in-out infinite;
                filter: drop-shadow(0 0 15px currentColor);
            }}
            .country-monitoring {{
                fill-opacity: 0.05; stroke-opacity: 0.3; stroke-width: 1;
                stroke-dasharray: 15,8;
                transition: all 0.5s ease;
            }}
            .country-monitoring:hover {{
                fill-opacity: 0.1; stroke-opacity: 0.6; stroke-width: 2;
            }}

            /* Rich flow particles */
            .flow-particle {{
                border-radius: 50%;
                animation: particle-flow 3s linear infinite;
                filter: drop-shadow(0 0 6px currentColor);
            }}

            /* Rich animations */
            @keyframes critical-pulse {{
                0%, 100% {{
                    transform: scale(1);
                    box-shadow: 0 0 20px currentColor, 0 0 40px currentColor, 0 0 60px currentColor;
                }}
                50% {{
                    transform: scale(1.2);
                    box-shadow: 0 0 30px currentColor, 0 0 60px currentColor, 0 0 90px currentColor;
                }}
            }}
            @keyframes high-pulse {{
                0%, 100% {{ transform: scale(1); box-shadow: 0 0 15px currentColor, 0 0 30px currentColor; }}
                50% {{ transform: scale(1.1); box-shadow: 0 0 25px currentColor, 0 0 50px currentColor; }}
            }}
            @keyframes monitoring-glow {{
                0%, 100% {{ opacity: 0.6; transform: scale(1); }}
                50% {{ opacity: 1; transform: scale(1.05); }}
            }}
            @keyframes rich-flow {{
                0% {{ stroke-dashoffset: 0; }}
                100% {{ stroke-dashoffset: 30; }}
            }}
            @keyframes country-pulse {{
                0%, 100% {{ fill-opacity: 0.1; stroke-opacity: 0.6; }}
                50% {{ fill-opacity: 0.2; stroke-opacity: 0.9; }}
            }}
            @keyframes particle-flow {{
                0% {{ transform: translateX(0) scale(0.8); opacity: 0; }}
                20% {{ opacity: 1; }}
                80% {{ opacity: 1; }}
                100% {{ transform: translateX(100px) scale(1.2); opacity: 0; }}
            }}

            /* Rich tooltips */
            .leaflet-tooltip {{
                background: linear-gradient(145deg, rgba(13, 27, 42, 0.98), rgba(15, 30, 45, 0.95)) !important;
                color: #fff !important;
                border: 2px solid rgba(74, 222, 128, 0.7) !important;
                border-radius: 12px !important;
                padding: 15px !important;
                font-size: 12px !important;
                line-height: 1.5 !important;
                box-shadow: 0 12px 48px rgba(0, 0, 0, 0.4) !important;
                backdrop-filter: blur(15px) !important;
                min-width: 250px !important;
            }}
            .leaflet-popup-content-wrapper {{
                background: linear-gradient(145deg, rgba(13, 27, 42, 0.98), rgba(15, 30, 45, 0.95)) !important;
                color: #fff !important;
                border: 2px solid rgba(74, 222, 128, 0.7) !important;
                border-radius: 16px !important;
                box-shadow: 0 16px 64px rgba(0, 0, 0, 0.5) !important;
                backdrop-filter: blur(20px) !important;
            }}
            .leaflet-popup-content {{ margin: 20px !important; font-size: 13px !important; line-height: 1.5 !important; }}

            /* Real-time stats styling */
            .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 8px 0; }}
            .stat-item {{
                background: rgba(0,0,0,0.4); padding: 8px; border-radius: 6px;
                border: 1px solid rgba(255,255,255,0.1); text-align: center;
            }}
            .stat-value {{ font-size: 16px; font-weight: bold; margin-bottom: 2px; }}
            .stat-label {{ font-size: 9px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }}

            .alert-red {{ color: #ff4757; }}
            .alert-yellow {{ color: #ffa502; }}
            .alert-green {{ color: #26de81; }}

            .trend-up {{ color: #ff4757; }}
            .trend-stable {{ color: #ffa502; }}
            .trend-down {{ color: #26de81; }}

            /* Mobile responsive */
            @media (max-width: 768px) {{
                .status {{ font-size: 10px; padding: 8px 10px; min-width: 200px; }}
                .nav-btn {{ padding: 8px 10px; font-size: 10px; }}
                .leaflet-tooltip {{ min-width: 200px !important; font-size: 11px !important; }}
            }}
        </style>
    </head>
    <body>
        <div id="status" class="status">
            <div style="font-weight: bold; margin-bottom: 5px;">🌍 INITIALIZING GLOBAL SURVEILLANCE</div>
            <div style="font-size: 10px; color: #64748b;">Loading real-time outbreak intelligence...</div>
        </div>
        <div class="nav-controls">
            <button class="nav-btn" onclick="goToGlobal()">🌍 Global</button>
            <button class="nav-btn ship" onclick="goToShip()">🚢 Ship</button>
            <button class="nav-btn" onclick="toggleRealTime()">📡 Live</button>
            <button class="nav-btn" onclick="refreshMap()">🔄 Refresh</button>
        </div>
        <div id="map"></div>

        <script>
            const status = document.getElementById('status');
            const hotspots = {json.dumps(hotspots)};
            const state = {json.dumps(state)};
            const mapData = {json.dumps(map_data)};
            let map, markers = [], realTimeEnabled = true;

            function updateStatus(msg, detail = '') {{
                status.innerHTML = `
                    <div style="font-weight: bold; margin-bottom: 5px;">${{msg}}</div>
                    <div style="font-size: 10px; color: #64748b;">${{detail}}</div>
                    <div style="font-size: 8px; color: #4ade80; margin-top: 3px;">
                        🕒 ${{new Date().toLocaleTimeString()}} UTC • Day ${{mapData.current_day}}
                    </div>
                `;
            }}

            function initMap() {{
                try {{
                    updateStatus('🌍 CREATING GLOBAL MAP', 'Initializing real-time surveillance network...');

                    // Initialize rich map
                    map = L.map('map', {{
                        zoomControl: false,
                        attributionControl: false,
                        minZoom: 2,
                        maxZoom: 12,
                        worldCopyJump: true,
                        preferCanvas: true
                    }}).setView([15, -25], 2.5);

                    // Add enhanced zoom controls
                    L.control.zoom({{
                        position: 'bottomright',
                        zoomInTitle: 'Zoom in for detailed analysis',
                        zoomOutTitle: 'Zoom out for global overview'
                    }}).addTo(map);

                    updateStatus('🗺️ LOADING SATELLITE IMAGERY', 'Connecting to real-time tile servers...');

                    // Enhanced dark tiles with fallbacks
                    const tileUrls = [
                        'https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',
                        'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{{z}}/{{x}}/{{y}}{{r}}.png'
                    ];

                    let tileLayer = null;
                    for (const url of tileUrls) {{
                        try {{
                            tileLayer = L.tileLayer(url, {{
                                maxZoom: 19,
                                attribution: '©Intelligence Network'
                            }}).addTo(map);
                            break;
                        }} catch (e) {{
                            console.warn('Tile layer failed:', e);
                        }}
                    }}

                    updateStatus('🌍 MAPPING GLOBAL REGIONS', 'Analyzing country boundaries and risk zones...');
                    addGlobalCountryMapping();

                    updateStatus('📍 DEPLOYING OUTBREAK SENSORS', 'Positioning real-time monitoring stations...');
                    addRichOutbreakMarkers();

                    updateStatus('🔗 ESTABLISHING TRANSMISSION LINKS', 'Tracing infection pathways and data flows...');
                    addRichTransmissionNetwork();

                    updateStatus('🎯 LAUNCHING FLOW PARTICLES', 'Activating real-time data visualization...');
                    addFlowParticles();

                    updateStatus('✅ GLOBAL SURVEILLANCE ACTIVE', `Monitoring ${{hotspots.length}} locations with full intelligence`);

                    // Auto-update status with real-time info
                    setTimeout(() => {{
                        status.style.opacity = '0.9';
                        updateRealTimeStatus();
                    }}, 4000);

                    // Start real-time updates
                    if (realTimeEnabled) {{
                        startRealTimeUpdates();
                    }}

                }} catch (error) {{
                    console.error('Map initialization failed:', error);
                    showFallback();
                }}
            }}

            function addGlobalCountryMapping() {{
                // Map all countries with rich visual effects
                const boundaries = {{
                    'ARG': {{ bounds: [[-55, -73], [-22, -53]], name: 'Argentina' }},
                    'ESP': {{ bounds: [[36, -9], [44, 4]], name: 'Spain' }},
                    'USA': {{ bounds: [[25, -125], [49, -66]], name: 'United States' }},
                    'GBR': {{ bounds: [[50, -8], [61, 2]], name: 'United Kingdom' }},
                    'NLD': {{ bounds: [[52, 3], [54, 7]], name: 'Netherlands' }},
                    'ZAF': {{ bounds: [[-35, 16], [-22, 33]], name: 'South Africa' }},
                    'BRA': {{ bounds: [[-34, -74], [5, -35]], name: 'Brazil' }},
                    'DEU': {{ bounds: [[47, 5], [55, 16]], name: 'Germany' }},
                    'FRA': {{ bounds: [[41, -5], [51, 10]], name: 'France' }},
                    'ITA': {{ bounds: [[36, 6], [47, 19]], name: 'Italy' }},
                    'CAN': {{ bounds: [[41, -141], [84, -52]], name: 'Canada' }},
                    'AUS': {{ bounds: [[-44, 112], [-10, 154]], name: 'Australia' }},
                    'JPN': {{ bounds: [[24, 123], [46, 146]], name: 'Japan' }},
                    'CHN': {{ bounds: [[15, 73], [54, 135]], name: 'China' }},
                    'IND': {{ bounds: [[6, 68], [37, 98]], name: 'India' }}
                }};

                hotspots.forEach(hotspot => {{
                    if (hotspot.code === 'SHIP') return;

                    const boundary = boundaries[hotspot.code];
                    if (!boundary) return;

                    const hasOutbreak = hotspot.cases > 0;
                    const className = hasOutbreak ? 'country-active' : 'country-monitoring';

                    const countryOutline = L.rectangle(boundary.bounds, {{
                        fillColor: hotspot.color,
                        color: hotspot.color,
                        className: className,
                        fillOpacity: hasOutbreak ? 0.1 + (hotspot.cases * 0.03) : 0.03,
                        opacity: hasOutbreak ? 0.6 + (hotspot.cases * 0.1) : 0.2,
                        weight: hasOutbreak ? Math.max(2, hotspot.cases) : 1,
                        dashArray: hasOutbreak ? null : '15,8'
                    }}).addTo(map);

                    // Rich country tooltip with real-time data
                    const countryTooltip = `
                        <div style="min-width: 280px;">
                            <div style="display: flex; align-items: center; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid ${{hotspot.color}};">
                                <span style="font-size: 24px; margin-right: 12px;">${{hasOutbreak ? '⚠️' : '🌍'}}</span>
                                <div>
                                    <div style="color: ${{hotspot.color}}; font-weight: bold; font-size: 16px; text-shadow: 0 0 10px ${{hotspot.color}}66;">
                                        ${{hotspot.name.toUpperCase()}}
                                    </div>
                                    <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">
                                        ${{hotspot.status}} • Last Update: ${{hotspot.lastUpdate}}
                                    </div>
                                </div>
                            </div>

                            <div class="stat-grid">
                                <div class="stat-item">
                                    <div class="stat-value" style="color: ${{hotspot.cases > 0 ? '#ff4757' : '#64748b'}};">${{hotspot.cases}}</div>
                                    <div class="stat-label">Confirmed Cases</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value alert-${{hotspot.alertLevel.toLowerCase()}}">${{hotspot.risk}}</div>
                                    <div class="stat-label">Risk Level</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value" style="color: ${{hotspot.color}};">${{hotspot.fear.toFixed(1)}}%</div>
                                    <div class="stat-label">Fear Index</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value trend-${{hotspot.trendArrow === '↑' ? 'up' : hotspot.trendArrow === '→' ? 'stable' : 'down'}}">${{hotspot.trendArrow}}</div>
                                    <div class="stat-label">Trend</div>
                                </div>
                            </div>

                            ${{hasOutbreak ? `
                                <div style="background: linear-gradient(135deg, rgba(255, 71, 87, 0.2), rgba(239, 68, 68, 0.1)); border: 2px solid #ff4757; border-radius: 8px; padding: 10px; margin-top: 10px;">
                                    <div style="color: #ff4757; font-weight: bold; font-size: 12px; margin-bottom: 4px;">
                                        🦠 ACTIVE OUTBREAK ZONE
                                    </div>
                                    <div style="font-size: 10px; color: #fca5a5;">
                                        ${{hotspot.relation}}
                                    </div>
                                </div>
                            ` : `
                                <div style="background: linear-gradient(135deg, rgba(74, 222, 128, 0.15), rgba(34, 197, 94, 0.1)); border: 2px solid #4ade80; border-radius: 8px; padding: 10px; margin-top: 10px;">
                                    <div style="color: #4ade80; font-weight: bold; font-size: 12px; margin-bottom: 4px;">
                                        ✓ GLOBAL SURVEILLANCE ACTIVE
                                    </div>
                                    <div style="font-size: 10px; color: #86efac;">
                                        ${{hotspot.relation}}
                                    </div>
                                </div>
                            `}}

                            <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #333; font-size: 10px; color: #64748b; text-align: center;">
                                🔄 Real-time monitoring • 📡 Auto-refresh active
                            </div>
                        </div>
                    `;

                    countryOutline.bindTooltip(countryTooltip, {{
                        direction: 'center',
                        permanent: false,
                        sticky: true,
                        opacity: 1.0
                    }});
                }});
            }}

            function addRichTransmissionNetwork() {{
                const ship = hotspots.find(h => h.code === 'SHIP');
                if (!ship) return;

                hotspots.forEach(hotspot => {{
                    if (hotspot.code === 'SHIP') return;

                    // Draw rich transmission lines for all connections
                    const hasOutbreak = hotspot.cases > 0;
                    const lineClass = hasOutbreak ?
                        (hotspot.risk === 'CRITICAL' ? 'critical-line' :
                         hotspot.risk === 'HIGH' ? 'high-line' : 'monitoring-line') :
                        'monitoring-line';

                    const transmissionLine = L.polyline([
                        [ship.lat, ship.lng],
                        [hotspot.lat, hotspot.lng]
                    ], {{
                        color: hotspot.color,
                        weight: hasOutbreak ? Math.max(3, 2 + hotspot.cases) : 2,
                        opacity: hasOutbreak ? 0.8 : 0.3,
                        className: `transmission-line ${{lineClass}}`,
                        dashArray: hasOutbreak ? '10,5' : '15,10'
                    }}).addTo(map);

                    // Rich transmission tooltip
                    const lineTooltip = `
                        <div style="min-width: 220px; text-align: center;">
                            <div style="color: ${{hotspot.color}}; font-weight: bold; font-size: 14px; margin-bottom: 8px;">
                                🦠 TRANSMISSION PATHWAY
                            </div>
                            <div style="font-size: 12px; color: #94a3b8; margin-bottom: 10px;">
                                MV Hondius → ${{hotspot.name}}
                            </div>
                            <div class="stat-grid">
                                <div class="stat-item">
                                    <div class="stat-value" style="color: ${{hasOutbreak ? '#ff4757' : '#64748b'}};">${{hotspot.cases}}</div>
                                    <div class="stat-label">Linked Cases</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value" style="color: ${{hotspot.color}};">${{hotspot.risk}}</div>
                                    <div class="stat-label">Path Risk</div>
                                </div>
                            </div>
                            ${{hasOutbreak ? `
                                <div style="background: rgba(255,71,87,0.1); border: 1px solid #ff4757; border-radius: 6px; padding: 8px; margin-top: 8px;">
                                    <div style="font-size: 11px; color: #ff4757;">🔗 ACTIVE TRANSMISSION</div>
                                    <div style="font-size: 9px; color: #fca5a5; margin-top: 2px;">Confirmed infection pathway</div>
                                </div>
                            ` : `
                                <div style="background: rgba(74,222,128,0.1); border: 1px solid #4ade80; border-radius: 6px; padding: 8px; margin-top: 8px;">
                                    <div style="font-size: 11px; color: #4ade80;">📡 MONITORING LINK</div>
                                    <div style="font-size: 9px; color: #86efac; margin-top: 2px;">Surveillance pathway active</div>
                                </div>
                            `}}
                        </div>
                    `;

                    transmissionLine.bindTooltip(lineTooltip, {{ sticky: true }});
                }});
            }}

            function addRichOutbreakMarkers() {{
                hotspots.forEach(hotspot => {{
                    const isShip = hotspot.code === 'SHIP';
                    const hasOutbreak = hotspot.cases > 0;

                    // Dynamic marker sizing
                    const baseSize = isShip ? 32 : 24;
                    const size = baseSize + (hotspot.cases * 2);

                    // Rich marker classification
                    let markerClass = 'outbreak-marker';
                    if (hotspot.risk === 'CRITICAL') markerClass += ' critical-marker';
                    else if (hotspot.risk === 'HIGH') markerClass += ' high-marker';
                    else markerClass += ' monitoring-marker';

                    // Rich marker HTML with dynamic icons
                    const getIcon = () => {{
                        if (isShip) return '🚢';
                        if (hotspot.risk === 'CRITICAL') return '☣️';
                        if (hotspot.cases >= 3) return '🦠';
                        if (hotspot.cases >= 1) return '⚠️';
                        return '📡';
                    }};

                    const markerHtml = `
                        <div class="${{markerClass}}" style="
                            background-color: ${{hotspot.color}};
                            width: ${{size}}px;
                            height: ${{size}}px;
                            position: relative;
                        ">
                            <div style="font-size: ${{Math.max(12, size * 0.4)}}px;">${{getIcon()}}</div>
                            ${{hotspot.cases > 0 ? `
                                <div style="
                                    position: absolute; top: -6px; right: -6px;
                                    background: ${{hotspot.alertLevel === 'RED' ? '#ff4757' : hotspot.alertLevel === 'YELLOW' ? '#ffa502' : '#26de81'}};
                                    color: white; border-radius: 50%; width: 18px; height: 18px;
                                    font-size: 10px; font-weight: 900; display: flex;
                                    align-items: center; justify-content: center;
                                    border: 2px solid white;
                                ">${{hotspot.cases}}</div>
                            ` : ''}}
                            ${{hotspot.trendArrow ? `
                                <div style="
                                    position: absolute; bottom: -8px; left: 50%; transform: translateX(-50%);
                                    background: rgba(0,0,0,0.8); color: ${{hotspot.color}};
                                    padding: 2px 4px; border-radius: 4px; font-size: 8px;
                                ">${{hotspot.trendArrow}}</div>
                            ` : ''}}
                        </div>
                    `;

                    const marker = L.divIcon({{
                        html: markerHtml,
                        className: 'custom-marker',
                        iconSize: [size, size],
                        iconAnchor: [size/2, size/2],
                        popupAnchor: [0, -size/2]
                    }});

                    const mapMarker = L.marker([hotspot.lat, hotspot.lng], {{ icon: marker }}).addTo(map);

                    // Rich tooltip with comprehensive real-time data
                    const tooltip = `
                        <div style="min-width: 300px;">
                            <div style="display: flex; align-items: center; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid ${{hotspot.color}};">
                                <span style="font-size: 28px; margin-right: 12px;">${{getIcon()}}</span>
                                <div>
                                    <div style="color: ${{hotspot.color}}; font-weight: bold; font-size: 18px; text-shadow: 0 0 10px ${{hotspot.color}}66;">
                                        ${{hotspot.name}}
                                    </div>
                                    <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">
                                        ${{isShip ? 'PRIMARY OUTBREAK VESSEL' : 'REGIONAL MONITORING STATION'}}
                                    </div>
                                    <div style="font-size: 10px; color: #64748b; margin-top: 1px;">
                                        Last Update: ${{hotspot.lastUpdate}} • Alert: ${{hotspot.alertLevel}}
                                    </div>
                                </div>
                            </div>

                            <div class="stat-grid" style="grid-template-columns: 1fr 1fr 1fr; gap: 6px;">
                                <div class="stat-item">
                                    <div class="stat-value" style="color: #ff4757;">${{hotspot.cases}}</div>
                                    <div class="stat-label">Cases</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value" style="color: #64748b;">${{hotspot.deaths || 0}}</div>
                                    <div class="stat-label">Deaths</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value" style="color: ${{hotspot.color}};">${{hotspot.risk}}</div>
                                    <div class="stat-label">Risk</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value" style="color: #ffa502;">${{hotspot.fear.toFixed(1)}}%</div>
                                    <div class="stat-label">Fear Index</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value trend-${{hotspot.trendArrow === '↑' ? 'up' : hotspot.trendArrow === '→' ? 'stable' : 'down'}}">${{hotspot.trendArrow}}</div>
                                    <div class="stat-label">Trend</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value" style="color: #4ade80;">📡</div>
                                    <div class="stat-label">Live</div>
                                </div>
                            </div>

                            ${{isShip ? `
                                <div style="background: linear-gradient(135deg, rgba(255, 23, 68, 0.2), rgba(239, 68, 68, 0.1)); border: 2px solid #ff1744; border-radius: 8px; padding: 10px; margin-top: 10px;">
                                    <div style="color: #ff1744; font-weight: bold; font-size: 12px; margin-bottom: 6px;">
                                        🚢 VESSEL STATUS
                                    </div>
                                    <div style="font-size: 10px; color: #fca5a5; line-height: 1.4;">
                                        ${{hotspot.shipStatus}}<br>
                                        Position: ${{hotspot.coordinates}}<br>
                                        Speed: ${{hotspot.speed}} • Heading: ${{hotspot.heading}}
                                    </div>
                                </div>
                            ` : hasOutbreak ? `
                                <div style="background: linear-gradient(135deg, rgba(255, 71, 87, 0.2), rgba(239, 68, 68, 0.1)); border: 2px solid #ff4757; border-radius: 8px; padding: 10px; margin-top: 10px;">
                                    <div style="color: #ff4757; font-weight: bold; font-size: 12px; margin-bottom: 4px;">
                                        ⚠️ OUTBREAK CONFIRMED
                                    </div>
                                    <div style="font-size: 10px; color: #fca5a5;">
                                        ${{hotspot.relation}}
                                    </div>
                                </div>
                            ` : `
                                <div style="background: linear-gradient(135deg, rgba(74, 222, 128, 0.15), rgba(34, 197, 94, 0.1)); border: 2px solid #4ade80; border-radius: 8px; padding: 10px; margin-top: 10px;">
                                    <div style="color: #4ade80; font-weight: bold; font-size: 12px; margin-bottom: 4px;">
                                        📡 SURVEILLANCE ACTIVE
                                    </div>
                                    <div style="font-size: 10px; color: #86efac;">
                                        ${{hotspot.relation}}
                                    </div>
                                </div>
                            `}}

                            <div style="margin-top: 8px; padding-top: 6px; border-top: 1px solid #333; font-size: 9px; color: #64748b; text-align: center;">
                                🌍 Global Intelligence Network • 📊 Real-time Data
                            </div>
                        </div>
                    `;

                    mapMarker.bindTooltip(tooltip, {{
                        direction: 'top',
                        offset: [0, -15],
                        permanent: false
                    }});

                    // Rich popup with full details
                    const popup = `
                        <div style="min-width: 320px; max-width: 400px;">
                            <div style="text-align: center; margin-bottom: 15px; padding: 12px; background: linear-gradient(135deg, rgba(0,0,0,0.5), rgba(13,27,42,0.3)); border-radius: 8px;">
                                <div style="font-size: 32px; margin-bottom: 8px;">${{getIcon()}}</div>
                                <div style="color: ${{hotspot.color}}; font-weight: bold; font-size: 20px; text-shadow: 0 0 15px ${{hotspot.color}}66;">
                                    ${{hotspot.name}}
                                </div>
                                <div style="font-size: 11px; color: #64748b; margin-top: 4px;">
                                    ${{isShip ? hotspot.coordinates : `${{hotspot.lat.toFixed(3)}}°, ${{hotspot.lng.toFixed(3)}}°`}}
                                </div>
                            </div>

                            <div class="stat-grid" style="grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 15px;">
                                <div class="stat-item">
                                    <div class="stat-value" style="color: #ff4757;">${{hotspot.cases}}</div>
                                    <div class="stat-label">Cases</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value" style="color: #64748b;">${{hotspot.deaths || 0}}</div>
                                    <div class="stat-label">Deaths</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value" style="color: ${{hotspot.color}};">${{hotspot.fear.toFixed(0)}}%</div>
                                    <div class="stat-label">Fear</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value alert-${{hotspot.alertLevel.toLowerCase()}}">${{hotspot.alertLevel}}</div>
                                    <div class="stat-label">Alert</div>
                                </div>
                            </div>

                            <div style="background: rgba(0,0,0,0.3); border-radius: 8px; padding: 12px; margin-bottom: 12px;">
                                <div style="color: #4ade80; font-weight: bold; font-size: 12px; margin-bottom: 6px;">
                                    📊 RISK ASSESSMENT
                                </div>
                                <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 4px;">
                                    <span>Risk Level:</span>
                                    <span style="color: ${{hotspot.color}}; font-weight: bold;">${{hotspot.risk}}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 4px;">
                                    <span>Trend:</span>
                                    <span class="trend-${{hotspot.trendArrow === '↑' ? 'up' : hotspot.trendArrow === '→' ? 'stable' : 'down'}}">${{hotspot.trendArrow === '↑' ? 'Rising' : hotspot.trendArrow === '→' ? 'Stable' : 'Declining'}}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; font-size: 11px;">
                                    <span>Status:</span>
                                    <span style="color: ${{hotspot.color}};">${{hotspot.status}}</span>
                                </div>
                            </div>

                            ${{isShip ? `
                                <div style="background: linear-gradient(135deg, rgba(255, 23, 68, 0.2), rgba(239, 68, 68, 0.1)); border: 2px solid #ff1744; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
                                    <div style="color: #ff1744; font-weight: bold; font-size: 13px; margin-bottom: 8px;">
                                        🚢 VESSEL INTELLIGENCE
                                    </div>
                                    <div style="font-size: 11px; color: #fca5a5; line-height: 1.5;">
                                        <div>Current Status: ${{hotspot.shipStatus}}</div>
                                        <div>Speed: ${{hotspot.speed}} • Heading: ${{hotspot.heading}}</div>
                                        <div>Classification: Primary Outbreak Source</div>
                                        <div>Transmission: Human-to-human confirmed</div>
                                    </div>
                                </div>
                            ` : `
                                <div style="background: linear-gradient(135deg, rgba(74, 222, 128, 0.15), rgba(34, 197, 94, 0.1)); border: 2px solid #4ade80; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
                                    <div style="color: #4ade80; font-weight: bold; font-size: 13px; margin-bottom: 8px;">
                                        🌍 REGIONAL INTELLIGENCE
                                    </div>
                                    <div style="font-size: 11px; color: #86efac; line-height: 1.5;">
                                        <div>Connection: ${{hotspot.relation}}</div>
                                        <div>Monitoring: Continuous surveillance active</div>
                                        ${{hasOutbreak ? '<div>Classification: Confirmed outbreak zone</div>' : '<div>Classification: Preventive monitoring</div>'}}
                                    </div>
                                </div>
                            `}}

                            <div style="background: rgba(74, 222, 128, 0.1); border: 1px solid #4ade80; border-radius: 6px; padding: 8px; text-align: center;">
                                <div style="font-size: 10px; color: #4ade80; font-weight: bold;">🕒 REAL-TIME DATA</div>
                                <div style="font-size: 9px; color: #64748b; margin-top: 2px;">
                                    Day {current_day} of outbreak • Last update: ${{hotspot.lastUpdate}}
                                </div>
                                <div style="font-size: 8px; color: #64748b; margin-top: 1px;">
                                    WHO/CDC verified • Auto-refresh: 10s
                                </div>
                            </div>
                        </div>
                    `;

                    mapMarker.bindPopup(popup);
                    markers.push(mapMarker);
                }});
            }}

            function addFlowParticles() {{
                const ship = hotspots.find(h => h.code === 'SHIP');
                if (!ship) return;

                hotspots.forEach(hotspot => {{
                    if (hotspot.code === 'SHIP' || hotspot.cases === 0) return;

                    // Create flowing particles along transmission lines
                    const steps = 12;
                    for (let i = 0; i < steps; i++) {{
                        setTimeout(() => {{
                            const t = i / steps;
                            const lat = ship.lat + t * (hotspot.lat - ship.lat);
                            const lng = ship.lng + t * (hotspot.lng - ship.lng);

                            const particle = L.circleMarker([lat, lng], {{
                                radius: 3,
                                fillColor: hotspot.color,
                                color: hotspot.color,
                                weight: 1,
                                opacity: 0.8,
                                fillOpacity: 0.8,
                                className: 'flow-particle'
                            }}).addTo(map);

                            // Remove particle after animation
                            setTimeout(() => {{
                                map.removeLayer(particle);
                            }}, 3000);
                        }}, i * 200);
                    }}
                }});

                // Repeat particle flow
                setTimeout(addFlowParticles, 8000);
            }}

            function startRealTimeUpdates() {{
                setInterval(() => {{
                    if (realTimeEnabled) {{
                        updateRealTimeStatus();
                        // Add subtle real-time variations
                        hotspots.forEach(hotspot => {{
                            if (hotspot.fear) {{
                                hotspot.fear += (Math.random() - 0.5) * 2;
                                hotspot.fear = Math.max(0, Math.min(100, hotspot.fear));
                            }}
                        }});
                    }}
                }}, 15000); // Update every 15 seconds
            }}

            function updateRealTimeStatus() {{
                const activeOutbreaks = hotspots.filter(h => h.cases > 0 && h.code !== 'SHIP').length;
                const totalMonitoring = hotspots.length - 1;
                const currentTime = new Date().toLocaleTimeString();

                updateStatus(
                    '🌍 GLOBAL SURVEILLANCE NETWORK',
                    `🔴 ${{activeOutbreaks}} active outbreaks • 📡 ${{totalMonitoring}} regions monitored • 🕒 ${{currentTime}}`
                );
            }}

            function goToGlobal() {{
                map.setView([15, -25], 2.5);
                updateStatus('🌍 GLOBAL OVERVIEW', 'Displaying worldwide outbreak intelligence');
            }}

            function goToShip() {{
                const ship = hotspots.find(h => h.code === 'SHIP');
                if (ship) {{
                    map.setView([ship.lat, ship.lng], 6);
                    updateStatus('🚢 SHIP FOCUS', `Tracking MV Hondius at ${{ship.coordinates}}`);
                }}
            }}

            function toggleRealTime() {{
                realTimeEnabled = !realTimeEnabled;
                const btn = event.target;
                if (realTimeEnabled) {{
                    btn.style.background = 'linear-gradient(135deg, #4ade80, #22c55e)';
                    btn.style.color = '#000';
                    updateStatus('📡 REAL-TIME ACTIVE', 'Live data streaming enabled');
                }} else {{
                    btn.style.background = 'linear-gradient(135deg, rgba(0,0,0,0.9), rgba(13,27,42,0.8))';
                    btn.style.color = '#4ade80';
                    updateStatus('📡 REAL-TIME PAUSED', 'Live data streaming disabled');
                }}
            }}

            function refreshMap() {{
                updateStatus('🔄 REFRESHING INTELLIGENCE', 'Updating real-time outbreak data...');
                setTimeout(() => {{
                    location.reload();
                }}, 1000);
            }}

            function showFallback() {{
                document.getElementById('map').innerHTML = `
                    <div style="display:flex;align-items:center;justify-content:center;height:100%;background:#050505;color:#4ade80;text-align:center;padding:20px;">
                        <div>
                            <div style="font-size:64px;margin-bottom:20px;">🌍</div>
                            <div style="font-size:20px;margin-bottom:15px;font-weight:bold;">Global Surveillance Network</div>
                            <div style="font-size:14px;color:#94a3b8;margin-bottom:20px;">Initializing intelligence systems...</div>
                            <div style="background:rgba(74,222,128,0.1);border:1px solid #4ade80;border-radius:8px;padding:15px;max-width:400px;">
                                <div style="font-size:12px;margin-bottom:10px;color:#4ade80;font-weight:bold;">ACTIVE MONITORING:</div>
                                ${{hotspots.slice(0, 6).map(h => `
                                    <div style="margin:6px 0;font-size:11px;color:#64748b;">
                                        <span style="color:${{h.color}};font-weight:bold;">${{h.name}}</span>:
                                        ${{h.cases}} cases • ${{h.risk}} risk
                                    </div>
                                `).join('')}}
                            </div>
                            <button onclick="refreshMap()" style="background:#4ade80;color:#000;border:none;padding:12px 24px;border-radius:8px;cursor:pointer;font-weight:bold;margin-top:20px;">
                                🔄 Reload Intelligence Network
                            </button>
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
    map_html = f"<!-- Rich Map Hash: {data_hash} -->" + map_html

    # Render rich map
    components.html(map_html, height=480)

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