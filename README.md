# eval-harness

Fireworks, Microsoft, and NVIDIA buildathon. 2 November 2026, San Francisco.

The brief: take open models and make a frontier on a task you define. Deploy it, evaluate it, measure the tradeoffs, tune one dimension against a baseline, and show the business value.

**Task.** Turn a plain-English business question into a database query. Analysts wait days on a data engineer for this.

**Approach.** A cheap model answers three times. A free check compares the result sets. A large model repairs only the questions that check rejects. The aim is large-model accuracy at a fraction of large-model cost.

## How this meets the brief

| Brief | What we ship |
| --- | --- |
| Pick a task | Text-to-SQL over real business databases |
| Deploy it | Cheap and large open models on Fireworks, behind a live `/ask` page |
| Build an eval | [BIRD Mini-Dev](https://huggingface.co/datasets/birdsql/bird_mini_dev): 500 questions, 11 SQLite databases. Score is execution accuracy. No AI judge. |
| Measure tradeoffs | Accuracy, percent escalated, dollars per 1,000 questions, p50/p95 latency for kept vs escalated |
| Tune one dimension | Agreement threshold τ, swept from 0 to 4, against cheap-alone and large-alone |
| Show the value | Cost per correct answer, seconds instead of days, share answered with no human |

## How the cascade works

1. The cheap model writes three SQLite queries (temperature 0.6).
2. Each query runs read-only, with a 5 second timeout and a 10,000 row cap.
3. Answers that return the same rows form a group. `c` is the size of the largest group (0–3). A crash, timeout, oversized result, or empty result never counts as agreement.
4. If `c < τ`, the large model sees the question, the schema, the hint, the three attempts, and what each one did, then writes one corrected query.

τ = 0 keeps the cheap answer every time. τ = 4 sends every question to the large model. Changing τ does not call the models again. The sweep reads cached results.

The winning τ is the most accurate setting on the 150-question tune split. A tie within 1 point goes to the cheaper τ. Report that choice on the 350-question test split. `split.json` is already frozen. Do not regenerate it.

## Models

Prices are dollars per 1 million tokens, input / output.

| Role | Model | Price |
| --- | --- | --- |
| Cheap | `accounts/fireworks/models/nemotron-3-ultra-nvfp4` (NVIDIA Nemotron 3 Ultra, reasoning off) | 0.60 / 2.40 |
| Cheap backup | `accounts/fireworks/models/gpt-oss-120b` | 0.15 / 0.60 |
| Large | `accounts/fireworks/models/kimi-k3` | 3.00 / 15.00 |
| Large backup | `accounts/fireworks/models/glm-5p3` | 1.40 / 4.40 |

Both cheap IDs are listed for serverless shutdown on 7 November 2026. They stay in place for event day. Confirm each model with one live call before the scored run. Record any switch in `CHANGELOG.md`.

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FIREWORKS_API_KEY=...
```

On the work laptop, set `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` to the corporate CA bundle.

The 500 questions are in git. The databases are not. All 500 reference queries run against the June 2024 SQLite files:

```bash
curl -L -o /tmp/minidev.zip https://bird-bench.oss-cn-beijing.aliyuncs.com/minidev.zip
unzip /tmp/minidev.zip "minidev/MINIDEV/dev_databases/*/*.sqlite" -d /tmp/minidev
mkdir -p data/MINIDEV
mv /tmp/minidev/minidev/MINIDEV/dev_databases data/MINIDEV/dev_databases
```

You should then have `data/MINIDEV/mini_dev_sqlite.json` and 11 folders named `dev_databases/<db_id>/<db_id>.sqlite`. Questions are CC BY-SA 4.0.

## Run

```bash
python negative_control.py                          # gold 20/20, three corruptions 0/20
python passes.py --stage base --split tune --limit 20 --out rows_20.pkl
python analyze.py --rows rows_20.pkl --split tune   # read the SQL before the full run
python passes.py --stage base                       # cheap alone, 3 samples, large alone
python passes.py --stage rerun --out rows_rerun.pkl &
python passes.py --stage repair                     # large model fixes the 3 cheap attempts
python passes.py --stage all
python analyze.py --split tune                      # prints the chosen tau
python analyze.py --split test --tau 2              # final table and chart_test.png
uvicorn serve:app --port 8000
cloudflared tunnel --url http://localhost:8000
```

Set `TAU` in `harness/config.py` to the tune-set choice, then restart the service. Five demo questions go in `demo_questions.txt`. The submission write-up is `WRITEUP.md`.

## Code

| Path | Role |
| --- | --- |
| `harness/cascade.py` | One question: three cheap answers, the gate, then repair |
| `harness/gate.py` | Agreement rule |
| `harness/sql.py` | Run SQL, time it out, compare result sets |
| `harness/llm.py` | Cached, metered Fireworks calls |
| `harness/scoring.py` | Accuracy, cost, latency, tau choice, chart |
| `harness/service.py` | Live `/ask` API |
| `harness/config.py` | Models, prices, limits, `TAU` |
| `passes.py`, `analyze.py`, `serve.py` | Commands above |
| `demo.py`, `demo_cases.json` | Five-question walkthrough; replays recorded results, `--live` for real calls |
