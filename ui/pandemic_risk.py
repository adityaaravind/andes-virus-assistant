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
    (0,  20,  "#22c55e", "LOW",      "Contained — limited P2P transmission"),
    (20, 40,  "#84cc16", "GUARDED",  "Regional concern — monitoring required"),
    (40, 60,  "#f59e0b", "ELEVATED", "Multi-national spread detected"),
    (60, 80,  "#ef4444", "HIGH",     "Sustained transmission — outbreak escalating"),
    (80, 101, "#dc2626", "CRITICAL", "Pandemic trajectory confirmed"),
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
    return "#dc2626", "CRITICAL", "Pandemic trajectory confirmed"


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
        title={"text": "PANDEMIC RISK SCORE", "font": {"size": 13, "color": "#94a3b8", "family": "monospace"}},
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#f8fafc"},
        margin=dict(l=20, r=20, t=30, b=10),
        height=260,
    )
    return fig


@st.cache_data(ttl=300, show_spinner=False)
def _build_comparison_bars(risk: dict[str, Any]) -> go.Figure:
    metrics = ["Transmission\nRisk", "Geographic\nSpread", "Growth\nRate", "CFR\n(Fatality Rate)"]
    andes   = [risk["transmission"], risk["spread"], risk["growth"], risk["severity"]]
    covid   = [95, 72, 88, 46]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Andes Virus (current)",
        x=metrics, y=andes,
        marker=dict(
            color=["rgba(0,180,216,0.85)"] * len(andes),
            line=dict(color="#00b4d8", width=1.5),
        ),
        text=[f"{v:.0f}%" for v in andes],
        textposition="outside",
        textfont=dict(color="#00b4d8", size=11, family="monospace"),
        hovertemplate="<b>Andes — %{x}</b><br>Score: %{y:.1f}%<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        name="COVID-19 (early stage ref.)",
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

    # ── Flashy header ────────────────────────────────────────────────────────
    import textwrap
    anim = "pulse-risk 1.8s ease-in-out infinite" if risk["overall"] >= 40 else "none"
    header_html = f"""
<div style="background:rgba(15, 23, 42, 0.4); border:1px solid {color}44; border-radius:12px; padding:1.2rem;
margin-bottom:1rem; position:relative; overflow:hidden;">
<div style="display:flex; align-items:center; gap:2rem; flex-wrap:wrap;">
<div style="flex-shrink:0;">
<p style="color:{color};font-size:0.7rem;font-weight:800;letter-spacing:0.12em;margin:0;font-family:monospace;opacity:0.8;">
GLOBAL PANDEMIC RISK ASSESSMENT</p>
<h2 style="margin:0.1rem 0 0;font-size:2.2rem !important;font-weight:900;color:white !important;letter-spacing:-0.02em;">{label}</h2>
</div>
<div style="background:{color}15; border:2px solid {color}88; border-radius:10px; padding:0.4rem 1.2rem; 
text-align:center; min-width:110px; box-shadow: 0 0 20px {color}15;">
<p style="color:{color}; font-size:1.8rem; font-weight:900; margin:0; line-height:1; text-shadow:0 0 10px {color}88;">{risk['overall']}%</p>
<p style="color:#94a3b8; font-size:0.6rem; font-weight:800; margin:2px 0 0; text-transform:uppercase; letter-spacing:0.05em; opacity:0.8;">RISK SCORE</p>
</div>
</div>
<div style="display:flex;gap:1.2rem;margin-top:1rem;flex-wrap:wrap;border-top:1px solid rgba(148,163,184,0.1);padding-top:0.6rem;">
<span style="color:#94a3b8;font-size:0.7rem;">📅 Day <b style="color:white;">{risk['days']}</b></span>
<span style="color:#94a3b8;font-size:0.7rem;">🧪 Cases: <b style="color:white;">{cases}</b></span>
<span style="color:#94a3b8;font-size:0.7rem;">📈 R₀: <b style="color:white;">{ANDES_FIXED['r0']}</b></span>
<span style="color:#94a3b8;font-size:0.7rem;">💀 CFR: <b style="color:white;">{ANDES_FIXED['cfr_pct']}%</b></span>
</div>
</div>
<style>
@keyframes pulse-risk {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.4; }} }}
</style>
""".replace("\n", "").strip()
    st.markdown(header_html, unsafe_allow_html=True)


    # ── Gauge + Comparison bars ───────────────────────────────────────────────
    col_gauge, col_bars = st.columns([1, 1.6])

    with col_gauge:
        fig_gauge = _build_gauge(risk["overall"], color)
        st.plotly_chart(fig_gauge, width="stretch", config={"displayModeBar": False})

        st.markdown(
            f"<p style='color:#64748b;font-size:0.72rem;text-align:center;margin-top:-0.5rem;'>"
            f"Score updates every 5 min · Methodology: P2P risk 40%, geographic spread 25%, "
            f"growth rate 20%, CFR severity 15%</p>",
            unsafe_allow_html=True,
        )

    with col_bars:
        st.markdown(
            "<p style='color:#94a3b8;font-size:0.8rem;margin-bottom:0.2rem;'>"
            "📊 <b>Risk Factor Comparison — Andes Virus vs COVID-19</b></p>",
            unsafe_allow_html=True,
        )
        fig_bars = _build_comparison_bars(risk)
        st.plotly_chart(fig_bars, width="stretch", config={"displayModeBar": False})

    # ── Key difference callout ────────────────────────────────────────────────
    callout_html = f"""
<style>
.risk-callout-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 0.6rem;
    margin-top: 0.3rem;
}}
</style>
<div class="risk-callout-grid">
<div style="background:rgba(34,197,94,0.08);border:1px solid #22c55e44;border-radius:8px;padding:0.6rem 0.8rem;">
<p style="color:#22c55e;font-size:0.72rem;font-weight:700;margin:0;">✓ LOWER RISK THAN COVID</p>
<p style="color:#94a3b8;font-size:0.73rem;margin:0.2rem 0 0;">
No airborne transmission. P2P spread requires close contact.
R₀ (reproduction rate) {ANDES_FIXED['r0']} vs COVID {COVID_EARLY['r0']}.
</p>
</div>
<div style="background:rgba(245,158,11,0.08);border:1px solid #f59e0b44;border-radius:8px;padding:0.6rem 0.8rem;">
<p style="color:#f59e0b;font-size:0.72rem;font-weight:700;margin:0;">⚠ HIGH SEVERITY</p>
<p style="color:#94a3b8;font-size:0.73rem;margin:0.2rem 0 0;">
CFR (case fatality rate) {ANDES_FIXED['cfr_pct']}% vs COVID {COVID_EARLY['cfr_pct']}%.
No approved antiviral treatment. Hospital mortality high.
</p>
</div>
<div style="background:rgba(239,68,68,0.08);border:1px solid #ef444444;border-radius:8px;padding:0.6rem 0.8rem;">
<p style="color:#ef4444;font-size:0.72rem;font-weight:700;margin:0;">🚨 WATCH: MUTATION RISK</p>
<p style="color:#94a3b8;font-size:0.73rem;margin:0.2rem 0 0;">
If P2P transmission efficiency increases, risk score escalates rapidly.
Multi-national passenger spread already confirmed.
</p>
</div>
</div>
""".replace("\n", "").strip()
    st.markdown(callout_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
