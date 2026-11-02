"""Print the results table, the tau choice, and the chart."""

import argparse
import pickle

import numpy as np

from harness.scoring import boot, chart, choose_tau, mcnemar, setups_for, summarize
from harness.sql import correct


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default="rows.pkl")
    ap.add_argument("--split", default="test")
    ap.add_argument("--tau", type=int)
    a = ap.parse_args()
    rows = [r for r in pickle.load(open(a.rows, "rb")) if r["split"] == a.split]
    setups = setups_for(rows)
    print(f"n = {len(rows)}; reference queries that fail: {sum(r['gold'][0] != 'ok' for r in rows)}")
    pts = {}
    for name, res in setups.items():
        pts[name] = summarize(res)
        print(f"{name:22s} {pts[name]} acc 95% CI {boot([x['ok'] for x in res])}")
    if all("b" in r for r in rows):
        pick = choose_tau(pts)
        print("tau by the selection rule:", pick, "(use the value from the tune split)")
        chart(pts, a.split, len(rows))
        if a.tau is not None:
            ours = [x["ok"] for x in setups[f"Cascade tau={a.tau}"]]
            large = [x["ok"] for x in setups["Large alone"]]
            b, c, p = mcnemar(ours, large)
            diff = np.array(ours, float) - np.array(large, float)
            print(
                f"tau={a.tau} vs large alone: fixed {b}, broke {c}, McNemar p = {p:.4f}, "
                f"paired difference 95% CI {boot(diff)} pts"
            )
            print("broke:", [r["qid"] for r, x, y in zip(rows, ours, large) if y and not x])
    for k in ("a0", "c"):
        if rows and all(f"{k}_r" in r for r in rows):
            x = [correct(r[k]["res"], r["gold"]) for r in rows]
            y = [correct(r[k + "_r"]["res"], r["gold"]) for r in rows]
            print(
                f"wobble {k}: {100 * (np.mean(x) - np.mean(y)):+.1f} pts, "
                f"{sum(i != j for i, j in zip(x, y))} questions flipped"
            )
    return pts
