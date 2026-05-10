"""Ship Telemetry component — minimalist mobile-friendly signal strip."""
from __future__ import annotations

import streamlit as st

def get_ship_bar_html(status: str) -> str:
    """Returns a minimalist, mobile-friendly horizontal bar for Ship Telemetry."""
    
    # Flattened high-contrast signal strip
    html = f"""
<style>
.telemetry-strip {{
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(0, 180, 216, 0.2);
    border-radius: 10px;
    padding: 10px 15px;
    margin-top: 1rem;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 15px;
    backdrop-filter: blur(10px);
}}

.signal-group {{
    display: flex;
    flex-direction: column;
    min-width: 120px;
}}

.signal-label {{
    font-size: 0.52rem;
    font-weight: 800;
    color: #48cae4;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 2px;
}}

.signal-value {{
    font-family: 'Inter', monospace;
    font-size: 0.85rem;
    font-weight: 900;
    color: #ffffff;
    text-shadow: 0 0 10px rgba(0, 180, 216, 0.3);
}}

.signal-live-dot {{
    width: 6px;
    height: 6px;
    background: #22c55e;
    border-radius: 50%;
    display: inline-block;
    margin-right: 6px;
    box-shadow: 0 0 8px #22c55e;
}}

@media (max-width: 600px) {{
    .telemetry-strip {{
        flex-direction: column;
        align-items: flex-start;
        padding: 12px;
        gap: 10px;
    }}
    .signal-group {{
        width: 100%;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        padding-bottom: 8px;
    }}
    .signal-group:last-child {{
        border-bottom: none;
        padding-bottom: 0;
    }}
}}
</style>
<div class="telemetry-strip">
<div class="signal-group">
<div class="signal-label">📡 MV HONDIUS STATUS</div>
<div class="signal-value" style="color:#22c55e;"><span class="signal-live-dot"></span>{status.upper()}</div>
</div>
<div class="signal-group" style="flex:1; text-align:center; min-width: 50px;" class="mobile-hide">
<div style="height:1px; background:rgba(0,180,216,0.1); width:100%;"></div>
</div>
<div class="signal-group" style="text-align: right;">
<div class="signal-label">📍 GEOGRAPHIC COORDINATES</div>
<div class="signal-value">28.2916° N, 16.6291° W</div>
</div>
</div>
""".replace("\n", " ").strip()
    return html
