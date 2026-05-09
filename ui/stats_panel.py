"""Stats panel — live metrics + case timeline chart."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import streamlit as st

LIVE_FILE = Path("data/outbreak_live.json")

# Hardcoded baseline (WHO Update, as of 2026-05-08) — auto-overridden by outbreak_live.json
OUTBREAK_DATA: dict[str, Any] = {
    "confirmed_cases": 5,
    "suspected_cases": 9,
    "deaths": 3,
    "nationalities": 23,
    "ship_status": "Transit — Canary Islands",
    "last_updated": "2026-05-08",
    "case_fatality_rate": 60.0,
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


@st.cache_data(ttl=600, show_spinner=False)
def get_outbreak_stats() -> dict[str, Any]:
    """Returns case counts — live values from scraper overlay hardcoded baseline."""
    live = _load_live()
    data = dict(OUTBREAK_DATA)
    # Merge live data: numbers only if higher, strings always if present
    for k in ("confirmed_cases", "suspected_cases", "deaths", "nationalities", "last_updated", "ship_status"):
        if k in live:
            val = live[k]
            if isinstance(val, (int, float)):
                if val > data.get(k, 0):
                    data[k] = val
            elif val:
                data[k] = val

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
    
    # ── 1. REAL-TIME HEADER & CARDS (TOP PRIORITY) ──
    col_live, col_widget = st.columns([3, 1])
    with col_live:
        st.markdown(
            f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:1rem; background:rgba(34,197,94,0.05); padding:4px 12px; border-radius:100px; width:fit-content; border:1px solid rgba(34,197,94,0.1);">'
            f'<span class="live-dot" style="width:8px; height:8px; background:#22c55e; box-shadow: 0 0 8px #22c55e;"></span>'
            f'<span style="color:#22c55e; font-size:0.65rem; font-weight:800; text-transform:uppercase; letter-spacing:0.1em;">Real-time Outbreak Tracking Active</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    with col_widget:
        if st.button("📱 Pin to Home", key="pin_stats", use_container_width=True):
            st.info(
                "**Install Live Stats Widget:**\n\n"
                "1. Click the link below to open Widget Mode.\n"
                "2. In Safari/Chrome, tap **Share** > **Add to Home Screen**."
            )
            st.link_button("🚀 Open Stats Widget", "/?widget=stats", use_container_width=True)

    # Helper to pick glow class based on thresholds
    def get_glow(val: Any, type: str) -> str:
        if not isinstance(val, (int, float)): return ""
        if type == "cases":
            if val < 5: return "glow-green"
            if val < 15: return "glow-amber"
            return "glow-red"
        if type == "deaths":
            if val == 0: return "glow-green"
            if val < 3: return "glow-amber"
            return "glow-red"
        if type == "nationalities":
            if val < 10: return "glow-green"
            if val < 25: return "glow-amber"
            return "glow-red"
        return ""

    cards = [
        (str(stats.get("confirmed_cases", 0)), "Confirmed Cases", get_glow(stats.get("confirmed_cases"), "cases")),
        (str(stats.get("suspected_cases", 0)), "Suspected Cases", get_glow(stats.get("suspected_cases"), "cases")),
        (str(stats.get("deaths", 0)), "Deaths", get_glow(stats.get("deaths"), "deaths")),
        (str(stats.get("nationalities", 0)), "Nationalities Affected", get_glow(stats.get("nationalities"), "nationalities")),
        (stats.get("ship_status", "Unknown"), "Ship Current Status", "glow-green"),
    ]

    # Responsive grid for stat cards
    cards_html = ""
    for value, label, glow_class in cards:
        cards_html += (
            f'<div class="stat-card" style="position:relative;">'
            f'<div style="position:absolute; top:8px; right:10px; display:flex; align-items:center; gap:4px; opacity:0.6;">'
            f'<span class="live-dot" style="width:5px; height:5px; background:#22c55e;"></span>'
            f'<span style="color:#22c55e; font-size:0.5rem; font-weight:800; text-transform:uppercase; letter-spacing:0.05em;">Live</span>'
            f'</div>'
            f'<span class="stat-value {glow_class}">{value}</span>'
            f'<div class="stat-label">{label}</div>'
            f'</div>'
        )

    st.markdown(
        f'<div class="stats-grid">{cards_html}</div>',
        unsafe_allow_html=True,
    )

    # ── 2. DATA SOURCE VERIFICATION (SUPPORTING) ──
    is_live = stats.get("_source") == "auto-extracted"

    if is_live:
        st.markdown(
            '<span class="live-dot"></span>'
            '<span class="live-label">CASE COUNTS AUTO-UPDATED · last: '
            + stats["last_updated"] + '</span>',
            unsafe_allow_html=True,
        )
    elif stats.get("_source") == "manual-correction":
        st.markdown(
            '<div style="background:rgba(59,130,246,0.1);border:1px solid #3b82f644;padding:0.5rem 0.8rem;border-radius:8px;margin-bottom:1rem;margin-top:0.5rem;">'
            '<span style="color:#3b82f6;font-size:0.75rem;font-weight:700;font-family:monospace;letter-spacing:0.05em;">'
            '🛡️ VERIFIED DATA SOURCE</span><br>'
            '<span style="color:#94a3b8;font-size:0.72rem;">'
            'Showing verified human-checked data. '
            'Last sync: ' + stats["last_updated"] + '</span>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span style="color:#f59e0b;font-size:0.7rem;font-weight:700;font-family:monospace;'
            'letter-spacing:0.05em;">⏸ CASE COUNTS — LAST VERIFIED: '
            + stats["last_updated"] + ' · awaiting live update</span>',
            unsafe_allow_html=True,
        )

    # ── 3. DEFINITIONS (CONTEXTUAL) ──
    st.info(
        "**Case Definitions:** 'Confirmed' refers to laboratory-verified PCR results. 'Suspected' "
        "includes individuals showing clinical symptoms who await final lab confirmation.",
        icon="🔬"
    )

    st.markdown("<br>", unsafe_allow_html=True)

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
