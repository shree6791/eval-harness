"""Sweep tau, print the results table, and save the chart.

Baselines are scored from their own passes: cheap alone from A0 (one call),
large alone from C (cold prompt). The cascade dots are scored from A + B.
"""

import argparse
import pickle

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import binomtest

from config import EMPTY_IS_FAILURE, K, SEED
from gate import gate
from llm import usd
from sqlrun import correct

rng = np.random.default_rng(SEED)
TAUS = range(K + 2)  # 0..4


def single(rows, key, esc=False):
    return [
        {
            "ok": correct(r[key]["res"], r["gold"]),
            "esc": esc,
            "ms": r[key]["ms"],
            "usd": usd(r[key]),
        }
        for r in rows
    ]


def exec_gate(rows):
    out = []
    for r in rows:
        kind, payload = r["a0"]["res"]
        esc = kind != "ok" or (EMPTY_IS_FAILURE and not payload)
        pick = r["c"] if esc else r["a0"]
        out.append(
            {
                "ok": correct(pick["res"], r["gold"]),
                "esc": esc,
                "ms": r["a0"]["ms"] + (r["c"]["ms"] if esc else 0),
                "usd": usd(r["a0"]) + (usd(r["c"]) if esc else 0),
            }
        )
    return out


def cascade(rows, tau):
    out = []
    for r in rows:
        esc, best, _ = gate([s["res"] for s in r["a"]], tau)
        pick = r["b"] if esc else r["a"][best]
        out.append(
            {
                "ok": correct(pick["res"], r["gold"]),
                "esc": esc,
                "ms": max(s["ms"] for s in r["a"]) + (r["b"]["ms"] if esc else 0),
                "usd": sum(usd(s) for s in r["a"]) + (usd(r["b"]) if esc else 0),
            }
        )
    return out


def pct(a, p):
    return round(float(np.percentile(a, p))) if len(a) else "-"


def summarize(res):
    ok = np.array([x["ok"] for x in res])
    esc = np.array([x["esc"] for x in res])
    ms = np.array([x["ms"] for x in res])
    cost = np.array([x["usd"] for x in res])
    return {
        "acc": round(float(ok.mean() * 100), 1),
        "esc%": round(float(esc.mean() * 100), 1),
        "$/1k": round(float(cost.mean() * 1000), 3),
        "p50 kept": pct(ms[~esc], 50),
        "p95 kept": pct(ms[~esc], 95),
        "p50 sent": pct(ms[esc], 50),
        "p95 sent": pct(ms[esc], 95),
    }


def boot(x, n=10_000):
    """95% interval, in points."""
    x = np.asarray(x, float)
    means = x[rng.integers(0, len(x), (n, len(x)))].mean(1) * 100
    lo, hi = np.percentile(means, [2.5, 97.5])
    return (round(float(lo), 1), round(float(hi), 1))


def mcnemar(ours, theirs):
    b = sum(x and not y for x, y in zip(ours, theirs))  # fixed
    c = sum(y and not x for x, y in zip(ours, theirs))  # broke
    return b, c, (binomtest(b, b + c, 0.5).pvalue if b + c else 1.0)


def chart(pts, split, n):
    fig, ax = plt.subplots(figsize=(11, 7))
    cas = [pts[f"Cascade tau={t}"] for t in TAUS]
    ax.plot(
        [p["$/1k"] for p in cas],
        [p["acc"] for p in cas],
        "-o",
        lw=3,
        ms=10,
        label="Agreement cascade",
    )
    for t, p in zip(TAUS, cas):
        ax.annotate(
            f"τ={t}",
            (p["$/1k"], p["acc"]),
            xytext=(8, 6),
            textcoords="offset points",
            fontsize=15,
        )
    for name, mark in [("Cheap alone", "s"), ("Large alone", "D"), ("Executability gate", "^")]:
        ax.plot(pts[name]["$/1k"], pts[name]["acc"], mark, ms=14, label=name)
    ax.set_xscale("log")
    ax.set_xlabel("Cost, $ per 1,000 questions (log scale)", fontsize=17)
    ax.set_ylabel("Execution accuracy, %", fontsize=17)
    ax.set_title(f"BIRD Mini-Dev, {split} set, n = {n}", fontsize=18)
    ax.tick_params(labelsize=14)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=14)
    fig.tight_layout()
    fig.savefig(f"chart_{split}.png", dpi=200)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default="rows.pkl")
    ap.add_argument("--split", default="test")
    ap.add_argument("--tau", type=int)
    a = ap.parse_args()
    rows = [r for r in pickle.load(open(a.rows, "rb")) if r["split"] == a.split]
    setups = {
        "Cheap alone": single(rows, "a0"),
        "Large alone": single(rows, "c", esc=True),
        "Executability gate": exec_gate(rows),
    }
    has_b = all("b" in r for r in rows)
    if has_b:
        for t in TAUS:
            setups[f"Cascade tau={t}"] = cascade(rows, t)
    print(f"n = {len(rows)}; reference queries that fail: {sum(r['gold'][0] != 'ok' for r in rows)}")
    pts = {}
    for name, res in setups.items():
        pts[name] = summarize(res)
        print(f"{name:22s} {pts[name]} acc 95% CI {boot([x['ok'] for x in res])}")
    if has_b:
        cas = {t: pts[f"Cascade tau={t}"] for t in TAUS}
        top = max(p["acc"] for p in cas.values())
        pick = min((t for t in cas if cas[t]["acc"] >= top - 1), key=lambda t: cas[t]["$/1k"])
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


if __name__ == "__main__":
    main()
