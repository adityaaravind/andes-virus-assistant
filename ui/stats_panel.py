"""Stats panel — live metrics + case timeline chart."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import streamlit as st

LIVE_FILE = Path("data/outbreak_live.json")

# Hardcoded baseline — auto-overridden by outbreak_live.json when scraper finds updates
OUTBREAK_DATA: dict[str, Any] = {
    "confirmed_cases": 9,
    "deaths": 2,
    "nationalities": 8,
    "ship_status": "Docked — Cape Verde",
    "last_updated": "2025-05-01",
    "case_fatality_rate": 22.2,
}

CASE_TIMELINE = [
    {"date": "2025-04-15", "cases": 1, "label": "First case confirmed"},
    {"date": "2025-04-18", "cases": 2, "label": "Second case"},
    {"date": "2025-04-21", "cases": 4, "label": "Cluster identified"},
    {"date": "2025-04-24", "cases": 6, "label": "Ship diverted"},
    {"date": "2025-04-27", "cases": 7, "label": "Quarantine declared"},
    {"date": "2025-04-30", "cases": 8, "label": "WHO notified"},
    {"date": "2025-05-01", "cases": 9, "label": "Current total"},
]


def _load_live() -> dict[str, Any]:
    if LIVE_FILE.exists():
        try:
            return json.loads(LIVE_FILE.read_text())
        except Exception:
            pass
    return {}


@st.cache_data(ttl=900, show_spinner=False)
def get_outbreak_stats() -> dict[str, Any]:
    """Returns case counts — live values from scraper overlay hardcoded baseline."""
    live = _load_live()
    data = dict(OUTBREAK_DATA)
    for k in ("confirmed_cases", "deaths", "nationalities", "last_updated"):
        if live.get(k):
            data[k] = live[k]
    if data["confirmed_cases"] and data["deaths"]:
        data["case_fatality_rate"] = round(data["deaths"] / data["confirmed_cases"] * 100, 1)
    data["_source"] = live.get("source", "manual")
    return data


@st.cache_data(ttl=21600)
def build_timeline_chart() -> go.Figure:
    dates  = [datetime.strptime(r["date"], "%Y-%m-%d") for r in CASE_TIMELINE]
    cases  = [r["cases"] for r in CASE_TIMELINE]
    labels = [r["label"] for r in CASE_TIMELINE]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=cases,
        mode="lines+markers",
        name="Cumulative Cases",
        line=dict(color="#00b4d8", width=2.5, shape="spline"),
        marker=dict(size=8, color="#00b4d8", line=dict(color="#ffffff", width=1.5)),
        hovertemplate="<b>%{text}</b><br>%{x|%b %d, %Y}<br>Cases: %{y}<extra></extra>",
        text=labels,
        fill="tozeroy",
        fillcolor="rgba(0,180,216,0.08)",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", size=11),
        margin=dict(l=40, r=10, t=10, b=30),
        height=200,
        xaxis=dict(gridcolor="#1b2e45", showline=False, tickformat="%b %d"),
        yaxis=dict(gridcolor="#1b2e45", showline=False,
                   title="Cumulative cases", tickfont=dict(size=10)),
        showlegend=False,
        hovermode="x unified",
    )
    return fig


def render_stats_panel() -> None:
    stats  = get_outbreak_stats()
    is_live = stats.get("_source") == "auto-extracted"

    if is_live:
        st.markdown(
            '<span class="live-dot"></span>'
            '<span class="live-label">CASE COUNTS AUTO-UPDATED · last: '
            + stats["last_updated"] + '</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span style="color:#f59e0b;font-size:0.7rem;font-weight:700;font-family:monospace;'
            'letter-spacing:0.05em;">⏸ CASE COUNTS — MANUALLY UPDATED · last: '
            + stats["last_updated"] + '</span>',
            unsafe_allow_html=True,
        )

    cols  = st.columns(4)
    cards = [
        ("🦠", str(stats["confirmed_cases"]), "Confirmed Cases"),
        ("💀", str(stats["deaths"]), "Deaths"),
        ("🌍", str(stats["nationalities"]), "Nationalities"),
        ("🚢", stats["ship_status"], "Ship Status"),
    ]
    for col, (icon, value, label) in zip(cols, cards):
        with col:
            st.markdown(
                f'<div class="stat-card">'
                f'<div style="font-size:1.4rem;">{icon}</div>'
                f'<div class="stat-value">{value}</div>'
                f'<div class="stat-label">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)


def render_timeline_chart() -> None:
    st.markdown("#### Case Progression")
    fig = build_timeline_chart()
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    stats = get_outbreak_stats()
    st.caption(
        f"CFR: {stats['case_fatality_rate']}% · "
        f"Last updated: {stats['last_updated']} · "
        "Case counts refresh every 15 min"
    )
