"""Shareable outbreak card generator — Apple-inspired black/white, PIL-based."""
from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from ui.stats_panel import OUTBREAK_DATA, CASE_TIMELINE
from ui.map_panel import NATIONALITIES_DATA

# ── Font paths — bundled in assets/fonts/ for cloud deployment ───────────────
_ASSET_FONT_DIR  = Path(__file__).parent.parent / "assets" / "fonts"
_SYSTEM_FONT_DIR = Path("/usr/share/fonts/truetype/inter-zorin-os")
_FONT_DIR        = _ASSET_FONT_DIR if _ASSET_FONT_DIR.exists() else _SYSTEM_FONT_DIR

_FONTS: dict[str, Path] = {
    "black":    _FONT_DIR / "Inter-Black.ttf",
    "bold":     _FONT_DIR / "Inter-Bold.ttf",
    "semibold": _FONT_DIR / "Inter-SemiBold.ttf",
    "medium":   _FONT_DIR / "Inter-Medium.ttf",
    "regular":  _FONT_DIR / "Inter-Regular.ttf",
    "light":    _FONT_DIR / "Inter-Light.ttf",
}


def _font(style: str, size: int) -> ImageFont.FreeTypeFont:
    path = _FONTS.get(style, _FONTS["regular"])
    try:
        return ImageFont.truetype(str(path), size)
    except (OSError, IOError):
        # Final fallback — PIL default bitmap font (no custom styling)
        return ImageFont.load_default()

# ── Palette ───────────────────────────────────────────────────────────────────
BG      = (0,   0,   0)        # true black
WHITE   = (255, 255, 255)
GRAY1   = (142, 142, 147)      # Apple secondary label
GRAY2   = (44,  44,  46)       # Apple separator
GRAY3   = (28,  28,  30)       # Apple grouped bg
RED     = (255, 59,  48)       # Apple red
AMBER   = (255, 159, 10)       # Apple amber
GREEN   = (52,  199, 89)       # Apple green

W, H    = 1200, 630
PAD     = 60


def _draw_text_right(draw: ImageDraw.ImageDraw, y: int, text: str,
                     font: ImageFont.FreeTypeFont, color: tuple) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((W - PAD - tw, y), text, font=font, fill=color)


def _bar(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
         fill: tuple, radius: int = 4) -> None:
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill)


def generate_card() -> bytes:
    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    d = OUTBREAK_DATA
    cases    = d["confirmed_cases"]
    deaths   = d["deaths"]
    cfr      = d["case_fatality_rate"]
    nat      = d["nationalities"]
    ship     = d["ship_status"]
    today    = datetime.utcnow().strftime("%B %d, %Y  %H:%M UTC")

    # ── Header band ──────────────────────────────────────────────────────────
    draw.rectangle([0, 0, W, 8], fill=RED)

    draw.text((PAD, 36),  "ANDES VIRUS / MV HONDIUS OUTBREAK", font=_font("black", 36),   fill=WHITE)
    draw.text((PAD, 82),  "Live Outbreak Assessment",            font=_font("light", 18),   fill=GRAY1)
    _draw_text_right(draw, 36, today, _font("regular", 14), GRAY1)
    _draw_text_right(draw, 56, "adityamedepalli@outlook.com", _font("regular", 13), GRAY1)

    # Separator
    draw.rectangle([PAD, 116, W - PAD, 117], fill=GRAY2)

    # ── Stats row ────────────────────────────────────────────────────────────
    col_w = (W - PAD * 2) // 4
    stats = [
        (str(cases),  "CONFIRMED CASES",   WHITE),
        (str(deaths), "DEATHS",            RED),
        (str(nat),    "NATIONALITIES",     WHITE),
        (f"{cfr}%",   "CASE FATALITY RATE",AMBER),
    ]
    for i, (val, label, color) in enumerate(stats):
        x = PAD + i * col_w
        draw.text((x, 132), val,   font=_font("black",   64), fill=color)
        draw.text((x, 208), label, font=_font("regular", 11), fill=GRAY1)

        if i < 3:
            draw.rectangle([x + col_w - 1, 135, x + col_w, 200], fill=GRAY2)

    # Separator
    draw.rectangle([PAD, 235, W - PAD, 236], fill=GRAY2)

    # ── Timeline mini-bars ───────────────────────────────────────────────────
    draw.text((PAD, 248), "CASE PROGRESSION", font=_font("semibold", 11), fill=GRAY1)

    max_cases = max(t["cases"] for t in CASE_TIMELINE)
    bar_area_w = W - PAD * 2
    n = len(CASE_TIMELINE)
    bar_w = bar_area_w // n - 6
    bar_max_h = 58
    bar_y_base = 330

    for i, entry in enumerate(CASE_TIMELINE):
        bh = max(4, int(entry["cases"] / max_cases * bar_max_h))
        bx = PAD + i * (bar_w + 6)
        by = bar_y_base - bh
        fill = RED if i == n - 1 else GRAY2
        _bar(draw, bx, by, bar_w, bh, fill, radius=3)
        draw.text(
            (bx + bar_w // 2 - 8, by - 20),
            str(entry["cases"]),
            font=_font("semibold", 12),
            fill=WHITE if i == n - 1 else GRAY1,
        )
        # Date label every other bar
        if i % 2 == 0:
            date_short = entry["date"][5:]  # MM-DD
            draw.text((bx, bar_y_base + 6), date_short, font=_font("light", 10), fill=GRAY1)

    # Separator
    draw.rectangle([PAD, 355, W - PAD, 356], fill=GRAY2)

    # ── Details row ──────────────────────────────────────────────────────────
    draw.text((PAD, 368), f"🚢  {ship}", font=_font("medium", 15), fill=WHITE)

    active = [d["code"] for d in NATIONALITIES_DATA if d["cases"] > 0]
    inactive = [d["code"] for d in NATIONALITIES_DATA if d["cases"] == 0]
    active_str   = "  ·  ".join(active)
    inactive_str = "  ·  ".join(inactive)

    draw.text((PAD, 398), f"AFFECTED:   {active_str}", font=_font("semibold", 13), fill=WHITE)
    draw.text((PAD, 420), f"MONITORING: {inactive_str}", font=_font("regular", 13), fill=GRAY1)

    # Risk level pill
    risk_text = "RISK: GUARDED"
    pill_bbox = draw.textbbox((0, 0), risk_text, font=_font("bold", 14))
    pw = pill_bbox[2] - pill_bbox[0] + 24
    draw.rounded_rectangle(
        [W - PAD - pw, 366, W - PAD, 392], radius=12,
        outline=AMBER, fill=(0, 0, 0), width=1,
    )
    draw.text((W - PAD - pw + 12, 368), risk_text, font=_font("bold", 14), fill=AMBER)

    # Separator
    draw.rectangle([PAD, 448, W - PAD, 449], fill=GRAY2)

    # ── Source / disclaimer ───────────────────────────────────────────────────
    draw.text(
        (PAD, 460),
        "Sources: WHO · CDC · PubMed · Reuters · BBC · ECDC · ProMED · Wikipedia",
        font=_font("regular", 12), fill=GRAY1,
    )
    draw.text(
        (PAD, 480),
        "Not medical advice. For emergencies contact your local health authority.",
        font=_font("light", 12), fill=GRAY2,
    )

    # Separator
    draw.rectangle([PAD, 502, W - PAD, 503], fill=GRAY2)

    # ── Author footer ─────────────────────────────────────────────────────────
    draw.text((PAD, 518), "Aditya Aravind Medepalli",     font=_font("bold", 18),    fill=WHITE)
    draw.text((PAD, 546), "adityamedepalli@outlook.com",  font=_font("regular", 13), fill=GRAY1)

    _draw_text_right(draw, 518, "Andes Virus Research Assistant",  _font("semibold", 14), GRAY1)
    _draw_text_right(draw, 540, "linkedin.com/in/aditya-aravind-medepalli", _font("regular", 12), GRAY1)

    # Bottom red bar
    draw.rectangle([0, H - 6, W, H], fill=RED)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def generate_story_card() -> bytes:
    """Vertical 1080x1920 card for Instagram/TikTok Stories."""
    SW, SH = 1080, 1920
    img  = Image.new("RGB", (SW, SH), BG)
    draw = ImageDraw.Draw(img)

    d = OUTBREAK_DATA
    today = datetime.utcnow().strftime("%B %d, %Y")

    draw.rectangle([0, 0, SW, 10], fill=RED)
    draw.rectangle([0, SH - 10, SW, SH], fill=RED)

    # Title block
    draw.text((80, 80),  "⚠",                              font=_font("black",  72), fill=RED)
    draw.text((80, 170), "ANDES VIRUS",                    font=_font("black",  78), fill=WHITE)
    draw.text((80, 260), "OUTBREAK",                       font=_font("black",  78), fill=WHITE)
    draw.text((80, 360), "MV Hondius · Live Assessment",   font=_font("light",  28), fill=GRAY1)
    draw.text((80, 400), today,                            font=_font("regular",22), fill=GRAY1)

    draw.rectangle([80, 450, SW - 80, 452], fill=GRAY2)

    # Big stats
    sy = 480
    for val, label, color in [
        (str(d["confirmed_cases"]), "CONFIRMED CASES",   WHITE),
        (str(d["deaths"]),          "DEATHS",            RED),
        (f"{d['case_fatality_rate']}%", "CASE FATALITY", AMBER),
        (str(d["nationalities"]),   "NATIONALITIES",     WHITE),
    ]:
        draw.text((80, sy),      val,   font=_font("black",   110), fill=color)
        draw.text((80, sy + 118), label, font=_font("regular",  22), fill=GRAY1)
        draw.rectangle([80, sy + 150, SW - 80, sy + 151], fill=GRAY2)
        sy += 170

    # Details
    draw.text((80, sy + 20), f"Ship: {d['ship_status']}", font=_font("medium", 26), fill=WHITE)
    draw.text((80, sy + 60), "Risk Level: GUARDED",       font=_font("semibold",26), fill=AMBER)

    # Author
    draw.rectangle([80, SH - 200, SW - 80, SH - 199], fill=GRAY2)
    draw.text((80, SH - 180), "Aditya Aravind Medepalli",     font=_font("bold",    30), fill=WHITE)
    draw.text((80, SH - 140), "adityamedepalli@outlook.com",  font=_font("regular", 22), fill=GRAY1)
    draw.text((80, SH - 100), "linkedin.com/in/aditya-aravind-medepalli", font=_font("regular", 18), fill=GRAY1)
    draw.text((80, SH - 60),  "Andes Virus Research Assistant",  font=_font("light", 20), fill=GRAY2)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
