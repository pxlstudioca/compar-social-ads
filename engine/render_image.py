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
  checklist  white carousel: cover + one ticked slide per item
             fields: label, headline (HTML), cover_subline, items: [{"title": html, "explanation": [p, p]}]
  comparatif one slide, A vs B on charcoal: label, headline, a_kicker, a_title, b_kicker, b_title,
             rows: [{"label", "a", "b"}] (3 to 4 rows), note (small print), grid_top
  chiffre_cle one big sourced number on blue-royal: kicker, number (HTML; <em> = unit), context (HTML),
             source (required, printed on the slide), format (4x5|9x16|4x3), number_size
  comment    how Compar works, numbered steps: kicker, headline (HTML), steps: [{"title", "text"}], url_pill, format

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


# ---------------------------------------------------------------- checklist
CHECK = ('<svg class="chk" width="{s}" height="{s}" viewBox="0 0 64 64"><rect width="64" height="64" rx="16" fill="{bg}"/>'
         '<path d="M17 33l10 10 20-22" stroke="{fg}" stroke-width="6" fill="none" stroke-linecap="round" '
         'stroke-linejoin="round"/></svg>')


def checklist(it):
    """White carousel: cover (title + empty boxes) and one slide per item (ticked box, n/N, title, lines)."""
    W, H = FORMATS["4x5"]
    items = it["items"]
    n = it.get("name", "checklist")
    css = PILL_CSS + f"""
.frame{{background:#fff;color:{C['ink']}}}
.pill{{border-color:{C['blue_royal']} !important;color:{C['blue_royal']} !important}}
.arrow{{border-color:{C['blue_royal']}}} .arrow path{{stroke:{C['blue_royal']}}}
.top{{position:absolute;left:80px;right:80px;top:96px}}
.top h1{{margin:44px 0 0;font-size:96px;line-height:1.04;font-weight:800;letter-spacing:-0.02em;color:{C['blue_royal']}}}
.top h1 em{{font-weight:600;font-size:1.06em}}
.boxes{{position:absolute;left:80px;right:80px;bottom:200px}}
.row{{display:flex;align-items:center;gap:30px;margin-top:26px}}
.row .line{{flex:1;height:14px;border-radius:7px;background:#e8edf6}}
.row:nth-child(2) .line{{flex:.8}} .row:nth-child(3) .line{{flex:.6}}
.cover-sub{{position:absolute;left:80px;right:260px;bottom:60px;font-size:34px;font-weight:600;line-height:1.3;color:#55607a}}
.item{{position:absolute;left:80px;right:80px;top:120px}}
.ghost{{position:absolute;right:50px;bottom:-190px;font-weight:800;font-size:640px;line-height:1;color:#f3f5fa;letter-spacing:-0.05em}}
.count{{font-weight:800;font-size:40px;color:{C['blue_sky']};letter-spacing:.02em}}
.item .chk{{display:block;margin:70px 0 56px}}
.item h2{{margin:0 0 48px;font-size:88px;line-height:1.1;font-weight:800;letter-spacing:-0.015em;color:{C['blue_royal']}}}
.item p{{margin:0 0 30px;font-size:46px;line-height:1.38;font-weight:500;color:#2b3245}}
.bar{{position:absolute;left:80px;right:80px;bottom:80px;display:flex;gap:14px}}
.bar i{{flex:1;height:10px;border-radius:5px;background:#e8edf6}} .bar i.on{{background:{C['blue_royal']}}}"""
    empty = CHECK.format(s=72, bg="#e8edf6", fg="#e8edf6")
    rows = "".join(f'<div class="row">{empty}<div class="line"></div></div>' for _ in items)
    cover = f"""<div class="top">{_pill(it['label'])}<h1>{it['headline']}</h1></div>
<div class="boxes">{rows}</div>
{f'<div class="cover-sub">{it["cover_subline"]}</div>' if it.get('cover_subline') else ''}{ARROW}"""
    out = [(f"{n}-0", W, H, _page(W, H, cover, css))]
    for i, m in enumerate(items, 1):
        ps = "".join(f"<p>{x}</p>" for x in m.get("explanation", []))
        bar = "".join(f'<i class="{"on" if k <= i else ""}"></i>' for k in range(1, len(items) + 1))
        body = f"""<div class="ghost">{i}</div><div class="item"><div class="count">{i}/{len(items)}</div>
{CHECK.format(s=140, bg=C['blue_royal'], fg='#fff')}<h2>{m['title']}</h2>{ps}</div><div class="bar">{bar}</div>"""
        out.append((f"{n}-{i}", W, H, _page(W, H, body, css)))
    return out


# ---------------------------------------------------------------- comparatif
def comparatif(it):
    """One slide, two columns A vs B on charcoal: label, headline, a header row, then aligned rows."""
    W, H = FORMATS["4x5"]
    rows = it["rows"]
    css = PILL_CSS + f"""
.frame{{background:{C['charcoal']}}}
.top{{position:absolute;left:70px;right:70px;top:80px}}
.top h1{{margin:30px 0 0;font-size:68px;line-height:1.08;font-weight:800;letter-spacing:-0.015em}}
.top h1 em{{font-weight:600;color:{C['blue_sky']};font-size:1.06em}}
.grid{{position:absolute;left:70px;right:70px;top:{it.get('grid_top', 380)}px;display:grid;grid-template-columns:1fr 1fr;column-gap:18px}}
.hd{{border-radius:28px 28px 0 0;padding:30px 34px 26px;font-size:46px;font-weight:800;line-height:1.05}}
.hd small{{display:block;font-size:24px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;margin-bottom:10px;opacity:.75}}
.a{{background:{C['blue_royal']}}} .b{{background:#fff;color:{C['ink']}}}
.cell{{padding:22px 34px 24px;font-size:33px;line-height:1.3;font-weight:600;border-top:2px solid rgba(255,255,255,.14)}}
.cell.b{{border-top-color:#e3e8f2}}
.cell .k{{display:block;font-size:23px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px;opacity:.65}}
.last{{border-radius:0 0 28px 28px;padding-bottom:34px}}
.note{{position:absolute;left:70px;right:70px;bottom:56px;font-size:24px;line-height:1.35;color:#9aa3b5}}"""
    cells = (f'<div class="hd a"><small>{it.get("a_kicker", "")}</small>{it["a_title"]}</div>'
             f'<div class="hd b"><small>{it.get("b_kicker", "")}</small>{it["b_title"]}</div>')
    for k, r in enumerate(rows):
        last = " last" if k == len(rows) - 1 else ""
        cells += (f'<div class="cell a{last}"><span class="k">{r["label"]}</span>{r["a"]}</div>'
                  f'<div class="cell b{last}"><span class="k">{r["label"]}</span>{r["b"]}</div>')
    body = f"""<div class="top">{_pill(it['label'])}<h1>{it['headline']}</h1></div><div class="grid">{cells}</div>
{f'<div class="note">{it["note"]}</div>' if it.get('note') else ''}"""
    return [(it.get("name", "comparatif"), W, H, _page(W, H, body, css))]


# ---------------------------------------------------------------- chiffre clé
# Shrinks .num until it fits its box (long numbers like "200 à 300 $").
FIT_JS = """<script>document.fonts.ready.then(()=>{const n=document.querySelector('.num');
let f=parseFloat(getComputedStyle(n).fontSize);while(n.scrollWidth>n.clientWidth&&f>60){f-=4;n.style.fontSize=f+'px';}});</script>"""


def chiffre_cle(it):
    """One big sourced number on blue-royal with the C: kicker, number, unit/context, source line (required)."""
    fmt = it.get("format", "4x5")
    W, H = FORMATS[fmt]
    if not it.get("source"):
        raise ValueError("chiffre_cle needs a 'source' (shown on the slide)")
    g = {"4x5": dict(top=230, num=250, ctx=50, s=24, cy=0.70),
         "9x16": dict(top=330, num=270, ctx=54, s=30, cy=0.70),
         "4x3": dict(top=90, num=190, ctx=40, s=18, cy=0.80)}[fmt]
    num = it.get("number_size", g["num"])
    svg = _c_band_svg(W, H, g["s"], W * 0.80, H * g["cy"], C["blue_compar"], C["blue_mid"])
    css = PILL_CSS + f"""
.frame{{background:{C['blue_royal']}}}
.t{{position:absolute;left:80px;right:80px;top:{g['top']}px}}
.kicker{{font-size:32px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:{C['blue_mist']}}}
.num{{margin:40px 0 10px;font-weight:800;font-size:{num}px;line-height:.95;letter-spacing:-0.04em;white-space:nowrap}}
.num em{{font-weight:600;font-size:.62em;letter-spacing:-0.01em;color:{C['blue_mid']}}}
.ctx{{margin:36px 0 0;max-width:{W - 260}px;font-size:{g['ctx']}px;line-height:1.22;font-weight:700}}
.ctx em{{font-size:1.06em}}
.src{{position:absolute;left:80px;bottom:{70 if fmt != '4x3' else 50}px;font-size:24px;font-weight:600;color:{C['blue_mist']}}}
.logo{{position:absolute;right:80px;bottom:{62 if fmt != '4x3' else 42}px}} .logo svg{{width:200px;height:auto;display:block}}"""
    body = f"""{svg}<div class="t"><div class="kicker">{it.get('kicker', '')}</div>
<div class="num">{it['number']}</div><p class="ctx">{it['context']}</p></div>
<div class="src">Source&nbsp;: {it['source']}</div><div class="logo">{LOGO_WHITE}</div>{FIT_JS}"""
    return [(it.get("name", "chiffre-cle"), W, H, _page(W, H, body, css))]


# ---------------------------------------------------------------- comment ça marche
def comment(it):
    """How Compar works: headline + numbered steps on a vertical rail, url pill and logo. 4x5, 9x16 or 4x3."""
    fmt = it.get("format", "4x5")
    W, H = FORMATS[fmt]
    steps = it["steps"]
    wide = fmt == "4x3"
    top = {"4x5": 110, "9x16": 280, "4x3": 70}[fmt]
    svg = _c_band_svg(W, H, 18 if wide else 26, W * 0.92, H * 0.80, C["blue_compar"], C["blue_mid"])
    css = PILL_CSS + f"""
.frame{{background:{C['blue_royal']}}}
.t{{position:absolute;left:80px;right:80px;top:{top}px}}
.kicker{{font-size:30px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:{C['blue_mist']}}}
h1{{margin:20px 0 0;font-size:{60 if wide else 84}px;line-height:1.05;font-weight:800;letter-spacing:-0.02em}}
h1 em{{font-weight:600;font-size:1.06em}}
.steps{{position:relative;margin-top:{40 if wide else 100}px}}
.steps:before{{content:"";position:absolute;left:{34 if wide else 47}px;top:40px;bottom:40px;width:3px;background:{C['blue_mid']};opacity:.6}}
.st{{position:relative;display:flex;gap:40px;align-items:flex-start;margin-bottom:{22 if wide else 76}px}}
.dot{{flex:none;width:{70 if wide else 96}px;height:{70 if wide else 96}px;border-radius:50%;background:#fff;color:{C['blue_royal']};
      font-weight:800;font-size:{36 if wide else 44}px;display:flex;align-items:center;justify-content:center}}
.st h2{{margin:{6 if wide else 12}px 0 10px;font-size:{38 if wide else 56}px;line-height:1.12;font-weight:800}}
.st p{{margin:0;font-size:{26 if wide else 38}px;line-height:1.3;font-weight:600;color:{C['blue_mist']}}}
.foot{{position:absolute;left:80px;right:80px;bottom:{50 if wide else (700 if fmt == '9x16' else 90)}px;display:flex;align-items:center;justify-content:space-between}}
.foot .pill{{font-size:30px;text-transform:none;letter-spacing:0;padding:14px 30px 13px}}
.logo svg{{width:230px;height:auto;display:block}}
.t .foot{{position:static;margin-top:30px}}"""
    tall = fmt == "9x16"   # Reel safe zone: the footer follows the steps instead of sitting at the bottom
    foot = f'<div class="foot">{_pill(it.get("url_pill", "comparassurance.ca"))}<div class="logo">{LOGO_WHITE}</div></div>'
    sts = ""
    for i, st in enumerate(steps, 1):
        txt = f"<p>{st['text']}</p>" if st.get("text") else ""
        sts += f'<div class="st"><div class="dot">{i}</div><div><h2>{st["title"]}</h2>{txt}</div></div>'

    body = f"""{svg}<div class="t"><div class="kicker">{it.get('kicker', '')}</div><h1>{it['headline']}</h1>
<div class="steps">{sts}</div>{foot if tall else ''}</div>{'' if tall else foot}"""
    return [(it.get("name", "comment"), W, H, _page(W, H, body, css))]


TEMPLATES = {"lifestyle": lifestyle, "vrai_faux": vrai_faux, "mythes": mythes, "cta": cta, "text_card": text_card,
             "checklist": checklist, "comparatif": comparatif, "chiffre_cle": chiffre_cle, "comment": comment}


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
