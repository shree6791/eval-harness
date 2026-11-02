# Write-up

Fill every blank from the 350-question test set unless the sentence says otherwise. Numbers freeze at 3:45 PT. Nothing measured after that goes on a slide.

## The task

Turning plain-English business questions into database queries. Analysts wait days on a data engineer for this.

## What we deployed

A cheap open model (Nemotron 3.5 Lightning) and a large one (Kimi K3) on Fireworks serverless, behind a service running the chain: the cheap model answers three times, an automatic checker compares the results, and the large model repairs only what the checker rejects. Live at ____.

## How we scored it

BIRD Mini-Dev: 500 real questions over 11 real databases, each with a reference query. We run ours, run the reference, and compare result sets with BIRD's own rule. No AI grader. Tuned on 150 questions, reported on the other 350.

## The checker

Three cheap answers that return the same rows are kept. Disagreement, a crash, a timeout, or an empty result escalates. The checker costs nothing but the cheap samples and needs no judge model. The obvious alternative, escalating only when the query fails to run, sits on the chart below ours: most wrong SQL runs fine and returns the wrong rows.

## What we tuned

One number, τ: how many of the three cheap answers must agree. Five settings give five points; cheap alone and large alone sit at the ends of the same curve.

## Business value

$____ per correct answer vs. $____ for the large model alone. ____ s median to an answer vs. days. ____% answered correctly with no human.

Cost per correct answer = ($ per question) ÷ (accuracy).

## How far we pushed it

Knee at τ = __. Past it, extra cost buys ____ points. The ceiling is below 100%: ____% of reference queries fail or are wrong on inspection, so ____% is the practical limit and the cascade is ____ points from it.

## What we broke

Against the large model alone: fixed __, broke __ (McNemar exact test, p = ____). Example broken question: ____.

## Why the numbers hold

Re-running an identical setup moves the score by ±__ points (model wobble). Changing which questions are in the set moves it by ±__ on 350 (sampling error, the larger one). Comparisons are paired, question by question. The grader passes the reference against itself 20/20 and fails deliberately wrong SQL 0/20.

## Results table (test set, n = 350)

| Setup | Accuracy % (95% CI) | % escalated | $ / 1k questions | p50 / p95 kept, ms | p50 / p95 escalated, ms |
| --- | --- | --- | --- | --- | --- |
| Cheap model alone | ____ (–) | 0 | ____ | ____ / ____ | – |
| Large model alone | ____ (–) | 100 | ____ | – | ____ / ____ |
| Executability gate | ____ (–) | ____ | ____ | ____ / ____ | ____ / ____ |
| Agreement cascade, τ = __ | ____ (–) | ____ | ____ | ____ / ____ | ____ / ____ |

Chart: `chart_test.png`.

## Slides

1. Task. Who currently waits for answers, and for how long.
2. Architecture. The cascade, and why agreement beats executability.
3. The curve. The chart in large fonts, with a one-sentence summary.
4. Trust. Two uncertainties, fixed/broke with p-value, negative control, ceiling.
5. Generalisation. Any output with a cheap deterministic check: SQL that must run, JSON that must validate, code that must compile, a tool call that must bind.
