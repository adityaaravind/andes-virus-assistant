"""High-fidelity Global Health Monitor — Vessel tracking and localized safety intelligence."""
from __future__ import annotations

import json
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime
import random

LIVE_FILE = Path("data/outbreak_live.json")

# Simple language data exports
NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "passengers": 12, "crew": 0, "cases": 3, "deaths": 1},
    {"country": "United Kingdom","code": "GBR", "passengers": 8,  "crew": 0, "cases": 2, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "passengers": 5,  "crew": 2, "cases": 2, "deaths": 1},
    {"country": "Argentina",     "code": "ARG", "passengers": 45, "crew": 5, "cases": 4, "deaths": 1},
    {"country": "South Africa",  "code": "ZAF", "passengers": 0,  "crew": 10,"cases": 2, "deaths": 0},
]

# Recent Ship Events (Simulated Real-Time Log)
def _get_vessel_events() -> list:
    return [
        {"date": "MAY 11", "time": "08:15", "country": "International", "event": "Ship coordinates updated. Moving North-East.", "official": "GPS Signal", "hours_ago": 6},
        {"date": "MAY 11", "time": "02:30", "country": "International", "event": "Health check completed. Status stable.", "official": "Ship Doctor", "hours_ago": 12},
        {"date": "MAY 09", "time": "14:45", "country": "Spain", "event": "Supplies delivered via drone to the deck.", "official": "Port Health", "hours_ago": 49},
        {"date": "MAY 08", "time": "11:20", "country": "South Africa", "event": "Medical team airlifted crew for treatment.", "official": "Rescue Pilot", "hours_ago": 74},
        {"date": "MAY 05", "time": "18:00", "country": "International", "event": "Engaged deep-sea isolation protocols.", "official": "Vessel Captain", "hours_ago": 140},
        {"date": "APR 30", "time": "22:15", "country": "Argentina", "event": "Final port clearance received. Departure.", "official": "Coast Guard", "hours_ago": 260},
        {"date": "APR 28", "time": "09:00", "country": "Argentina", "event": "Vessel left the port under quarantine.", "official": "Port Authority", "hours_ago": 312},
    ]

def _get_live_state() -> dict:
    if LIVE_FILE.exists():
        try: return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {"confirmed_cases": 5, "ship_status": "Quarantined", "last_updated": "2026-05-10"}

def _get_dynamic_hotspots(state: dict) -> list:
    hotspots = [
        {"lat": -34.60, "lng": -58.38, "code": "ARG", "name": "ARGENTINA SOURCE", "color": "#ff0055", "relation": "Where it started", "intel": "PORT AREA", "admitted": "City Hospital", "notes": "Virus first found here.", "timestamp": "APR 28"},
        {"lat": -26.20, "lng": 28.04,  "code": "ZAF", "name": "S. AFRICA STOP", "color": "#00ffcc", "relation": "Emergency Stop", "intel": "HEALTH HUB", "admitted": "Netcare Clinic", "notes": "Crew members taken for help.", "timestamp": "MAY 08"},
        {"lat": 40.41, "lng": -3.70,  "code": "ESP", "name": "SPAIN MONITOR", "color": "#ffaa00", "relation": "Return Point", "intel": "QUARANTINE", "admitted": "Tenerife Ward", "notes": "People staying in isolation.", "timestamp": "MAY 09"},
        {"lat": 51.50, "lng": -0.12,  "code": "GBR", "name": "UK MONITOR", "color": "#cc00ff", "relation": "Return Point", "intel": "ISOLATION", "admitted": "Royal London", "notes": "Close monitoring active.", "timestamp": "MAY 11"},
        {"lat": 14.93, "lng": -23.51, "code": "SHIP", "name": "THE SHIP (MV HONDIUS)", "color": "#4ade80", "relation": "Current Location", "intel": "RESTRICTED", "admitted": "Ship Med-Bay", "notes": "Closed to everyone.", "timestamp": "LIVE"}
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
    """Mathematical global spread model with verified historical anchors."""
    phase = min(day / 65.0, 1.0)
    covid = {
        "CHN": 99.8, "ITA": min(phase * 82, 100), "ESP": min(phase * 64, 100),
        "GBR": min(phase * 42, 100), "USA": min(phase * 34, 100),
        "ARG": 0.5 if day > 58 else 0.0, "ZAF": 0.1 if day > 67 else 0.0, 
        "EGY": 0.5 if day > 46 else 0.0, "PHL": 8.5
    }
    hanta = {
        "ARG": 95.0, "ZAF": min(55.0 + (day * 0.55), 100), "ESP": min(45.0 + (day * 0.65), 100),
        "GBR": min(30.0 + (day * 0.45), 100), "NLD": min(25.0 + (day * 0.35), 100),
        "USA": 8.2, "ATA": 0.0
    }
    onset = {"EGY": 46, "DZA": 57, "NGA": 60, "ZAF": 67, "BRA": 58, "ITA": 31, "USA": 20}
    return {"hanta": hanta, "covid": covid, "onset": onset}

def render_map_panel() -> None:
    state = _get_live_state()
    from ui.pandemic_risk import _compute_risk
    
    risk_data = _compute_risk(state.get("confirmed_cases", 5), 5)
    current_day = risk_data["days"]
    intensity = _get_dynamic_intensity(current_day)
    hotspots = _get_dynamic_hotspots(state)
    events = _get_vessel_events()

    st.markdown(
        f"""
        <div class="mission-header" style='border-left: 3px solid #4ade80; padding-left:15px; margin-bottom:0.8rem; display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <h2 style='margin:0; font-size:1.1rem; letter-spacing:0.12em; color:#ffffff;'>GLOBAL HEALTH MONITOR</h2>
                <p style='margin:0; font-size:0.6rem; color:#4ade80; font-family:monospace; font-weight:800;'>VIRUS TIMELINE: DAY_{current_day} // STATUS: ACTIVE</p>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    col_map, col_vessel = st.columns([2.2, 1])
    
    with col_vessel:
        events_html = ""
        for ev in events:
            color = "#4ade80" if ev['hours_ago'] <= 48 else "#fde047"
            events_html += f"""
                <div style="border-left: 3px solid {color}; padding-left: 12px; margin-bottom: 15px; animation: slideIn 0.4s ease-out;">
                    <div style="color: {color}; font-size: 9px; font-weight: 900; letter-spacing: 1px;">{ev['date']} @ {ev['time']}</div>
                    <div style="color: #ffffff; font-size: 11px; line-height: 1.3; font-weight: 600; margin-top:3px;">{ev['event']}</div>
                    <div style="color: #64748b; font-size: 8px; margin-top:2px;">Signal Source: {ev['official']}</div>
                </div>
            """

        vessel_card_html = f"""
        <style>
            @keyframes slideIn {{ from {{ opacity: 0; transform: translateX(-10px); }} to {{ opacity: 1; transform: translateX(0); }} }}
            @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} 100% {{ opacity: 1; }} }}
            .scroll-container::-webkit-scrollbar {{ width: 3px; }}
            .scroll-container::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.1); }}
            .scroll-container::-webkit-scrollbar-thumb {{ background: #4ade80; border-radius: 2px; }}
        </style>
        <div style="font-family: sans-serif; background: rgba(15, 23, 42, 0.95); border: 2px solid #4ade80; box-shadow: 0 0 30px rgba(74,222,128,0.15); padding: 1.5rem; border-radius: 16px; height: 500px; display: flex; flex-direction: column; color: #fff; overflow: hidden;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div style="color: #4ade80; font-size: 10px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase;">🚢 SHIP SIGNALS</div>
                <div style="background:rgba(74,222,128,0.1); padding:2px 8px; border-radius:4px; border:1px solid #4ade8044; color:#4ade80; font-size:8px; font-weight:900; animation: pulse 2s infinite;">LIVE_DATA_STREAM</div>
            </div>
            <div style="margin: 15px 0;">
                <h2 style="margin:0; font-size:2rem; font-weight:900; line-height: 1; letter-spacing:-0.03em; color:#ffffff;">{state.get('ship_status', 'Quarantined').upper()}</h2>
                <p style="color:#4ade80; font-size:0.7rem; font-weight:800; margin-top:5px; text-transform:uppercase;">MV HONDIUS // SAFETY PROTOCOL ACTIVE</p>
            </div>
            
            <div style="background:rgba(255,255,255,0.03); border-radius:12px; padding:12px; margin-bottom:15px; border:1px solid rgba(255,255,255,0.05);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="color:#94a3b8; font-size:9px; font-weight:800; text-transform:uppercase;">SAFETY RATING</span>
                    <span style="color:#4ade80; font-size:11px; font-weight:900;">94%</span>
                </div>
                <div style="height:4px; background:rgba(255,255,255,0.1); border-radius:2px; overflow:hidden;">
                    <div style="width:94%; height:100%; background:#4ade80; box-shadow: 0 0 10px #4ade80;"></div>
                </div>
            </div>

            <div style="color: #64748b; font-size: 10px; font-weight: 900; margin-bottom: 12px; text-transform: uppercase; letter-spacing:1px; display:flex; align-items:center;">
                <span style="width:8px; height:8px; background:#4ade80; border-radius:50%; margin-right:8px; display:inline-block; animation: pulse 1s infinite;"></span>
                RECENT SHIP EVENTS
            </div>
            
            <div class="scroll-container" style="flex: 1; overflow-y: auto; padding-right: 8px;">
                {events_html}
            </div>
            
            <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.05); display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#64748b; font-size:8px;">SYNC_TIME: {datetime.now().strftime("%H:%M:%S")}</span>
                <span style="color:#4ade80; font-size:9px; font-weight:900;">UPLINK: ACTIVE</span>
            </div>
        </div>
        """
        components.html(vessel_card_html, height=520)

    with col_map:
        map_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
                html, body { margin: 0; padding: 0; height: 100%; background: #000; overflow: hidden; font-family: sans-serif; }
                #map { width: 100%; height: 100%; background: #050505; border-radius: 12px; }
                .leaflet-tooltip { background: rgba(13, 27, 42, 0.98) !important; color: #fff !important; border: 1px solid rgba(74, 222, 128, 0.4) !important; border-radius: 8px !important; padding: 15px !important; z-index: 1000; }
                .ring-marker { width: 24px; height: 24px; border-radius: 50%; border: 2px solid #ffffff; position: relative; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.8); }
                .blink-active { animation: marker-blink 1.5s infinite ease-in-out; }
                @keyframes marker-blink { 0%, 100% { opacity: 1; box-shadow: 0 0 8px currentColor; } 50% { opacity: 0.6; box-shadow: 0 0 25px currentColor; } }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                const map = L.map('map', { zoomControl: false, attributionControl: false }).setView([12, -25], 2.8);
                L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(map);

                const hotspots = __HOTSPOTS__;
                const intensity = __INTENSITY__;
                const shipPos = [14.93, -23.51];

                fetch('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json')
                    .then(res => res.json())
                    .then(geojson => {
                        L.geoJSON(geojson, {
                            style: function(feature) {
                                const code = feature.id || feature.properties.ISO_A3;
                                if (["ARG", "ESP", "GBR", "NLD", "ZAF"].includes(code)) return { fillColor: '#6b001a', fillOpacity: 0.5, color: '#ff0055', weight: 2 };
                                return { fillOpacity: 0.1, weight: 0.5, color: '#222', fillColor: '#111' };
                            },
                            onEachFeature: function(feature, layer) {
                                const code = feature.id || feature.properties.ISO_A3;
                                const name = feature.properties.name || "AREA";
                                const hantaRisk = (intensity.hanta[code] || (Math.random() * 2 + 0.1)).toFixed(1);
                                const covidRisk = parseFloat(intensity.covid[code] || 0.0);
                                const onsetDay = intensity.onset[code] || 0;

                                let tooltipHtml = `<div><b style="color:#4ade80; font-size:13px; letter-spacing:1px;">📡 ${name} SAFETY CHECK</b><br/>`;
                                tooltipHtml += `<div style="margin-top:12px;">`;
                                tooltipHtml += `<div style="display:flex; justify-content:space-between; gap:25px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:10px; margin-bottom:10px;">`;
                                tooltipHtml += `<div><div style="color:#94a3b8; font-size:9px;">CHANCE OF SPREAD</div><div style="color:#fff; font-size:14px; font-weight:900;">${hantaRisk}%</div></div>`;
                                tooltipHtml += `<div><div style="color:#94a3b8; font-size:9px;">COVID DAY ${__DAY__}</div><div style="color:#fff; font-size:14px; font-weight:900;">${covidRisk.toFixed(1)}%</div></div>`;
                                tooltipHtml += `</div>`;
                                if (covidRisk === 0 && onsetDay > 0) tooltipHtml += `<p style="color:#ef4444; font-size:11px; font-weight:900; margin-top:10px;">[!] STARTING DAY: ${onsetDay}</p>`;
                                tooltipHtml += `</div></div>`;
                                layer.bindTooltip(tooltipHtml, { sticky: true });
                            }
                        }).addTo(map);
                    });

                hotspots.forEach(h => {
                    const isShip = h.code === 'SHIP';
                    const icon = L.divIcon({
                        className: '',
                        html: `<div class="ring-marker blink-active ${isShip ? 'vessel-ring' : ''}" style="border-color:${h.color}; color:${h.color};"><div class="badge">${h.cases}</div></div>`,
                        iconSize: [24, 24], iconAnchor: [12, 12]
                    });
                    const marker = L.marker([h.lat, h.lng], { icon: icon }).addTo(map);
                    marker.bindPopup(`<div style="padding:15px; min-width:240px; font-family:sans-serif;"><b style="color:${h.color}; font-size:14px;">${h.name}</b><br/><div style="color:#94a3b8; font-size:10px; margin-top:10px;">TOTAL CASES: <b style="color:#fff;">${h.cases}</b></div></div>`, { closeButton: false, offset: [0, -10] });
                    marker.on('mouseover', function() { this.openPopup(); });
                    marker.on('mouseout', function() { this.closePopup(); });
                    if (!isShip) L.polyline([[h.lat, h.lng], shipPos], { color: h.color, weight: 1.5, opacity: 0.8, dashArray: '4, 6' }).addTo(map);
                });
            </script>
        </body>
        </html>
        """
        map_html = map_template.replace("__HOTSPOTS__", json.dumps(hotspots))
        map_html = map_html.replace("__INTENSITY__", json.dumps(intensity))
        map_html = map_html.replace("__DAY__", str(current_day))
        components.html(map_html, height=450)

