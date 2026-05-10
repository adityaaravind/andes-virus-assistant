"""Ship Telemetry component — full-width horizontal command bar."""
from __future__ import annotations

import streamlit as st

def get_ship_bar_html(status: str) -> str:
    """Returns a full-width horizontal bar for Ship Telemetry."""
    is_transit = "Transit" in status or "Sea" in status
    anim_class = "ship-moving" if is_transit else "ship-docked"
    
    # CRITICAL: No leading spaces in multi-line string to prevent markdown code block bug
    return f"""
<style>
@keyframes ship-float-wide {{ 0%, 100% {{ transform: translateY(0) rotate(0deg); }} 50% {{ transform: translateY(-3px) rotate(1deg); }} }}
@keyframes sea-move-wide {{ 0% {{ background-position: 0 0; }} 100% {{ background-position: 100px 0; }} }}

.telemetry-bar {{
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(0, 180, 216, 0.2);
    border-radius: 12px;
    padding: 0.8rem 1.5rem;
    margin-top: 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
    gap: 20px;
    backdrop-filter: blur(10px);
}}

.ship-visual-section {{
    flex: 1;
    height: 45px;
    position: relative;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 6px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.pixel-ship-large {{
    width: 36px;
    height: 14px;
    background: #00b4d8;
    position: relative;
    box-shadow: 0 3px 0 #0077b6;
    z-index: 2;
    animation: ship-float-wide 2.5s infinite ease-in-out;
}}

.sea-wide {{
    position: absolute;
    bottom: 0;
    left: -100px;
    right: -100px;
    height: 10px;
    background-image: linear-gradient(90deg, transparent 0%, transparent 45%, rgba(72, 202, 228, 0.2) 50%, transparent 55%);
    background-size: 80px 100%;
    animation: sea-move-wide 2s infinite linear;
}}

.telemetry-data {{
    display: flex;
    flex-direction: column;
    min-width: 180px;
}}

.telemetry-label {{
    font-size: 0.55rem;
    font-weight: 800;
    color: #48cae4;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 2px;
}}

.telemetry-value {{
    font-family: monospace;
    font-size: 0.95rem;
    font-weight: 900;
    color: #ffffff;
    text-shadow: 0 0 10px rgba(0, 180, 216, 0.5);
}}
</style>

<div class="telemetry-bar">
    <div class="telemetry-data">
        <div class="telemetry-label">MV HONDIUS STATUS</div>
        <div class="telemetry-value" style="color:#22c55e;">{status.upper()}</div>
    </div>
    
    <div class="ship-visual-section">
        <div class="pixel-ship-large"></div>
        <div class="sea-wide"></div>
        <div style="position:absolute; top:5px; right:10px; font-family:monospace; font-size:0.5rem; color:#475569;">SAT-LINK: ACTIVE</div>
    </div>

    <div class="telemetry-data" style="text-align: right; min-width: 140px;">
        <div class="telemetry-label">CURRENT COORDINATES</div>
        <div class="telemetry-value">28.29N / 16.62W</div>
    </div>
</div>
""".strip()
