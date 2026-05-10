"""Ship Telemetry component — pixel art animation and live signals."""
from __future__ import annotations

import streamlit as st

def render_ship_pixel_art(status: str) -> str:
    """Returns CSS/HTML for a live pixel-art ship animation."""
    is_transit = "Transit" in status or "Sea" in status
    anim_class = "ship-moving" if is_transit else "ship-docked"
    
    return f"""
    <style>
    .telemetry-box {{
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(0, 180, 216, 0.3);
        border-radius: 8px;
        padding: 10px;
        position: relative;
        overflow: hidden;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 8px;
    }}
    
    .pixel-ship {{
        width: 32px;
        height: 16px;
        background: #00b4d8;
        position: relative;
        box-shadow: 
            0 4px 0 #0077b6,
            -4px 0 0 #00b4d8, 4px 0 0 #00b4d8,
            0 -4px 0 #48cae4;
        image-rendering: pixelated;
    }}
    
    .pixel-ship::before {{
        content: '';
        position: absolute;
        top: -8px;
        left: 8px;
        width: 8px;
        height: 8px;
        background: #f8fafc;
        box-shadow: 0 4px 0 #94a3b8;
    }}
    
    @keyframes ship-float {{
        0%, 100% {{ transform: translateY(0) rotate(0deg); }}
        50% {{ transform: translateY(-3px) rotate(1deg); }}
    }}
    
    @keyframes sea-move {{
        0% {{ background-position: 0 0; }}
        100% {{ background-position: 40px 0; }}
    }}
    
    .ship-moving {{
        animation: ship-float 2s infinite ease-in-out;
    }}
    
    .sea-background {{
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 12px;
        background-image: linear-gradient(90deg, transparent 0%, transparent 50%, rgba(72, 202, 228, 0.3) 50%, rgba(72, 202, 228, 0.3) 100%);
        background-size: 20px 100%;
        animation: sea-move 1s infinite linear;
    }}
    
    .telemetry-coords {{
        position: absolute;
        top: 4px;
        left: 8px;
        font-family: monospace;
        font-size: 0.55rem;
        color: #48cae4;
        opacity: 0.8;
    }}
    </style>
    <div class="telemetry-box">
        <div class="telemetry-coords">28.2916° N, 16.6291° W</div>
        <div class="pixel-ship {anim_class}"></div>
        <div class="sea-background"></div>
    </div>
    """

def get_ship_card_html(status: str) -> str:
    """Returns the full HTML for the Ship status card."""
    pixel_art = render_ship_pixel_art(status)
    
    return f"""
    <div class="stat-card" style="position:relative; border-color: rgba(0, 180, 216, 0.4) !important; background: rgba(15, 23, 42, 0.7) !important;">
        <div style="position:absolute; top:8px; right:10px; display:flex; align-items:center; gap:4px; opacity:0.8;">
            <span class="live-dot" style="width:6px; height:6px; background:#22c55e; box-shadow: 0 0 10px #22c55e;"></span>
            <span style="color:#22c55e; font-size:0.55rem; font-weight:900; text-transform:uppercase; letter-spacing:0.05em;">TELEMETRY ACTIVE</span>
        </div>
        <span class="stat-value glow-green" style="font-size: 1.2rem !important; text-transform: uppercase; letter-spacing: 0.05em;">{status}</span>
        <div class="stat-label">MV HONDIUS STATUS</div>
        {pixel_art}
    </div>
    """
