"""Ship Telemetry component — pixel art animation and live signals."""
from __future__ import annotations

import streamlit as st

def get_ship_card_html(status: str) -> str:
    """Returns minimalist HTML for the Ship status card to match others."""
    is_transit = "Transit" in status or "Sea" in status
    anim_class = "ship-moving" if is_transit else "ship-docked"
    
    return f"""
    <style>
    @keyframes ship-float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-2px); }} }}
    @keyframes sea-move {{ 0% {{ background-position: 0 0; }} 100% {{ background-position: 20px 0; }} }}
    .mini-ship {{
        width: 20px; height: 10px; background: #00b4d8; position: relative; margin: 5px auto;
        box-shadow: 0 2px 0 #0077b6; animation: ship-float 2s infinite ease-in-out;
    }}
    .mini-sea {{
        height: 4px; width: 40px; margin: 0 auto;
        background: linear-gradient(90deg, transparent 50%, rgba(72, 202, 228, 0.3) 50%);
        background-size: 10px 100%; animation: sea-move 1s infinite linear;
    }}
    </style>
    <div class="stat-card" style="position:relative;">
        <div style="position:absolute; top:8px; right:10px; display:flex; align-items:center; gap:4px; opacity:0.6;">
            <span class="live-dot" style="width:5px; height:5px; background:#22c55e;"></span>
            <span style="color:#22c55e; font-size:0.5rem; font-weight:800; text-transform:uppercase;">Live</span>
        </div>
        <span class="stat-value glow-green" style="font-size: 1.1rem !important;">{status}</span>
        <div class="stat-label">MV HONDIUS STATUS
            <div style="display:flex; flex-direction:column; align-items:center; margin-top:8px; opacity:0.8;">
                <div class="mini-ship"></div>
                <div class="mini-sea"></div>
                <span style="font-family:monospace; font-size:0.5rem; color:#48cae4; margin-top:4px;">28.29N, 16.62W</span>
            </div>
        </div>
    </div>
    """
