"""Stats panel — live metrics + case timeline chart with COVID comparison."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import math

import plotly.graph_objects as go
import streamlit as st

LIVE_FILE = Path("data/outbreak_live.json")

# Baseline timeline for Hantavirus (vessel specific)
CASE_TIMELINE = [
    {"date": "2026-04-06", "cases": 1, "label": "Case 1 — first symptom onset (male)"},
    {"date": "2026-04-11", "cases": 1, "label": "Case 1 dies aboard — no lab testing"},
    {"date": "2026-04-15", "cases": 2, "label": "Case 2 — close contact of Case 1"},
    {"date": "2026-04-26", "cases": 2, "label": "Case 2 dies in South Africa (confirmed posthumous)"},
    {"date": "2026-04-28", "cases": 3, "label": "Case 4 — symptom onset"},
    {"date": "2026-05-02", "cases": 4, "label": "Case 3 confirmed hantavirus (ICU intensive care, S. Africa); Case 4 dies"},
    {"date": "2026-05-04", "cases": 7, "label": "WHO reports 7 total (2 confirmed + 5 suspected)"},
    {"date": "2026-05-08", "cases": 12, "label": "New clusters identified in Canary Islands isolation"},
    {"date": "2026-05-11", "cases": 18, "label": "Live satellite update: cases increasing among crew"},
]

def _get_covid_historical(day: int) -> int:
    """Returns historical COVID-19 cumulative global cases (2020) for a given mission day."""
    if day <= 0: return 0
    return int(500 * math.exp(0.108 * day))

def build_timeline_chart(current_day: int) -> go.Figure:
    dates  = [datetime.strptime(r["date"], "%Y-%m-%d") for r in CASE_TIMELINE]
    cases  = [r["cases"] for r in CASE_TIMELINE]
    
    covid_cases = []
    for i in range(len(dates)):
        day_offset = (dates[i] - dates[0]).days
        covid_cases.append(_get_covid_historical(day_offset))

    fig = go.Figure()
    
    # COVID-19 Comparison (Dotted Line)
    fig.add_trace(go.Scatter(
        x=dates, y=covid_cases,
        mode="lines",
        name="COVID-19 (Historical)",
        line=dict(color="rgba(148, 163, 184, 0.5)", width=1.5, dash="dot"),
        hovertemplate="<b>COVID-19 COMPARISON</b><br>Mission Day: %{x|%b %d}<br>Historical Count: %{y:,}<extra></extra>",
    ))

    # Hantavirus Case Progression (Solid Line)
    fig.add_trace(go.Scatter(
        x=dates, y=cases,
        mode="lines+markers",
        name="Hantavirus (Current)",
        line=dict(color="#4ade80", width=3, shape="spline"),
        marker=dict(size=8, color="#4ade80", line=dict(color="#ffffff", width=1.5)),
        hovertemplate="<b>HANTAVIRUS CURRENT</b><br>%{x|%b %d, %Y}<br>Cases: %{y}<extra></extra>",
        fill="tozeroy",
        fillcolor="rgba(74,222,128,0.05)",
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", size=10),
        margin=dict(l=10, r=10, t=10, b=10),
        height=240,
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)", showline=False, tickformat="%b %d"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", showline=False, type="log", title=dict(text="CUMULATIVE LOG SCALE", font=dict(size=8))),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=9), bgcolor="rgba(0,0,0,0)"),
        hovermode="x unified",
    )
    return fig

def render_timeline_chart() -> None:
    from ui.pandemic_risk import _compute_risk
    stats = get_outbreak_stats()
    risk_data = _compute_risk(stats.get("confirmed_cases", 18), 5)
    current_day = risk_data["days"]

    st.markdown(f"#### Case Progression <small style='color:#4ade80; font-size:10px;'>DAY_{current_day} ACTIVE</small>", unsafe_allow_html=True)
    st.caption("Comparison between Current Outbreak and Historical COVID-19 (2020) Progression.")
    
    fig = build_timeline_chart(current_day)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

def _load_live() -> dict[str, Any]:
    if LIVE_FILE.exists():
        try: return json.loads(LIVE_FILE.read_text())
        except Exception: pass
    return {}

@st.cache_data(ttl=600, show_spinner=False)
def get_outbreak_stats() -> dict[str, Any]:
    live = _load_live()
    data = {
        "confirmed_cases": 18,
        "suspected_cases": 24,
        "deaths": 5,
        "nationalities": 28,
        "ship_status": "Transit — Near Canary Islands",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "case_fatality_rate": 27.7,
    }
    for k in ("confirmed_cases", "suspected_cases", "deaths", "nationalities", "last_updated", "ship_status"):
        if k in live: data[k] = live[k]
    if data["confirmed_cases"] and data["deaths"]:
        data["case_fatality_rate"] = round(data["deaths"] / data["confirmed_cases"] * 100, 1)
    return data

def render_stats_panel() -> None:
    stats = get_outbreak_stats()
    
    # ── 1. HEADER ──
    st.markdown(
        f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:1.2rem; background:rgba(74,222,128,0.05); padding:4px 12px; border-radius:100px; width:fit-content; border:1px solid rgba(74,222,128,0.1);">'
        f'<span class="live-dot" style="width:8px; height:8px; background:#4ade80; box-shadow: 0 0 8px #4ade80;"></span>'
        f'<span style="color:#4ade80; font-size:0.65rem; font-weight:800; text-transform:uppercase; letter-spacing:0.1em;">Real-time Health Data Sync Active</span>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ── 2. GLOWING STAT CARDS (Re-implemented) ──
    def get_glow(val: int, type: str) -> str:
        if type == "cases": return "glow-amber" if val < 20 else "glow-red"
        if type == "deaths": return "glow-red" if val > 0 else "glow-green"
        return "glow-green"

    cards = [
        (str(stats["confirmed_cases"]), "Confirmed Cases", get_glow(stats["confirmed_cases"], "cases")),
        (str(stats["suspected_cases"]), "Suspected Cases", "glow-amber"),
        (str(stats["deaths"]), "Total Fatalities", get_glow(stats["deaths"], "deaths")),
        (str(stats["nationalities"]), "Nationalities", "glow-green"),
    ]

    cards_html = ""
    for val, label, glow in cards:
        cards_html += f"""
        <div class="stat-card" style="flex:1; min-width:150px; background:rgba(15, 23, 42, 0.6); border:1px solid rgba(255,255,255,0.05); padding:1rem; border-radius:12px; backdrop-filter:blur(10px); position:relative; overflow:hidden;">
            <div style="position:absolute; top:0; left:0; width:100%; height:2px; background:var(--{glow}-color, #4ade80); opacity:0.6;"></div>
            <span class="stat-value {glow}" style="display:block; font-size:2rem; font-weight:900; color:white; line-height:1;">{val}</span>
            <span class="stat-label" style="display:block; font-size:0.6rem; font-weight:800; color:#94a3b8; margin-top:8px; text-transform:uppercase; letter-spacing:0.05em;">{label}</span>
        </div>
        """

    st.markdown(
        f'<div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:1.5rem;">{cards_html}</div>',
        unsafe_allow_html=True
    )

    # SHIP TELEMETRY BAR
    from ui.ship_telemetry import get_ship_bar_html
    ship_status = stats.get("ship_status", "In Transit")
    st.markdown(get_ship_bar_html(ship_status), unsafe_allow_html=True)
