import sqlite3
import time

from harness.config import MAX_ROWS, TIMEOUT_S


def _connect(db_path):
    # Read-only: a generated query cannot DROP or write a table.
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    # Some BIRD text is not valid UTF-8.
    con.text_factory = lambda b: b.decode(errors="replace")
    return con


def execute(db_path, sql, timeout_s=TIMEOUT_S):
    """Run one query. sqlite3.connect(timeout=...) is only a lock timeout.

    The progress handler is what stops a runaway join.
    """
    con = _connect(db_path)
    deadline = time.monotonic() + timeout_s
    con.set_progress_handler(lambda: time.monotonic() > deadline, 1000)
    try:
        rows = con.execute(sql).fetchmany(MAX_ROWS + 1)
        return ("oversize", None) if len(rows) > MAX_ROWS else ("ok", rows)
    except Exception as e:
        # A timeout arrives as OperationalError: interrupted.
        return ("error", f"{type(e).__name__}: {e}"[:300])
    finally:
        con.close()


def norm(v):
    return round(v, 6) if isinstance(v, float) else v


def as_set(rows):
    return {tuple(norm(v) for v in r) for r in rows}


def correct(pred, gold):
    """BIRD rule: order and duplicates ignored, floats rounded to 6 places."""
    return pred[0] == "ok" and gold[0] == "ok" and as_set(pred[1]) == as_set(gold[1])


def schema_ddl(db_path):
    con = _connect(db_path)
    try:
        rows = con.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
        ).fetchall()
        return "\n\n".join(r[0] for r in rows)
    finally:
        con.close()
