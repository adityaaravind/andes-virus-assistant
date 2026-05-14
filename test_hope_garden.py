#!/usr/bin/env python3
"""Test script for Hope Garden functionality."""

import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Hope Garden Test", layout="wide")

st.title("🌱 Hope Garden Test Environment")

# Enable debug mode for testing
st.session_state["debug_mode"] = True

# Test the Hope Garden components
st.subheader("1. Hope Garden Card")
from ui.hope_garden import render_hope_garden_card, render_garden_debug_info

render_hope_garden_card()

st.subheader("2. Debug Controls")
render_garden_debug_info()

st.subheader("3. Sentiment Analysis Test")
from game.sentiment_analyzer import sentiment_analyzer

test_news = st.text_area(
    "Test News Text",
    value="Three new patients have recovered from the virus, showing promising signs of treatment effectiveness."
)

if st.button("Analyze Sentiment"):
    result = sentiment_analyzer.analyze_news_chunk(test_news)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Sentiment Score", result['sentiment_score'])
        st.metric("Sentiment Type", result['sentiment_type'])
        st.metric("Confidence", f"{result['confidence']:.1%}")

    with col2:
        st.write("**Keywords Found:**")
        st.write(result['keywords_found'])
        st.write(f"**Hopeful words:** {result['hopeful_count']}")
        st.write(f"**Concerning words:** {result['concerning_count']}")

st.subheader("4. Garden State Info")
from game.garden_state import garden_state

state = garden_state.get_current_state()
display_info = garden_state.get_garden_display_info()

col1, col2 = st.columns(2)
with col1:
    st.write("**Raw State:**")
    st.json(state)

with col2:
    st.write("**Display Info:**")
    st.json(display_info)