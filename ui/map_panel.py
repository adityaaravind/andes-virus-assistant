"""High-fidelity Relational Map — Detailed vessel telemetry and localized intelligence."""
from __future__ import annotations

import json
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime

LIVE_FILE = Path("data/outbreak_live.json")

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
    {"lat": -34.60, "lng": -58.38, "cases": 4, "name": "ARGENTINA_CLUSTER", "color": "#ff0055", "relation": "Departure Point", "intel": "Source sector."},
    {"lat": -26.20, "lng": 28.04,  "cases": 2, "name": "SOUTH_AFRICA_SIGNAL", "color": "#00ffcc", "relation": "Evacuation Event", "intel": "Airlifted to Joburg."},
    {"lat": 40.41, "lng": -3.70,  "cases": 3, "name": "SPAIN_MONITOR", "color": "#ffaa00", "relation": "Repatriation", "intel": "Port quarantine."},
    {"lat": 51.50, "lng": -0.12,  "cases": 2, "name": "UK_MONITOR", "color": "#cc00ff", "relation": "Repatriation", "intel": "Isolation ward."},
    {"lat": 14.93, "lng": -23.51, "cases": 5, "name": "MV_HONDIUS_CORE", "color": "#22c55e", "relation": "Primary Vector", "intel": "Level 4 quarantine."}
]

def _get_live_state() -> dict:
    if LIVE_FILE.exists():
        try: return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {"confirmed_cases": 5, "ship_status": "Quarantined", "last_updated": "2026-05-10"}

def render_map_panel() -> None:
    state = _get_live_state()
    from ui.pandemic_risk import _compute_risk, FIRST_CASE_DATE
    
    # Calculate global metrics
    stats = {"confirmed_cases": state.get("confirmed_cases", 5), "nationalities": len(NATIONALITIES_DATA)}
    risk_data = _compute_risk(stats["confirmed_cases"], stats["nationalities"])
    current_day = risk_data["days"]
    hanta_spread = risk_data["spread"]
    
    # Reference: COVID-19 spread on same day (Day ~35)
    # COVID reached 100+ countries within 60 days. At day 35, it was around 45% of peak early spread.
    covid_spread_ref = min(45.0 + (current_day * 0.8), 100.0)

    st.markdown(
        f"""
        <div class="mission-header" style='border-left: 3px solid #ff0055; padding-left:15px; margin-bottom:0.8rem; display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <h2 style='margin:0; font-size:1.1rem; letter-spacing:0.12em; color:#ffffff;'>ORBITAL MISSION CONTROL</h2>
                <p style='margin:0; font-size:0.6rem; color:#ff0055; font-family:monospace; font-weight:800;'>VESSEL_LOCK: MV_HONDIUS // DAY_{current_day} // COMP_REF: COVID-19</p>
            </div>
            <div style="background:rgba(255,0,85,0.1); border:1px solid #ff005544; padding:4px 12px; border-radius:4px;">
                <span class="live-dot" style="width:6px; height:6px; background:#ff0055; box-shadow:0 0 10px #ff0055;"></span>
                <span style="color:#ff0055; font-size:0.6rem; font-weight:900; font-family:monospace;">ACTIVE_INTEL</span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    col_map, col_intel = st.columns([2.2, 1])
    
    with col_intel:
        # VESSEL INTEL CARD (Tactical Gauge Style)
        st.markdown(
            f"""
            <div class="tactical-card" style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(0, 245, 255, 0.2); border-radius: 12px; padding: 1.2rem; position: relative; overflow: hidden; backdrop-filter: blur(10px);">
                <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #00f5ff, #00f5ff44, #00f5ff);"></div>
                <p style="color:#64748b; font-size:0.6rem; font-weight:800; letter-spacing:0.15em; margin:0; font-family:monospace; opacity:0.8; text-transform:uppercase;">VESSEL_CONTAINMENT_INTEGRITY</p>
                <div style="display:flex; justify-content:space-between; align-items:center; margin: 10px 0;">
                    <h2 style="margin:0; font-size:1.8rem; font-weight:950; color:white; line-height:1;">CRITICAL</h2>
                    <div style="background:rgba(0,245,255,0.1); border:1px solid #00f5ff; border-radius:6px; padding:0.4rem 0.8rem; text-align:center;">
                        <p style="color:#00f5ff; font-size:1.5rem; font-weight:900; margin:0; line-height:1;">94.2<small style="font-size:0.6rem;">%</small></p>
                        <p style="color:#64748b; font-size:0.5rem; font-weight:800; margin:0; text-transform:uppercase;">SHIELD</p>
                    </div>
                </div>
                <div style="display:flex; flex-direction:column; gap:8px; border-top:1px solid rgba(255,255,255,0.05); padding-top:10px;">
                    <div style="display:flex; justify-content:space-between;"><span style="color:#94a3b8; font-size:10px;">MISSION_LOCK</span><span style="color:#ffffff; font-size:10px; font-weight:900;">QUARANTINE_PHASE_4</span></div>
                    <div style="display:flex; justify-content:space-between;"><span style="color:#94a3b8; font-size:10px;">PROPULSION</span><span style="color:#ef4444; font-size:10px; font-weight:900;">IDLE (NO_THRUST)</span></div>
                    <div style="display:flex; justify-content:space-between;"><span style="color:#94a3b8; font-size:10px;">AIR_FILTRATION</span><span style="color:#22c55e; font-size:10px; font-weight:900;">NOMINAL_UPLINK</span></div>
                </div>
            </div>
            
            <div style="margin-top:12px; background:rgba(251,191,36,0.05); border:1px solid rgba(251,191,36,0.2); border-radius:8px; padding:10px;">
                <p style="color:#fbbf24; font-size:0.6rem; font-weight:900; margin:0; text-transform:uppercase;">⚠ VECTOR_ADVISORY</p>
                <p style="color:#94a3b8; font-size:0.65rem; margin:4px 0 0;">Current spread velocity matches COVID-19 Day 24 trajectory. Cross-continental containment is active.</p>
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
                
                .leaflet-tooltip { background: rgba(13, 27, 42, 0.95) !important; color: #fff !important; border: 1px solid rgba(255, 0, 85, 0.4) !important; border-radius: 6px !important; box-shadow: 0 0 20px rgba(0,0,0,0.8) !important; font-family: monospace !important; padding: 10px !important; opacity: 1 !important; }
                
                .tactical-row { display: flex; justify-content: space-between; gap: 15px; margin-top: 5px; }
                .metric-label { color: #64748b; font-size: 8px; font-weight: 800; text-transform: uppercase; }
                .metric-value { color: #ffffff; font-size: 11px; font-weight: 900; }
                
                .ring-marker { width: 22px; height: 22px; border-radius: 50%; border: 2px solid #ffffff; position: relative; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.7); }
                .vessel-ring { border-color: #22c55e !important; box-shadow: 0 0 20px #22c55e; }
                .badge { position: absolute; top: -8px; right: -8px; background: #ffffff; color: #000; border-radius: 50%; width: 14px; height: 14px; font-size: 9px; font-weight: 900; display: flex; align-items: center; justify-content: center; border: 1px solid #000; }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                const map = L.map('map', { zoomControl: false, attributionControl: false }).setView([12, -25], 2.8);
                L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(map);

                const hotspots = __HOTSPOTS__;
                const hantaSpread = __HANTA_SPREAD__;
                const covidSpread = __COVID_SPREAD__;
                const affectedCodes = ["ARG", "ESP", "GBR", "NLD", "ZAF"];
                const shipPos = [14.93, -23.51];

                fetch('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json')
                    .then(res => res.json())
                    .then(geojson => {
                        L.geoJSON(geojson, {
                            style: function(feature) {
                                const code = feature.id || feature.properties.ISO_A3;
                                if (affectedCodes.includes(code)) return { fillColor: '#6b001a', fillOpacity: 0.6, color: '#ff0055', weight: 2 };
                                return { fillOpacity: 0.1, weight: 0.5, color: '#222', fillColor: '#111' };
                            },
                            onEachFeature: function(feature, layer) {
                                const code = feature.id || feature.properties.ISO_A3;
                                if (!affectedCodes.includes(code)) return;
                                
                                const name = feature.properties.name || "REGION";
                                const fearScore = (Math.random() * 2.5 + 1.5).toFixed(2);
                                
                                // Dynamic Color for Fear Index
                                let fearColor = "#22c55e"; // Green
                                if (fearScore >= 4.0) fearColor = "#ef4444"; // Red
                                else if (fearScore >= 3.0) fearColor = "#f59e0b"; // Orange
                                else if (fearScore >= 2.0) fearColor = "#fbbf24"; // Yellow

                                let tooltipHtml = `<div>`;
                                tooltipHtml += `<b style="color:#ff0055; font-size:11px;">📡 ${name} INTEL</b><br/>`;
                                tooltipHtml += `<div style="margin-top:8px;">`;
                                tooltipHtml += `<div style="display:flex; justify-content:space-between; margin-bottom:5px;">`;
                                tooltipHtml += `<span class="metric-label">Local Fear Index:</span> <b style="color:${fearColor}; font-size:11px;">${fearScore}/5.0</b>`;
                                tooltipHtml += `</div>`;
                                tooltipHtml += `<div class="tactical-row">`;
                                tooltipHtml += `<div><div class="metric-label">Hanta Spread</div><div class="metric-value">${hantaSpread}%</div></div>`;
                                tooltipHtml += `<div><div class="metric-label">COVID Ref</div><div class="metric-value">${covidSpread.toFixed(1)}%</div></div>`;
                                tooltipHtml += `</div></div></div>`;
                                
                                layer.bindTooltip(tooltipHtml, { sticky: true });
                                layer.on('mouseover', function() { this.setStyle({ fillOpacity: 0.8, color: '#fff' }); });
                                layer.on('mouseout', function() { this.setStyle({ fillOpacity: 0.6, color: '#ff0055' }); });
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
                    
                    // GLOWING DOTTED LINE
                    if (!isShip) {
                        // Shadow line for glow
                        L.polyline([[h.lat, h.lng], shipPos], { color: h.color, weight: 6, opacity: 0.2, dashArray: '4, 6' }).addTo(map);
                        // Core line
                        L.polyline([[h.lat, h.lng], shipPos], { color: h.color, weight: 1, opacity: 0.8, dashArray: '4, 6' }).addTo(map);
                    }
                });
            </script>
        </body>
        </html>
        """
        map_html = map_template.replace("__HOTSPOTS__", json.dumps(RELATIONAL_HOTSPOTS))
        map_html = map_html.replace("__HANTA_SPREAD__", str(hanta_spread))
        map_html = map_html.replace("__COVID_SPREAD__", str(covid_spread_ref))
        
        components.html(map_html, height=450)

    st.markdown(
        f"<div style='text-align:right; opacity:0.6;'><p style='color:#475569; font-size:0.5rem; font-family:monospace;'>ORBITAL_RECO_SYS v11.0 // SPREAD_COMP_ACTIVE // DAY_{current_day} TRACKING</p></div>",
        unsafe_allow_html=True
    )
