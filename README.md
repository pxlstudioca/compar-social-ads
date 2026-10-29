# compar-social-ads

Compar Assurance's automated social posting: Claude plans, produces and queues posts every day; GoHighLevel Social Planner publishes them after approval.

Files here are **public** (Meta and TikTok fetch media from these URLs at publish time). No secrets in this repo.

| Path | What it is |
| --- | --- |
| `DAILY.md` | The daily run, step by step (queues tomorrow's posts as "in review") |
| `WEEKLY.md` | The Monday review that updates posting times and learnings |
| `strategy/playbook.md` | Rules: compliance, formats per placement, weekly mix, hooks, captions, QA |
| `strategy/calendar.yaml` | Québec moments by date window, with sources |
| `strategy/slots.yaml` | Posting time candidates and their learned weights |
| `strategy/voice.yaml` | Voiceover settings for Reels |
| `strategy/learnings.md` | What the weekly review learned |
| `engine/render_image.py` | Brand templates: lifestyle (exact logo C), Vrai ou faux (continuous card), Mythes, CTA, text card; 4:5, 9:16, 4:3 |
| `engine/render_video.py` | Reels assembly: 9:16 b-roll, burned captions, hook, end card, voice, -14 LUFS |
| `engine/fetch_media.py` + `.github/workflows/fetch-media.yml` | Higgsfield downloads via GitHub: the run pushes `inbox/<id>.json`, the Action saves the files on the `media` branch (cache, last 7 days) |
| `engine/brand.py` | Colours, the C path from the logo, sizes, safe zones |
| `posts/YYYY-MM-DD-slug/` | Published media, one folder per post |
| `log/posts.csv` | Every queued post with IDs, slot, credits and results |

Requirements in the run environment: Python 3, Pillow, Playwright (Chromium), ffmpeg; push access to this repo (Higgsfield files are downloaded by the `fetch-media` GitHub Action through `engine/fetch_media.py`, because the runs can't reach Higgsfield's CDNs); connectors GoHighLevel and Higgsfield (custom, https://mcp.higgsfield.ai/mcp).
