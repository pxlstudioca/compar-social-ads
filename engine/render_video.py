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
- Captions are burned in (most people watch muted).
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


def ass_time(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def ass_escape(s):
    return s.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", "\\N")


def split_caption(line, max_words=7):
    """Split a spoken line into screens of <= max_words, preferring breaks after punctuation."""
    words = line.split()
    if len(words) <= max_words:
        return [line]
    best, best_score = len(words) // 2, 1e9
    for k in range(2, len(words) - 1):
        score = abs(k - len(words) / 2)
        if words[k - 1][-1] in ",.?!:;…" or words[k - 1].endswith("..."):
            score -= 3
        if score < best_score:
            best, best_score = k, score
    return split_caption(" ".join(words[:best]), max_words) + split_caption(" ".join(words[best:]), max_words)


def build_ass(lines, total_speech, offset, path):
    # Time each line by its length; the hook gets a minimum of 1.6 s.
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
        cd = d / len(chunks)
        for k, c in enumerate(chunks):
            events.append(f"Dialogue: 0,{ass_time(t + k*cd)},{ass_time(t + (k+1)*cd)},{style},,0,0,0,,{ass_escape(c)}")
        t += d
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,CManropeXB,84,&H00FFFFFF,&H00FFFFFF,&H00A63C00,&H00A63C00,0,0,0,0,100,100,0,0,3,22,0,8,90,90,380,1
Style: Cap,CManropeXB,62,&H00FFFFFF,&H00FFFFFF,&H00A63C00,&H00A63C00,0,0,0,0,100,100,0,0,3,16,0,2,110,110,700,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    Path(path).write_text(head + "\n".join(events) + "\n")
    return t


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

        # captions on the body
        ass = td / "caps.ass"
        build_ass(spec["lines"], speech, 0.15, ass)
        body_c = td / "body_c.mp4"
        run(["ffmpeg", "-y", "-i", str(body), "-vf", f"ass={ass}:fontsdir={TTF}",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(body_c)])

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
