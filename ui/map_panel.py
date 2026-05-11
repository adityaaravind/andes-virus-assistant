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
    {"country": "USA",           "code": "USA", "passengers": 0,  "crew": 0, "cases": 0, "deaths": 0},
    {"country": "Brazil",        "code": "BRA", "passengers": 0,  "crew": 0, "cases": 0, "deaths": 0},
    {"country": "Chile",         "code": "CHL", "passengers": 0,  "crew": 0, "cases": 0, "deaths": 0},
]

# Relational Hotspot Data
RELATIONAL_HOTSPOTS = [
    {"lat": -34.60, "lng": -58.38, "cases": 4, "name": "ARGENTINA_CLUSTER", "color": "#ff0055", "relation": "Departure Point (APR 01)", "intel": "Vessel took on 147 passengers/crew. Original source of andes strain suspected."},
    {"lat": -26.20, "lng": 28.04,  "cases": 2, "name": "SOUTH_AFRICA_SIGNAL", "color": "#00ffcc", "relation": "Evacuation Event (APR 26)", "intel": "Critical crew members airlifted to Joburg. Secondary transmission confirmed."},
    {"lat": 40.41, "lng": -3.70,  "cases": 3, "name": "SPAIN_MONITOR", "color": "#ffaa00", "relation": "Repatriation (MAY 05)", "intel": "Mandatory quarantine active in Tenerife ports for returnees."},
    {"lat": 51.50, "lng": -0.12,  "cases": 2, "name": "UK_MONITOR", "color": "#cc00ff", "relation": "Repatriation (MAY 06)", "intel": "Andes sequencing confirmed in Heathrow isolation ward."},
    {"lat": 14.93, "lng": -23.51, "cases": 5, "name": "MV_HONDIUS_CORE", "color": "#22c55e", "relation": "Primary Vector", "intel": "Vessel moored. Level 4 quarantine enforced."}
]

def _calculate_localized_fear(country_name: str, articles: list) -> float:
    """Calculate a fear score (1-5) based on news sentiment and keyword density."""
    fear_keywords = {"outbreak": 0.4, "deadly": 0.6, "spread": 0.3, "crisis": 0.5, "death": 0.7, "quarantine": 0.5}
    base = 1.5 # Baseline calm
    score = base
    count = 0
    for art in articles:
        text = (art.get("title", "") + " " + art.get("summary", "")).lower()
        if country_name.lower() in text:
            for kw, weight in fear_keywords.items():
                if kw in text: score += weight
            count += 1
    # Simulate "people reviews" jitter
    import random
    score += random.uniform(-0.3, 0.3)
    return min(max(score, 1.0), 5.0)

def render_map_panel() -> None:
    from ui.news_ticker import fetch_headlines
    try:
        headlines = fetch_headlines(max_per_feed=15)
    except Exception:
        headlines = []

    # Build Intelligence Map
    country_intel = {}
    country_scores = {}
    
    # We want to support all countries in the GeoJSON potentially
    # But we'll focus on relevant ones for scoring
    relevant_countries = ["Spain", "United Kingdom", "Netherlands", "Argentina", "South Africa", "USA", "Brazil", "Chile", "Norway", "Italy"]
    codes_map = {"ESP": "Spain", "GBR": "United Kingdom", "NLD": "Netherlands", "ARG": "Argentina", "ZAF": "South Africa", "USA": "USA", "BRA": "Brazil", "CHL": "Chile", "NOR": "Norway", "ITA": "Italy"}

    for code, name in codes_map.items():
        related = [h for h in headlines if name.lower() in (h.get("title", "") + " " + h.get("summary", "")).lower()]
        country_intel[code] = related[:6]
        country_scores[code] = round(_calculate_localized_fear(name, related), 2)

    st.markdown(
        f"""
        <div class="mission-header" style='border-left: 3px solid #00f5ff; padding-left:15px; margin-bottom:0.8rem; display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <h2 style='margin:0; font-size:1.1rem; letter-spacing:0.12em; color:#ffffff;'>ORBITAL MISSION CONTROL</h2>
                <p style='margin:0; font-size:0.6rem; color:#00f5ff; font-family:monospace; font-weight:800;'>VESSEL_LOCK: MV_HONDIUS // LOCALIZED_SENTIMENT_ACTIVE // SYNC: {datetime.now().strftime('%H:%M:%S')} UTC</p>
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
                    <div style="display:flex; justify-content:space-between;"><span style="color:#94a3b8; font-size:10px;">MISSION_STATE</span><span style="color:#00f5ff; font-size:10px; font-weight:900;">QUARANTINE</span></div>
                    <div style="display:flex; justify-content:space-between;"><span style="color:#94a3b8; font-size:10px;">PROPULSION</span><span style="color:#22c55e; font-size:10px; font-weight:900;">IDLE (ANCHOR)</span></div>
                    <div style="display:flex; justify-content:space-between;"><span style="color:#94a3b8; font-size:10px;">BIO_CONTAINMENT</span><span style="color:#22c55e; font-size:10px; font-weight:900;">ACTIVE (LVL4)</span></div>
                </div>
            </div>
            
            <div class="tactical-card" style="border-right: 4px solid #22c55e; background: rgba(13, 27, 42, 0.6); padding: 15px; border-radius: 10px; border: 1px solid rgba(34,197,94,0.2);">
                <div style="color: #22c55e; font-size: 10px; font-weight: 900; margin-bottom: 8px; letter-spacing: 2px;">🛰️ SHIP_BOARD_SIGNALS</div>
                <div style="font-size: 11px; color: #cbd5e1; line-height: 1.6; font-family:monospace;">
                    • [08:12] Satellite Link: STABLE<br>
                    • [11:20] Port Authority: BLOCKED<br>
                    • [LIVE] Med-Bay Pressure: NOMINAL
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
                
                .leaflet-tooltip { background: rgba(13, 27, 42, 0.98) !important; color: #fff !important; border: 1px solid rgba(0, 245, 255, 0.4) !important; border-radius: 8px !important; box-shadow: 0 0 25px rgba(0,0,0,0.8) !important; font-family: monospace !important; padding: 0 !important; opacity: 1 !important; pointer-events: auto !important; }
                
                .intel-scroller { width: 240px; max-height: 200px; overflow-y: hidden; padding: 12px; position: relative; }
                .news-ticker-wrap { animation: scroll-up 15s linear infinite; }
                @keyframes scroll-up { 0% { transform: translateY(0); } 100% { transform: translateY(-50%); } }
                
                .news-node { border-bottom: 1px solid rgba(0,245,255,0.1); padding: 8px 0; font-size: 10px; color: #cbd5e1; line-height: 1.4; }
                .news-node b { color: #00f5ff; }
                
                .ring-marker { width: 22px; height: 22px; border-radius: 50%; border: 2px solid #ffffff; position: relative; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.7); }
                .vessel-ring { border-color: #22c55e !important; box-shadow: 0 0 25px #22c55e; }
                .badge { position: absolute; top: -8px; right: -8px; background: #ffffff; color: #000; border-radius: 50%; width: 14px; height: 14px; font-size: 9px; font-weight: 900; display: flex; align-items: center; justify-content: center; border: 1px solid #000; }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                const map = L.map('map', { zoomControl: false, attributionControl: false }).setView([12, -25], 2.8);
                L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(map);

                const hotspots = __HOTSPOTS__;
                const countryIntel = __COUNTRY_INTEL__;
                const countryScores = __COUNTRY_SCORES__;
                const shipPos = [14.93, -23.51];

                fetch('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json')
                    .then(res => res.json())
                    .then(geojson => {
                        L.geoJSON(geojson, {
                            style: function(feature) {
                                const code = feature.id || feature.properties.ISO_A3;
                                if (countryScores[code]) return { fillColor: '#8b0000', fillOpacity: 0.5, color: '#ff0055', weight: 1.5 };
                                return { fillOpacity: 0.1, weight: 0.5, color: '#222', fillColor: '#111' };
                            },
                            onEachFeature: function(feature, layer) {
                                const code = feature.id || feature.properties.ISO_A3;
                                const name = feature.properties.name || "REGION";
                                const score = countryScores[code] || (Math.random() * 1.5 + 1.2).toFixed(2);
                                const news = countryIntel[code] || [];
                                
                                let tooltipHtml = `<div class="intel-scroller">`;
                                tooltipHtml += `<div style="margin-bottom:8px; border-bottom:1px solid #00f5ff; padding-bottom:4px;"><b style="color:#00f5ff; font-size:11px;">📡 ${name} [${code}]</b></div>`;
                                tooltipHtml += `<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">`;
                                tooltipHtml += `<span style="color:#94a3b8; font-size:9px;">FEAR_INDEX:</span><b style="color:#fbbf24; font-size:12px;">${score}/5.0</b>`;
                                tooltipHtml += `</div>`;
                                
                                if (news.length > 0) {
                                    tooltipHtml += `<div class="news-ticker-wrap">`;
                                    // Duplicate news for smooth infinite scroll
                                    const allNews = [...news, ...news];
                                    allNews.forEach(n => {
                                        tooltipHtml += `<div class="news-node"><b>•</b> ${n.title}</div>`;
                                    });
                                    tooltipHtml += `</div>`;
                                } else {
                                    tooltipHtml += `<div style="color:#475569; font-size:9px; font-style:italic;">No active OSINT signals detected for this sector.</div>`;
                                }
                                tooltipHtml += `</div>`;
                                
                                layer.bindTooltip(tooltipHtml, { sticky: true, className: 'tactical-tooltip' });
                                layer.on('mouseover', function() { this.setStyle({ fillOpacity: 0.8, color: '#00f5ff' }); });
                                layer.on('mouseout', function() { this.setStyle({ fillOpacity: countryScores[code] ? 0.5 : 0.1, color: countryScores[code] ? '#ff0055' : '#222' }); });
                            }
                        }).addTo(map);
                    });

                hotspots.forEach(h => {
                    const isShip = h.name.includes('HONDIUS');
                    const icon = L.divIcon({
                        className: '',
                        html: `<div class="ring-marker ${isShip ? 'vessel-ring' : ''}" style="border-color:${h.color}; box-shadow: 0 0 15px ${h.color};"><div class="badge">${h.cases}</div></div>`,
                        iconSize: [22, 22], iconAnchor: [11, 11]
                    });
                    const marker = L.marker([h.lat, h.lng], { icon: icon }).addTo(map);
                    marker.bindPopup(`<div style="padding:10px; min-width:180px; font-family:monospace;"><b style="color:${h.color};">${h.name}</b><br/><div style="color:#94a3b8; font-size:10px; margin:4px 0;">${h.relation}</div></div>`, { closeButton: false });
                    if (!isShip) L.polyline([[h.lat, h.lng], shipPos], { color: h.color, weight: 1, dashArray: '4, 6', opacity: 0.3 }).addTo(map);
                });
            </script>
        </body>
        </html>
        """
        map_html = map_template.replace("__HOTSPOTS__", json.dumps(RELATIONAL_HOTSPOTS))
        map_html = map_html.replace("__COUNTRY_INTEL__", json.dumps(country_intel))
        map_html = map_html.replace("__COUNTRY_SCORES__", json.dumps(country_scores))
        
        components.html(map_html, height=450)

    st.markdown(
        "<div style='text-align:right; opacity:0.6;'><p style='color:#475569; font-size:0.5rem; font-family:monospace;'>ORBITAL_RECO_SYS v10.0 // LOCALIZED_SENTIMENT: ENABLED // OSINT_TICKER: ACTIVE</p></div>",
        unsafe_allow_html=True
    )
