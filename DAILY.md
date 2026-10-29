# Daily run: plan, produce and queue tomorrow's posts

The scheduled task follows these steps every morning (~4:45 a.m. America/Toronto). Posts are queued for **tomorrow**, so Marc-Antoine has a full day to approve them. Nothing publishes without approval.

Read first: `strategy/playbook.md` (rules), `strategy/calendar.yaml`, `strategy/slots.yaml`, `strategy/learnings.md`, the last 30 rows of `log/posts.csv`.

## IDs

- GoHighLevel sub-account (Marketing): `nyVU0kBrGuBVyIufe6ir`
- Approver and userId (Compar Assurance user): `VfKKC78PqV5Rcfbt7mwc`
- Accounts (Social Planner `get-account` to refresh if one fails):
  - Instagram @comparassurance: `6658a768c6923b276486bcbf_nyVU0kBrGuBVyIufe6ir_17841462844170781`
  - Facebook page Compar Assurance: `6658a75bf948f869bdff7e95_nyVU0kBrGuBVyIufe6ir_187504001102646_page`
  - TikTok compar.assurance: `6ae2bd383fda1b691f9d06b5_nyVU0kBrGuBVyIufe6ir_000BYiOls1kXsO6E30qt0rRXAuRC7tQQzc_business`
  - YouTube @comparassurance: `6ae2bd4d34aa87a1af86a751_nyVU0kBrGuBVyIufe6ir_UCW1Q5sT0qWaZBHgrb2Y_YBg_profile`
  - Google Business Profile: `6ae2bd66c6275d391b629837_nyVU0kBrGuBVyIufe6ir_8625268722161074652`
- Public media base: `https://raw.githubusercontent.com/pxlstudioca/compar-social-ads/main/`

## Steps

1. **Repo.** Work in a clone of `pxlstudioca/compar-social-ads` with push access (attach it if the session doesn't have it). `git pull` first.
2. **Context.** Today's date in America/Toronto. Current conditions and 3-day forecast for Québec City and Montréal from Environment Canada (weather.gc.ca): snow on the ground yes/no, temperature, precipitation. Which `calendar.yaml` moments are active tomorrow. Any major Québec news that would make a post tone-deaf (storm, tragedy): if so, queue a neutral evergreen post or nothing, and say why in the log.
3. **Plan tomorrow.** From the playbook's weekly mix and the last 14 days of the log, choose 1 feed post, plus a Reel if fewer than 2 Reels are queued this week, plus a Google post if none this week. Pick topic, product, template, hook and CTA. Respect: no template twice in a row, no product three days running. **No duplicates:** if `log/posts.csv` already has a feed post (or Reel) with `publish_at` tomorrow (America/Toronto), don't queue another one for that day; if nothing is left to queue, skip to the report and say "already queued".
4. **Facts.** For every claim, open the official source and confirm it for this year. No source, no claim.
5. **Times.** Pick slots with `strategy/slots.yaml` (75% best weight, 25% explore, ±12 min jitter, 4 h minimum between posts on one platform).
6. **Credits.** Check the Higgsfield balance. Cap: 24 credits per run; below 100 credits, make a no-generation post (Vrai ou faux, Mythes, text card) instead.
7. **Produce.**
   - Photos: Higgsfield connector `generate_image`, model `nano_banana_pro`, 4:5 (or 9:16 for Reels), 2K, 4 options. Prompt with the playbook's visual rules and the real weather (no snow unless snow now). Download the results (Higgsfield CDNs: `d8j0ntlcm91z4.cloudfront.net`, `d1xarpci4ikg0w.cloudfront.net`, `cdn.higgsfield.ai`), look at each at full size, keep the best one, reject anything with badges, plates, text, extra fingers.
   - Images: write a spec and run `python3 engine/render_image.py spec.json` (templates: lifestyle, vrai_faux, mythes, cta, text_card). Look at every output image before using it.
   - Reels: 2 clips with `generate_video` model `seedance_2_5` (pass the kept photo's job_id as `start_image`, 9:16, 5 s, `generate_audio: false`), voiceover with `generate_audio` model `text2speech_v2` variant `elevenlabs` (voice in `strategy/voice.yaml`; if `voice_id` is empty, make one 6 s sample per candidate, save them in `posts/voice-samples/`, use the best and say so in the report), then `python3 engine/render_video.py spec.json` with the hook as line 1 and a 9:16 `cta` end card. Watch 4 frames (0.8 s, middle, last line, end card) before using it.
   - Without the Higgsfield generation tools, skip photos and video and make a no-generation post.
8. **Publish the files.** Save outputs under `posts/YYYY-MM-DD-slug/`, commit (`Add <slug> (<date>)`) and push **to `main`** (the public URLs point at `main`; do not use a `claude/` branch). Confirm each public URL answers 200 before using it.
9. **Queue in GoHighLevel.** Social Planner `create-post`, one request per platform, `status: in_review`, `scheduleDate` = chosen slot (UTC ISO), `postApprovalDetails: {approver, approvalStatus: pending, requesterNote: "<topic> — créé par Claude, à approuver"}`, `userId`, alt text on every image.
   - Instagram: `instagramPostDetails.type` post or reel; caption ends with "lien en bio 🔗".
   - Facebook: same visual; caption has the UTM link.
   - TikTok: Reels only; `tiktokPostDetails.privacyLevel: PUBLIC_TO_EVERYONE`; shorter caption.
   - YouTube: Reels only; `youtubePostDetails: {type: short, title (≤70 chars), privacyLevel: public}`; link in description.
   - Google: weekly; `gmbPostDetails: {gmbEventType: STANDARD, actionType: learn_more, url: <product page with UTM>}`; 4:3 image.
10. **Log.** Append one row per platform to `log/posts.csv` (IDs, slot choice best/explore, credits, fact source). Commit and push to `main`.
11. **Report.** End with a short summary: what was queued, when, the media links, credits used and anything that needs a decision.

## If something fails

- A connector call fails twice: stop that branch, log it, finish what you can, and say so in the report.
- Never publish directly, never change status to `scheduled` or `published`, never delete posts.
