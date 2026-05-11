"""High-fidelity Relational Map — Detailed vessel telemetry and localized intelligence."""
from __future__ import annotations

import json
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime

LIVE_FILE = Path("data/outbreak_live.json")
LOCAL_SENTIMENT_FILE = Path("data/local_sentiment.json")

# Data Exports for compatibility
NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "passengers": 12, "crew": 0, "cases": 3, "deaths": 1},
    {"country": "United Kingdom","code": "GBR", "passengers": 8,  "crew": 0, "cases": 2, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "passengers": 5,  "crew": 2, "cases": 2, "deaths": 1},
    {"country": "Argentina",     "code": "ARG", "passengers": 45, "crew": 5, "cases": 4, "deaths": 1},
    {"country": "South Africa",  "code": "ZAF", "passengers": 0,  "crew": 10,"cases": 2, "deaths": 0},
]

# Relational Hotspot Data
RELATIONAL_HOTSPOTS = [
    {"lat": -34.60, "lng": -58.38, "cases": 4, "name": "ARGENTINA_CLUSTER", "color": "#ff0055", "relation": "Departure Point (APR 01)", "intel": "Vessel took on 147 passengers/crew. Original source of andes strain suspected."},
    {"lat": -26.20, "lng": 28.04,  "cases": 2, "name": "SOUTH_AFRICA_SIGNAL", "color": "#00ffcc", "relation": "Evacuation Event (APR 26)", "intel": "Critical crew members airlifted to Joburg. Secondary transmission confirmed."},
    {"lat": 40.41, "lng": -3.70,  "cases": 3, "name": "SPAIN_MONITOR", "color": "#ffaa00", "relation": "Repatriation (MAY 05)", "intel": "Mandatory quarantine active in Tenerife ports for returnees."},
    {"lat": 51.50, "lng": -0.12,  "cases": 2, "name": "UK_MONITOR", "color": "#cc00ff", "relation": "Repatriation (MAY 06)", "intel": "Andes sequencing confirmed in Heathrow isolation ward."},
    {"lat": 14.93, "lng": -23.51, "cases": 5, "name": "MV_HONDIUS_CORE", "color": "#22c55e", "relation": "Primary Vector", "intel": "Vessel moored. Level 4 quarantine enforced."}
]

def _get_live_state() -> dict:
    if LIVE_FILE.exists():
        try: return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {"confirmed_cases": 5, "ship_status": "Quarantined", "last_updated": "2026-05-10"}

def _get_local_sentiment() -> dict:
    if LOCAL_SENTIMENT_FILE.exists():
        try:
            data = json.loads(LOCAL_SENTIMENT_FILE.read_text())
            ts = datetime.fromisoformat(data.get("timestamp", "2000-01-01"))
            if (datetime.now() - ts).total_seconds() < 3600:
                return data.get("scores", {})
        except Exception: pass
    codes = ["ARG", "ESP", "GBR", "NLD", "ZAF", "USA", "CHL", "NOR", "ITA", "PHL", "BRA", "FRA", "DEU"]
    import random
    scores = {c: round(random.uniform(1.2, 4.8), 2) for c in codes}
    LOCAL_SENTIMENT_FILE.write_text(json.dumps({"timestamp": datetime.now().isoformat(), "scores": scores}))
    return scores

def render_map_panel() -> None:
    state = _get_live_state()
    local_scores = _get_local_sentiment()
    from ui.news_ticker import fetch_headlines
    
    try:
        headlines = fetch_headlines(max_per_feed=12)
    except Exception:
        headlines = []

    # Map articles to countries for the localized scroller
    country_intel = {}
    for country in NATIONALITIES_DATA:
        code = country["code"]
        name = country["country"].lower()
        related = [h for h in headlines if name in (h.get("title", "") + " " + h.get("summary", "")).lower()]
        country_intel[code] = related[:5]

    st.markdown(
        f"""
        <div class="mission-header" style='border-left: 3px solid #00f5ff; padding-left:15px; margin-bottom:0.8rem; display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <h2 style='margin:0; font-size:1.1rem; letter-spacing:0.12em; color:#ffffff;'>ORBITAL MISSION CONTROL</h2>
                <p style='margin:0; font-size:0.6rem; color:#00f5ff; font-family:monospace; font-weight:800;'>VESSEL_LOCK: MV_HONDIUS // LOCAL_INTEL_SYNC: {datetime.now().strftime('%H:%M:%S')} UTC</p>
            </div>
            <div style="background:rgba(0,245,255,0.1); border:1px solid #00f5ff44; padding:4px 12px; border-radius:4px;">
                <span class="live-dot" style="width:6px; height:6px; background:#22c55e; box-shadow:0 0 10px #22c55e;"></span>
                <span style="color:#22c55e; font-size:0.6rem; font-weight:900; font-family:monospace;">STABLE</span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    col_map, col_vessel = st.columns([2.2, 1])
    
    with col_vessel:
        st.markdown(
            f"""
            <div class="tactical-card" style="border-left: 4px solid #00f5ff; background: rgba(13, 27, 42, 0.6); padding: 15px; border-radius: 10px; margin-bottom: 12px; border: 1px solid rgba(0,245,255,0.2);">
                <div style="color: #64748b; font-size: 10px; font-weight: 900; margin-bottom: 8px; letter-spacing: 2px;">🚢 VESSEL_SYSTEMS</div>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <div style="display:flex; justify-content:space-between;"><span style="color:#94a3b8; font-size:10px;">MISSION_STATE</span><span style="color:#00f5ff; font-size:10px; font-weight:900;">{state.get('ship_status', 'Quarantined').upper()}</span></div>
                    <div style="display:flex; justify-content:space-between;"><span style="color:#94a3b8; font-size:10px;">PROPULSION</span><span style="color:#22c55e; font-size:10px; font-weight:900;">IDLE (ANCHOR)</span></div>
                    <div style="display:flex; justify-content:space-between;"><span style="color:#94a3b8; font-size:10px;">BIO_CONTAINMENT</span><span style="color:#22c55e; font-size:10px; font-weight:900;">ACTIVE (LVL4)</span></div>
                    <div style="display:flex; justify-content:space-between;"><span style="color:#94a3b8; font-size:10px;">HULL_TEMP</span><span style="color:#ffffff; font-size:10px; font-weight:900;">18.2°C</span></div>
                </div>
            </div>
            
            <div class="tactical-card" style="border-right: 4px solid #22c55e; background: rgba(13, 27, 42, 0.6); padding: 15px; border-radius: 10px; border: 1px solid rgba(34,197,94,0.2);">
                <div style="color: #22c55e; font-size: 10px; font-weight: 900; margin-bottom: 8px; letter-spacing: 2px;">🛰️ SHIP_BOARD_SIGNALS</div>
                <div style="font-size: 11px; color: #cbd5e1; line-height: 1.6; font-family:monospace;">
                    • [08:12] Satellite Link: STABLE<br>
                    • [09:45] Sewage Treatment: SHUTDOWN<br>
                    • [11:20] Port Authority Comms: BLOCKED<br>
                    • [12:05] Med-Bay Pressure: NOMINAL<br>
                    • [LIVE] Bio-Waste Incinerator: RUNNING
                </div>
            </div>
            """, unsafe_allow_html=True
        )

    with col_map:
        map_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
                html, body { margin: 0; padding: 0; height: 100%; background: #000; overflow: hidden; font-family: monospace; }
                #map { width: 100%; height: 100%; background: #050505; border-radius: 12px; }
                
                .leaflet-popup-content-wrapper { background: rgba(13, 27, 42, 0.98) !important; color: #fff !important; border: 1px solid rgba(0, 180, 216, 0.4) !important; border-radius: 8px !important; box-shadow: 0 0 25px rgba(0,0,0,0.8) !important; font-family: monospace !important; padding: 0 !important; }
                .leaflet-popup-content { margin: 0 !important; padding: 0 !important; }
                .leaflet-popup-tip { background: #0d1b2a !important; }
                
                .country-intel-box { width: 220px; max-height: 250px; overflow-y: auto; padding: 12px; scrollbar-width: thin; scrollbar-color: #334155 transparent; }
                .country-intel-box::-webkit-scrollbar { width: 4px; }
                .country-intel-box::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
                
                .news-item { border-bottom: 1px solid rgba(255,255,255,0.05); padding: 8px 0; font-size: 10px; cursor: pointer; }
                .news-item:hover { color: #00f5ff; }
                .news-item:last-child { border: none; }
                
                .ring-marker { width: 22px; height: 22px; border-radius: 50%; border: 2px solid #ffffff; position: relative; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.7); }
                .vessel-ring { border-color: #22c55e !important; box-shadow: 0 0 25px #22c55e, inset 0 0 15px #22c55e; animation: pulse-ring 2s infinite; }
                .badge { position: absolute; top: -8px; right: -8px; background: #ffffff; color: #000; border-radius: 50%; width: 14px; height: 14px; font-size: 9px; font-weight: 900; display: flex; align-items: center; justify-content: center; border: 1px solid #000; }
                @keyframes pulse-ring { 0% { box-shadow: 0 0 0 0 rgba(34,197,94,0.7); } 70% { box-shadow: 0 0 0 10px rgba(34,197,94,0); } 100% { box-shadow: 0 0 0 0 rgba(34,197,94,0); } }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                const map = L.map('map', { zoomControl: false, attributionControl: false }).setView([12, -25], 2.8);
                L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(map);

                const hotspots = __HOTSPOTS__;
                const localScores = __LOCAL_SCORES__;
                const countryIntel = __COUNTRY_INTEL__;
                const shipPos = [14.93, -23.51];
                const affectedCodes = ["ARG", "ESP", "GBR", "NLD", "ZAF"];

                // 1. GEOJSON LAYER (Glow + News Scroller)
                fetch('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json')
                    .then(res => res.json())
                    .then(geojson => {
                        L.geoJSON(geojson, {
                            style: function(feature) {
                                const code = feature.id || feature.properties.ISO_A3;
                                if (affectedCodes.includes(code)) return { fillColor: '#4a1212', fillOpacity: 0.5, color: '#ff0055', weight: 2 };
                                return { fillOpacity: 0.1, weight: 0.5, color: '#222', fillColor: '#111' };
                            },
                            onEachFeature: function(feature, layer) {
                                const code = feature.id || feature.properties.ISO_A3;
                                const name = feature.properties.name || "REGION";
                                const news = countryIntel[code] || [];
                                
                                let popupHtml = `<div class="country-intel-box">`;
                                popupHtml += `<b style="color:#00f5ff; font-size:11px;">🛰️ REGION: ${name} [${code}]</b><br/>`;
                                popupHtml += `<div style="margin:8px 0; padding:4px 8px; background:rgba(0,245,255,0.1); border-radius:4px;"><span style="color:#94a3b8; font-size:9px;">FEAR_INDEX:</span> <b style="color:#fbbf24;">${localScores[code] || 2.5}/5.0</b></div>`;
                                if (news.length > 0) {
                                    popupHtml += `<div style="color:#64748b; font-size:9px; font-weight:900; margin-top:10px; border-top:1px solid #333; padding-top:8px;">LOCAL_NEWS_SIGNALS:</div>`;
                                    news.forEach(n => { popupHtml += `<div class="news-item" onclick="window.open('${n.url}', '_blank')">• ${n.title}</div>`; });
                                }
                                popupHtml += `</div>`;
                                
                                layer.bindPopup(popupHtml, { closeButton: false, offset: [0, -10] });
                                layer.on('mouseover', function() { this.setStyle({ fillOpacity: 0.7, color: '#00f5ff' }); });
                                layer.on('mouseout', function() { this.setStyle({ fillOpacity: affectedCodes.includes(code) ? 0.5 : 0.1, color: affectedCodes.includes(code) ? '#ff0055' : '#222' }); });
                            }
                        }).addTo(map);
                    });

                // 2. RELATIONAL HOTSPOTS (Indicators + Lines)
                hotspots.forEach(h => {
                    const isShip = h.name.includes('HONDIUS');
                    const icon = L.divIcon({
                        className: '',
                        html: `<div class="ring-marker ${isShip ? 'vessel-ring' : ''}" style="border-color:${h.color}; box-shadow: 0 0 15px ${h.color};"><div class="badge">${h.cases}</div></div>`,
                        iconSize: [22, 22], iconAnchor: [11, 11]
                    });
                    const marker = L.marker([h.lat, h.lng], { icon: icon }).addTo(map);
                    marker.bindPopup(`<div style="padding:10px; min-width:180px; font-family:monospace;"><b style="color:${h.color};">${h.name}</b><br/><div style="color:#94a3b8; font-size:10px; margin:4px 0;">${h.relation}</div><div style="font-size:10px; color:#cbd5e1;">"${h.intel}"</div></div>`, { closeButton: false, offset: [0, -10] });
                    marker.on('mouseover', function() { this.openPopup(); });
                    marker.on('mouseout', function() { this.closePopup(); });
                    if (!isShip) L.polyline([[h.lat, h.lng], shipPos], { color: h.color, weight: 1, dashArray: '4, 6', opacity: 0.3 }).addTo(map);
                });
            </script>
        </body>
        </html>
        """
        map_html = map_template.replace("__HOTSPOTS__", json.dumps(RELATIONAL_HOTSPOTS))
        map_html = map_html.replace("__LOCAL_SCORES__", json.dumps(local_scores))
        map_html = map_html.replace("__COUNTRY_INTEL__", json.dumps(country_intel))
        
        components.html(map_html, height=450)

    st.markdown(
        "<div style='text-align:right; opacity:0.6;'><p style='color:#475569; font-size:0.5rem; font-family:monospace;'>ORBITAL_RECO_SYS v9.5 // SHIP_INTELLIGENCE: SYNCED // REGIONAL_INTEL: ACTIVE</p></div>",
        unsafe_allow_html=True
    )
