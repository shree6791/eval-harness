$ PROJECT.NAME
Nemotron-First SQL Cascade

$ PROJECT.README
Turn a plain-English business question into a database query: cheap-model cost, close to large-model accuracy.

Analysts wait days on a data engineer for this. Our cascade answers in seconds.

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

Results (test set, n = 350)
- Nemotron 3 Ultra alone: __% accurate, $__ per 1,000 questions
- Kimi K3 alone: __% accurate, $__ per 1,000 questions
- Cascade at τ = __: __% accurate, $__ per 1,000 questions, __% escalated to Kimi
- Cost per correct answer: $__ (cascade) vs $__ (Kimi alone)
- Median time to answer: __ s

Live demo: ____
Code: https://github.com/shree6791/eval-harness

$ PROJECT.STACK
Fireworks.ai: serverless inference for NVIDIA Nemotron 3 Ultra (cheap tier) and Kimi K3 (repair tier) through the OpenAI-compatible API
Microsoft: ____
NVIDIA: Nemotron 3 Ultra (NVFP4) as the first-pass model
other stack: Python, SQLite, FastAPI and Uvicorn (live /ask page), NumPy, SciPy and Matplotlib (scoring, bootstrap intervals, McNemar test, chart)
anything else you used: BIRD Mini-Dev benchmark (birdsql/bird_mini_dev on Hugging Face)

$ TEAM.ROSTER
Shreenidhi Sudhakar · shree6791@gmail.com · LEAD
Joseph Mikhail · mikhailj@gmail.com
