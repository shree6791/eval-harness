# Write-up

## Project name

Countersign: SQL drafted by Nemotron, signed off by analysts.

## Overview

**Ask a business question in plain English. Get a checked answer in minutes. Each analyst handles 43% more questions.**

### The problem

- Business teams rely on a few analysts to turn questions into database queries (SQL). Questions wait in a queue.
- Analysts spend hours writing routine queries instead of analyzing results.
- AI on its own is not safe to trust: the best single model we tested is wrong about 1 time in 3, and nothing tells you which answers are wrong.

### How Countersign works

1. **Ask.** A business user types a question, such as "How many customers churned last quarter?"
2. **Draft.** NVIDIA Nemotron 3 Ultra writes three versions of the query in about 2 seconds. It sees real example values from the database, so it uses the formats the data actually has ('M' or 'Male', a number stored as text).
3. **Check.** All three drafts run on the database. If they disagree or fail, Kimi K3, a larger model, reviews the three drafts and their results and writes a corrected query.
4. **Sign off.** An analyst approves or edits the draft. A person checks every answer.

### What it delivers

| Per question | Analyst today | Countersign + analyst review |
| --- | --- | --- |
| Time to an answer | Days | **Seconds to draft, minutes to approve** |
| Analyst time | 30 min | **21 min: 43% more questions per analyst** |
| Accuracy | 100% | 100% (a person checks every answer) |
| Cost | $31.04 | **$21.75 (30% lower)** |

With Kimi K3 checking every question, the most accurate setting, analyst time drops to 17 min (74% more questions per analyst) and cost to $17.98 (42% lower).

No one is replaced. Analysts stay responsible for every answer and clear their backlog faster.

### Results

**Baseline:** Kimi K3 on its own, a frontier-class open model answering each question by itself.

| Setup (350 test questions) | Right answers (95% CI) | Cost per 1,000 questions | Typical time |
| --- | --- | --- | --- |
| Nemotron 3 Ultra alone | 43.4% (38.3–48.6) | $2.54 | 2 s |
| Kimi K3 alone (baseline) | 68.0% (63.1–72.9) | $32.41 | 15 s |
| Countersign, Kimi steps in only when drafts disagree (τ = 3) | 63.4% (58.6–68.3) | $44.61 | 7 s |
| **Countersign, Kimi checks every question (τ = 4)** | **75.7% (71.1–80.0)** | $98.58 | 44 s |

What we found:

- **Countersign beats the baseline by 7.7 points** (95% CI +2.6 to +12.9; p = 0.006), so the gain is very unlikely to be luck. It costs three times as much per question as the baseline.
- **Showing the models real data values was the biggest single gain.** Nemotron rose from 28.1% to 43.8% (+15.7) and Kimi K3 from 50.3% to 67.5% (+17.2), on the same 320 questions.
- **Agreement is not proof.** When all three drafts agree (53% of questions), they are right only 53% of the time. A person still signs off.
- **Speed and reliability fixes.** Switching to Nemotron 3 Ultra cut draft time from about 6 minutes to about 2 seconds. Format fixes cut unusable replies from 72 of 100 to 0.

![Before vs after real column values, and a data analyst](results/chart_bars.png)

### How we tested it

- **Dataset:** BIRD Mini-Dev, 500 real business questions over 11 databases, each with a correct query written by people.
- **Grading:** we run our query and the correct one; an answer counts only if both return the same rows. No AI grades another AI.
- **Fair test:** settings were chosen on 150 questions; results come from the other 350, never used for tuning.
- **Grader check:** the grader accepts the correct query 20 of 20 times and rejects deliberately broken queries 20 of 20 times.

![Accuracy vs cost for every setting of τ](results/chart_compare.png)

### What's next

- **Get to 88% accurate.** The right answer is already among our drafts 88% of the time; we need to get better at choosing it.
- **Cut the cost** of Kimi K3's fixes.
- **Let business users self-serve** routine questions; analysts check only the high-stakes ones.
- **Apply it to other tasks** that can be checked automatically, such as forms, reports or code.

### Code

https://github.com/shree6791/eval-harness

## Tech stack

- **Fireworks.ai:** runs both models through one API, billed per token, with no servers to manage. Three drafts per question stay affordable, and we swapped models mid-event with one line.
- **NVIDIA Nemotron 3 Ultra:** writes every first draft in about 2 seconds for under a cent, and answers 53% of questions without needing Kimi K3 (τ = 3).
- **Kimi K3:** the larger model that fixes the drafts.
- **Python, SQLite, FastAPI:** runs the queries safely (read-only, with time limits) and serves the `/ask` page.
- **NumPy, SciPy, Matplotlib:** scoring, significance tests and charts.
- **BIRD Mini-Dev** (Hugging Face): the questions, databases and correct queries.

## Team

- Shreenidhi Sudhakar · shree6791@gmail.com
- Joseph Mikhail · mikhailj@gmail.com

## Notes and assumptions

- **τ (tau):** how many of Nemotron's three drafts must agree before skipping Kimi K3. τ = 3 means Kimi steps in unless all three agree. τ = 4 can't be met with three drafts, so Kimi K3 checks every question.
- **Analyst cost:** $62.07 an hour, operations research analysts in the San Jose area (US Bureau of Labor Statistics, May 2025), the closest official role to a data analyst.
- **Assumed:** 30 minutes to write a query and 10 minutes to review a draft. With review, analyst time = 10 minutes on every question + 30 minutes rewriting the 36.6% the τ = 3 setup gets wrong = 21 minutes.
- **Run:** all 500 questions completed (150 to choose settings, 350 reported). No failed calls; 4 of about 1,000 Kimi K3 replies ran out of length and count as wrong.
- **Statistics:** p = 0.006 is a McNemar test; 95% confidence intervals use 10,000 bootstrap resamples of the 350 test questions, paired for the 7.7-point gain.
- **Two question counts:** the before/after rows and charts use the 320 test questions both runs answered; everything else uses all 350.
- **Scope:** the baseline is Kimi K3, an open model; closed models (GPT, Claude, Gemini) were not tested. This question set is mostly the hardest tier (460 of 500), so scores are not comparable to the public BIRD leaderboard.
- **Execution accuracy:** the share of questions where our query returns the same rows as the correct query.
