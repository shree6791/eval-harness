"""Walk through the cascade on a few tune-set questions.

    python demo.py                    # replay recorded results, no API calls
    python demo.py --tau 4            # same questions, a different threshold
    python demo.py --live             # real Fireworks calls (needs FIREWORKS_API_KEY)
    python demo.py --export rows.pkl  # rebuild demo_cases.json from a full run
    python demo.py --compare          # baseline prompt vs schema example values
    python demo.py --export-compare baseline_rows.pkl  # rebuild demo_compare.json

Replay is the default so a recording never depends on Fireworks rate limits.
"""

import argparse
import asyncio
import json
import time
from pathlib import Path

from harness.config import K, QUESTIONS, db_path

CASES = Path("demo_cases.json")
# Tune split only. Two the cheap model keeps at tau = 3, three it escalates.
DEMO_QIDS = [53, 118, 57, 0, 60]
SHOW_ROWS = 3


def label(res):
    kind, payload = res
    if kind == "error":
        return f"error: {str(payload)[:80]}"
    if kind == "oversize":
        return "more than 10,000 rows"
    if not payload:
        return "0 rows"
    head = ", ".join(str(tuple(r)) for r in payload[:SHOW_ROWS])
    more = f" (+{len(payload) - SHOW_ROWS} more)" if len(payload) > SHOW_ROWS else ""
    return f"{len(payload)} row(s): {head}{more}"


def rec_json(rec, gold):
    from harness.llm import usd
    from harness.sql import correct

    kind, payload = rec["res"]
    return {
        "sql": rec["sql"],
        "res": [kind, [[str(v) for v in r] for r in payload[:SHOW_ROWS]] if kind == "ok" else str(payload)],
        "n_rows": len(payload) if kind == "ok" and payload else 0,
        "ok": correct(rec["res"], gold),
        "ms": round(rec["ms"]),
        "usd": usd(rec),
        "sig": None,  # filled below for cheap samples
    }


def export(rows_path):
    """Store the recorded calls for DEMO_QIDS so replay needs no API and no pickle."""
    import pickle

    from harness.gate import signature

    rows = {r["qid"]: r for r in pickle.load(open(rows_path, "rb"))}
    qs = {q["question_id"]: q for q in json.load(open(QUESTIONS))}
    out = []
    for qid in DEMO_QIDS:
        r, q = rows[qid], qs[qid]
        samples = []
        for i, s in enumerate(r["a"]):
            j = rec_json(s, r["gold"])
            sig = signature(s["res"], i)
            # Groups compare result sets; store a stable id for each group.
            j["sig"] = str(hash(sig)) if sig[0] == "rows" else f"{sig[0]}-{i}"
            samples.append(j)
        out.append(
            {
                "qid": qid,
                "db_id": r["db"],
                "question": q["question"],
                "evidence": q.get("evidence") or "",
                "gold_sql": q["SQL"],
                "gold": label(r["gold"]),
                "samples": samples,
                "repair": rec_json(r["b"], r["gold"]),
                "large_alone": rec_json(r["c"], r["gold"]),
            }
        )
    CASES.write_text(json.dumps(out, indent=1))
    print(f"{len(out)} cases -> {CASES}")


def gate_from_sigs(sigs, tau):
    """Same rule as harness.gate.gate, on stored group ids."""
    groups = {}
    for i, s in enumerate(sigs):
        if not s.startswith(("fail-", "empty-")):
            groups.setdefault(s, []).append(i)
    if not groups:
        return 0 < tau, 0, 0
    best = max(groups.values(), key=len)
    return len(best) < tau, best[0], len(best)


def fmt_res(res):
    kind, payload = res
    if kind != "ok":
        return f"{kind}: {str(payload)[:80]}"
    return ", ".join(str(tuple(r)) for r in payload) or "0 rows"


def verdict(ok):
    return "CORRECT" if ok else "wrong"


def replay(tau):
    cases = json.loads(CASES.read_text())
    totals = {"cascade": [0, 0.0], "large": [0, 0.0], "cheap": [0, 0.0]}
    for n, c in enumerate(cases, 1):
        print("=" * 78)
        print(f"Question {n} of {len(cases)}  [{c['db_id']}]")
        print(c["question"])
        if c["evidence"]:
            print(f"Hint: {c['evidence']}")
        print(f"Reference answer: {c['gold']}")
        print()
        print(f"Step 1. Nemotron 3 Ultra writes {K} queries in parallel")
        for i, s in enumerate(c["samples"], 1):
            print(f"  Attempt {i}  ({s['ms'] / 1000:.1f} s, ${s['usd']:.4f})  -> {fmt_res(s['res'])}")
        esc, best, agree = gate_from_sigs([s["sig"] for s in c["samples"]], tau)
        cheap_usd = sum(s["usd"] for s in c["samples"])
        print()
        print(f"Step 2. Gate: {agree}/{K} attempts return the same rows. Threshold tau = {tau}.")
        if not esc:
            pick, usd = c["samples"][best], cheap_usd
            ms = max(s["ms"] for s in c["samples"])
            print(f"  {agree} >= {tau}: keep the cheap answer. Kimi K3 is not called.")
        else:
            pick, usd = c["repair"], cheap_usd + c["repair"]["usd"]
            ms = max(s["ms"] for s in c["samples"]) + c["repair"]["ms"]
            print(f"  {agree} < {tau}: escalate. Kimi K3 sees the question, schema and all {K} attempts.")
            print()
            print("Step 3. Kimi K3 repair")
            print("  " + pick["sql"].replace("\n", "\n  "))
            print(f"  -> {fmt_res(pick['res'])}")
        print()
        print(f"Cascade:          {verdict(pick['ok']):8s} ${usd:.4f}  {ms / 1000:5.1f} s")
        la = c["large_alone"]
        print(f"Kimi K3 alone:    {verdict(la['ok']):8s} ${la['usd']:.4f}  {la['ms'] / 1000:5.1f} s")
        a0 = c["samples"][0]
        print(f"Nemotron alone:   {verdict(a0['ok']):8s} ${a0['usd']:.4f}  {a0['ms'] / 1000:5.1f} s")
        for k, ok, u in (("cascade", pick["ok"], usd), ("large", la["ok"], la["usd"]), ("cheap", a0["ok"], a0["usd"])):
            totals[k][0] += ok
            totals[k][1] += u
    print("=" * 78)
    print(f"Totals on these {len(cases)} questions (tau = {tau})")
    for name, k in (("Cascade", "cascade"), ("Kimi K3 alone", "large"), ("Nemotron alone", "cheap")):
        print(f"  {name:15s} {totals[k][0]}/{len(cases)} correct   ${totals[k][1]:.4f}")
    print("Full results: 458 questions, see WRITEUP.md and chart_test.png.")


async def live(tau):
    from harness.cascade import live_answer
    from harness.sql import correct, run_sql

    cases = json.loads(CASES.read_text())
    for n, c in enumerate(cases, 1):
        print("=" * 78)
        print(f"Question {n} of {len(cases)}  [{c['db_id']}]  LIVE")
        print(c["question"])
        db = db_path(c["db_id"])
        t0 = time.monotonic()
        pick, tier, agree, usd = await live_answer(db, c["question"], c["evidence"], tau, f"demo-{time.time()}")
        gold = await run_sql(db, c["gold_sql"], 30)
        print(f"Agreement {agree}/{K}, tau = {tau} -> answered by: {tier}")
        print("  " + pick["sql"].replace("\n", "\n  "))
        print(f"  -> {label(pick['res'])}")
        print(f"Reference: {label(gold)}")
        print(f"{verdict(correct(pick['res'], gold))}   ${usd:.4f}   {time.monotonic() - t0:.1f} s")


COMPARE = Path("demo_compare.json")
# Tune questions where the baseline prompt's majority answer was wrong.
COMPARE_QIDS = [196, 472, 471, 57]


def _example_lines(ddl, sqls):
    """Example-value lines for columns the new queries use (max 3)."""
    used = " ".join(sqls).lower()
    out = []
    for line in ddl.splitlines():
        if line.startswith("--   ") and " (" in line:
            col = line[5:].split(" (", 1)[0]
            if col.lower() in used and line not in out:
                out.append(line[:160])
    # Category lists ("all values") say the most; ID samples say the least.
    out.sort(key=lambda s: ("(all values)" not in s, "id (" in s.lower()))
    return out[:3]


def export_compare(rows_path):
    """Baseline answers from a pre-example-values run vs the current prompt.

    The current-prompt calls come from the cache when present; otherwise they are made live.
    """
    import pickle

    from harness.cascade import attach_results, safe_call, schema_for
    from harness.config import CHEAP, TEMP_A
    from harness.gate import gate
    from harness.llm import usd
    from harness.prompts import cheap_prompt
    from harness.sql import correct

    rows = {r["qid"]: r for r in pickle.load(open(rows_path, "rb"))}
    qs = {q["question_id"]: q for q in json.load(open(QUESTIONS))}

    async def build():
        out = []
        for qid in COMPARE_QIDS:
            r, q = rows[qid], qs[qid]
            db = db_path(q["db_id"])
            ddl = await schema_for(q["db_id"])
            new = await asyncio.gather(
                *[safe_call(CHEAP, cheap_prompt(q, ddl), TEMP_A, sample=i) for i in range(K)]
            )
            await attach_results(db, new)

            def side(samples):
                _, best, agree = gate([s["res"] for s in samples], K + 1)
                return {
                    "answers": [label(s["res"]) for s in samples],
                    "agree": agree,
                    "pick_sql": samples[best]["sql"],
                    "ok": correct(samples[best]["res"], r["gold"]),
                    "usd": sum(usd(s) for s in samples),
                    "tin": round(sum(s["tin"] for s in samples) / len(samples)),
                }

            out.append(
                {
                    "qid": qid,
                    "db_id": r["db"],
                    "question": q["question"],
                    "gold": label(r["gold"]),
                    "before": side(r["a"]),
                    "before_large_alone_ok": correct(r["c"]["res"], r["gold"]),
                    "before_large_alone_usd": usd(r["c"]),
                    "after": side(new),
                    "examples": _example_lines(ddl, [s["sql"] for s in new]),
                }
            )
        return out

    out = asyncio.run(build())
    COMPARE.write_text(json.dumps(out, indent=1))
    print(f"{len(out)} cases -> {COMPARE}")


def compare(tau):
    cases = json.loads(COMPARE.read_text())
    print("Baseline: schema as CREATE TABLE statements only.")
    print("Now:      schema plus example values from each column (commit 9e71811).")
    print(f"Same {K} Nemotron 3 Ultra samples per question, same gate, tau = {tau}.")
    for n, c in enumerate(cases, 1):
        b, a = c["before"], c["after"]
        print("=" * 78)
        print(f"Question {n} of {len(cases)}  [{c['db_id']}]")
        print(c["question"])
        print(f"Reference answer: {c['gold']}")
        for name, s in (("BASELINE", b), ("WITH EXAMPLE VALUES", a)):
            print()
            print(f"{name}  (prompt ~{s['tin']:,} tokens)")
            for i, ans in enumerate(s["answers"], 1):
                print(f"  Attempt {i} -> {ans}")
            route = "kept, Kimi not called" if s["agree"] >= tau else "escalated to Kimi K3"
            print(f"  Agreement {s['agree']}/{K}: {route}. Majority answer: {verdict(s['ok'])}.")
            if name == "BASELINE" and s["agree"] == K and not s["ok"]:
                print("  All three agreed on a wrong answer, so the gate could not catch it.")
            if name == "BASELINE":
                print(f"  Kimi K3 alone on the baseline prompt: {verdict(c['before_large_alone_ok'])}.")
        if c["examples"]:
            print()
            print("Example values the model now sees:")
            for line in c["examples"]:
                print("  " + line.lstrip("- ").strip())
    print("=" * 78)
    nb = sum(c["before"]["ok"] for c in cases)
    na = sum(c["after"]["ok"] for c in cases)
    print(f"Nemotron majority answer: baseline {nb}/{len(cases)} correct, with example values {na}/{len(cases)}.")
    print("Chosen from the 7 short tune questions where the baseline majority was wrong; 4 of 7 fixed.")
    print("Across all questions, see the full-run numbers in WRITEUP.md.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tau", type=int, default=3, help="agreement threshold, 0-4")
    ap.add_argument("--live", action="store_true", help="real Fireworks calls")
    ap.add_argument("--export", metavar="ROWS_PKL", help="rebuild demo_cases.json")
    ap.add_argument("--compare", action="store_true", help="baseline prompt vs example values")
    ap.add_argument("--export-compare", metavar="BASELINE_ROWS_PKL", help="rebuild demo_compare.json")
    a = ap.parse_args()
    if a.export_compare:
        export_compare(a.export_compare)
    elif a.compare:
        compare(a.tau)
    elif a.export:
        export(a.export)
    elif a.live:
        asyncio.run(live(a.tau))
    else:
        replay(a.tau)


if __name__ == "__main__":
    main()
