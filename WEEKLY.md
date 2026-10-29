# Weekly review (Mondays)

1. `git pull`. Read `log/posts.csv` for the last 7 days and `strategy/learnings.md`.
2. For each published post, read its numbers with GoHighLevel Social Planner `get-post` (likes, comments, shares) and update the log row. Mark posts that were rejected or never approved.
3. Score each post: likes + 2×comments + 3×shares. Compare by template, hook pattern, product, platform and time slot. With fewer than 3 posts in a group, call it a hint, not a finding.
4. Update `strategy/slots.yaml` weights: move each slot's weight 20% toward its average score relative to the overall average (clamp 0.5 to 2.0). Keep exploration at 0.25 for the first 8 weeks.
5. Append 3 to 5 lines to `strategy/learnings.md`: what worked, what didn't, what to try next week. Concrete (hook text, slot, template), no generalities.
6. Note the Higgsfield credits spent this week and the balance.
7. Commit (`Weekly review <date>`), push, and end with a short report: top post, worst post, slot changes, next week's focus, credits.
