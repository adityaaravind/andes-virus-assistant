import streamlit as st
from rag.chain import build_chain

def render_war_room_panel():
    """
    Renders an interactive 'Expert Room' UI component.
    Uses simple language for general users.
    """
    if "war_room_msgs" not in st.session_state:
        st.session_state.war_room_msgs = [
            {"role": "Assistant", "color": "#00b4d8", "icon": "🔍", "text": "Checking latest news and medical reports..."},
            {"role": "Health Expert", "color": "#94a3b8", "icon": "🩺", "text": "New reports show the virus is spreading faster in some areas. Ask me about 'how it spreads' or 'current safety rules'."},
        ]

    # Header with simple title
    st.markdown(
        """
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <h3 class="glowing-title" style="margin:0;font-size:1.1rem!important;color:#00b4d8">🛡️ Expert Discussion</h3>
            <div class='outbreak-badge' style="font-size:0.5rem;padding:2px 6px">LIVE UPDATES</div>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # Chat Log
    chat_html = ""
    for msg in st.session_state.war_room_msgs:
        bg = f"rgba({int(msg['color'][1:3], 16)}, {int(msg['color'][3:5], 16)}, {int(msg['color'][5:7], 16)}, 0.1)"
        chat_html += f"""
        <div style="background:{bg}; border-left:3px solid {msg['color']}; padding:8px; border-radius:4px; margin-bottom:8px;">
            <div style="font-size:0.6rem; font-weight:900; color:{msg['color']}; text-transform:uppercase; margin-bottom:2px;">
                {msg.get('icon', '👤')} {msg['role']}
            </div>
            <div style="font-size:0.8rem; color:#e2e8f0; line-height:1.3;">
                {msg['text']}
            </div>
        </div>
        """

    st.markdown(
        f"""
        <div class="stat-card" style="border-color:rgba(0,180,216,0.3); padding:12px!important; margin-bottom: 10px;">
            <div style="overflow-y:auto; max-height:320px; padding-right:5px;">
                {chat_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # SIMPLE SUGGESTIONS
    st.markdown("<p style='font-size:0.65rem; color:#64748b; font-weight:800; margin-bottom:5px; text-transform:uppercase;'>Common Questions</p>", unsafe_allow_html=True)

    s_cols = st.columns(3)
    suggestions = ["How it spreads", "Safety rules", "Latest news"]

    for i, s in enumerate(suggestions):
        if s_cols[i].button(s, key=f"sug_{i}", use_container_width=True):
            st.session_state.war_room_msgs.append({"role": "User", "color": "#00b4d8", "icon": "👤", "text": f"Tell me about {s.lower()}"})
            st.rerun()

    # Input handling
    if prompt := st.chat_input("Ask the experts anything...", key="war_room_chat_input"):
        st.session_state.war_room_msgs.append({"role": "User", "color": "#00b4d8", "icon": "👤", "text": prompt})

        chain = st.session_state.get("rag_chain") or build_chain()
        with st.spinner("Experts are talking..."):
            result = chain.query(prompt)
            st.session_state.war_room_msgs.append({
                "role": "Response", 
                "color": "#ffffff", 
                "icon": "✅", 
                "text": result["answer"]
            })
        st.rerun()
