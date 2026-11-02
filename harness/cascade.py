"""Run one question through cheap samples, the agreement gate, and repair.

Evaluation passes cache every model call. The live service does not.
"""

import asyncio

from harness.config import CHEAP, GOLD_TIMEOUT_S, K, LARGE, TEMP_A, db_path
from harness.gate import gate
from harness.llm import call, usd
from harness.prompts import cheap_prompt, repair_prompt
from harness.sql import execute, schema_ddl

_DDL = {}


async def run_sql(db, sql, timeout=None):
    args = (db, sql) if timeout is None else (db, sql, timeout)
    return await asyncio.to_thread(execute, *args)


async def schema_for(db_id):
    if db_id not in _DDL:
        _DDL[db_id] = schema_ddl(db_path(db_id))
    return _DDL[db_id]


async def attach_results(db, recs):
    for rec in recs:
        rec["res"] = await run_sql(db, rec["sql"])


async def eval_question(q, stage):
    """One cached row for passes A0, A, C, and, when asked, B and R."""
    db = db_path(q["db_id"])
    ddl = await schema_for(q["db_id"])
    prompt = cheap_prompt(q, ddl)
    row = {
        "qid": q["question_id"],
        "db": q["db_id"],
        "difficulty": q["difficulty"],
        "gold": await run_sql(db, q["SQL"], GOLD_TIMEOUT_S),
    }
    jobs = {"a0": call(CHEAP, prompt, 0.0), "c": call(LARGE, prompt, 0.0)}
    jobs.update({f"s{i}": call(CHEAP, prompt, TEMP_A, sample=i) for i in range(K)})
    if stage in ("rerun", "all"):
        jobs["a0_r"] = call(CHEAP, prompt, 0.0, tag="rerun")
        jobs["c_r"] = call(LARGE, prompt, 0.0, tag="rerun")
    recs = dict(zip(jobs, await asyncio.gather(*jobs.values())))
    await attach_results(db, recs.values())
    row["a"] = [recs.pop(f"s{i}") for i in range(K)]
    row.update(recs)
    if stage in ("repair", "all"):
        # tau = K + 1 only to recover c. The escalate flag is unused.
        _, _, c = gate([s["res"] for s in row["a"]], K + 1)
        row["b"] = await call(LARGE, repair_prompt(q, ddl, row["a"], c), 0.0)
        row["b"]["res"] = await run_sql(db, row["b"]["sql"])
    return row


async def live_answer(db, question, evidence, tau, tag):
    """Uncached cascade for one live question. Returns pick, tier, c, cost."""
    ddl = schema_ddl(db)
    q = {"question": question, "evidence": evidence}
    prompt = cheap_prompt(q, ddl)
    samples = await asyncio.gather(
        *[
            call(CHEAP, prompt, TEMP_A, sample=i, tag=tag, use_cache=False)
            for i in range(K)
        ]
    )
    await attach_results(db, samples)
    esc, best, c = gate([s["res"] for s in samples], tau)
    pick, tier = samples[best], "cheap"
    cost = sum(usd(s) for s in samples)
    if esc:
        pick = await call(
            LARGE,
            repair_prompt(q, ddl, samples, c),
            0.0,
            tag=tag,
            use_cache=False,
        )
        pick["res"] = await run_sql(db, pick["sql"])
        tier = "large (repair)"
        cost += usd(pick)
    return pick, tier, c, cost
