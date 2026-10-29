# Compar Assurance social playbook

The rules the daily run follows. Edit this file to change how posts are made; the weekly review appends what it learns to `learnings.md`.

## Goal

1. **Leads first:** clicks to the quote forms (tracked by UTM) and comments asking for the link.
2. **Then reach** among Québec households: saves, shares, follows.

Every post has exactly one call to action that leads to a form.

## Hard rules (never break)

- Compar Assurance is a **comparateur**: never call it an insurer, a broker or a "courtier". It never sells policies, gives quotes, or says "votre assureur".
- **No promised outcome.** No "économisez X $", "le meilleur prix", "garanti". Write "peut", "pourrait", "comparez". A dollar figure needs a cited source in the log.
- **Every fact has a source** (Québec.ca, SAAQ, AMF, BAC/IBC, Environnement Canada). Put the URL in `log/posts.csv`. No source, no fact.
- **No disaster imagery.** No crashes, fires, floods, injuries or worried faces. Show the life that's protected.
- **Season reality.** Before choosing imagery, check today's conditions for Québec City and Montréal (Environment Canada). No snow on the ground in the image unless there is snow on the ground now. Foliage, light and clothing match the week.
- **No real brands:** no car badges, readable plates, store names or logos in generated images. No real people's likeness.
- **AI people are not customers.** Never present a generated person as a client, a testimonial or an employee.
- **One form of address per piece.** `tu` for Reels, humour, Vrai ou faux and Mythes; `vous` for informative image posts and Google posts.
- **Québec French**, not France French: soumission (not devis), char only in spoken Reels, chum/blonde ok in humour, no sacres.
- Every post waits for approval in GoHighLevel (status `in_review`). Nothing publishes on its own.

## Formats by placement

| Placement | Format | Size | Notes |
| --- | --- | --- | --- |
| Instagram feed | Carousel (2 to 7 slides) or single image | 1080×1350 JPEG | Carousels for education (Vrai ou faux, Mythes, checklists); the last slide is always the CTA slide |
| Instagram Reels | Video 12 to 25 s | 1080×1920 MP4 | Hook spoken and on screen in the first 2 s, burned captions, end card. Also feeds the grid |
| Facebook page | Same visual as Instagram | 4:5 or 9:16 | Caption has the clickable UTM link instead of "lien en bio" |
| TikTok | Same Reel | 1080×1920 | Caption shorter, 3 to 5 hashtags, privacy PUBLIC_TO_EVERYONE |
| YouTube Shorts | Same Reel | 1080×1920 | Title ≤ 70 characters, link in description |
| Google Business Profile | Lifestyle 4:3 | 1200×900 | `vous`, "En savoir plus" button to the product page, once a week |
| Stories | Not automated | | Link stickers can't be set through the API |

## Weekly mix (inside the credit budget)

About 5 feed posts and 2 to 3 Reels a week, varied by the calendar. A typical week:

- 1 *Vrai ou faux* carousel (no generation cost)
- 1 *Mythes* or checklist carousel (no or 1 image)
- 2 lifestyle image posts tied to the season or a calendar moment
- 2 to 3 Reels (one photo set + Seedance clips + voice), cross-posted to Instagram, Facebook, TikTok and Shorts
- 1 Google Business post (reuse a lifestyle photo in 4:3)

Never two posts of the same template in a row. Never the same product three days in a row.

## Credit budget (Higgsfield Pro plan, via the Higgsfield connector)

- Photos: Nano Banana Pro, 2K, 2 credits each: 4 options per feed post (8), 2 options on Reel days (4).
- Reels: one Seedance 2.5 image-to-video clip from our approved photo (9:16, 5 s, no native audio, 35 credits) as the opening shot, the rest as photo push-ins. Eleven v4 (`text2speech_v2` elevenlabs) for the voice, about 1.3 credits per Reel.
- **Hard caps:** at most 24 credits per daily run, **40 on a day that includes a Reel** (set by Marc-Antoine 2026-10-29); stop generating if the balance is below 100 and post a carousel instead; log credits spent per post. At 2 to 3 Reels a week this is roughly 100 to 160 credits a week.

## Lead-generation mechanics

- Instagram: "Lien en bio 🔗" CTA. Once the comment-keyword workflow exists in GoHighLevel, use "Commente PNEUS (or the keyword) et on t'envoie le lien".
- Facebook, YouTube, Google: full link with UTM: `?utm_source={platform}&utm_medium=social&utm_campaign={yyyy-mm-slug}`.
- Destinations:
  - Auto: https://comparassurance.ca/assurance-vehicule-motorise/assurance-automobile-personnelle/
  - Auto form direct: https://app.comparassurance.ca/forms/formulaire-assurance-auto-2/
  - All other products: https://comparassurance.ca/selection-services/
- CTA slide/end card wording: "Compare tes options en quelques minutes." / "Gratuit, sans engagement." / "Un professionnel te contacte." Never "2 minutes" unless timed.

## Hooks (Québécois, first 2 seconds)

Pick a pattern, adapt to the topic, keep it under 9 words:

- "T'as pas encore [action saisonnière]?"
- "Personne te dit ça quand t'achètes ton premier char."
- "Si ton [objet] [événement] demain, t'es-tu couvert?"
- "Vrai ou faux: [croyance répandue]."
- "3 affaires à vérifier avant [moment]."
- "Ça, c'est l'erreur que tout le monde fait en [mois]."
- "Ton assurance auto augmente? Voici pourquoi."
- "Le [date], c'est obligatoire. Pis toi?"
- "Arrête de renouveler les yeux fermés."

## Visual rules

- Photos: real Québec life, natural light, one orange element (clothing or object), no text in the generated image.
- Lifestyle composition: subject in the upper 60% of the frame (the C band covers the bottom).
- The C is always the exact logo path from `engine/brand.py`. Never draw circles or arcs to imitate it.
- Fonts: Manrope; one or two words in the serif italic (Tiempos, Newsreader fallback).
- Colours: blue-royal #003ca6 grounds and bands; blue-sky accents on charcoal; coral only for "Faux.", green only for "vrai.".

## Captions

1. Hook line with one emoji.
2. 2 to 4 short lines; bullets "•" for facts.
3. CTA line.
4. Hashtags: `#ComparAssurance` + 3 to 5 topical French tags.
Straight apostrophes in captions. Prices the French way (200 $, 100 %).

## Approval QA (before creating the GoHighLevel post)

- [ ] Fact sources logged; dates checked for this year
- [ ] No promise of savings, no broker/insurer wording
- [ ] Season/weather matches today
- [ ] One form of address; Québec French; proofread
- [ ] Image checked at full size: no badges, plates, extra fingers, garbled text
- [ ] Right format and size per placement; Instagram media is JPEG
- [ ] UTM link (Facebook, YouTube, Google) or "lien en bio" (Instagram)
- [ ] Alt text in French
