from harness.config import MAX_ROWS

CHEAP_TMPL = """You write SQLite queries. Return only one SQLite query inside a ```sql code block. No explanation.
Schema, with example values from the data (match their exact format and type):
{ddl}

Hint: {evidence}
Question: {question}
SQL:"""

REPAIR_TMPL = """You are fixing a SQLite query. Return only one SQLite query inside a ```sql code block. No explanation.
Schema, with example values from the data (match their exact format and type):
{ddl}

Hint: {evidence}
Question: {question}

A smaller model attempted this {k} times:
{attempts}

{verdict} Write the correct query."""


def describe(res):
    kind, payload = res
    if kind == "error":
        return f"error: {payload}"  # exact error text, never paraphrased
    if kind == "oversize":
        return f"returned more than {MAX_ROWS} rows"
    if not payload:
        return "returned 0 rows"
    return f"returned {len(payload)} rows, first row: {str(payload[0])[:150]}"


def verdict(c, k):
    if c == k:
        return "All attempts returned the same rows, which can still be wrong."
    if c >= 2:
        return f"{c} of {k} attempts agree; the others differ."
    return "The attempts disagree or failed, so some are wrong."


def cheap_prompt(q, ddl):
    return CHEAP_TMPL.format(
        ddl=ddl,
        evidence=q.get("evidence") or "none",
        question=q["question"],
    )


def repair_prompt(q, ddl, samples, c):
    attempts = "\n".join(
        f"Attempt {i + 1}: {s['sql']}\n  -> {describe(s['res'])}"
        for i, s in enumerate(samples)
    )
    return REPAIR_TMPL.format(
        ddl=ddl,
        evidence=q.get("evidence") or "none",
        question=q["question"],
        k=len(samples),
        attempts=attempts,
        verdict=verdict(c, len(samples)),
    )
