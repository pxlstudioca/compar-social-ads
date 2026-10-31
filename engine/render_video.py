"""Assemble a Compar Assurance vertical video (Reels, TikTok, YouTube Shorts) from a JSON spec.

usage:
  python3 engine/render_video.py spec.json

spec.json:
{
  "out": "posts/2026-11-04-slug/reel.mp4",
  "segments": [                                 # b-roll in order; videos are cropped to 9:16, photos get a slow push-in
    {"src": "clip1.mp4", "dur": 4.0},
    {"src": "photo.jpg", "dur": 3.5, "move": "in"}   # move: in | out
  ],
  "voice": "voice.mp3",                         # optional voiceover (Eleven v4); sets the timing of the captions
  "lines": [                                    # what is said, in order; first line is the hook
    "T'as pas encore booké ton changement de pneus?",
    "Au Québec, c'est obligatoire dès le 1er décembre.",
    "Pis tant qu'à y être... ton assurance auto, elle?"
  ],
  "end_card": "endcard.jpg",                    # 1080x1920 still from render_image.py (template cta, format 9x16)
  "end_dur": 2.5,
  "music": null, "music_volume": 0.10
}

Rules baked in:
- 1080x1920, 30 fps, H.264 + AAC, loudness -14 LUFS, faststart.
- Hook (line 1) is big, top third, inside the Reels safe zone; other lines are captions just above the bottom UI.
- Captions are burned in (most people watch muted): white Manrope ExtraBold on blue-royal boxes with rounded corners.
- Without a voiceover, lines are timed by length and the track is silent; music optional.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TTF = ROOT / "fonts" / "ttf"
W, H, FPS = 1080, 1920, 30


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"ffmpeg failed: {' '.join(cmd)}\n{r.stderr[-3000:]}")
    return r


def duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)])
    return float(r.stdout.strip())


def is_image(p):
    return Path(p).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}


def segment(src, dur, move, out):
    frames = int(round(dur * FPS))
    if is_image(src):
        z = "min(1.0+0.10*on/{n},1.10)".format(n=frames) if move != "out" else "max(1.10-0.10*on/{n},1.0)".format(n=frames)
        vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
              f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},"
              f"format=yuv420p")
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(src), "-t", f"{dur}", "-vf", vf, "-an",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(out)]
    else:
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p")
        cmd = ["ffmpeg", "-y", "-i", str(src), "-t", f"{dur}", "-vf", vf, "-an",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(out)]
    run(cmd)


FUNCTION_WORDS = set("""le la les l' un une des du de d' à au aux en et ou pis que qu' qui ta ton tes ma mon mes sa son ses
notre votre leur leurs pour par sur dans avec sans ne n' pas plus très ce cet cette ces se s' te t' me m' nous vous il ils elle
on y c' j' si mais car dès entre vers chez contre depuis avant après jusqu' comme est sont""".split())


def split_caption(line, max_chars=32):
    """Split a spoken line into the fewest screens of <= max_chars, cutting at sentence ends first, then commas,
    never right after a small word (le, du, à, ton, pis...) and never leaving a one-word screen."""
    words = line.split()
    n = len(words)
    if len(line) <= max_chars:
        return [line]

    def brk(w):  # cost of cutting right after word w
        if w[-1] in ".?!…":
            return 0
        if w[-1] in ",:;":
            return 1
        return 8 if w.lower().strip("«»\"") in FUNCTION_WORDS else 3

    INF = float("inf")
    best = [INF] * (n + 1)
    cut = [0] * (n + 1)
    best[0] = 0
    for i in range(1, n + 1):
        for j in range(i - 1, -1, -1):
            chunk = " ".join(words[j:i])
            if len(chunk) > max_chars and i - j > 1:
                break
            cost = best[j] + 10 + (brk(words[i - 1]) if i < n else 0)
            if i - j == 1 or len(chunk) < 8:
                cost += 6
            if cost < best[i]:
                best[i], cut[i] = cost, j
    chunks, i = [], n
    while i > 0:
        chunks.append(" ".join(words[cut[i]:i]))
        i = cut[i]
    return chunks[::-1]


CAPTION_STYLES = {
    # font size, max text width, vertical anchor, padding x/y, corner radius
    "Hook": dict(size=84, maxw=940, top=380, padx=30, pady=16, radius=22),
    "Cap": dict(size=62, maxw=940, bottom=H - 700, padx=24, pady=12, radius=18),
}
CAPTION_BG = (0, 60, 166, 255)   # blue-royal #003ca6
CAPTION_FG = (255, 255, 255, 255)


def build_events(lines, total_speech, offset, max_end=None):
    """Time each line by its length (the hook gets at least 1.6 s); returns [(start, stop, style, text)]."""
    weights = [max(len(x), 12) for x in lines]
    tot = sum(weights)
    t = offset
    events = []
    for i, (line, w) in enumerate(zip(lines, weights)):
        d = total_speech * w / tot
        if i == 0:
            d = max(d, 1.6)
        style = "Hook" if i == 0 else "Cap"
        # Captions: split long lines in two chunks so no screen holds more than ~7 words.
        chunks = [line] if i == 0 else split_caption(line)
        lens = [max(len(c), 8) for c in chunks]
        start = t
        for c, L in zip(chunks, lens):
            stop = start + d * L / sum(lens)
            if max_end is not None:
                stop = min(stop, max_end)
            if stop > start:
                events.append((start, stop, style, c))
            start = stop
        t += d
    return events


def _wrap(text, font, maxw):
    """Fewest lines that fit maxw; among those, the split with the narrowest widest line (even lines)."""
    from itertools import combinations
    from PIL import Image, ImageDraw
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    width = lambda s: d.textlength(s, font=font)
    words = text.split()
    if width(text) <= maxw or len(words) < 2:
        return [text]
    for n in range(2, len(words) + 1):
        best, best_w = None, None
        for cuts in combinations(range(1, len(words)), n - 1):
            idx = (0,) + cuts + (len(words),)
            lines = [" ".join(words[idx[k]:idx[k + 1]]) for k in range(n)]
            mw = max(width(l) for l in lines)
            if mw <= maxw and (best_w is None or mw < best_w):
                best, best_w = lines, mw
        if best:
            return best
    return [text]


def caption_png(style, text, out):
    """Transparent 1080x1920 PNG: white Manrope ExtraBold on blue-royal rounded boxes, one box per line."""
    from PIL import Image, ImageDraw, ImageFont
    st = CAPTION_STYLES[style]
    font = ImageFont.truetype(str(TTF / "CManropeXB.ttf"), st["size"])
    lines = _wrap(text, font, st["maxw"])
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    asc, desc = font.getmetrics()
    line_h = asc + desc
    box_h = line_h + 2 * st["pady"]
    gap = 0  # boxes touch so a two-line caption reads as one block
    total_h = len(lines) * box_h + (len(lines) - 1) * gap
    y = st["top"] if "top" in st else st["bottom"] - total_h
    for ln in lines:
        tw = d.textlength(ln, font=font)
        x0 = (W - tw) / 2 - st["padx"]
        d.rounded_rectangle([x0, y, x0 + tw + 2 * st["padx"], y + box_h], radius=st["radius"], fill=CAPTION_BG)
        d.text(((W - tw) / 2, y + st["pady"]), ln, font=font, fill=CAPTION_FG)
        y += box_h + gap
    img.save(out)


def burn_captions(src, events, td, out):
    """Overlay one PNG per caption event, each enabled only during its time window."""
    inputs, chain, last = [], [], "[0:v]"
    for k, (a, b, style, text) in enumerate(events):
        png = Path(td) / f"cap{k}.png"
        caption_png(style, text, png)
        inputs += ["-i", str(png)]
        lab = f"[v{k}]"
        chain.append(f"{last}[{k + 1}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'{lab}")
        last = lab
    if not events:
        run(["ffmpeg", "-y", "-i", str(src), "-c", "copy", str(out)])
        return
    chain[-1] = chain[-1][: -len(last)] + ",format=yuv420p[vout]"
    run(["ffmpeg", "-y", "-i", str(src)] + inputs + ["-filter_complex", ";".join(chain), "-map", "[vout]",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(out)])


def render(spec):
    out = Path(spec["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        parts = []
        for i, s in enumerate(spec["segments"]):
            p = td / f"seg{i}.mp4"
            segment(s["src"], float(s["dur"]), s.get("move", "in"), p)
            parts.append(p)
        body_dur = sum(float(s["dur"]) for s in spec["segments"])

        voice = spec.get("voice")
        speech = duration(voice) if voice else body_dur * 0.92
        if voice and speech > body_dur:
            # stretch the last segment so the voice never gets cut
            extra = speech - body_dur + 0.3
            last = spec["segments"][-1]
            segment(last["src"], float(last["dur"]) + extra, last.get("move", "in"), parts[-1])
            body_dur += extra

        # concat body
        lst = td / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in parts))
        body = td / "body.mp4"
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(body)])

        # captions on the body (rounded blue boxes, rendered as PNG overlays)
        events = build_events(spec["lines"], speech, 0.15,
                              max_end=(body_dur - 0.35) if spec.get("end_card") else None)
        body_c = td / "body_c.mp4"
        burn_captions(body, events, td, body_c)

        # end card
        end_dur = float(spec.get("end_dur", 2.5))
        video = body_c
        if spec.get("end_card"):
            endv = td / "end.mp4"
            segment(spec["end_card"], end_dur, "out", endv)
            video = td / "joined.mp4"
            off = body_dur - 0.35
            run(["ffmpeg", "-y", "-i", str(body_c), "-i", str(endv), "-filter_complex",
                 f"[0][1]xfade=transition=fade:duration=0.35:offset={off:.2f},format=yuv420p[v]",
                 "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(video)])
        total = duration(video)

        # audio: voice (+ optional music), loudness -14 LUFS
        inputs, filters, mix = [], [], []
        if voice:
            inputs += ["-i", str(voice)]
            filters.append(f"[{len(inputs)//2}:a]adelay=150|150,apad,atrim=0:{total:.2f}[vo]")
            mix.append("[vo]")
        if spec.get("music"):
            inputs += ["-stream_loop", "-1", "-i", str(spec["music"])]
            vol = spec.get("music_volume", 0.10)
            filters.append(f"[{(len(inputs))//2 if not voice else 2}:a]volume={vol},atrim=0:{total:.2f},"
                           f"afade=t=out:st={total-1.2:.2f}:d=1.2[mu]")
            mix.append("[mu]")
        cmd = ["ffmpeg", "-y", "-i", str(video)] + inputs
        if mix:
            fc = ";".join(filters) + f";{''.join(mix)}amix=inputs={len(mix)}:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
            cmd += ["-filter_complex", fc, "-map", "0:v", "-map", "[a]"]
        else:
            cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-map", "0:v", "-map", f"{1 + len(inputs)//2}:a"]
        cmd += ["-t", f"{total:.2f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
                "-movflags", "+faststart", str(out)]
        run(cmd)
    return out


if __name__ == "__main__":
    print(render(json.loads(Path(sys.argv[1]).read_text())))
