"""Sidebar tile menu for rapid navigation with hover/touch animations."""
from __future__ import annotations

import streamlit as st


NAV_ITEMS = [
    {"label": "Outbreak Stats", "icon": "📊", "anchor": "stats"},
    {"label": "Live News",      "icon": "📰", "anchor": "news"},
    {"label": "Global Map",     "icon": "🌍", "anchor": "map"},
]


def render_tile_menu() -> None:
    """Render a grid of interactive tiles in the sidebar."""
    st.markdown(
        "<h3 style='color:#94a3b8;font-size:0.85rem;margin-bottom:0.8rem;text-transform:uppercase;letter-spacing:0.05em;'>"
        "⚡ Quick Navigate</h3>",
        unsafe_allow_html=True,
    )

    # We use HTML/CSS directly for the scaling/real-time animation effect
    # since Streamlit buttons don't support the specific 'get bigger on hover' 
    # and 'return to normal' animation fluidly enough.
    
    menu_html = "<div class='nav-tile-grid'>"
    
    for item in NAV_ITEMS:
        menu_html += f"""
<a href="#{item['anchor']}" class="nav-tile">
    <div class="nav-tile-icon">{item['icon']}</div>
    <div class="nav-tile-label">{item['label']}</div>
</a>
"""
    
    menu_html += "</div>"
    
    st.markdown(menu_html, unsafe_allow_html=True)
