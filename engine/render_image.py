"""Render Compar Assurance social images from a JSON spec.

usage:
  python3 engine/render_image.py spec.json

spec.json:
  {"out_dir": "posts/2026-11-03-slug", "items": [ {<template spec>}, ... ]}

Templates (each item has "template", "name" and its own fields):
  lifestyle  photo inside the frame, the logo's exact C as a blue band, headline on the band
             fields: photo, headline (HTML; <em> = Tiempos/Newsreader italic), subline, format (4x5|9x16|4x3),
                     zoom (>=1), focus [fx, fy] (subject point in the photo, 0-1), target [tx, ty] (where it lands, 0-1)
  vrai_faux  2 slides: question (white, giant quotes, charcoal card) and verdict
             fields: label (pill, e.g. "ASSURANCE AUTO"), statement, verdict ("vrai"|"faux"), explanation (list of lines, HTML ok)
  mythes     cover + one slide per myth
             fields: product (lowercase, e.g. "auto"), myths: [{"statement": html, "verdict": "faux"|"vrai", "explanation": [p, p]}]
  cta        closing slide: headline (HTML), subline, url_pill (e.g. "comparassurance.ca"), format
  text_card  bold statement on blue-royal with the C (no photo): kicker, headline (HTML), subline, format

Every image is written as JPEG (Instagram's API accepts JPEG only) and PNG preview off.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from brand import (ASSETS, BASE_CSS, C_COUNTER_BOTTOM, C_PATH, COLORS, FORMATS,  # noqa: E402
                   SEG_PATH, font_face_css)
from PIL import Image  # noqa: E402

C = COLORS
LOGO_WHITE = (ASSETS / "logo-white.svg").read_text()


def _c_transform(s, cbx, cby):
    tx = cbx - C_COUNTER_BOTTOM[0] * s
    ty = cby - C_COUNTER_BOTTOM[1] * s
    return f"translate({tx:.2f} {ty:.2f}) scale({s})"


def _photo_box(photo, W, H, zoom=1.0, focus=(0.5, 0.45), target=(0.45, 0.36)):
    w, h = Image.open(photo).size
    sc = max(W / w, H / h) * max(1.0, zoom)
    pw, ph = w * sc, h * sc
    px = target[0] * W - focus[0] * pw
    py = target[1] * H - focus[1] * ph
    px = min(0, max(W - pw, px))
    py = min(0, max(H - ph, py))
    return px, py, pw, ph


def _page(W, H, body, extra_css=""):
    return f"""<!doctype html><html lang="fr-CA"><head><meta charset="utf-8"><style>
{font_face_css()}{BASE_CSS}
.frame{{width:{W}px;height:{H}px}}
{extra_css}
</style></head><body><div class="frame">{body}</div></body></html>"""


# ---------------------------------------------------------------- lifestyle
LIFESTYLE_GEOMETRY = {
    # C scale, counter-bottom position, text bottom, headline px, subline px
    "4x5": dict(s=27, cbx=420, cby=1008, textbottom=104, h1=60, sub=33, left=80, right=80),
    "9x16": dict(s=36, cbx=430, cby=1290, textbottom=400, h1=68, sub=36, left=80, right=80),
    "4x3": dict(s=21, cbx=600, cby=600, textbottom=64, h1=44, sub=25, left=110, right=430),
}


def lifestyle(it):
    fmt = it.get("format", "4x5")
    W, H = FORMATS[fmt]
    g = dict(LIFESTYLE_GEOMETRY[fmt])
    g.update(it.get("geometry", {}))
    px, py, pw, ph = _photo_box(it["photo"], W, H, it.get("zoom", 1.0),
                                tuple(it.get("focus", (0.5, 0.45))), tuple(it.get("target", (0.45, 0.36))))
    ctr = _c_transform(g["s"], g["cbx"], g["cby"])
    body = f"""
<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" style="position:absolute;inset:0">
  <image href="{Path(it['photo']).resolve()}" x="{px:.1f}" y="{py:.1f}" width="{pw:.1f}" height="{ph:.1f}" preserveAspectRatio="none"/>
  <path transform="{ctr}" d="{C_PATH}" fill="{C['blue_royal']}"/>
</svg>
<div class="copy"><h1>{it['headline']}</h1>{f'<p class="sub">{it["subline"]}</p>' if it.get('subline') else ''}</div>"""
    css = f"""
.frame{{background:{C['blue_royal']}}}
.copy{{position:absolute;left:{g['left']}px;right:{g['right']}px;bottom:{g['textbottom']}px}}
h1{{margin:0;font-weight:700;font-size:{g['h1']}px;line-height:1.17;letter-spacing:-0.012em}}
h1 em{{font-size:1.08em}}
.sub{{margin:{round(g['sub']*0.8)}px 0 0;font-weight:600;font-size:{g['sub']}px;line-height:1.3;color:{C['blue_mist']}}}"""
    return [(it.get("name", "lifestyle"), W, H, _page(W, H, body, css))]


# ---------------------------------------------------------------- shared bits
def _pill(text, color="#fff"):
    return f'<span class="pill" style="border-color:{color};color:{color}">{text}</span>'


PILL_CSS = """
.pill{display:inline-block;border:2px solid #fff;border-radius:999px;padding:10px 26px 9px;font-weight:700;
      font-size:26px;letter-spacing:.02em;text-transform:uppercase;line-height:1}
.arrow{position:absolute;right:56px;bottom:52px;width:150px;height:62px;border:2px solid #fff;border-radius:999px}
.arrow svg{position:absolute;left:30px;top:20px}
"""
ARROW = ('<div class="arrow"><svg width="90" height="22" viewBox="0 0 90 22"><path d="M0 11H86M76 1l10 10-10 10" '
         'stroke="#fff" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg></div>')


# ---------------------------------------------------------------- vrai ou faux
def vrai_faux(it):
    """One continuous card across both slides: it starts on slide 1 and finishes on slide 2,
    so the swipe reads as a single piece. Rendered as one 2160-wide canvas, then split in two."""
    w, H = FORMATS["4x5"]
    W = w * 2
    css = PILL_CSS + f"""
.frame{{background:#fff}}
.q{{position:absolute;font-weight:800;color:{C['blue_royal']};font-size:520px;line-height:1;letter-spacing:-0.06em}}
.q1{{left:96px;top:-10px}} .q2{{right:96px;bottom:-250px}}
.card{{position:absolute;left:56px;right:56px;top:330px;bottom:330px;background:{C['charcoal']};border-radius:44px;
       box-shadow:0 30px 60px rgba(0,0,0,.28)}}
.half{{position:absolute;top:330px;bottom:330px;width:{w}px;padding:70px 90px 70px 110px}}
.h1{{left:0}} .h2{{left:{w}px;padding-left:110px}}
.half h2{{margin:44px 0 30px;font-size:96px;line-height:1;font-weight:800;letter-spacing:-0.02em}}
.half h2 em{{color:{C['blue_sky']};font-size:1.04em}}
.half p{{margin:0;font-weight:600;font-size:44px;line-height:1.28}}
.half p.small{{font-size:38px;font-weight:500;line-height:1.38;margin-top:22px}}
.half .arrow{{right:56px}}
.half h2 em.green{{color:{C['green']}}} .half h2 em.coral{{color:{C['coral']}}}"""
    word = it["verdict"].lower()
    cls = "green" if word == "vrai" else "coral"
    lines = "".join(f'<p class="small">{x}</p>' for x in it["explanation"])
    body = f"""<div class="q q1">“</div><div class="q q2">”</div><div class="card"></div>
<div class="half h1">{_pill(it['label'])}<h2><em>Vrai</em> ou <em>faux?</em></h2><p>{it['statement']}</p>{ARROW}</div>
<div class="half h2">{_pill(it['label'])}<h2>C’est <em class="{cls}">{word}.</em></h2>{lines}</div>"""
    n = it.get("name", "vrai-faux")
    return [(n, W, H, _page(W, H, body, css), 2)]


# ---------------------------------------------------------------- mythes
def mythes(it):
    W, H = FORMATS["4x5"]
    myths = it["myths"]
    css = PILL_CSS + f"""
.frame{{background:{C['charcoal']}}}
.top{{position:absolute;left:80px;top:96px}}
.top h3{{margin:22px 0 0;font-size:104px;line-height:1}}
.big{{position:absolute;left:60px;top:430px;display:flex;align-items:flex-start;gap:6px}}
.num{{font-weight:800;font-size:520px;line-height:.78;color:{C['blue_sky']};letter-spacing:-0.05em}}
.word{{font-weight:600;font-size:150px;line-height:1;margin-top:10px;letter-spacing:-0.02em}}
.cover-sub{{position:absolute;left:80px;right:80px;bottom:110px;font-size:40px;font-weight:600;line-height:1.3;color:{C['blue_mist']}}}
.m{{position:absolute;left:80px;right:80px;top:120px}}
.m .label{{font-weight:700;font-size:64px;color:{C['blue_sky']}}}
.m h2{{margin:40px 0 70px;font-size:64px;line-height:1.2;font-weight:700;letter-spacing:-0.01em}}
.m .verdict{{font-size:84px;line-height:1;margin-bottom:44px}}
.m p{{margin:0 0 30px;font-size:40px;line-height:1.38;font-weight:500}}
.coral{{color:{C['coral']}}} .green{{color:{C['green']}}}"""
    n = it.get("name", "mythes")
    out = []
    cover = f"""<div class="top">{_pill('Assurance')}<h3><em>{it['product']}</em></h3></div>
<div class="big"><div class="num">{len(myths)}</div><div class="word">Mythes</div></div>
{f'<div class="cover-sub">{it["cover_subline"]}</div>' if it.get('cover_subline') else ''}{ARROW}"""
    out.append((f"{n}-0", W, H, _page(W, H, cover, css)))
    for i, m in enumerate(myths, 1):
        v = m.get("verdict", "faux").lower()
        cls = "coral" if v == "faux" else "green"
        ps = "".join(f"<p>{p}</p>" for p in m["explanation"])
        body = f"""<div class="m"><div class="label">Mythe {i}</div><h2>{m['statement']}</h2>
<div class="verdict"><em class="{cls}">{v.capitalize()}.</em></div>{ps}</div>"""
        out.append((f"{n}-{i}", W, H, _page(W, H, body, css)))
    return out


# ---------------------------------------------------------------- cta / text card
def _c_band_svg(W, H, s, cbx, cby, fill, seg_fill=None):
    ctr = _c_transform(s, cbx, cby)
    seg = f'<path transform="{ctr}" d="{SEG_PATH}" fill="{seg_fill}"/>' if seg_fill else ""
    return (f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" style="position:absolute;inset:0">'
            f'<path transform="{ctr}" d="{C_PATH}" fill="{fill}"/>{seg}</svg>')


def cta(it):
    fmt = it.get("format", "4x5")
    W, H = FORMATS[fmt]
    tall = fmt == "9x16"
    s = 24 if not tall else 30
    svg = _c_band_svg(W, H, s, W * 0.66, H * (0.46 if not tall else 0.5), C["blue_compar"], C["blue_mid"])
    top = 150 if not tall else 360
    body = f"""{svg}
<div class="t" style="top:{top}px">{f'<div class="kicker">{it["kicker"]}</div>' if it.get('kicker') else ''}
<h1>{it['headline']}</h1>{f'<p class="sub">{it["subline"]}</p>' if it.get('subline') else ''}</div>
<div class="foot" style="bottom:{110 if not tall else 700}px">{_pill(it.get('url_pill', 'comparassurance.ca'))}
<div class="logo">{LOGO_WHITE}</div></div>"""
    css = PILL_CSS + f"""
.frame{{background:{C['blue_royal']}}}
.t{{position:absolute;left:80px;right:110px}}
.kicker{{font-size:32px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:{C['blue_mist']};margin-bottom:28px}}
h1{{margin:0;font-weight:800;font-size:{86 if not tall else 92}px;line-height:1.08;letter-spacing:-0.02em}}
h1 em{{font-weight:650;font-size:1.06em}}
.sub{{margin:36px 0 0;font-size:40px;line-height:1.3;font-weight:600;color:{C['blue_mist']}}}
.foot{{position:absolute;left:80px;right:80px;display:flex;align-items:center;justify-content:space-between}}
.foot .pill{{font-size:30px;text-transform:none;letter-spacing:0;padding:14px 30px 13px}}
.logo svg{{width:250px;height:auto;display:block}}"""
    return [(it.get("name", "cta"), W, H, _page(W, H, body, css))]


def text_card(it):
    it = dict(it)
    it.setdefault("url_pill", "comparassurance.ca")
    return cta(it)


TEMPLATES = {"lifestyle": lifestyle, "vrai_faux": vrai_faux, "mythes": mythes, "cta": cta, "text_card": text_card}


def render_spec(spec):
    out_dir = Path(spec["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = []
    for it in spec["items"]:
        pages += TEMPLATES[it["template"]](it)
    written = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for page in pages:
            name, W, H, html = page[:4]
            split = page[4] if len(page) > 4 else 1   # >1: one wide canvas cut into seamless carousel slides
            tmp = out_dir / f".{name}.html"
            tmp.write_text(html)
            pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
            pg.goto("file://" + str(tmp.resolve()))
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(250)
            png = out_dir / f".{name}.png"
            pg.locator(".frame").screenshot(path=str(png))
            pg.close()
            img = Image.open(png).convert("RGB")
            sw = W // split
            for k in range(split):
                jpg = out_dir / (f"{name}-{k + 1}.jpg" if split > 1 else f"{name}.jpg")
                img.crop((k * sw, 0, (k + 1) * sw, H)).save(jpg, "JPEG", quality=92, optimize=True, subsampling=0)
                written.append(str(jpg))
            png.unlink()
            tmp.unlink()
        b.close()
    return written


if __name__ == "__main__":
    spec = json.loads(Path(sys.argv[1]).read_text())
    for f in render_spec(spec):
        print(f)
