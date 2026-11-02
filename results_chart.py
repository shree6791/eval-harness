"""Compare full runs on one chart: Nemotron alone, Kimi K3 alone, and the cascade.

    # Save a run's per-question results (small JSON, safe to commit)
    python results_chart.py --export rows.pkl results/example_values.json
    # A run made before 9e71811 used the old empty rule (all-NULL rows could agree)
    python results_chart.py --export rows.pkl results/baseline.json --old-gate

    # Chart one or more saved runs on the questions they share
    python results_chart.py results/baseline.json results/example_values.json --split test

Each run is one colour. Nemotron alone is a square, Kimi K3 alone a diamond, and the
cascade (Nemotron x3, Kimi repairs when agreement < tau) a line through tau = 0..4.
"""

import argparse
import json
import pickle
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

K = 3
TAUS = range(K + 2)
COLOURS = ["#2563eb", "#dc2626", "#16a34a", "#9333ea"]


def export(rows_path, out_path, old_gate=False):
    """One line per question: correctness, cost and time for every call that scoring needs."""
    from harness.gate import signature
    from harness.sql import as_set

    def old_signature(res, i):
        """Gate rule before 9e71811: only zero rows counted as empty."""
        kind, payload = res
        if kind != "ok":
            return ("fail", i)
        if not payload:
            return ("empty", i)
        return ("rows", frozenset(as_set(payload)))

    sign = old_signature if old_gate else signature
    from harness.llm import usd
    from harness.sql import correct

    def call(rec, gold):
        return {"ok": bool(correct(rec["res"], gold)), "usd": usd(rec), "ms": round(rec["ms"])}

    out = []
    for r in pickle.load(open(rows_path, "rb")):
        samples = []
        for i, s in enumerate(r["a"]):
            sig = sign(s["res"], i)
            samples.append({**call(s, r["gold"]), "sig": str(hash(sig)) if sig[0] == "rows" else f"{sig[0]}-{i}"})
        row = {
            "qid": r["qid"],
            "split": r["split"],
            "difficulty": r["difficulty"],
            "cheap_alone": call(r["a0"], r["gold"]),
            "large_alone": call(r["c"], r["gold"]),
            "samples": samples,
        }
        if "b" in r:
            row["repair"] = call(r["b"], r["gold"])
        out.append(row)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(sorted(out, key=lambda x: x["qid"])))
    print(f"{len(out)} questions -> {out_path}")


def gate(sigs, tau):
    groups = {}
    for i, s in enumerate(sigs):
        if not s.startswith(("fail-", "empty-")):
            groups.setdefault(s, []).append(i)
    if not groups:
        return 0 < tau, 0
    best = max(groups.values(), key=len)
    return len(best) < tau, best[0]


def score(rows):
    """Accuracy %, $ per 1,000 questions and p50 seconds for each setup."""

    def summary(picks):
        ok = np.array([p[0] for p in picks], float)
        cost = np.array([p[1] for p in picks])
        ms = np.array([p[2] for p in picks])
        return {"acc": 100 * ok.mean(), "usd1k": 1000 * cost.mean(), "p50s": float(np.median(ms)) / 1000,
                "per_correct": cost.sum() / ok.sum() if ok.sum() else float("nan")}

    res = {
        "Nemotron alone": summary([(r["cheap_alone"]["ok"], r["cheap_alone"]["usd"], r["cheap_alone"]["ms"]) for r in rows]),
        "Kimi K3 alone": summary([(r["large_alone"]["ok"], r["large_alone"]["usd"], r["large_alone"]["ms"]) for r in rows]),
    }
    for tau in TAUS:
        picks = []
        for r in rows:
            esc, best = gate([s["sig"] for s in r["samples"]], tau)
            cheap_usd = sum(s["usd"] for s in r["samples"])
            cheap_ms = max(s["ms"] for s in r["samples"])
            if esc:
                b = r["repair"]
                picks.append((b["ok"], cheap_usd + b["usd"], cheap_ms + b["ms"]))
            else:
                picks.append((r["samples"][best]["ok"], cheap_usd, cheap_ms))
        res[f"Cascade tau={tau}"] = summary(picks)
        res[f"Cascade tau={tau}"]["esc"] = 100 * np.mean([gate([s["sig"] for s in r["samples"]], tau)[0] for r in rows])
    return res


def bars(scored, tau, split, n, out):
    """Four panels: accuracy, $ per 1,000, $ per correct, median seconds. One bar group per setup."""
    setups = ["Nemotron alone", "Kimi K3 alone", f"Cascade tau={tau}"]
    names = {"Nemotron alone": "Nemotron 3 Ultra\nalone", "Kimi K3 alone": "Kimi K3\nalone",
             f"Cascade tau={tau}": "Cascade\n(Nemotron x3 +\nKimi repair)"}
    panels = [("acc", "Accuracy, %", "{:.1f}%"), ("usd1k", "Cost, $ per 1,000 questions", "${:.2f}"),
              ("per_correct", "Cost, $ per correct answer", "${:.3f}"), ("p50s", "Median time to answer, s", "{:.1f} s")]
    fig, axes = plt.subplots(1, 4, figsize=(20, 6))
    width = 0.8 / len(scored)
    x = np.arange(len(setups))
    for ax, (key, title, fmt) in zip(axes, panels):
        for j, (colour, (name, res)) in enumerate(zip(COLOURS, scored.items())):
            vals = [res[s][key] for s in setups]
            pos = x + (j - (len(scored) - 1) / 2) * width
            bs = ax.bar(pos, vals, width, color=colour, label=name)
            for b, v in zip(bs, vals):
                ax.annotate(fmt.format(v), (b.get_x() + b.get_width() / 2, b.get_height()),
                            textcoords="offset points", xytext=(0, 3), ha="center", fontsize=10)
        ax.set_title(title, fontsize=13)
        ax.set_xticks(x, [names[s] for s in setups], fontsize=10)
        ax.margins(y=0.15)
        ax.grid(axis="y", alpha=0.3)
    axes[0].legend(fontsize=11)
    fig.suptitle(f"BIRD Mini-Dev, {split} split, n = {n}. Cascade at τ = {tau}.", fontsize=15)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    print(f"bars -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="*", help="saved runs (results/*.json)")
    ap.add_argument("--export", nargs=2, metavar=("ROWS_PKL", "OUT_JSON"))
    ap.add_argument("--old-gate", action="store_true", help="export with the gate rule before 9e71811")
    ap.add_argument("--split", choices=["tune", "test", "all"], default="test")
    ap.add_argument("--out", default="chart_compare.png")
    ap.add_argument("--bars-out", default="chart_bars.png")
    ap.add_argument("--tau", type=int, default=4, help="cascade setting shown in the bar charts")
    a = ap.parse_args()
    if a.export:
        export(*a.export, old_gate=a.old_gate)
        return

    runs = {Path(p).stem: json.loads(Path(p).read_text()) for p in a.runs}
    # Same questions in every run, so the comparison is paired.
    shared = set.intersection(*[{r["qid"] for r in rows if a.split in ("all", r["split"]) and "repair" in r} for rows in runs.values()])
    scored = {name: score([r for r in rows if r["qid"] in shared]) for name, rows in runs.items()}

    print(f"Questions shared by all runs ({a.split} split): {len(shared)}")
    for name, res in scored.items():
        print(f"\n{name}")
        print(f"  {'setup':16s} {'accuracy':>9s} {'$/1k':>8s} {'$/correct':>10s} {'p50 s':>6s} {'escalated':>9s}")
        for setup, m in res.items():
            esc = f"{m['esc']:.0f}%" if "esc" in m else ""
            print(f"  {setup:16s} {m['acc']:8.1f}% {m['usd1k']:8.2f} {m['per_correct']:10.4f} {m['p50s']:6.1f} {esc:>9s}")

    bars(scored, a.tau, a.split, len(shared), a.bars_out)

    fig, ax = plt.subplots(figsize=(11, 7))
    for colour, (name, res) in zip(COLOURS, scored.items()):
        cas = [res[f"Cascade tau={t}"] for t in TAUS]
        ax.plot([m["usd1k"] for m in cas], [m["acc"] for m in cas], "-o", color=colour, lw=2.5, ms=8,
                label=f"{name}: cascade (Nemotron x3, Kimi repairs)")
        for t, m in zip(TAUS, cas):
            ax.annotate(f"τ={t}", (m["usd1k"], m["acc"]), textcoords="offset points", xytext=(7, -12), fontsize=10, color=colour)
        ch, lg = res["Nemotron alone"], res["Kimi K3 alone"]
        ax.plot(ch["usd1k"], ch["acc"], "s", color=colour, ms=13, mec="black", label=f"{name}: Nemotron alone")
        ax.plot(lg["usd1k"], lg["acc"], "D", color=colour, ms=13, mec="black", label=f"{name}: Kimi K3 alone")
    ax.set_xscale("log")
    ax.set_xlabel("Cost, $ per 1,000 questions (log scale)", fontsize=13)
    ax.set_ylabel("Execution accuracy, %", fontsize=13)
    ax.set_title(f"BIRD Mini-Dev, {a.split} split, n = {len(shared)} (same questions in every run)", fontsize=14)
    ax.grid(alpha=0.3, which="both")
    ax.legend(fontsize=10, loc="upper left")
    fig.tight_layout()
    fig.savefig(a.out, dpi=200)
    print(f"\nchart -> {a.out}")


if __name__ == "__main__":
    main()
