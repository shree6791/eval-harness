# Write-up

## Project name

FirstDraft: Nemotron-first text-to-SQL, analyst-approved

## Overview

**Business questions answered in minutes, not days. Analysts answer 43% more of them.**

### The problem

Every business decision waits on a data question: which region is slipping, which customers churned, which product line grew. Those questions reach the data through SQL, and SQL sits with a small team of analysts.

- Business users queue for an analyst and wait days for an answer.
- Analysts spend skilled hours writing routine queries instead of analyzing results.
- Many questions never get asked, because the wait is not worth it.
- Fully automatic AI is not safe to act on alone. On our test set, the strongest single model is wrong on one question in three, and nothing in its output says which.

The bottleneck is time-to-decision and analyst capacity.

### What we built

A business user types a question in plain English. The system returns a working SQL query and its results, drafted in seconds and ready for an analyst to approve.

1. **Three drafts from NVIDIA Nemotron 3 Ultra**, written in parallel in about 2 seconds.
2. **Real data in the prompt.** The model sees the database schema plus real values from each column, so it matches how the data is actually stored ('M' vs 'Male', 'south Bohemia', a number stored as text).
3. **A free consistency check.** Each draft runs read-only against the live database. When drafts disagree, crash or return nothing, the question escalates.
4. **Expert repair.** Kimi K3 sees the question, the schema and all three drafts with what each returned, and writes one corrected query.
5. **Analyst approval.** The analyst approves or edits a working draft instead of starting from a blank page. Every answer that reaches the business is reviewed.

### What it delivers

| Per question | Analyst writes the query today | Our draft + analyst review |
| --- | --- | --- |
| Time to an answer | Days in a queue | **Draft in seconds, reviewed in minutes** |
| Analyst time | 30 min | **21 min: 43% more questions per analyst** |
| Accuracy delivered to the business | 100% | 100% (every answer is reviewed) |
| Cost | $31.04 | $21.75 (30% lower) |

The same analysts clear the backlog faster and answer the questions that never got asked. No one is replaced: the analyst stays accountable for every answer and spends more time on analysis.

### Why this is different

Natural-language-to-SQL is a crowded market. Our edge is evidence and design, not the idea.

- **Measured where it fails.** 350 held-out questions scored against human-written answers by running both queries. No AI grades another AI.
- **Built for review.** Model agreement does not reliably signal a correct answer, so the workflow keeps the analyst in charge instead of promising full automation.
- **A measured lever any team can use.** Showing real column values in the prompt added 16 to 17 points of accuracy to both models, with no fine-tuning and no bigger model.
- **Open models, no lock-in.** Everything runs on open models through Fireworks. The first-pass model was swapped mid-event with a one-line change.
- **A known path to the next gain.** On 88% of test questions, at least one generated draft is already correct; the best setup picks the right one 76% of the time.

### Results

| What we changed | Before | After |
| --- | --- | --- |
| Real column values in the prompt, NVIDIA Nemotron 3 Ultra alone | 28.1% | **43.8% (+15.7 pts)** |
| Real column values in the prompt, Kimi K3 alone | 50.3% | **67.5% (+17.2 pts)** |
| Kimi K3 repairing Nemotron's three drafts vs Kimi K3 alone (all 350 test questions; McNemar p = 0.006) | 68.0% | **75.7% (+7.7 pts)** |
| First-pass model latency (Nemotron 3.5 Lightning → Nemotron 3 Ultra) | ~6 min per call | **~2 s per call** |
| Empty or prose replies, 20-question smoke test (output format and reasoning settings) | 72 of 100 | **0 of 100** |

The first two rows compare the same 320 test questions before (baseline run) and after the change (complete run).

![Accuracy, cost and time: baseline vs the complete run vs a data analyst](results/chart_bars.png)

Full results on the test set (n = 350):

| Setup | Accuracy | 95% CI | Cost per 1,000 questions | Cost per correct answer | Median time |
| --- | --- | --- | --- | --- | --- |
| NVIDIA Nemotron 3 Ultra alone | 43.4% | 38.3–48.6 | $2.54 | $0.006 | 2.1 s |
| Kimi K3 alone | 68.0% | 63.1–72.9 | $32.41 | $0.048 | 15.0 s |
| Cascade, τ = 3, 47% escalated to Kimi K3 | 63.4% | 58.3–68.3 | $44.61 | $0.070 | 7.1 s |
| Cascade, τ = 4, every question repaired by Kimi K3 (highest tune accuracy) | **75.7%** | 71.1–80.3 | $98.58 | $0.130 | 43.9 s |

Intervals are 95% bootstrap intervals over the 350 test questions. Nemotron alone and Kimi K3 alone do not overlap, and τ = 4 beats Kimi K3 alone in a paired test: 59 questions fixed, 32 broken, McNemar p = 0.006.

τ = 4 is the most accurate setup, 7.7 points above Kimi K3 alone, at three times its cost: Kimi reasons about twice as long when repairing three drafts as when answering cold. τ = 3 is the balanced setting the review workflow uses.

![Accuracy vs cost for every setting of τ](results/chart_compare.png)

### When the drafts agree, are they right?

When all three Nemotron drafts return the same rows (53% of test questions), they are right only 53% of the time, so agreement alone cannot certify an answer. That is why every answer goes to an analyst for review. The repair helps most where Nemotron does worst: when all three drafts fail, it gets 75% right against 38% for Kimi K3 answering cold.

### One question, start to finish

Test question 346 asks how many superheroes have an alignment that is neither good nor bad. All three Nemotron drafts and Kimi K3 on its own use an inner join and answer 28, silently dropping the six heroes with no alignment. Shown the three matching drafts and told they can still be wrong, the Kimi K3 repair switches to a left join and returns the correct 34. It is one of 59 test questions the repair fixed over Kimi K3 alone.

### How we proved it

- **Benchmark:** BIRD Mini-Dev, 500 real business questions over 11 real SQLite databases (banking, schools, sports, chemistry, healthcare and more), each with a reference query written by people.
- **Scoring:** execution accuracy. Our query and the reference query both run; an answer counts only when the result sets match.
- **No tuning on the test set:** τ was chosen on 150 questions and reported on the other 350. The highest tune accuracy was τ = 4 (74.0% vs 71.3% for Kimi K3 alone).
- **Grader check:** the grader passes the reference query against itself 20 of 20 times and fails three kinds of deliberately broken SQL 20 of 20 times.
- **Paired comparisons:** every setup answers the same questions.

### Where this goes next

- **Pick the right draft.** A selector that chooses among the existing drafts could close most of the 12-point gap between 76% and 88%, without a larger model.
- **A cheaper repair.** Lower reasoning effort on the repair call would bring τ = 3 below the cost of Kimi K3 alone.
- **Self-serve for routine questions.** As accuracy rises, low-risk questions go straight to the business user; analysts review high-stakes and uncertain ones.
- **Beyond SQL.** The same pattern fits any output with a cheap automatic check: JSON that must validate, code that must compile, a tool call that must bind.

### Demo and code

- Code: https://github.com/shree6791/eval-harness
- `python demo.py` walks five questions through the cascade; `python demo.py --compare` shows four questions before and after real column values.

## Tech stack

- **Fireworks.ai:** serverless inference for both models behind one OpenAI-compatible API, billed per token with no GPUs to provision. Three drafts per question are affordable only at serverless per-token prices, and the first-pass model was swapped mid-event without redeploying anything.
- **NVIDIA Nemotron 3 Ultra (NVFP4):** the first-pass model. It writes every draft in about 2 seconds at under a cent per question and answers 53% of test questions without escalation at τ = 3.
- **Kimi K3:** the repair model, called only when Nemotron's drafts disagree.
- **Python, SQLite, FastAPI and Uvicorn:** the harness, read-only query execution with timeouts, and the /ask service.
- **NumPy, SciPy and Matplotlib:** scoring, confidence intervals, McNemar test and charts.
- **BIRD Mini-Dev** (birdsql/bird_mini_dev on Hugging Face): questions, databases and reference queries.

## Team

Shreenidhi Sudhakar · shree6791@gmail.com · LEAD
Joseph Mikhail · mikhailj@gmail.com

## Notes and assumptions

- **Analyst cost:** $62.07 per hour, the mean wage for operations research analysts in the San Jose-Sunnyvale-Santa Clara metro (BLS OEWS, May 2025; $129,110 a year). BLS has no separate data analyst code; this is the closest analyst role.
- **Assumed:** 30 minutes for an analyst to write a query, 10 minutes to review a draft, and a multi-day queue today. Savings depend on the ratio of review time to write time, not on the wage.
- **Draft + review:** cascade cost per question at τ = 3, plus 10 minutes of review on every question, plus 30 minutes of rewriting on the 36.6% the cascade gets wrong. Analyst time: 10 + 0.366 × 30 = 21 minutes.
- **Which run:** every result comes from the second, complete run (500 questions, 0 failed calls; 4 Kimi K3 replies cut off at 32,768 tokens count as wrong). The before/after rows and the charts compare the baseline run with the complete run on the 320 test questions both answered. An earlier full run lost 53 test repair calls to the Fireworks spending limit and is not used.
- **Benchmark comparability:** the 2026-10-28 question file is mostly the hardest tier (460 of 500 questions are challenging), so scores are not comparable to the published BIRD leaderboard.
- **Cascade:** a cheap model answers first and a stronger model handles only the questions the cheap model is unsure about.
- **τ (tau):** the number of Nemotron's three drafts that must return the same rows for the answer to be kept without escalation.
- **Execution accuracy:** the share of questions where our query returns the same result set as the reference query (row order and duplicates ignored, floats rounded to 6 places).
