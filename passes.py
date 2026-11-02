"""Runs passes A0, A, C, B, and R.

Every stage re-reads the cache, so --stage all after the others costs no API
calls. Pass B runs on every selected question; tau = 4 needs it.
"""

import argparse
import asyncio
import json
import pickle

from config import CHEAP, GOLD_TIMEOUT_S, K, LARGE, QUESTIONS, TEMP_A, db_path
from gate import gate
from llm import call
from prompts import cheap_prompt, repair_prompt
from sqlrun import execute, schema_ddl

DDL = {}


async def run_sql(db, sql, timeout=None):
    args = (db, sql) if timeout is None else (db, sql, timeout)
    return await asyncio.to_thread(execute, *args)


async def one(q, stage):
    db = db_path(q["db_id"])
    if q["db_id"] not in DDL:
        DDL[q["db_id"]] = schema_ddl(db)
    ddl = DDL[q["db_id"]]
    p = cheap_prompt(q, ddl)
    row = {
        "qid": q["question_id"],
        "db": q["db_id"],
        "difficulty": q["difficulty"],
        "gold": await run_sql(db, q["SQL"], GOLD_TIMEOUT_S),
    }
    jobs = {"a0": call(CHEAP, p, 0.0), "c": call(LARGE, p, 0.0)}
    jobs.update({f"s{i}": call(CHEAP, p, TEMP_A, sample=i) for i in range(K)})
    if stage in ("rerun", "all"):
        jobs["a0_r"] = call(CHEAP, p, 0.0, tag="rerun")
        jobs["c_r"] = call(LARGE, p, 0.0, tag="rerun")
    recs = dict(zip(jobs, await asyncio.gather(*jobs.values())))
    for rec in recs.values():
        rec["res"] = await run_sql(db, rec["sql"])
    row["a"] = [recs.pop(f"s{i}") for i in range(K)]
    row.update(recs)
    if stage in ("repair", "all"):
        # tau = K + 1 only to recover c. The escalate flag is unused.
        _, _, c = gate([s["res"] for s in row["a"]], K + 1)
        row["b"] = await call(LARGE, repair_prompt(q, ddl, row["a"], c), 0.0)
        row["b"]["res"] = await run_sql(db, row["b"]["sql"])
    return row


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["base", "repair", "rerun", "all"], default="base")
    ap.add_argument("--split", choices=["tune", "test", "all"], default="all")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--out", default="rows.pkl")
    a = ap.parse_args()
    split = json.load(open("split.json"))
    qs = [
        q
        for q in json.load(open(QUESTIONS))
        if a.split == "all" or split[str(q["question_id"])] == a.split
    ][: a.limit]
    done = 0

    async def tracked(q):
        nonlocal done
        try:
            r = await one(q, a.stage)
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


if __name__ == "__main__":
    asyncio.run(main())
