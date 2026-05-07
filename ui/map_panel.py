"""Outbreak map — choropleth by nationality + confirmed case/death markers + ship dock."""
from __future__ import annotations

import json
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

LIVE_FILE = Path("data/outbreak_live.json")

MV_HONDIUS_LAT = 14.93
MV_HONDIUS_LON = -23.51

# Source: WHO DON599 (2026-DON599) — 147 aboard (88 pass, 59 crew, 23 nationalities)
# Nationality breakdown approximated from response countries; per-nationality case data not disclosed by WHO
NATIONALITIES_DATA = [
    {"country": "Spain",         "code": "ESP", "passengers": 27, "crew": 0,  "cases": 2, "deaths": 1},
    {"country": "United Kingdom","code": "GBR", "passengers": 20, "crew": 0,  "cases": 1, "deaths": 0},
    {"country": "United States", "code": "USA", "passengers": 15, "crew": 0,  "cases": 0, "deaths": 0},
    {"country": "Netherlands",   "code": "NLD", "passengers": 12, "crew": 5,  "cases": 1, "deaths": 1},
    {"country": "Germany",       "code": "DEU", "passengers": 10, "crew": 0,  "cases": 0, "deaths": 0},
    {"country": "Philippines",   "code": "PHL", "passengers": 0,  "crew": 38, "cases": 2, "deaths": 1},
    {"country": "South Africa",  "code": "ZAF", "passengers": 0,  "crew": 16, "cases": 0, "deaths": 0},
    {"country": "Argentina",     "code": "ARG", "passengers": 4,  "crew": 0,  "cases": 1, "deaths": 0},
]

# Most-recent confirmed case: Case 3 — confirmed hantavirus May 2, 2026 (ICU, South Africa)
LATEST_CASE = {
    "lat": -26.2041, "lon": 28.0473,
    "city": "Johannesburg, South Africa",
    "detail": "Case 3 — confirmed hantavirus May 2, 2026 · ICU at NICD partner hospital",
    "date": "May 2, 2026",
}

# Case locations from WHO DON599 — Cases 2 & 3 evacuated to South Africa; remainder on ship
CASE_LOCATIONS = [
    {
        "lat": -26.2041, "lon": 28.0473,
        "city": "Johannesburg, South Africa", "cases": 2, "deaths": 1,
        "detail": "Case 2 died Apr 26 (confirmed posthumous) · Case 3 ICU — confirmed May 2 · NICD lab testing",
        "type": "case",
    },
    {
        "lat": 14.93, "lon": -23.51,
        "city": "MV Hondius — São Vicente, Cabo Verde", "cases": 5, "deaths": 2,
        "detail": "Case 1 died Apr 11 (aboard) · Case 4 died May 2 · Cases 5–7 suspected (still aboard)",
        "type": "case",
    },
]

# Actual itinerary per WHO DON599: departed Ushuaia Apr 1, 2026
SHIP_ROUTE = [
    {"lat": -54.8, "lon": -68.3,  "label": "Ushuaia, Argentina (departure Apr 1)"},
    {"lat": -54.3, "lon": -36.5,  "label": "South Georgia Island"},
    {"lat": -37.1, "lon": -12.3,  "label": "Tristan da Cunha"},
    {"lat": -15.9, "lon":  -5.7,  "label": "Saint Helena"},
    {"lat":  -7.9, "lon": -14.4,  "label": "Ascension Island"},
    {"lat":  14.93, "lon": -23.51, "label": "Cabo Verde (moored May 4 — current)"},
]


def _live_totals() -> dict:
    """Read confirmed/deaths from live file if available."""
    if LIVE_FILE.exists():
        try:
            return json.loads(LIVE_FILE.read_text())
        except Exception:
            pass
    return {}


@st.cache_data(ttl=7200, show_spinner=False)
def build_outbreak_map() -> go.Figure:
    live   = _live_totals()
    codes  = [d["code"] for d in NATIONALITIES_DATA]
    cases  = [d["cases"] for d in NATIONALITIES_DATA]
    total_board = [d["passengers"] + d["crew"] for d in NATIONALITIES_DATA]

    # Override total confirmed from live file if newer
    live_total = live.get("confirmed_cases", sum(d["cases"] for d in NATIONALITIES_DATA))

    hover_text = [
        f"<b>{d['country']}</b><br>"
        f"On board: {d['passengers'] + d['crew']} (pass: {d['passengers']} · crew: {d['crew']})<br>"
        f"Confirmed cases: {d['cases']}<br>"
        f"Deaths: {d['deaths']}"
        for d in NATIONALITIES_DATA
    ]

    fig = go.Figure()

    # Choropleth: cases by nationality
    fig.add_trace(go.Choropleth(
        locations=codes,
        z=cases,
        text=hover_text,
        hoverinfo="text",
        colorscale=[
            [0.0,  "#1b2e45"],
            [0.01, "#0077b6"],
            [0.5,  "#00b4d8"],
            [1.0,  "#ef4444"],
        ],
        zmin=0,
        zmax=max(cases) if cases else 3,
        showscale=True,
        colorbar=dict(
            title=dict(text="Cases", font=dict(color="#94a3b8", size=10)),
            tickfont=dict(color="#94a3b8"),
            bgcolor="rgba(13,27,42,0.8)",
            bordercolor="#243b55",
            len=0.5,
            x=1.01,
        ),
        marker=dict(line=dict(color="#0d1b2a", width=0.5)),
        name="Cases by nationality",
    ))

    # Ship route line
    fig.add_trace(go.Scattergeo(
        lat=[p["lat"] for p in SHIP_ROUTE],
        lon=[p["lon"] for p in SHIP_ROUTE],
        mode="lines",
        line=dict(color="#f59e0b", width=1.5, dash="dot"),
        hoverinfo="skip",
        name="Ship route",
        showlegend=False,
    ))

    # Confirmed case markers (cyan circles)
    active_cases = [loc for loc in CASE_LOCATIONS if loc["cases"] > 0]
    fig.add_trace(go.Scattergeo(
        lat=[loc["lat"] for loc in active_cases],
        lon=[loc["lon"] for loc in active_cases],
        mode="markers",
        marker=dict(
            size=[8 + loc["cases"] * 4 for loc in active_cases],
            color="#00b4d8",
            opacity=0.85,
            line=dict(color="#ffffff", width=1),
            symbol="circle",
        ),
        hovertext=[
            f"<b>{loc['city']}</b><br>"
            f"Cases: {loc['cases']}<br>"
            f"Deaths: {loc['deaths']}<br>"
            f"{loc['detail']}"
            for loc in active_cases
        ],
        hoverinfo="text",
        name="Confirmed cases",
    ))

    # Death markers (red X)
    death_locs = [loc for loc in CASE_LOCATIONS if loc["deaths"] > 0]
    if death_locs:
        fig.add_trace(go.Scattergeo(
            lat=[loc["lat"] for loc in death_locs],
            lon=[loc["lon"] for loc in death_locs],
            mode="markers",
            marker=dict(
                size=14,
                color="#ef4444",
                opacity=1.0,
                line=dict(color="#ffffff", width=1.5),
                symbol="x",
            ),
            hovertext=[
                f"<b>{loc['city']} — FATALITY</b><br>"
                f"Deaths: {loc['deaths']}<br>"
                f"{loc['detail']}"
                for loc in death_locs
            ],
            hoverinfo="text",
            name="Deaths",
        ))

    # Latest case — gold star, pulsing ring effect via oversized transparent circle behind it
    fig.add_trace(go.Scattergeo(
        lat=[LATEST_CASE["lat"]],
        lon=[LATEST_CASE["lon"]],
        mode="markers",
        marker=dict(
            size=34,
            color="rgba(251,191,36,0.18)",
            symbol="circle",
            line=dict(color="#fbbf24", width=1.5),
        ),
        hoverinfo="skip",
        showlegend=False,
        name="_ring",
    ))
    fig.add_trace(go.Scattergeo(
        lat=[LATEST_CASE["lat"]],
        lon=[LATEST_CASE["lon"]],
        mode="markers+text",
        marker=dict(
            size=14,
            color="#fbbf24",
            symbol="star",
            line=dict(color="#ffffff", width=1.5),
        ),
        text=["⭐ LATEST"],
        textposition="top right",
        textfont=dict(color="#fbbf24", size=10, family="monospace"),
        hovertext=(
            f"<b>⭐ LATEST CONFIRMED CASE</b><br>"
            f"{LATEST_CASE['city']}<br>"
            f"{LATEST_CASE['detail']}<br>"
            f"Date: {LATEST_CASE['date']}"
        ),
        hoverinfo="text",
        name="Latest case",
    ))

    # MV Hondius dock position
    fig.add_trace(go.Scattergeo(
        lat=[MV_HONDIUS_LAT],
        lon=[MV_HONDIUS_LON],
        mode="markers+text",
        marker=dict(
            size=16,
            color="#f59e0b",
            symbol="triangle-up",
            line=dict(color="#ffffff", width=2),
        ),
        text=["MV Hondius"],
        textposition="top center",
        textfont=dict(color="#f8fafc", size=11, family="monospace"),
        hovertext=(
            "<b>MV Hondius — MOORED</b><br>"
            "Location: São Vicente, Cabo Verde<br>"
            "14.93°N, 23.51°W<br>"
            "Status: Moored — port authority hold (as of May 4, 2026)<br>"
            "Passengers: 88 · Crew: 59 · 23 nationalities<br>"
            "Source: WHO DON599"
        ),
        hoverinfo="text",
        name="MV Hondius",
    ))

    fig.update_geos(
        showcoastlines=True,
        coastlinecolor="#243b55",
        showland=True,
        landcolor="#1b2e45",
        showocean=True,
        oceancolor="#0d1b2a",
        showframe=False,
        showcountries=True,
        countrycolor="#243b55",
        projection_type="natural earth",
        bgcolor="rgba(0,0,0,0)",
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=480,
        legend=dict(
            bgcolor="rgba(13,27,42,0.85)",
            bordercolor="#243b55",
            borderwidth=1,
            font=dict(color="#94a3b8", size=10),
            x=0.01,
            y=0.01,
        ),
        font=dict(color="#f8fafc"),
    )

    return fig


def render_map_panel() -> None:
    live = _live_totals()
    total_confirmed = live.get("confirmed_cases", sum(d["cases"] for d in NATIONALITIES_DATA))
    total_deaths    = live.get("deaths", sum(d["deaths"] for d in NATIONALITIES_DATA))
    total_countries = sum(1 for d in NATIONALITIES_DATA if d["cases"] > 0)
    total_on_board  = sum(d["passengers"] + d["crew"] for d in NATIONALITIES_DATA)

    st.markdown(
        '<span class="live-dot"></span>'
        '<span class="live-label">OUTBREAK GEOGRAPHY</span>'
        f'&nbsp;&nbsp;<span style="color:#f8fafc;font-size:0.8rem;">'
        f'<b>{total_confirmed}</b> confirmed · <b>{total_deaths}</b> deaths · '
        f'<b>{total_countries}</b> nationalities · <b>{total_on_board}</b> total on board</span>',
        unsafe_allow_html=True,
    )

    col_legend1, col_legend2, col_legend3, col_legend4 = st.columns(4)
    with col_legend1:
        st.markdown(
            "<span style='color:#00b4d8;font-size:0.8rem;'>⬤ Confirmed cases</span> "
            "<span style='color:#64748b;font-size:0.75rem;'>(size = count)</span>",
            unsafe_allow_html=True,
        )
    with col_legend2:
        st.markdown(
            "<span style='color:#ef4444;font-size:0.8rem;'>✕ Death location</span>",
            unsafe_allow_html=True,
        )
    with col_legend3:
        st.markdown(
            "<span style='color:#f59e0b;font-size:0.8rem;'>▲ MV Hondius (docked)</span>",
            unsafe_allow_html=True,
        )
    with col_legend4:
        st.markdown(
            "<span style='color:#fbbf24;font-size:0.8rem;'>★ Latest confirmed case</span>",
            unsafe_allow_html=True,
        )

    fig = build_outbreak_map()
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    # ── Country breakdown table ───────────────────────────────────────────────
    st.markdown(
        '<p style="color:#94a3b8;font-size:0.75rem;font-weight:600;margin:0.4rem 0 0.3rem;">'
        '📊 Cases by Nationality — Confirmed vs Total On Board</p>',
        unsafe_allow_html=True,
    )

    rows_html = ""
    for d in sorted(NATIONALITIES_DATA, key=lambda x: x["cases"], reverse=True):
        on_board = d["passengers"] + d["crew"]
        pct      = f"{d['cases']/on_board*100:.1f}%" if on_board else "—"
        case_color = "#ef4444" if d["cases"] >= 2 else "#f59e0b" if d["cases"] == 1 else "#64748b"
        rows_html += (
            f'<tr>'
            f'<td style="padding:4px 10px;color:#f1f5f9;font-size:0.78rem;">{d["country"]}</td>'
            f'<td style="padding:4px 10px;color:#94a3b8;font-size:0.78rem;text-align:center;">'
            f'{d["passengers"]} pass · {d["crew"]} crew</td>'
            f'<td style="padding:4px 10px;text-align:center;">'
            f'<span style="color:{case_color};font-weight:700;font-size:0.82rem;">{d["cases"]}</span>'
            f'<span style="color:#64748b;font-size:0.72rem;"> / {on_board} ({pct})</span></td>'
            f'<td style="padding:4px 10px;color:{"#ef4444" if d["deaths"] else "#64748b"};'
            f'text-align:center;font-size:0.78rem;">{d["deaths"] or "—"}</td>'
            f'</tr>'
        )

    st.markdown(
        '<table style="width:100%;border-collapse:collapse;background:rgba(13,27,42,0.6);'
        'border:1px solid #243b55;border-radius:8px;overflow:hidden;">'
        '<thead><tr style="background:rgba(0,180,216,0.1);">'
        '<th style="padding:6px 10px;color:#00b4d8;font-size:0.72rem;text-align:left;'
        'text-transform:uppercase;letter-spacing:0.05em;">Country</th>'
        '<th style="padding:6px 10px;color:#00b4d8;font-size:0.72rem;text-align:center;'
        'text-transform:uppercase;letter-spacing:0.05em;">On Board</th>'
        '<th style="padding:6px 10px;color:#00b4d8;font-size:0.72rem;text-align:center;'
        'text-transform:uppercase;letter-spacing:0.05em;">Confirmed / Total (%)</th>'
        '<th style="padding:6px 10px;color:#00b4d8;font-size:0.72rem;text-align:center;'
        'text-transform:uppercase;letter-spacing:0.05em;">Deaths</th>'
        '</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        '</table>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="color:#475569;font-size:0.68rem;margin-top:0.3rem;">'
        f'Total: {total_confirmed} confirmed · {total_deaths} deaths · '
        f'{total_on_board} people on board across {len(NATIONALITIES_DATA)} nationalities · '
        f'Updates every 2h</p>',
        unsafe_allow_html=True,
    )
