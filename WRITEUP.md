# Nemotron-First SQL Cascade

**Ask your data in plain English. Get a reviewed, correct answer in minutes, at 26% lower cost than an analyst writing the query from scratch.**

## The problem

Every business team runs on data questions: which region is slipping, which customers churned, which product line grew. Those questions reach the data through SQL, and SQL sits with a small number of analysts.

- Business users queue for an analyst and wait days for an answer.
- Analysts spend skilled hours writing routine queries instead of analyzing results.
- Fully automatic AI answers are not safe to act on alone. On our test set, the strongest single model is wrong on one question in three, and nothing in its output says which.

The cost is time-to-decision and analyst capacity, both of which compound across every team that depends on data.

## The product

A business user types a question. The system returns a working SQL query, the rows it produces, and a draft ready for an analyst to approve.

1. **Three drafts from a fast NVIDIA model.** NVIDIA Nemotron 3 Ultra writes three candidate queries in parallel, in about 2 seconds.
2. **Real data in the prompt.** The model sees the database schema plus real example values from each column, so it matches how the data is actually stored ('M' vs 'Male', 'south Bohemia', a number stored as text).
3. **A free consistency check.** Each draft runs read-only against the live database. When the drafts disagree, crash or return nothing, the question escalates.
4. **Expert repair.** Kimi K3 sees the question, the schema and all three drafts with what each returned, and writes one corrected query.
5. **Analyst review.** The analyst approves or edits a working draft instead of writing from a blank page.

## Results that matter

| Per question | Analyst writes the query today | Our draft + analyst review |
| --- | --- | --- |
| Accuracy delivered to the business | 100% | 100% (every answer is reviewed) |
| Cost | $31.04 | **$22.88 (26% lower)** |
| Analyst time | 30 min | **22 min (36% more questions per analyst)** |
| Time to an answer | Days in a queue | **Draft in seconds, reviewed in minutes** |

At 1,000 questions a month, the difference is about **$98,000 a year** for one team, with the same analysts answering about a third more questions.

## What we improved, measured

| Lever | Before | After |
| --- | --- | --- |
| Real example values in the schema, NVIDIA Nemotron alone | 28.1% | **41.9% (+13.8 pts)** |
| Real example values in the schema, Kimi K3 alone | 50.3% | **65.9% (+15.6 pts)** |
| Kimi K3 repairing Nemotron's three drafts vs Kimi K3 alone (questions where repair ran, n = 297) | 64.0% | **72.4% (+8.4 pts)** |
| Empty or prose replies on the 20-question smoke test (output format and reasoning settings) | 72 of 100 | **0 of 100** |
| First-pass model latency (Nemotron 3.5 Lightning → Nemotron 3 Ultra) | ~6 min per call | **~2 s per call** |

The first two rows compare the same 320 test questions before and after the change.

![Accuracy, cost and time: baseline vs final vs a data analyst](results/chart_bars.png)

## Full results (test set, n = 350)

| Setup | Accuracy | Cost per 1,000 questions | Cost per correct answer | Median time |
| --- | --- | --- | --- | --- |
| NVIDIA Nemotron 3 Ultra alone | 42.6% | $2.50 | $0.006 | 1.6 s |
| Kimi K3 alone | 66.3% | $34.11 | $0.052 | 11.6 s |
| Cascade, τ = 3 (49% escalated to Kimi K3) | 59.7% | $34.63 | $0.058 | 4.3 s |

![Accuracy vs cost for every setting of τ](results/chart_compare.png)

## How we proved it

- **Benchmark:** BIRD Mini-Dev, 500 real business questions over 11 real SQLite databases (banking, schools, sports, chemistry, healthcare and more), each with a reference query written by people.
- **Scoring:** execution accuracy. Our query and the reference query both run; the answer counts only if the result sets match. No AI grades another AI.
- **No tuning on the test set:** the agreement threshold τ was chosen on 150 questions and reported on the other 350.
- **Grader check:** the grader passes the reference query against itself 20 of 20 times and fails three kinds of deliberately broken SQL 20 of 20 times.
- **Paired comparisons:** every setup answers the same questions, so differences come from the method, not the question mix.

## Why NVIDIA and Fireworks

- **NVIDIA Nemotron 3 Ultra** is the workhorse. It writes every first draft, in about 2 seconds, at under a cent per question.
- **Fireworks serverless** serves both models behind one API with per-token pricing and no GPUs to manage. Swapping the first-pass model on event day was a one-line change.

## Where this goes next

- **Better selection.** On 88% of test questions, at least one generated candidate is already correct. The best single setup reaches 66%. A selector that picks the right candidate closes most of that 22-point gap without a larger model.
- **Self-serve for low-risk questions.** As accuracy rises, routine questions skip review and go straight to the business user; analysts review only high-stakes or uncertain ones.
- **Any structured check.** The same pattern applies wherever a cheap automatic test exists: SQL that must run, JSON that must validate, code that must compile, a tool call that must bind.

## Tech stack

- Fireworks.ai: serverless inference for NVIDIA Nemotron 3 Ultra (first-pass model) and Kimi K3 (repair model) through the OpenAI-compatible API
- NVIDIA: Nemotron 3 Ultra (NVFP4) as the first-pass model
- Python, SQLite, FastAPI and Uvicorn (the /ask service), NumPy, SciPy and Matplotlib (scoring, confidence intervals, McNemar test, charts)
- BIRD Mini-Dev benchmark (birdsql/bird_mini_dev on Hugging Face)

Code: https://github.com/shree6791/eval-harness

## Team

Shreenidhi Sudhakar · shree6791@gmail.com · LEAD
Joseph Mikhail · mikhailj@gmail.com

## Notes and assumptions

- **Analyst cost:** $62.07 per hour, the mean wage for operations research analysts in the San Jose-Sunnyvale-Santa Clara metro (BLS OEWS, May 2025; $129,110 a year). BLS has no separate data analyst code; this is the closest analyst role.
- **Assumed:** 30 minutes for an analyst to write a query, 10 minutes to review a draft, and a 2-day queue today. Savings depend on the ratio of review time to write time, not on the wage: 31% at 30/10 minutes on the baseline run, 26% on the final run.
- **Draft + review cost:** cascade cost per question plus 10 minutes of review on every question plus 30 minutes of rewriting on the 40.3% the cascade gets wrong.
- **Annual figure:** 1,000 questions a month × 12 × $8.16 saved per question. Illustrative volume.
- **Repair failures:** 53 of 350 test repair calls failed when the Fireworks account reached its spending limit. They count as wrong in the full results table. The +8.4-point repair result uses the 297 questions where repair ran.
- **Benchmark comparability:** the 2026-10-28 question file is mostly the hardest tier (460 of 500 questions are challenging), so scores are not comparable to the published BIRD leaderboard.
- **τ (tau):** the number of the three Nemotron drafts that must return the same rows for the answer to be kept without escalation.
- **Execution accuracy:** the share of questions where our query returns the same result set as the reference query (row order and duplicates ignored, floats rounded to 6 places).
