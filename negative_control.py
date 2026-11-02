"""Proves the grader passes gold SQL and fails deliberately wrong SQL.

A pass on other_question means two questions share an answer; inspect it by hand.
"""

import json
import random

from config import GOLD_TIMEOUT_S, QUESTIONS, SEED, db_path
from sqlrun import correct, execute


def main():
    qs = json.load(open(QUESTIONS))
    by_db = {}
    for q in qs:
        by_db.setdefault(q["db_id"], []).append(q)
    random.Random(SEED).shuffle(qs)

    def run(q, sql):
        return execute(db_path(q["db_id"]), sql, GOLD_TIMEOUT_S)

    picked = []
    for q in qs:
        g = run(q, q["SQL"])
        if g[0] == "ok" and g[1]:
            picked.append((q, g))
        if len(picked) == 20:
            break

    def corrupt(q, how):
        s = q["SQL"].strip().rstrip(";")
        if how == "false_filter":
            return f"SELECT * FROM ({s}) WHERE 1 = 0"
        if how == "extra_column":
            return f"SELECT *, 1 FROM ({s})"
        other = next(o for o in by_db[q["db_id"]] if o["question_id"] != q["question_id"])
        return other["SQL"]

    print(
        "gold vs gold:",
        sum(correct(run(q, q["SQL"]), g) for q, g in picked),
        "/ 20 (must be 20)",
    )
    for how in ("false_filter", "extra_column", "other_question"):
        hits = sum(correct(run(q, corrupt(q, how)), g) for q, g in picked)
        print(f"{how}: {hits} / 20 pass (must be 0)")


if __name__ == "__main__":
    main()
