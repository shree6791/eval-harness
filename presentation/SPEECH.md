# Countersign: 2-minute pitch

Joseph covers slides 1–3 (about 1 minute) and Shree covers slides 4–5 (about 1 minute). At about 145 words per minute the full script runs roughly 2:00. The same text is in each slide's speaker notes.

## Joseph (slides 1–3, ~1:00)

**Slide 1: Countersign**

Hi, we're Joseph and Shree, and this is Countersign. A business user asks a question in plain English and gets a working SQL query back in seconds: drafted by NVIDIA Nemotron, repaired by Kimi K3, and signed off by an analyst.

**Slide 2: Data waits on analysts; AI alone is not safe**

Today those questions wait days for an analyst. And AI alone isn't safe: the best model is wrong one time in three, without saying which. So Nemotron writes three drafts using real column values, we run them on the live database, and Kimi K3 repairs them.

**Slide 3: Three drafts agreed. All three were wrong.**

Here's a real test question: how many superheroes are neither good nor bad? All three drafts agree: 28. Kimi on its own: also 28. All wrong, because the join silently drops six heroes. Shown the three drafts, Kimi switches to a left join and gets 34, the right answer. Agreement isn't proof, so an analyst always signs off. Shree?

## Shree (slides 4–5, ~1:00)

**Slide 4: Cascade wins: 75.7% vs 68.0% for Kimi K3 alone**

Thanks. We didn't just demo this, we measured it. BIRD Mini-Dev: 500 real business questions over 11 databases, each with a human-written answer. An answer counts only if our query returns the same rows, so no AI grades AI. We tuned on 150 questions and report on the other 350. The cascade reaches 75.7%, versus 68% for Kimi alone, a statistically significant gap. Just showing the models real column values added 16 to 17 points.

**Slide 5: 43% more capacity, no one replaced**

For the business: analysts still approve every answer, but reviewing a draft takes 21 minutes instead of 30. Same team, 43% more questions, 30% lower cost, and no one replaced. It runs on NVIDIA Nemotron and Fireworks serverless, and next, we get to 88% accuracy: the right answer is already among our drafts 88% of the time, so we just need to get better at choosing it. Thank you.

## Backup answers for Q&A

- **Why does the business case use τ = 3 but the chart shows 75.7%?** 75.7% is Kimi repairing every question (τ = 4), our most accurate setup. τ = 3 sends only disagreements to Kimi: 63.4% at half the cost. The analyst math uses τ = 3.
- **Is 75.7% vs 68.0% real?** McNemar test, p = 0.006: the cascade fixed 59 questions Kimi alone got wrong and broke 32.
- **Why not compare to the BIRD leaderboard?** This question file is mostly the hardest tier (460 of 500), so scores aren't comparable.
- **Speed?** Nemotron drafts in about 2 s; the full repair takes about 44 s median at τ = 4 and 7 s at τ = 3.
