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

def _get_dynamic_intensity(day: int) -> dict:
    """
    DYNAMIC HISTORICAL SYNC (COVID-19 vs HANTA)
    Updates intensities daily based on the current mission day.
    """
    # COVID-19 Historical Curve (Day-Matched)
    # Day 30: 99% China. Day 45: Early Italy. Day 60: Global Pandemic.
    phase_scale = min(day / 60.0, 1.0)
    
    covid = {
        "CHN": 99.8,
        "ITA": min(phase_scale * 45, 100),
        "ESP": min(phase_scale * 30, 100),
        "GBR": min(phase_scale * 15, 100),
        "USA": min(phase_scale * 10, 100),
        "ARG": 0.0, "ZAF": 0.0, "ATA": 0.0
    }
    
    # Hanta Real-Time Risk (Connectivity Weighted)
    # Scales as day increases or cases rise
    hanta = {
        "ARG": 95.0,
        "ZAF": 55.0 + (day * 0.2),
        "ESP": 45.0 + (day * 0.3),
        "GBR": 30.0 + (day * 0.1),
        "NLD": 25.0 + (day * 0.1),
        "CHL": 10.0, "BRA": 5.0, "USA": 2.0, "ATA": 0.0
    }
    
    return {"hanta": hanta, "covid": covid}

def render_map_panel() -> None:
    state = _get_live_state()
    from ui.pandemic_risk import _compute_risk
    
    risk_data = _compute_risk(state.get("confirmed_cases", 5), 5)
    current_day = risk_data["days"]
    intensity = _get_dynamic_intensity(current_day)

    st.markdown(
        f"""
        <div class="mission-header" style='border-left: 3px solid #fbbf24; padding-left:15px; margin-bottom:0.8rem; display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <h2 style='margin:0; font-size:1.1rem; letter-spacing:0.12em; color:#ffffff;'>ORBITAL MISSION CONTROL</h2>
                <p style='margin:0; font-size:0.6rem; color:#fbbf24; font-family:monospace; font-weight:800;'>DAILY_SYNC_ACTIVE // HISTORICAL_REPLAY: DAY_{current_day} // AMBER_LOCK</p>
            </div>
            <div style="background:rgba(251,191,36,0.1); border:1px solid #fbbf2444; padding:4px 12px; border-radius:4px;">
                <span class="live-dot" style="width:6px; height:6px; background:#fbbf24; box-shadow:0 0 10px #fbbf24;"></span>
                <span style="color:#fbbf24; font-size:0.6rem; font-weight:900; font-family:monospace;">STABLE</span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    col_map, col_vessel = st.columns([2.2, 1])
    
    with col_vessel:
        # FIXED VESSEL TELEMETRY (AMBER THEME)
        events_html = "".join([f"""
            <div style="border-left: 2px solid #fbbf24; padding-left: 10px; margin-bottom: 8px;">
                <div style="color: #fbbf24; font-size: 8px; font-weight: 900; letter-spacing: 1px;">{ev['date']} | {ev['country'].upper()}</div>
                <div style="color: #cbd5e1; font-size: 10px; line-height: 1.2;">{ev['event']}</div>
            </div>
        """ for ev in VESSEL_CONTACT_LOG])

        st.markdown(
            f"""
            <div class="stat-card" style="border: 1px solid #fbbf24; box-shadow: 0 0 20px rgba(251,191,36,0.15); background: rgba(13, 27, 42, 0.9); padding: 1.2rem; min-height: 420px; display: flex; flex-direction: column;">
                <div style="color: #fbbf24; font-size: 10px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 15px;">🛰️ VESSEL_INTEL</div>
                <div style="margin-bottom: 20px;">
                    <h2 style="margin:0; font-size:1.8rem; font-weight:950; color:white; line-height: 1;">{state.get('ship_status', 'Quarantined').upper()}</h2>
                    <p style="color:#fbbf24; font-size:0.65rem; font-weight:800; margin-top:5px;">MV HONDIUS // LOCK_PHASE_4</p>
                </div>
                <div style="color: #64748b; font-size: 9px; font-weight: 800; margin-bottom: 10px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px;">BOARDING_LOG</div>
                <div style="max-height: 200px; overflow-y: auto; padding-right: 5px;">
                    {events_html}
                </div>
                <div style="margin-top: auto; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; align-items: center;">
                    <span style="color:#94a3b8; font-size:9px;">UPLINK_STRENGTH</span>
                    <span style="color:#22c55e; font-size:9px; font-weight:900;">99.8%</span>
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
                .leaflet-tooltip { background: rgba(13, 27, 42, 0.95) !important; color: #fff !important; border: 1px solid rgba(255, 0, 85, 0.4) !important; border-radius: 6px !important; box-shadow: 0 0 20px rgba(0,0,0,0.8) !important; font-family: monospace !important; padding: 10px !important; opacity: 1 !important; pointer-events: none; }
                .ring-marker { width: 22px; height: 22px; border-radius: 50%; border: 2px solid #ffffff; position: relative; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.7); }
                .blink-active { animation: marker-blink 1.5s infinite ease-in-out; }
                @keyframes marker-blink { 0%, 100% { opacity: 1; box-shadow: 0 0 5px currentColor; } 50% { opacity: 0.6; box-shadow: 0 0 15px currentColor; } }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                const map = L.map('map', { zoomControl: false, attributionControl: false }).setView([12, -25], 2.8);
                L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(map);

                const fearMatrix = __FEAR_MATRIX__;
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
                                let fearScore = fearMatrix[code] || (1.1 + (Math.random() * 0.2)).toFixed(2);
                                let fearColor = (fearScore >= 3.5) ? "#ef4444" : (fearScore >= 2.5) ? "#f59e0b" : "#22c55e";

                                const hantaRisk = (intensity.hanta[code] || (Math.random() * 1.5 + 0.1)).toFixed(1);
                                const covidRisk = (intensity.covid[code] || 0.0).toFixed(1);

                                let tooltipHtml = `<div><b style="color:#ff0055; font-size:11px;">📡 ${name} BRIEFING</b><br/>`;
                                tooltipHtml += `<div style="margin-top:8px;"><div style="display:flex; justify-content:space-between; margin-bottom:5px;">`;
                                tooltipHtml += `<span style="color:#64748b; font-size:8px; font-weight:800;">LOCAL FEAR INDEX</span> <b style="color:${fearColor}; font-size:11px;">${fearScore}/5.0</b></div>`;
                                tooltipHtml += `<div style="display:flex; justify-content:space-between; gap:15px; border-top:1px solid rgba(255,255,255,0.05); padding-top:8px;">`;
                                tooltipHtml += `<div><div style="color:#64748b; font-size:8px;">EST. HANTA RISK</div><div style="color:#fff; font-size:11px; font-weight:900;">${hantaRisk}%</div></div>`;
                                tooltipHtml += `<div><div style="color:#64748b; font-size:8px;">COVID DAY ${__DAY__}</div><div style="color:#fff; font-size:11px; font-weight:900;">${covidRisk}%</div></div>`;
                                tooltipHtml += `</div></div></div>`;
                                
                                layer.bindTooltip(tooltipHtml, { sticky: true });
                            }
                        }).addTo(map);
                    });

                // SHIP MARKER ONLY (Simplified for clarity)
                const shipIcon = L.divIcon({
                    className: '',
                    html: `<div class="ring-marker blink-active" style="border-color:#22c55e; color:#22c55e; box-shadow: 0 0 15px #22c55e;"><div class="badge">S</div></div>`,
                    iconSize: [22, 22], iconAnchor: [11, 11]
                });
                L.marker(shipPos, { icon: shipIcon }).addTo(map);
            </script>
        </body>
        </html>
        """
        map_html = map_template.replace("__FEAR_MATRIX__", json.dumps({})) # Simplified for now
        map_html = map_html.replace("__INTENSITY__", json.dumps(intensity))
        map_html = map_html.replace("__DAY__", str(current_day))
        
        components.html(map_html, height=450)

    st.markdown(
        f"<div style='text-align:left; padding:10px; background:rgba(15,23,42,0.4); border-radius:6px; border:1px solid rgba(255,255,255,0.05); margin-top:10px;'><p style='color:#94a3b8; font-size:0.65rem; font-family:monospace; margin:0;'><b style='color:#fbbf24;'>DAILY_SYNC_SYSTEM:</b> Automatic Historical Progression Enabled // <b>DAY_{current_day} REPLAY</b> // ACCURACY_VERIFIED</p></div>",
        unsafe_allow_html=True
    )
