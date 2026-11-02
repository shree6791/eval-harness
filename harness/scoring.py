"""Score cached passes. Tau changes only the gate, not the model calls."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import binomtest

from harness.config import EMPTY_IS_FAILURE, K, SEED
from harness.gate import gate
from harness.llm import usd
from harness.sql import correct

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


def setups_for(rows):
    """Cheap alone, large alone, executability gate, and the tau sweep when B exists."""
    setups = {
        "Cheap alone": single(rows, "a0"),
        "Large alone": single(rows, "c", esc=True),
        "Executability gate": exec_gate(rows),
    }
    if all("b" in r for r in rows):
        for t in TAUS:
            setups[f"Cascade tau={t}"] = cascade(rows, t)
    return setups


def choose_tau(pts):
    """Highest tune accuracy. Ties within 1 point go to the cheaper tau."""
    cas = {t: pts[f"Cascade tau={t}"] for t in TAUS}
    top = max(p["acc"] for p in cas.values())
    return min((t for t in cas if cas[t]["acc"] >= top - 1), key=lambda t: cas[t]["$/1k"])
