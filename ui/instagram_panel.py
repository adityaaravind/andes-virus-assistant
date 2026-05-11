"""Instagram Intelligence Feed — Mock Prototype for Outbreak Social Proof."""
from __future__ import annotations

import streamlit as st
from datetime import datetime

# Mock data for local design preview
MOCK_INSTA_POSTS = [
    {
        "user": "@epidemiology_daily",
        "handle": "epidemiology_daily",
        "caption": "BREAKING: New sightings of MV Hondius off the coast of Cabo Verde. Local health authorities are on high alert as the situation evolves. #Hantavirus #Outbreak2026 #GlobalHealth",
        "image": "https://images.unsplash.com/photo-1584036561566-baf8f5f1b144?w=400&q=80",
        "likes": 1240,
        "date": "2h ago",
        "url": "https://instagram.com"
    },
    {
        "user": "@field_reporter_leo",
        "handle": "field_reporter_leo",
        "caption": "Inside the designated quarantine zone. The medical teams are working around the clock to contain the Andes Virus strain. Vigilance is key. #AndesVirus #Hondius #FieldReport",
        "image": "https://images.unsplash.com/photo-1579152276507-24823146b53b?w=400&q=80",
        "likes": 850,
        "date": "4h ago",
        "url": "https://instagram.com"
    },
    {
        "user": "@global_health_watch",
        "handle": "global_health_watch",
        "caption": "Heatmap projection of the potential spread from the Hondius lineage. Contact tracing protocols have been activated across three continents. #Epidemiology #DataViz #VirusWatch",
        "image": "https://images.unsplash.com/photo-1581093458791-9f3c3250bb8b?w=400&q=80",
        "likes": 3200,
        "date": "6h ago",
        "url": "https://instagram.com"
    }
]

def render_instagram_panel() -> None:
    """Render the Instagram Social Intelligence feed."""
    
    # Header with Instagram-themed gradient label
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:1rem; margin-top:0.5rem;">
            <div style="background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); 
                        padding: 8px; border-radius: 10px; display: flex; align-items: center; justify-content: center;
                        box-shadow: 0 0 15px rgba(225, 48, 108, 0.3);">
                <span style="font-size:1.2rem;">📸</span>
            </div>
            <div>
                <h3 style="margin:0; font-size:1.0rem !important; letter-spacing: 0.05em; color: #f1f5f9;">SOCIAL INTEL</h3>
                <p style="margin:0; font-size:0.6rem; color: #e1306c; font-weight: 800; text-transform: uppercase;">Instagram Network</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Scrollable container for posts
    posts_html = '<div style="height: 450px; overflow-y: auto; padding-right: 5px; scrollbar-width: thin; scrollbar-color: #e1306c rgba(0,0,0,0.1);">'
    
    for post in MOCK_INSTA_POSTS:
        posts_html += f"""
        <div style="background: rgba(15, 23, 42, 0.4); 
                    border: 1px solid rgba(255, 255, 255, 0.05); 
                    border-left: 3px solid #e1306c; 
                    border-radius: 12px; 
                    padding: 1rem; 
                    margin-bottom: 1rem;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 24px; height: 24px; border-radius: 50%; background: #e1306c; display: flex; align-items: center; justify-content: center; font-size: 0.6rem; font-weight: 900; color: white;">
                        {post['handle'][0].upper()}
                    </div>
                    <span style="color: #f1f5f9; font-weight: 700; font-size: 0.75rem;">{post['user']}</span>
                </div>
                <span style="color: #64748b; font-size: 0.6rem; font-weight: 600;">{post['date']}</span>
            </div>
            <div style="position: relative; margin-bottom: 0.8rem;">
                <img src="{post['image']}" style="width: 100%; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1); display: block;">
                <div style="position: absolute; bottom: 8px; right: 8px; background: rgba(0, 0, 0, 0.6); padding: 2px 6px; border-radius: 4px; font-size: 0.55rem; color: white; font-weight: 800;">
                    LIVE_FEED
                </div>
            </div>
            <p style="font-size: 0.75rem; line-height: 1.5; color: #cbd5e1; margin-bottom: 0.8rem;">
                {post['caption']}
            </p>
            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255, 255, 255, 0.05); padding-top: 0.8rem;">
                <div style="display: flex; align-items: center; gap: 4px;">
                    <span style="color: #e1306c; font-size: 0.7rem;">❤️</span>
                    <span style="color: #94a3b8; font-size: 0.65rem; font-weight: 700;">{post['likes']:,}</span>
                </div>
                <a href="{post['url']}" target="_blank" style="text-decoration: none; color: #00b4d8; font-size: 0.65rem; font-weight: 800; letter-spacing: 0.05em;">
                    VIEW ON INSTAGRAM →
                </a>
            </div>
        </div>
        """
    
    posts_html += '</div>'
    
    st.markdown(posts_html, unsafe_allow_html=True)
    
    # Add a small footer for the panel
    st.markdown(
        """
        <div style="margin-top: 0.5rem; text-align: right;">
            <span style="color: #64748b; font-size: 0.55rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em;">
                Aggregated from #hantavirus #hondius
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )
