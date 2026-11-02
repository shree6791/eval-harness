# Write-up

## Project name
Nemotron-First SQL Cascade

## Overview
Turn a plain-English business question into a database query: cheap-model cost, close to large-model accuracy.

Business teams send every data question to an analyst, and analysts spend a large share of their week writing routine SQL instead of analyzing. Our cascade drafts the query in under a minute: NVIDIA Nemotron writes three attempts, and Kimi K3 repairs them. The analyst reviews a draft instead of writing from scratch. The answer is just as correct, about 26% cheaper, and arrives in minutes instead of days.

How it works
- NVIDIA Nemotron 3 Ultra (reasoning off, on Fireworks) writes three SQLite queries for the question. The prompt shows the schema with real example values from each column, so the model matches stored formats instead of guessing them.
- Each query runs read-only against the real database. If at least τ of the three return the same rows, we keep that answer.
- If they disagree, crash, time out or return nothing, Kimi K3 sees the question, the schema and all three attempts with what each one returned, and writes one corrected query.
- The check costs nothing extra: no judge model, just comparing result sets.

How we scored it
- BIRD Mini-Dev: 500 questions over 11 real SQLite databases, each with a reference query. We use the 2026-10-28 SQLite question file, which is mostly challenging questions (460 of 500), so scores are not comparable to the published BIRD leaderboard. Every setup is scored on the same questions.
- Execution accuracy: run our query and the reference, compare result sets (order and duplicates ignored, floats rounded to 6 places). No AI grader.
- τ tuned on 150 questions, reported on the other 350.
- Negative control: the grader passes the reference against itself 20/20 and fails deliberately broken SQL 0/20 (wrong filter, extra column, another question's query).

What we optimized
- Schema example values: both prompts list real values from each column after its CREATE TABLE (all values for columns with up to 20 distinct values, else 3 examples). Same 320 test questions before and after: Nemotron alone 28.1% → 41.9%, Kimi K3 alone 50.3% → 65.9%.
- Output format: both prompts ask for one SQLite query inside a ```sql block with no explanation. On the 20-question smoke test, empty or prose replies went from 72 of 100 to 0.
- Reasoning settings: Nemotron 3 Ultra runs with reasoning off (2 s instead of minutes per call); Kimi K3 gets a 16,384-token budget so reasoning does not crowd out the query.
- Model switch: Nemotron 3.5 Lightning took about 6 minutes per call on event day; Nemotron 3 Ultra replaced it as the first-pass model.

Results (test set, n = 350)
- Nemotron 3 Ultra alone: 42.6% accurate, $2.50 per 1,000 questions, 1.6 s median
- Kimi K3 alone: 66.3% accurate, $34.11 per 1,000 questions, 11.6 s median
- Cascade at τ = 3 (chosen on the tune split): 59.7% accurate, $34.63 per 1,000 questions, 49% escalated to Kimi, 4.3 s median
- Cost per correct answer: $0.058 (cascade) vs $0.052 (Kimi alone)
- Schema example values, same 320 questions before and after: Nemotron alone 28.1% → 41.9%, Kimi K3 alone 50.3% → 65.9%
- Cascade draft + analyst review: $22.88 per question vs $31.04 for an analyst writing the query, 26% lower, at 100% accuracy (analyst at $62.07/h, BLS May 2025; 30 min to write and 10 min to review assumed)
- 53 of 350 test repair calls failed when the Fireworks account hit its spending limit; they count as wrong. On the 297 questions where repair ran, Kimi repairing Nemotron's three drafts (τ = 4) scored 72.4% vs 64.0% for Kimi alone.

Live demo: ____
Code: https://github.com/shree6791/eval-harness

## Tech stack
Fireworks.ai: serverless inference for NVIDIA Nemotron 3 Ultra (cheap tier) and Kimi K3 (repair tier) through the OpenAI-compatible API
Microsoft: ____
NVIDIA: Nemotron 3 Ultra (NVFP4) as the first-pass model
other stack: Python, SQLite, FastAPI and Uvicorn (live /ask page), NumPy, SciPy and Matplotlib (scoring, bootstrap intervals, McNemar test, chart)
anything else you used: BIRD Mini-Dev benchmark (birdsql/bird_mini_dev on Hugging Face)

## Team
Shreenidhi Sudhakar · shree6791@gmail.com · LEAD
Joseph Mikhail · mikhailj@gmail.com
