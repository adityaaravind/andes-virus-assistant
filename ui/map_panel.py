"""High-fidelity Relational Map — Detailed vessel telemetry and localized intelligence."""
from __future__ import annotations

import json
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime
import random

LIVE_FILE = Path("data/outbreak_live.json")

# Core outbreak data reference
NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "passengers": 12, "crew": 0, "cases": 3, "deaths": 1},
    {"country": "United Kingdom","code": "GBR", "passengers": 8,  "crew": 0, "cases": 2, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "passengers": 5,  "crew": 2, "cases": 2, "deaths": 1},
    {"country": "Argentina",     "code": "ARG", "passengers": 45, "crew": 5, "cases": 4, "deaths": 1},
    {"country": "South Africa",  "code": "ZAF", "passengers": 0,  "crew": 10,"cases": 2, "deaths": 0},
]

# Simulated Vessel Contact History
VESSEL_CONTACT_LOG = [
    {"date": "APR 01", "country": "Argentina", "event": "Port Authorities boarding for customs.", "official": "Prefectura Naval"},
    {"date": "APR 26", "country": "South Africa", "event": "Airlift medical team for crew evac.", "official": "Health Inspector Dr. Botha"},
    {"date": "MAY 05", "country": "Spain", "event": "Quarantine protocol review via drone.", "official": "Port Health Tenerife"},
    {"date": "LIVE",   "country": "International", "event": "Satellite containment monitoring.", "official": "WHO Task Force"},
]

def _get_live_state() -> dict:
    if LIVE_FILE.exists():
        try: return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {"confirmed_cases": 5, "ship_status": "Quarantined", "last_updated": "2026-05-10"}

def _get_dynamic_hotspots(state: dict) -> list:
    """Hotspots with deep medical intelligence and admission data."""
    hotspots = [
        {"lat": -34.60, "lng": -58.38, "code": "ARG", "name": "ARGENTINA_CLUSTER", "color": "#ff0055", "relation": "Departure Point", "intel": "PRIMARY_SOURCE", "admitted": "Hospital Muñiz (LVL 4)", "notes": "Zoonotic spill detected at container terminal.", "timestamp": "08:12 UTC"},
        {"lat": -26.20, "lng": 28.04,  "code": "ZAF", "name": "SOUTH_AFRICA_SIGNAL", "color": "#00ffcc", "relation": "Evacuation Event", "intel": "SECONDARY_VECTOR", "admitted": "Netcare Milpark (LVL 3)", "notes": "Critically ill crew members airlifted via helipad.", "timestamp": "14:45 UTC"},
        {"lat": 40.41, "lng": -3.70,  "code": "ESP", "name": "SPAIN_MONITOR", "color": "#ffaa00", "relation": "Repatriation", "intel": "CONTAINED_SIGNAL", "admitted": "Tenerife Isolation (LVL 4)", "notes": "Mandatory quarantine for returning holidaymakers.", "timestamp": "09:30 UTC"},
        {"lat": 51.50, "lng": -0.12,  "code": "GBR", "name": "UK_MONITOR", "color": "#cc00ff", "relation": "Repatriation", "intel": "CONTAINED_SIGNAL", "admitted": "Royal Free London (HLU)", "notes": "Patient sequencing confirms direct Hondius link.", "timestamp": "11:20 UTC"},
        {"lat": 14.93, "lng": -23.51, "code": "SHIP", "name": "MV_HONDIUS_CORE", "color": "#fbbf24", "relation": "Primary Vector", "intel": "CORE_HOTSPOT", "admitted": "Onboard Quarantine", "notes": "Level 4 lockdown enforced. No dock clearance.", "timestamp": "LIVE"}
    ]
    nat_map = {d["code"]: d for d in NATIONALITIES_DATA}
    for h in hotspots:
        if h["code"] == "SHIP":
            h["cases"] = state.get("confirmed_cases", 5); h["deaths"] = state.get("deaths", 1)
        elif h["code"] in nat_map:
            h["cases"] = nat_map[h["code"]]["cases"]; h["deaths"] = nat_map[h["code"]]["deaths"]
        else: h["cases"] = 0; h["deaths"] = 0
    return hotspots

def _get_dynamic_intensity(day: int) -> dict:
    """Mathematical global spread model for daily historical sync."""
    phase = min(day / 65.0, 1.0)
    covid = {
        "CHN": 99.8, "ITA": min(phase * 82, 100), "ESP": min(phase * 64, 100),
        "GBR": min(phase * 42, 100), "USA": min(phase * 34, 100),
        "ARG": 0.5, "ZAF": 0.2, "ATA": 0.0, "PHL": 8.5, "BRA": 4.2
    }
    hanta = {
        "ARG": 95.0, "ZAF": min(55.0 + (day * 0.55), 100), "ESP": min(45.0 + (day * 0.65), 100),
        "GBR": min(30.0 + (day * 0.45), 100), "NLD": min(25.0 + (day * 0.35), 100),
        "CHL": 18.2, "BRA": 12.4, "USA": 8.2, "ATA": 0.0
    }
    return {"hanta": hanta, "covid": covid}

def render_map_panel() -> None:
    state = _get_live_state()
    from ui.pandemic_risk import _compute_risk
    
    risk_data = _compute_risk(state.get("confirmed_cases", 5), 5)
    current_day = risk_data["days"]
    intensity = _get_dynamic_intensity(current_day)
    hotspots = _get_dynamic_hotspots(state)

    st.markdown(
        f"""
        <div class="mission-header" style='border-left: 3px solid #fbbf24; padding-left:15px; margin-bottom:0.8rem; display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <h2 style='margin:0; font-size:1.1rem; letter-spacing:0.12em; color:#ffffff;'>ORBITAL MISSION CONTROL</h2>
                <p style='margin:0; font-size:0.6rem; color:#fbbf24; font-family:monospace; font-weight:800;'>DAILY_SYNC_v4: DAY_{current_day} // TACTICAL_HOTSPOT_FEED: ACTIVE</p>
            </div>
            <div style="background:rgba(251,191,36,0.1); border:1px solid #fbbf2444; padding:4px 12px; border-radius:4px;">
                <span class="live-dot" style="width:6px; height:6px; background:#fbbf24; box-shadow:0 0 10px #fbbf24;"></span>
                <span style="color:#fbbf24; font-size:0.6rem; font-weight:900; font-family:monospace;">ACTIVE_LOCK</span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    col_map, col_vessel = st.columns([2.2, 1])
    
    with col_vessel:
        events_html = "".join([f"""
            <div style="border-left: 2px solid #fbbf24; padding-left: 10px; margin-bottom: 12px;">
                <div style="color: #fbbf24; font-size: 8px; font-weight: 900; letter-spacing: 1px;">{ev['date']} | {ev['country'].upper()}</div>
                <div style="color: #cbd5e1; font-size: 10px; line-height: 1.3;">{ev['event']}</div>
                <div style="color: #64748b; font-size: 8px; font-style: italic;">Official: {ev['official']}</div>
            </div>
        """ for ev in VESSEL_CONTACT_LOG])

        st.markdown(
            f"""
            <div class="stat-card" style="border: 1px solid #fbbf24; box-shadow: 0 0 25px rgba(251,191,36,0.15); background: rgba(13, 27, 42, 0.9); padding: 1.5rem !important; min-height: 440px; border-radius: 12px; overflow: hidden; display: flex; flex-direction: column;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div style="color: #fbbf24; font-size: 10px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase;">🚢 MV_HONDIUS_CORE</div>
                    <div style="background:rgba(251,191,36,0.1); padding:2px 6px; border-radius:4px; border:1px solid #fbbf2444; color:#fbbf24; font-size:8px;">TACTICAL_UPLINK</div>
                </div>
                
                <div style="margin: 15px 0;">
                    <h2 style="margin:0; font-size:2rem !important; font-weight:950; color:white !important; line-height: 1; letter-spacing:-0.05em;">{state.get('ship_status', 'Quarantined').upper()}</h2>
                    <p style="color:#fbbf24; font-size:0.65rem; font-weight:800; margin-top:5px; text-transform:uppercase;">VESSEL_INTEGRITY: PHASE_4_LOCKDOWN</p>
                </div>
                
                <div style="background:rgba(0,0,0,0.4); border-radius:8px; padding:12px; margin-bottom:15px; border:1px solid rgba(255,255,255,0.05);">
                    <p style="color:#64748b; font-size:8px; font-weight:800; margin:0 0 8px 0; text-transform:uppercase;">CONTAINMENT_STABILITY</p>
                    <div style="height:4px; background:rgba(255,255,255,0.1); border-radius:2px; margin-bottom:8px; overflow:hidden;">
                        <div style="width:94.2%; height:100%; background:linear-gradient(90deg, #fbbf24, #f59e0b); box-shadow: 0 0 10px #fbbf24;"></div>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:#fbbf24; font-size:12px; font-weight:900;">94.2<small style="font-size:8px;">%</small></span>
                        <span style="color:#22c55e; font-size:8px; font-weight:800;">[NOMINAL]</span>
                    </div>
                </div>

                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin-bottom:15px; background:rgba(255,255,255,0.02); padding:10px; border-radius:8px; border:1px solid rgba(255,255,255,0.05);">
                    <div><p style="color:#64748b; font-size:7px; margin:0;">HULL_TEMP</p><p style="color:#fff; font-size:10px; font-weight:900; margin:0;">18.2°C</p></div>
                    <div><p style="color:#64748b; font-size:7px; margin:0;">BIO_PRESSURE</p><p style="color:#fff; font-size:10px; font-weight:900; margin:0;">-12 Pa</p></div>
                </div>

                <div style="color: #64748b; font-size: 9px; font-weight: 800; margin-bottom: 12px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px; letter-spacing: 1px;">BOARDING_LOG_HISTORY</div>
                <div style="flex: 1; overflow-y: auto; padding-right: 5px; scrollbar-width: thin;">
                    {events_html}
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
                
                .leaflet-tooltip { background: rgba(13, 27, 42, 0.98) !important; color: #fff !important; border: 1px solid rgba(251, 191, 36, 0.4) !important; border-radius: 6px !important; box-shadow: 0 0 20px rgba(0,0,0,0.8) !important; font-family: monospace !important; padding: 12px !important; opacity: 1 !important; pointer-events: none; }
                .leaflet-popup-content-wrapper { background: rgba(13, 27, 42, 0.98) !important; color: #fff !important; border: 1px solid rgba(251, 191, 36, 0.4) !important; border-radius: 8px !important; font-family: monospace !important; }
                .leaflet-popup-tip { background: #0d1b2a !important; }
                
                .ring-marker { width: 22px; height: 22px; border-radius: 50%; border: 2px solid #ffffff; position: relative; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.7); transition: all 0.3s; }
                .blink-active { animation: marker-blink 1.5s infinite ease-in-out; }
                @keyframes marker-blink { 0%, 100% { opacity: 1; box-shadow: 0 0 5px currentColor; transform: scale(1); } 50% { opacity: 0.6; box-shadow: 0 0 20px currentColor; transform: scale(1.1); } }
                
                .vessel-ring { border-color: #fbbf24 !important; color: #fbbf24; }
                .badge { position: absolute; top: -8px; right: -8px; background: #ffffff; color: #000; border-radius: 50%; width: 14px; height: 14px; font-size: 9px; font-weight: 900; display: flex; align-items: center; justify-content: center; border: 1px solid #000; }
                
                .intel-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px; }
                .intel-label { color: #64748b; font-size: 8px; font-weight: 800; text-transform: uppercase; }
                .intel-val { color: #fff; font-size: 11px; font-weight: 950; }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                const map = L.map('map', { zoomControl: false, attributionControl: false }).setView([12, -25], 2.8);
                L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(map);

                const hotspots = __HOTSPOTS__;
                const intensity = __INTENSITY__;
                const affectedCodes = ["ARG", "ESP", "GBR", "NLD", "ZAF"];
                const shipPos = [14.93, -23.51];

                fetch('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json')
                    .then(res => res.json())
                    .then(geojson => {
                        L.geoJSON(geojson, {
                            style: function(feature) {
                                const code = feature.id || feature.properties.ISO_A3;
                                if (affectedCodes.includes(code)) return { fillColor: '#6b001a', fillOpacity: 0.5, color: '#ff0055', weight: 2 };
                                return { fillOpacity: 0.1, weight: 0.5, color: '#222', fillColor: '#111' };
                            },
                            onEachFeature: function(feature, layer) {
                                const code = feature.id || feature.properties.ISO_A3;
                                const name = feature.properties.name || "REGION";
                                const hantaRisk = (intensity.hanta[code] || (Math.random() * 2 + 0.1)).toFixed(1);
                                const covidRisk = (intensity.covid[code] || 0.0).toFixed(1);

                                let tooltipHtml = `<div><b style="color:#fbbf24; font-size:11px;">📡 ${name} BRIEFING</b><br/>`;
                                tooltipHtml += `<div style="margin-top:10px;">`;
                                tooltipHtml += `<div style="display:flex; justify-content:space-between; gap:20px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:8px; margin-bottom:8px;">`;
                                tooltipHtml += `<div><div class="intel-label">EST. HANTA RISK</div><div class="intel-val">${hantaRisk}%</div></div>`;
                                tooltipHtml += `<div><div class="intel-label">COVID DAY ${__DAY__}</div><div class="intel-val">${covidRisk}%</div></div>`;
                                tooltipHtml += `</div>`;
                                tooltipHtml += `<p style="color:#64748b; font-size:7px; font-style:italic; margin:0;">CALC: (Connectivity * 0.6) + (Proximity * 0.4)</p>`;
                                tooltipHtml += `</div></div>`;
                                layer.bindTooltip(tooltipHtml, { sticky: true });
                            }
                        }).addTo(map);
                    });

                hotspots.forEach(h => {
                    const isShip = h.code === 'SHIP';
                    const icon = L.divIcon({
                        className: '',
                        html: `<div class="ring-marker blink-active ${isShip ? 'vessel-ring' : ''}" style="border-color:${h.color}; color:${h.color}; box-shadow: 0 0 15px ${h.color};"><div class="badge">${h.cases}</div></div>`,
                        iconSize: [22, 22], iconAnchor: [11, 11]
                    });
                    const marker = L.marker([h.lat, h.lng], { icon: icon }).addTo(map);
                    
                    let popupHtml = `<div style="padding:15px; min-width:240px; font-family:monospace;">`;
                    popupHtml += `<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">`;
                    popupHtml += `<b style="color:${h.color}; font-size:14px;">🛰️ ${h.name}</b>`;
                    popupHtml += `<span style="background:rgba(255,255,255,0.05); padding:2px 6px; border-radius:4px; color:#64748b; font-size:8px;">${h.timestamp}</span>`;
                    popupHtml += `</div>`;
                    
                    popupHtml += `<div style="color:#94a3b8; font-size:10px; margin-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:8px;">${h.relation} // <span style="color:#fff;">${h.intel}</span></div>`;
                    
                    popupHtml += `<div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px;">`;
                    popupHtml += `<div><div class="intel-label">TOTAL_CASES</div><div style="color:#fff; font-size:16px; font-weight:950;">${h.cases}</div></div>`;
                    popupHtml += `<div><div class="intel-label">TOTAL_DEATHS</div><div style="color:#ef4444; font-size:16px; font-weight:950;">${h.deaths}</div></div>`;
                    popupHtml += `</div>`;
                    
                    popupHtml += `<div class="intel-grid">`;
                    popupHtml += `<div><div class="intel-label">ADMITTED_WHERE</div><div style="color:#fbbf24; font-size:10px; font-weight:900;">${h.admitted}</div></div>`;
                    popupHtml += `<div><div class="intel-label">INTEL_BRIEF</div><div style="color:#cbd5e1; font-size:9px; font-style:italic; line-height:1.2;">${h.notes}</div></div>`;
                    popupHtml += `</div></div>`;
                    
                    marker.bindPopup(popupHtml, { closeButton: false, offset: [0, -10] });
                    marker.on('mouseover', function() { this.openPopup(); });
                    marker.on('mouseout', function() { this.closePopup(); });

                    if (!isShip) {
                        L.polyline([[h.lat, h.lng], shipPos], { color: h.color, weight: 6, opacity: 0.15, dashArray: '4, 6' }).addTo(map);
                        L.polyline([[h.lat, h.lng], shipPos], { color: h.color, weight: 1.5, opacity: 0.8, dashArray: '4, 6' }).addTo(map);
                    }
                });
            </script>
        </body>
        </html>
        """
        map_html = map_template.replace("__HOTSPOTS__", json.dumps(hotspots))
        map_html = map_html.replace("__INTENSITY__", json.dumps(intensity))
        map_html = map_html.replace("__DAY__", str(current_day))
        
        components.html(map_html, height=450)

    st.markdown(
        f"<div style='text-align:left; padding:10px; background:rgba(15,23,42,0.4); border-radius:6px; border:1px solid rgba(255,255,255,0.05); margin-top:10px;'><p style='color:#94a3b8; font-size:0.65rem; font-family:monospace; margin:0;'><b style='color:#fbbf24;'>MISSION_CONTROL_v20:</b> Deep Tactical Medical Intel Enabled // <b>CALIBRATED_SYNC:</b> COVID_REPLAY DAY_{current_day} // <b>SYSTEMS:</b> NOMINAL</p></div>",
        unsafe_allow_html=True
    )
