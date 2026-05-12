"""Pandemic risk panel — live gauge, Andes vs COVID-19 comparison bars."""
from __future__ import annotations

from datetime import datetime
from typing import Any

import plotly.graph_objects as go
import streamlit as st

from ui.stats_panel import get_outbreak_stats, CASE_TIMELINE


# ── COVID-19 reference metrics (at equivalent early stage & current) ────────
COVID_EARLY = {
    "r0":            2.5,
    "cfr_pct":       2.3,
    "days_to_100":   14,
    "p2p_risk":      95,
    "airborne":      True,
    "continents":    5,
    "growth_rate":   1.35,
}

ANDES_FIXED = {
    "r0":            1.4,
    "cfr_pct":       35.0,
    "days_to_100":   None,
    "p2p_risk":      22,
    "airborne":      False,
    "continents":    3,
    "growth_rate":   1.08,
}

FIRST_CASE_DATE = datetime(2026, 4, 6)

RISK_THRESHOLDS = [
    (0,  20,  "#22c55e", "STABLE",      "Contained — limited spread"),
    (20, 40,  "#84cc16", "MODERATE",    "Being watched by local health teams"),
    (40, 60,  "#f59e0b", "HIGH ALERT", "Spreading across borders"),
    (60, 80,  "#ef4444", "CRITICAL",  "Spreading continuously — situation worsening"),
    (80, 101, "#dc2626", "EXTREME",   "Global health alert"),
]


def _compute_risk(cases: int, countries: int) -> dict[str, Any]:
    days = max((datetime.utcnow() - FIRST_CASE_DATE).days, 1)

    transmission   = ANDES_FIXED["p2p_risk"]          # 22 — limited P2P
    spread         = min(countries / 15 * 100, 100)    # 8 countries → 53
    growth_daily   = cases / days
    growth_score   = min(growth_daily * 18, 100)       # normalised
    severity       = min(ANDES_FIXED["cfr_pct"] / 50 * 100, 100)  # 35% CFR → 70

    overall = (
        transmission * 0.40
        + spread     * 0.25
        + growth_score * 0.20
        + severity   * 0.15
    )
    return {
        "overall":       round(overall, 1),
        "transmission":  round(transmission, 1),
        "spread":        round(spread, 1),
        "growth":        round(growth_score, 1),
        "severity":      round(severity, 1),
        "days":          days,
    }


def _risk_meta(score: float) -> tuple[str, str, str]:
    for lo, hi, color, label, desc in RISK_THRESHOLDS:
        if lo <= score < hi:
            return color, label, desc
    return "#dc2626", "EXTREME", "Global health alert"


@st.cache_data(ttl=300, show_spinner=False)
def _build_gauge(score: float, color: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        delta={"reference": 15, "valueformat": ".1f",
               "increasing": {"color": "#ef4444"},
               "decreasing": {"color": "#22c55e"}},
        number={"suffix": "%", "font": {"size": 52, "color": "#f8fafc", "family": "monospace"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1,
                     "tickcolor": "#475569", "tickfont": {"color": "#94a3b8", "size": 10}},
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": "rgba(27,46,69,0.6)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  20],  "color": "rgba(34,197,94,0.12)"},
                {"range": [20, 40],  "color": "rgba(132,204,22,0.12)"},
                {"range": [40, 60],  "color": "rgba(245,158,11,0.12)"},
                {"range": [60, 80],  "color": "rgba(239,68,68,0.12)"},
                {"range": [80, 100], "color": "rgba(220,38,38,0.18)"},
            ],
            "threshold": {
                "line": {"color": "#ffffff", "width": 3},
                "thickness": 0.85,
                "value": score,
            },
        },
        title={"text": "VIRUS SPREAD RISK", "font": {"size": 13, "color": "#94a3b8", "family": "monospace"}},
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#f8fafc"},
        margin=dict(l=20, r=20, t=30, b=10),
        height=280,
    )
    return fig


@st.cache_data(ttl=300, show_spinner=False)
def _build_comparison_bars(risk: dict[str, Any]) -> go.Figure:
    metrics = ["How Easily it\nSpreads", "Where it has\nReached", "Speed of\nSpread", "Severity of\nSickness"]
    andes   = [risk["transmission"], risk["spread"], risk["growth"], risk["severity"]]
    covid   = [95, 72, 88, 46]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Current Outbreak",
        x=metrics, y=andes,
        marker=dict(
            color=["rgba(0,180,216,0.85)"] * len(andes),
            line=dict(color="#00b4d8", width=1.5),
        ),
        text=[f"{v:.0f}%" for v in andes],
        textposition="outside",
        textfont=dict(color="#00b4d8", size=11, family="monospace"),
        hovertemplate="<b>Current Outbreak — %{x}</b><br>Score: %{y:.1f}%<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        name="COVID-19 (Early 2020)",
        x=metrics, y=covid,
        marker=dict(
            color=["rgba(239,68,68,0.55)"] * len(covid),
            line=dict(color="#ef4444", width=1.5),
        ),
        text=[f"{v}%" for v in covid],
        textposition="outside",
        textfont=dict(color="#ef4444", size=11, family="monospace"),
        hovertemplate="<b>COVID-19 — %{x}</b><br>Score: %{y:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", size=11),
        margin=dict(l=10, r=10, t=20, b=10),
        height=280,
        legend=dict(
            bgcolor="rgba(13,27,42,0.85)",
            bordercolor="#243b55",
            borderwidth=1,
            font=dict(color="#94a3b8", size=10),
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right",  x=1,
        ),
        xaxis=dict(gridcolor="#1b2e45", tickfont=dict(size=10)),
        yaxis=dict(gridcolor="#1b2e45", range=[0, 115], title="Risk Score (0–100)"),
        bargap=0.25,
        bargroupgap=0.08,
    )
    return fig


def render_pandemic_risk_panel() -> None:
    stats     = get_outbreak_stats()
    cases     = stats["confirmed_cases"]
    countries = stats["nationalities"]
    risk      = _compute_risk(cases, countries)
    color, label, desc = _risk_meta(risk["overall"])
    risk_score = risk["overall"]

    score = risk["overall"]

    st.markdown(
        f'<div style="border-left: 4px solid {color}; padding-left: 10px; margin-bottom: 1rem;">'
        f'<div style="display:flex; justify-content:space-between; align-items:baseline;">'
        f'<div><p style="color:#94a3b8; font-size:0.6rem; font-weight:800; letter-spacing:0.1em; margin:0; text-transform:uppercase;">Outbreak Status Check</p>'
        f'<h2 style="margin:0; font-size:1.4rem; font-weight:900; color:white; letter-spacing:-0.02em; line-height:1.1;">{label.upper()}</h2></div>'
        f'<div><span style="color:{color}; font-size:1.6rem; font-weight:900;">{score:.1f}</span>'
        f'<span style="color:#94a3b8; font-size:0.6rem; font-weight:800; margin-left:4px;">SCORE</span></div>'
        f'</div>'
        f'<p style="color:#cbd5e1; font-size:0.75rem; margin:4px 0 0; font-weight:500;">{desc}</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ── Gauge + Comparison bars ───────────────────────────────────────────────
    col_gauge, col_bars = st.columns([1, 1.6])

    with col_gauge:
        fig_gauge = _build_gauge(risk["overall"], color)
        st.plotly_chart(fig_gauge, width="stretch", config={"displayModeBar": False})

        st.markdown(
            f"<p style='color:#64748b;font-size:0.72rem;text-align:center;margin-top:-0.5rem;'>"
            f"Score updates every 5 min · Methodology: P2P spread 40%, geographic reach 25%, "
            f"growth rate 20%, CFR severity 15%</p>",
            unsafe_allow_html=True,
        )

    with col_bars:
        st.markdown(
            "<p style='color:#94a3b8;font-size:0.8rem;margin-bottom:0.2rem;'>"
            "📊 <b>Spread Factor Baseline — Andes Virus vs COVID-19</b></p>",
            unsafe_allow_html=True,
        )
        fig_bars = _build_comparison_bars(risk)
        st.plotly_chart(fig_bars, width="stretch", config={"displayModeBar": False})

    # ── Key difference callout ────────────────────────────────────────────────
    callout_html = f"""
    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:0.6rem; margin-top:0.8rem;">
        <div style="background:rgba(34,197,94,0.03); border:1px solid rgba(34,197,94,0.1); padding:0.6rem; border-radius:8px;">
            <p style="color:#4ade80; font-size:0.6rem; font-weight:900; text-transform:uppercase; margin-bottom:4px;">✓ Lower Risk Than COVID</p>
            <p style="color:#94a3b8; font-size:0.7rem; line-height:1.2; margin:0;">Less contagious. Requires close contact; not airborne like COVID.</p>
        </div>
        <div style="background:rgba(245,158,11,0.03); border:1px solid rgba(245,158,11,0.1); padding:0.6rem; border-radius:8px;">
            <p style="color:#f59e0b; font-size:0.6rem; font-weight:900; text-transform:uppercase; margin-bottom:4px;">▲ High Severity</p>
            <p style="color:#94a3b8; font-size:0.7rem; line-height:1.2; margin:0;">35% fatality rate. Much more dangerous if contracted.</p>
        </div>
        <div style="background:rgba(239,68,68,0.03); border:1px solid rgba(239,68,68,0.1); padding:0.6rem; border-radius:8px;">
            <p style="color:#f87171; font-size:0.6rem; font-weight:900; text-transform:uppercase; margin-bottom:4px;">🚨 WATCH: MUTATION</p>
            <p style="color:#94a3b8; font-size:0.7rem; line-height:1.2; margin:0;">Monitoring changes in spread efficiency across borders.</p>
        </div>
    </div>
    """
    st.markdown(callout_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
