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
