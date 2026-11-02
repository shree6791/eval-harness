# Change log

Settings in the runbook change only through an entry here.

| Time | Source | Change | Section |
| --- | --- | --- | --- |
| 1 Nov, 23:00 | Plan review | Baselines scored from their own passes (A0 single call, C cold), not from the cascade at τ = 0 and τ = 4 | 3, 6 |
| 1 Nov, 23:00 | Plan review | Gate groups only successful results, so a crash never ties with a real answer | 6 |
| 1 Nov, 23:00 | Plan review | Executability gate uses A0 with C as fallback, costed as one cheap call | 3, 6 |
| 1 Nov, 23:00 | Plan review | Reference queries get a 30 s timeout; generated queries keep 5 s | 2, 6 |
| 1 Nov, 23:15 | Team | Event laptop changed to the work laptop; corporate TLS certificate setup added | 2, 4, 8 |
| 2 Nov, 08:00 PT | Setup | Repository is `shree6791/eval-harness`. The runbook name `bird-cascade` is not used. | 4 |
| 2 Nov, 08:00 PT | Setup | Question file is the 2026-10-28 Hugging Face Mini-Dev SQLite update (500 questions). Databases are the 11 SQLite files from `minidev.zip` (June 2024). All 500 reference queries returned rows under the 30 s limit. `split.json` generated once: 150 tune / 350 test, seed 42. | 2, 4 |
| 2 Nov, 08:00 PT | Fireworks changelog | Serverless shutdown scheduled for 7 Nov 2026 includes `nemotron-lightning-3p5-30b-a3b` and `gpt-oss-120b`. Event day is 2 Nov, so both locked tier-1 IDs stay. Confirm with one live call at check-in. Kimi K3 and GLM 5.3 are unaffected. | 2 |
| 2 Nov, 08:15 PT | Code | Library moved under `harness/`. Root commands are unchanged. `TAU` lives in `harness/config.py`. | 6 |
| 2 Nov, 12:15 PT | Live check | Cheap tier switched from `nemotron-lightning-3p5-30b-a3b` to `nemotron-3-ultra-nvfp4` (NVIDIA Nemotron 3 Ultra, $0.60 / $2.40). Lightning took ~6 min per call and timed out; Ultra with `reasoning_effort="none"` returned SQL in ~2 s. | 2 |
| 2 Nov, 12:15 PT | Smoke test | Replies were empty because reasoning used the 2,048-token cap. `max_tokens` is now 8,192; `reasoning_effort` is `none` for the cheap tier and `low` for the cheap backup; others use their default. Both settings are in the cache key. Client timeout is 120 s. Records store `finish`, and `raw` when no SQL is found. | 6 |
| 2 Nov, 12:15 PT | Smoke test | `clean()` falls back to the first SELECT or WITH line when there is no code fence. Both prompts ask for one query in a ```sql block. | 6 |
| 2 Nov, 12:15 PT | Smoke test | 20 tune questions: 0 empty, 0 truncated replies. Cheap alone 25%, Kimi K3 alone 45%. Cheap p50 2.6 s; Kimi p50 9.0 s, p95 121 s. | 6 |
| 2 Nov, 12:25 PT | Full run | `CONCURRENCY` raised from 16 to 48. At 16 the full run did ~70 calls a minute (Kimi K3 latency); at 48 it does ~290 with no rate-limit errors. Cache keys are unchanged. | 6 |
| 2 Nov, 12:31 PT | Smoke test | Re-run of the same 20 tune questions on a second laptop: cheap alone 20%, Kimi K3 alone 45%. Kimi qid 16 ended at 8,192 output tokens with an empty reply; Kimi used 4,053–8,192 tokens on 4 of 20. Kimi p95 131 s, above the 120 s client timeout. | 6 |
| 2 Nov, 12:31 PT | Code | Client timeout raised from 120 s to 300 s so slow Kimi K3 replies finish instead of retrying. | 6 |
| 2 Nov, 12:31 PT | Code | Kimi K3 `max_tokens` is 16,384 (`MAX_TOKENS_BY_MODEL`); other models stay at 8,192. The per-model limit is in the cache key. Records store `treason` (reasoning tokens) when the API reports it. | 6 |
| 2 Nov, 12:31 PT | Code | The schema in both prompts now lists example values after each CREATE TABLE: all values for columns with at most 20 distinct non-null, non-BLOB values (found within 0.5 s), else 3 examples. Text over 40 characters is cut and marked `(truncated)`; quotes are escaped as SQL literals; line breaks show as `\n` with a note; an over-long list is marked `(list cut)`. Values come from the databases only, never from reference SQL. Reason: wrong answers on tune guessed formats (codes with leading zeros, `CharterNum` stored as text, category names, dividing fractions by 100). Measured cheap prompt input grew from ~1,100 to ~4,900 tokens. Prompt change: no cached answers are reused. Same 20 tune questions after this and the Kimi budget change: cheap alone 20% → 35%, Kimi K3 alone 45% → 60%, no cut-off replies, Kimi p95 131 s → 57 s. Twenty questions from two databases; treat as directional. | 6 |
| 2 Nov, 12:31 PT | Code | The gate and the executability gate treat a result whose values are all NULL as empty, so three NULLs no longer agree. No reference answer is all-NULL. | 6 |
| 2 Nov, 12:31 PT | Code | A failed API call is recorded as a wrong answer (`finish="error"`, not cached) instead of dropping the whole question from the denominator. Its time includes retries; its tokens are unknown and count as $0 (`billed="unknown"`). The live `/ask` path uses the same handling, so an outage returns an error instead of a server crash, and an empty repair reply returns an error instead of zero rows. | 6 |
| 2 Nov, 12:31 PT | Code | `analyze.py` prints `$/correct` (total spend ÷ correct answers) and `p50 all` (median API time over all questions, ms) for the write-up. | 6 |
| 2 Nov, 12:45 PT | Full run | Fireworks returned HTTP 429 at `CONCURRENCY` 48 and 76 questions failed after 4 short retries. `CONCURRENCY` lowered to 24; retries raised to 8 with backoff up to 60 s plus jitter. Cached calls were kept; the rerun makes only the missing calls. | 6 |
