# eval-harness

Text-to-SQL cascade for the Fireworks × Microsoft × NVIDIA Buildathon (2 Nov 2026).

A cheap model answers three times. A free agreement check compares the result sets. A large model repairs only the questions the check rejects. The target is large-model execution accuracy at a fraction of large-model cost.

The runbook called the repository `bird-cascade`. This repository is `eval-harness`.

## Locked settings

| Setting | Value |
| --- | --- |
| Dataset | BIRD Mini-Dev, SQLite, all 500 questions, 11 databases |
| Hint field | Used in every prompt |
| Grader | `set(predicted rows) == set(reference rows)`, floats rounded to 6 places |
| Split | 150 tune / 350 test, stratified by database × difficulty, seed 42. Committed. Do not regenerate. |
| Tier 1 | `accounts/fireworks/models/nemotron-lightning-3p5-30b-a3b` ($0.05 / $0.20 per 1M) |
| Tier 1 backup | `accounts/fireworks/models/gpt-oss-120b` ($0.15 / $0.60) |
| Tier 2 | `accounts/fireworks/models/kimi-k3` ($3.00 / $15.00 per 1M) |
| Tier 2 backup | `accounts/fireworks/models/glm-5p3` ($1.40 / $4.40) |
| Samples | k = 3, pass A temperature 0.6. Passes A0, B, and C use temperature 0. |
| Query limits | 5 s and 10,000 rows for generated SQL. 30 s for reference SQL. Read-only. |
| Empty result | Failure in the gate (`EMPTY_IS_FAILURE = True`) |
| Tuned parameter | τ only. Escalate when the largest agreeing cluster `c < τ`. |
| τ rule | Highest accuracy on the 150 tune questions. Ties within 1 point go to the cheaper τ. Report on the 350 test questions. |

τ = 0 never escalates. τ = 4 always escalates. The sweep is offline: τ changes only the gate, not what any model returned.

Fireworks lists both tier-1 model IDs for serverless shutdown on 7 Nov 2026. The event is 2 Nov, so the locked IDs stay. Confirm each model with one live call at check-in and record any switch in `CHANGELOG.md` before the first scored run.

## Layout

| File | Job |
| --- | --- |
| `config.py` | Paths, model IDs, prices, settings |
| `sqlrun.py` | Execute SQL with a real timeout, compare results, read schema |
| `gate.py` | Agreement gate |
| `split.py` | 150/350 split. Already run. |
| `negative_control.py` | Proves the grader fails wrong SQL |
| `prompts.py` | Cheap prompt and repair prompt |
| `llm.py` | Cached, metered Fireworks calls |
| `passes.py` | Passes A0, A, C, B, R |
| `analyze.py` | Sweep, results table, statistics, chart |
| `serve.py` | Live `/ask` service and demo page |
| `split.json` | Frozen split |
| `data/MINIDEV/mini_dev_sqlite.json` | 500 questions, 2026-10-28 Mini-Dev update |
| `demo_questions.txt` | Five tune questions for the live demo |
| `WRITEUP.md` | Fill-in write-up for the submission |

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FIREWORKS_API_KEY=...   # also in ~/.zshrc on the event laptop
```

On the work laptop, point `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` at the corporate CA bundle before calling `api.fireworks.ai`.

Databases are not in git. The question file is. Download the SQLite databases (the June 2024 `minidev.zip` backup; all 500 reference queries from the 2026 question file execute against these files):

```bash
curl -L -o /tmp/minidev.zip https://bird-bench.oss-cn-beijing.aliyuncs.com/minidev.zip
unzip /tmp/minidev.zip "minidev/MINIDEV/dev_databases/*/*.sqlite" -d /tmp/minidev
mkdir -p data/MINIDEV
mv /tmp/minidev/minidev/MINIDEV/dev_databases data/MINIDEV/dev_databases
```

Confirm `data/MINIDEV/mini_dev_sqlite.json` and 11 folders of `dev_databases/<db_id>/<db_id>.sqlite`.

Questions are the 2026-10-28 Hugging Face update (`birdsql/bird_mini_dev`, SQLite split). The older JSON packed inside `minidev.zip` is unused. License: CC BY-SA 4.0. That file labels 460 questions challenging, 32 moderate, and 8 simple. The frozen split is still stratified on database × those labels.

## Commands, in order

`split.json` is already committed. Do not run `split.py` again.

```bash
python negative_control.py                         # 20/20, then 0/20 three times
python passes.py --stage base --split tune --limit 20 --out rows_20.pkl
python analyze.py --rows rows_20.pkl --split tune  # then review the SQL manually
python passes.py --stage base                      # A0, A, C on all 500
python passes.py --stage rerun --out rows_rerun.pkl &
python passes.py --stage repair                    # B on all 500
python passes.py --stage all                       # merge; everything cached
python analyze.py --split tune                     # prints the chosen tau
python analyze.py --split test --tau 2             # final numbers + chart_test.png
uvicorn serve:app --port 8000
cloudflared tunnel --url http://localhost:8000
```

Pass R is the run-to-run wobble re-run of A0 and C. Set `TAU` in `serve.py` to the tune-set choice and restart the service before judging.

## Gate

Execute all three cheap samples. Group them by result set. `c` is the size of the largest group that returned real rows (0–3). A crash, timeout, oversize result, or empty result never groups with anything. Escalate when `c < τ`.

On escalation the large model sees the question, schema, hint, the three cheap queries, and what each one did: the exact error text, the row count, or the disagreement. It writes one corrected query.
