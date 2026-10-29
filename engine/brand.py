"""Compar Assurance brand constants for the social engine.

Source of truth: the Compar Assurance design system (claude.ai artifact 7dPeusZWf38DDfEk32X6Ue).
Colours are the measured tokens; the C path is copied from compar-fav-logo-blue.svg.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FONTS = ROOT / "fonts"
ASSETS = ROOT / "assets"

COLORS = {
    "blue_royal": "#003ca6",   # post grounds, C band, quotation marks
    "blue_compar": "#254aad",  # logo blue
    "blue_sky": "#5995ff",     # accent words on charcoal
    "blue_mid": "#6b99e6",     # C mark segment, sublines on royal (24px+)
    "blue_mist": "#bfcce2",    # muted text on royal
    "charcoal": "#1e1e1e",     # Vrai ou faux / Mythes cards
    "ink": "#0b0f19",
    "coral": "#ff5959",        # the word "Faux." only
    "green": "#5aff7d",        # the word "vrai." only
    "orange": "#ed783d",       # warm accent, small fills only
    "white": "#ffffff",
}

# Exact paths from compar-fav-logo-blue.svg (viewBox 0 0 112 112)
C_PATH = ("M85.9,83.9c-3.4,3.9-7.5,7.1-12.1,9.5-4.5,2.3-10.2,3.5-17.3,3.5-12.6,0-22.3-4-29.2-11.9-6.8-8-10.2-17.7-10.2-29.1,"
          "0-11.4,3.4-21,10.2-28.8,6.8-7.9,16.5-11.8,29.2-11.8,5.6,0,11.1,1,16.2,3.1,4.8,1.9,9.1,5,12.4,9l-12.6,12.4c-4.9-5.1-10.2-7.7-16-7.7"
          "-6.6,0-11.7,2.3-15.2,6.9-3.6,4.6-5.4,10.3-5.4,17.1-.2,6.1,1.7,12,5.3,16.9,3.5,4.6,8.6,7,15.2,7,2.5,0,5-.5,7.3-1.6,1.7-.7,3.3-1.6,4.7-2.6"
          ".8-.7,2.2-1.9,4-3.6l13.4,11.9Z")
SEG_PATH = "M95.9,55.9c0,8.3-1.8,15.6-5.4,22.1l-15.5-13.3c.9-2.8,1.2-5.7,1.2-8.6,0-2.9-.4-5.9-1.2-8.7l14.9-14.2c4,6.6,6,14.2,6,22.8Z"
# The counter's bottom point in logo units; used to place the C on a frame.
C_COUNTER_BOTTOM = (56.4, 80.0)

FORMATS = {
    "4x5": (1080, 1350),    # Instagram / Facebook feed, carousels
    "9x16": (1080, 1920),   # Reels, Stories, TikTok, Shorts
    "4x3": (1200, 900),     # Google Business Profile
    "1x1": (1080, 1080),
}

# Reels/TikTok interface covers roughly the top 14% and bottom 35%; keep text inside.
SAFE_9x16 = {"top": 270, "bottom": 1920 - 670}


def font_face_css() -> str:
    f = FONTS
    return f"""
@font-face {{ font-family:"Manrope"; src:url({f}/manrope-latin-400-normal.woff2) format("woff2"); font-weight:400; }}
@font-face {{ font-family:"Manrope"; src:url({f}/manrope-latin-600-normal.woff2) format("woff2"); font-weight:600; }}
@font-face {{ font-family:"Manrope"; src:url({f}/manrope-latin-700-normal.woff2) format("woff2"); font-weight:700; }}
@font-face {{ font-family:"Manrope"; src:url({f}/manrope-latin-800-normal.woff2) format("woff2"); font-weight:800; }}
@font-face {{ font-family:"Newsreader"; src:url({f}/newsreader-latin-opsz-italic.woff2) format("woff2"); font-style:italic; font-weight:200 800; }}
"""


BASE_CSS = """
html,body{margin:0;padding:0}
*{box-sizing:border-box}
.frame{position:relative;overflow:hidden;font-family:Manrope,sans-serif;color:#fff}
em,.it{font-family:Newsreader,Georgia,serif;font-style:italic;font-weight:650;font-variation-settings:"opsz" 72;letter-spacing:-0.01em}
sup{font-size:.5em;vertical-align:.95em;line-height:0;margin-left:.02em}
"""
