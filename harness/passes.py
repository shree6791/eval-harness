"""Runs passes A0, A, C, B, and R.

Every stage re-reads the cache, so --stage all after the others costs no API
calls. Pass B runs on every selected question; tau = 4 needs it.
"""

import argparse
import asyncio
import json
import pickle

from harness.cascade import eval_question
from harness.config import QUESTIONS


def select_questions(questions, split, which, limit):
    chosen = [
        q
        for q in questions
        if which == "all" or split[str(q["question_id"])] == which
    ]
    return chosen[:limit]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["base", "repair", "rerun", "all"], default="base")
    ap.add_argument("--split", choices=["tune", "test", "all"], default="all")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--out", default="rows.pkl")
    a = ap.parse_args()
    split = json.load(open("split.json"))
    qs = select_questions(json.load(open(QUESTIONS)), split, a.split, a.limit)
    done = 0

    async def tracked(q):
        nonlocal done
        try:
            r = await eval_question(q, a.stage)
        except Exception as e:
            print("FAILED", q["question_id"], e, flush=True)
            return None
        done += 1
        if done % 25 == 0:
            print(done, "/", len(qs), flush=True)
        return r

    rows = [r for r in await asyncio.gather(*[tracked(q) for q in qs]) if r]
    for r in rows:
        r["split"] = split[str(r["qid"])]
    pickle.dump(rows, open(a.out, "wb"))
    print(len(rows), "rows ->", a.out)
