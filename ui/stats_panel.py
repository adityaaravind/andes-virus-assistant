"""Stats panel — live metrics + case timeline chart."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import streamlit as st

LIVE_FILE = Path("data/outbreak_live.json")

# Hardcoded baseline (WHO DON599, as of 2026-05-04) — auto-overridden by outbreak_live.json
OUTBREAK_DATA: dict[str, Any] = {
    "confirmed_cases": 7,
    "deaths": 3,
    "nationalities": 23,
    "ship_status": "Moored — Cabo Verde",
    "last_updated": "2026-05-04",
    "case_fatality_rate": 42.9,
}

# Timeline built from WHO DON599 (2026-DON599)
CASE_TIMELINE = [
    {"date": "2026-04-06", "cases": 1, "label": "Case 1 — first symptom onset (male)"},
    {"date": "2026-04-11", "cases": 1, "label": "Case 1 dies aboard — no lab testing"},
    {"date": "2026-04-15", "cases": 2, "label": "Case 2 — close contact of Case 1"},
    {"date": "2026-04-26", "cases": 2, "label": "Case 2 dies in South Africa (confirmed posthumous)"},
    {"date": "2026-04-28", "cases": 3, "label": "Case 4 — symptom onset"},
    {"date": "2026-05-02", "cases": 4, "label": "Case 3 confirmed hantavirus (ICU intensive care, S. Africa); Case 4 dies"},
    {"date": "2026-05-04", "cases": 7, "label": "WHO (World Health Org) reports 7 total (2 confirmed + 5 suspected)"},
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
            'letter-spacing:0.05em;">⏸ CASE COUNTS — LAST VERIFIED: '
            + stats["last_updated"] + ' · awaiting live update</span>',
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
    st.caption("Apr–May 2026 outbreak on MV Hondius · WHO DON599 · timeline shows case progression from first symptom onset")
    fig = build_timeline_chart()
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    stats = get_outbreak_stats()
    st.caption(
        f"CFR: {stats['case_fatality_rate']}% · "
        f"Last verified: {stats['last_updated']} · "
        "Auto-updates every 15 min from live feeds"
    )
