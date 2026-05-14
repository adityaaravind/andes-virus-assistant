#!/usr/bin/env python3
"""Debug HTML rendering in Streamlit."""

import streamlit as st

st.set_page_config(page_title="HTML Debug Test", layout="wide")

st.title("HTML Rendering Debug Test")

# Test 1: Simple HTML
st.markdown("### Test 1: Simple HTML")
st.markdown("""
<div style='background: red; color: white; padding: 10px;'>
    This should be a red box with white text
</div>
""", unsafe_allow_html=True)

# Test 2: Complex HTML (like gamification)
st.markdown("### Test 2: Complex HTML")
st.markdown("""
<div style='background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(168,85,247,0.1));
            border: 2px solid #3b82f6; border-radius: 16px; padding: 2rem; margin-bottom: 1.5rem;
            text-align: center;'>
    <div style='font-size: 4rem; margin-bottom: 1rem;'>🦸‍♀️</div>
    <h2 style='color: #3b82f6; margin: 0 0 0.5rem 0; font-size: 1.8rem; font-weight: 900;'>
        Test Hero Card
    </h2>
    <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;'>
        <div style='background: rgba(74,222,128,0.1); padding: 1rem; border-radius: 8px;'>
            <div style='color: #4ade80; font-size: 1.2rem; font-weight: 900;'>150,847</div>
            <div style='color: #4ade80; font-size: 0.8rem;'>Lives Protected Today</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Test 3: Check if it's a string escaping issue
st.markdown("### Test 3: Direct HTML Write")
html_content = """
<div style='background: green; color: white; padding: 10px; border-radius: 5px;'>
    Direct HTML content test
</div>
"""
st.markdown(html_content, unsafe_allow_html=True)

# Test 4: Show raw vs rendered
st.markdown("### Test 4: Raw vs Rendered")
st.text("This is what the HTML looks like as raw text:")
st.code(html_content)
st.markdown("This is what it should look like rendered:")
st.markdown(html_content, unsafe_allow_html=True)