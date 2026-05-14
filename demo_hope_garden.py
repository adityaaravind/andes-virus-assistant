#!/usr/bin/env python3
"""Demo script showing Hope Garden in action."""

import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Hope Garden Demo", layout="wide", page_icon="🌱")

st.title("🌱 Hope Garden - Auto-Sentiment Demo")
st.markdown("**Community healing space that responds to news sentiment in real-time**")

# Enable debug mode
st.session_state["debug_mode"] = True

# Main demo sections
st.markdown("### 🎮 Interactive Demo")

# Show current garden state
from ui.hope_garden import render_hope_garden_card
render_hope_garden_card()

st.markdown("---")

# News simulation section
st.markdown("### 📰 News Impact Simulator")
st.markdown("See how different types of news affect the community garden:")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**🌟 Good News Examples**")

    good_news_examples = [
        "Breakthrough vaccine shows 95% effectiveness in trials",
        "Three patients have fully recovered and been discharged",
        "New treatment reduces symptoms significantly in clinical study",
        "Outbreak cases decline for third consecutive day"
    ]

    for news in good_news_examples:
        if st.button(f"📈 {news[:30]}...", key=f"good_{hash(news)}"):
            from game.sentiment_analyzer import sentiment_analyzer
            from game.garden_state import garden_state

            # Analyze sentiment
            result = sentiment_analyzer.analyze_news_chunk(news)

            # Create batch format for garden update
            sentiment_data = {
                'overall_sentiment': result['sentiment_score'],
                'sentiment_type': result['sentiment_type'],
                'confidence': result['confidence'],
                'timestamp': datetime.utcnow().isoformat(),
                'total_chunks': 1
            }

            # Update garden
            garden_state.update_from_sentiment(sentiment_data)

            st.success(f"✅ Applied to garden: {result['sentiment_type']} (score: {result['sentiment_score']})")
            st.rerun()

with col2:
    st.markdown("**⚠️ Concerning News Examples**")

    bad_news_examples = [
        "Outbreak spreads to three new regions, cases surge",
        "Five additional deaths reported as crisis deepens",
        "Emergency lockdown declared as situation worsens",
        "New variant shows resistance to current treatments"
    ]

    for news in bad_news_examples:
        if st.button(f"📉 {news[:30]}...", key=f"bad_{hash(news)}"):
            from game.sentiment_analyzer import sentiment_analyzer
            from game.garden_state import garden_state

            # Analyze sentiment
            result = sentiment_analyzer.analyze_news_chunk(news)

            # Create batch format for garden update
            sentiment_data = {
                'overall_sentiment': result['sentiment_score'],
                'sentiment_type': result['sentiment_type'],
                'confidence': result['confidence'],
                'timestamp': datetime.utcnow().isoformat(),
                'total_chunks': 1
            }

            # Update garden
            garden_state.update_from_sentiment(sentiment_data)

            st.warning(f"⚠️ Applied to garden: {result['sentiment_type']} (score: {result['sentiment_score']})")
            st.rerun()

st.markdown("---")

# Show how it works
st.markdown("### 🔧 How It Works")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **🤖 Automatic News Analysis:**
    - Every 15 minutes: RAG ingests news from RSS feeds
    - Sentiment analyzer processes news chunks
    - Keywords classified as HOPEFUL/CONCERNING/NEUTRAL
    - Overall sentiment score calculated (-1 to +1)
    """)

with col2:
    st.markdown("""
    **🌱 Garden Response:**
    - **Good news** → Plants grow automatically, stress reduces
    - **Bad news** → Plants get stressed, community care needed
    - **User actions** → Water/sunlight/hope to heal stressed plants
    - **Real-time updates** → Garden state persists across sessions
    """)

# Technical details
with st.expander("🔍 Technical Implementation"):
    st.markdown("""
    **Components:**
    - `game/sentiment_analyzer.py` - News sentiment analysis with keyword matching
    - `game/garden_state.py` - Garden health & care point management
    - `ui/hope_garden.py` - Streamlit UI components
    - `app.py` - Integration with RAG news polling pipeline

    **Data Flow:**
    ```
    RSS News → RAG Chunks → Sentiment Analysis → Garden State Update → UI Refresh
    ```

    **Storage:**
    - Garden state stored in `persistent_kv` (Qdrant vector DB)
    - Survives app restarts and deployments
    - Community actions tracked across all users
    """)

st.markdown("---")
st.success("🚀 **Ready for production!** Add to main app by uncommenting the Hope Garden section.")

# Reset button
if st.button("🔄 Reset Garden to Default"):
    from alerts.persistent_kv import kv_set
    kv_set("hope_garden_state", None)
    st.success("Garden reset to default state!")
    st.rerun()