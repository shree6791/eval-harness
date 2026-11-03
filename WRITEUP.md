# Write-up

## Project name

Countersign: SQL drafted by Nemotron, signed off by analysts.

## Overview

**Business questions answered in minutes, not days. Analysts answer 43% more of them.**

### The problem

Business decisions wait on data questions, and those questions wait on a small team of analysts who write SQL.

- Business users wait in an analyst queue, and low-priority questions often go unanswered.
- Analysts spend skilled hours on routine queries instead of analysis.
- AI alone is not safe to act on: the best single model is wrong on one question in three, with no signal of which.

### What we built

A user asks in plain English and gets a working SQL query with results, drafted in seconds for an analyst to approve.

1. **NVIDIA Nemotron 3 Ultra** writes three drafts in about 2 seconds.
2. **Real column values in the prompt** show how data is actually stored ('M' vs 'Male', a number stored as text).
3. **A free check** runs each draft on the live database; drafts that disagree, crash or return nothing escalate.
4. **Kimi K3** sees all three drafts and their results, and writes one corrected query.
5. **The analyst** approves or edits a working draft instead of a blank page.

### What it delivers

| Per question | Analyst today | Countersign + analyst review |
| --- | --- | --- |
| Time to an answer | Days | **Seconds to draft, minutes to approve** |
| Analyst time | 30 min | **21 min (43% more questions per analyst)** |
| Accuracy | 100% | 100% (every answer reviewed) |
| Cost | $31.04 | $21.75 (30% lower) |

With τ = 4, where Kimi K3 repairs every draft, the same math gives 17 min per question (74% more questions per analyst) at $17.98 (42% lower).

No one is replaced. Analysts stay accountable for every answer and clear the backlog faster.

### Why this is different

Text-to-SQL is crowded. Our edge is evidence and design.

- **Measured, not demoed:** 350 held-out questions scored against human-written answers by running both queries. No AI grader.
- **Built for review:** model agreement does not signal correctness, so the analyst stays in charge.
- **A lever any team can use:** real column values add 16–17 points to both models, with no fine-tuning.
- **No lock-in:** open models on Fireworks; we swapped the first-pass model mid-event with one line.
- **Room to grow:** the right answer is already among our drafts on 88% of questions; today we deliver it on 76%.

### Results

**Baseline:** Kimi K3 alone, a frontier-class open model answering each question by itself. The full Countersign cascade beats it by 7.7 points (95% CI +2.6 to +12.9; p = 0.006) on 350 held-out questions.

| What we changed | Before | After |
| --- | --- | --- |
| Real column values: Nemotron 3 Ultra alone | 28.1% | **43.8% (+15.7)** |
| Real column values: Kimi K3 alone | 50.3% | **67.5% (+17.2)** |
| Kimi K3 repairing Nemotron's drafts vs Kimi K3 alone (95% CI +2.6 to +12.9; p = 0.006) | 68.0% | **75.7% (+7.7)** |
| First-pass model: Nemotron 3.5 Lightning → 3 Ultra | ~6 min per call | **~2 s** |
| Unusable replies, 20-question trial (format and reasoning fixes) | 72 of 100 | **0** |

The two real-column-value rows and the charts use the 320 test questions both runs answered. All other figures use the full 350.

![Before vs after real column values, and a data analyst](results/chart_bars.png)

| Test set (n = 350) | Accuracy (95% CI) | $ per 1,000 questions | $ per correct answer | Median time |
| --- | --- | --- | --- | --- |
| Nemotron 3 Ultra alone | 43.4% (38.3–48.6) | $2.54 | $0.006 | 2.1 s |
| Kimi K3 alone (baseline) | 68.0% (63.1–72.9) | $32.41 | $0.048 | 15.0 s |
| Cascade τ = 3: Kimi fixes disagreements only (47%) | 63.4% (58.6–68.3) | $44.61 | $0.070 | 7.1 s |
| Cascade τ = 4: Kimi repairs every question | **75.7% (71.1–80.0)** | $98.58 | $0.130 | 43.9 s |

τ = 4 is the most accurate setup, at three times the cost of Kimi K3 alone. τ = 3 is the balanced setting used in the review workflow.

### How we proved it

- **Benchmark:** BIRD Mini-Dev, 500 business questions over 11 real databases, each with a human-written reference query.
- **Scoring:** our query and the reference both run; an answer counts only if the results match.
- **No test-set tuning:** τ chosen on 150 separate questions, reported on 350.
- **Grader check:** passes the reference against itself 20/20; fails deliberately broken SQL 20/20.

![Accuracy vs cost for every τ](results/chart_compare.png)

### Where this goes next

- **Get to 88% accurate:** the right answer is already among our drafts 88% of the time; we need to get better at choosing it.
- **Cut the cost** of the expert model's fixes.
- **Let business users self-serve** routine questions; analysts check only the high-stakes ones.
- **Apply it to other tasks** that can be checked automatically, like forms, reports or code.

### Code

https://github.com/shree6791/eval-harness

## Tech stack

- **Fireworks.ai:** both models behind one OpenAI-compatible API, billed per token, no GPUs to manage. Makes three drafts per question affordable and model swaps instant.
- **NVIDIA Nemotron 3 Ultra (NVFP4):** first-pass model. Drafts in about 2 seconds at under a cent per question; answers 53% of questions without escalation at τ = 3.
- **Kimi K3:** repair model, on disagreements (τ = 3) or every question (τ = 4).
- **Python, SQLite, FastAPI, Uvicorn:** harness, read-only query execution, /ask service.
- **NumPy, SciPy, Matplotlib:** scoring, significance tests, charts.
- **BIRD Mini-Dev** (Hugging Face): questions, databases, reference queries.

## Team

- Shreenidhi Sudhakar · shree6791@gmail.com
- Joseph Mikhail · mikhailj@gmail.com

## Notes and assumptions

- **Analyst cost:** $62.07/h, operations research analysts, San Jose metro (BLS OEWS, May 2025), the closest BLS role to a data analyst.
- **Assumed:** 30 min to write a query, 10 min to review a draft. Draft + review = 10 min review + 30 min rewrite on the 36.6% the τ = 3 cascade gets wrong = 21 min.
- **Run:** 500 of 500 questions (150 to choose τ, 350 reported). No failed calls; 144 rate-limited Kimi calls retried successfully. 4 of about 1,000 Kimi replies ran out of length and count as wrong.
- **p = 0.006:** McNemar test; a gap this large would appear by chance less than 1% of the time.
- **Confidence intervals:** 95% bootstrap intervals over the 350 test questions (10,000 resamples); the +7.7-point interval is paired, question by question.
- **Baseline scope:** the frontier baseline is Kimi K3, an open model. Closed models (GPT, Claude, Gemini) were not tested.
- **Comparability:** this question file is mostly the hardest tier (460 of 500), so scores are not comparable to the public BIRD leaderboard.
- **Cascade:** a cheap model answers first; a stronger model handles only what the cheap model is unsure about.
- **τ (tau):** how many of Nemotron's three drafts must return the same rows to skip escalation.
- **Execution accuracy:** share of questions where our query returns the same rows as the reference.
