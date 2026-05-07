"""Journalist & influencer tools — share, download, embed."""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any
from urllib.parse import quote

import streamlit as st

from ui.stats_panel import OUTBREAK_DATA, CASE_TIMELINE
from ui.map_panel import NATIONALITIES_DATA


def _summary_text() -> str:
    d = OUTBREAK_DATA
    return (
        f"🧬 Andes Virus / MV Hondius Outbreak Update ({datetime.utcnow().strftime('%b %d, %Y')})\n\n"
        f"• Confirmed cases: {d['confirmed_cases']}\n"
        f"• Deaths: {d['deaths']} (CFR {d['case_fatality_rate']}%)\n"
        f"• Nationalities affected: {d['nationalities']}\n"
        f"• Ship status: {d['ship_status']}\n\n"
        f"Data sourced from WHO, CDC, PubMed. Not medical advice."
    )


def _csv_data() -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Country", "Passengers", "Crew", "Cases", "Deaths", "Status"])
    for row in NATIONALITIES_DATA:
        writer.writerow([
            row["country"], row["passengers"], row["crew"],
            row["cases"], row["deaths"],
            "Active monitoring" if row["cases"] > 0 else "Under observation",
        ])
    writer.writerow([])
    writer.writerow(["Date", "Cumulative Cases", "Event"])
    for t in CASE_TIMELINE:
        writer.writerow([t["date"], t["cases"], t["label"]])
    return buf.getvalue()


def _full_report() -> str:
    d = OUTBREAK_DATA
    lines = [
        "=" * 60,
        "ANDES VIRUS / MV HONDIUS OUTBREAK — SITUATION REPORT",
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "=" * 60,
        "",
        "SUMMARY",
        f"  Confirmed cases:       {d['confirmed_cases']}",
        f"  Deaths:                {d['deaths']}",
        f"  Case fatality rate:    {d['case_fatality_rate']}%",
        f"  Nationalities:         {d['nationalities']}",
        f"  Ship status:           {d['ship_status']}",
        f"  Last updated:          {d['last_updated']}",
        "",
        "CASES BY NATIONALITY",
    ]
    for row in NATIONALITIES_DATA:
        if row["cases"] > 0 or row["passengers"] > 0 or row["crew"] > 0:
            lines.append(
                f"  {row['country']:<20} Passengers: {row['passengers']:>3}  "
                f"Crew: {row['crew']:>3}  Cases: {row['cases']:>2}  Deaths: {row['deaths']:>1}"
            )
    lines += [
        "",
        "CASE TIMELINE",
    ]
    for t in CASE_TIMELINE:
        lines.append(f"  {t['date']}  {t['cases']:>3} cases  {t['label']}")
    lines += [
        "",
        "=" * 60,
        "Data sourced from WHO, CDC, PubMed, Reuters, BBC, Wikipedia.",
        "NOT MEDICAL ADVICE. For emergencies contact local health authority.",
        "Tool: Andes Virus Research Assistant",
    ]
    return "\n".join(lines)


def render_journalist_tools() -> None:
    summary = _summary_text()
    encoded = quote(summary)

    st.markdown(
        '<div style="background:linear-gradient(135deg,rgba(13,27,42,0.95),rgba(27,46,69,0.95));'
        'border:1px solid rgba(0,180,216,0.3);border-top:3px solid #00b4d8;border-radius:12px;'
        'padding:1rem 1.2rem;margin-bottom:0.5rem;">'
        '<p style="color:#00b4d8;font-size:0.95rem;font-weight:700;margin:0 0 0.8rem;letter-spacing:0.04em;">'
        '📤 SHARE & DOWNLOAD</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<p style="color:#64748b;font-size:0.73rem;margin:0 0 0.8rem;">'
        'Share the outbreak update, download shareable cards, or export raw data.</p>',
        unsafe_allow_html=True,
    )

    # ── Shareable image cards ────────────────────────────────────────────────
    st.markdown(
        '<p style="color:#94a3b8;font-size:0.75rem;font-weight:600;margin:0 0 0.4rem;">'
        '🖼 Shareable Cards (download → post on social media):</p>',
        unsafe_allow_html=True,
    )

    card_col1, card_col2 = st.columns(2)
    with card_col1:
        with st.spinner("Generating card…"):
            from ui.card_generator import generate_card
            card_bytes = generate_card()
        st.download_button(
            "⬛ Outbreak Card  (1200×630 · Twitter / LinkedIn)",
            data=card_bytes,
            file_name=f"andes_card_{datetime.utcnow().strftime('%Y%m%d')}.png",
            mime="image/png",
            use_container_width=True,
            key="dl_card_wide",
        )
    with card_col2:
        with st.spinner("Generating story…"):
            from ui.card_generator import generate_story_card
            story_bytes = generate_story_card()
        st.download_button(
            "⬛ Story Card  (1080×1920 · Instagram / TikTok)",
            data=story_bytes,
            file_name=f"andes_story_{datetime.utcnow().strftime('%Y%m%d')}.png",
            mime="image/png",
            use_container_width=True,
            key="dl_card_story",
        )

    st.markdown("<div style='margin-top:0.8rem;'></div>", unsafe_allow_html=True)

    # ── Share buttons ────────────────────────────────────────────────────────
    st.markdown(
        '<p style="color:#94a3b8;font-size:0.75rem;font-weight:600;margin:0 0 0.4rem;">'
        '🔗 Share update text directly:</p>',
        unsafe_allow_html=True,
    )

    share_links = [
        ("𝕏 Twitter/X",  f"https://twitter.com/intent/tweet?text={encoded}",         "#1a1a1a", "#ffffff"),
        ("in LinkedIn",  f"https://www.linkedin.com/shareArticle?mini=true&title=Andes+Virus+Outbreak&summary={encoded}", "#0a66c2", "#ffffff"),
        ("✈ Telegram",   f"https://t.me/share/url?text={encoded}",                    "#0088cc", "#ffffff"),
        ("💬 WhatsApp",  f"https://api.whatsapp.com/send?text={encoded}",             "#25d366", "#000000"),
    ]

    cols = st.columns(len(share_links))
    for col, (label, url, bg, fg) in zip(cols, share_links):
        with col:
            st.markdown(
                f'<a href="{url}" target="_blank" rel="noopener" style="display:block;text-align:center;'
                f'background:{bg};color:{fg};border-radius:8px;padding:0.45rem 0.3rem;font-size:0.72rem;'
                f'font-weight:700;text-decoration:none;border:1px solid rgba(255,255,255,0.1);">'
                f'{label}</a>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='margin-top:0.8rem;'></div>", unsafe_allow_html=True)

    # ── Download data ────────────────────────────────────────────────────────
    st.markdown(
        '<p style="color:#94a3b8;font-size:0.75rem;font-weight:600;margin:0 0 0.4rem;">'
        '📊 Download raw data:</p>',
        unsafe_allow_html=True,
    )

    dl_col1, dl_col2, dl_col3 = st.columns(3)
    with dl_col1:
        st.download_button(
            "📄 Situation Report",
            data=_full_report(),
            file_name=f"andes_outbreak_{datetime.utcnow().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with dl_col2:
        st.download_button(
            "📊 Case Data (CSV)",
            data=_csv_data(),
            file_name=f"andes_cases_{datetime.utcnow().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with dl_col3:
        st.download_button(
            "📋 Summary Text",
            data=summary,
            file_name="andes_summary.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
