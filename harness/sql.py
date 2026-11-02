import functools
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


EXAMPLES = 3  # values shown for a column with many distinct values
ALL_VALUES_MAX = 20  # show every value when a column has at most this many
VALUE_CHARS = 40  # truncate long text values
LINE_CHARS = 300  # cap one column's example line
ALL_LINE_CHARS = 800  # higher cap when listing every category value
EXAMPLE_DEADLINE_S = 0.5  # per column; big tables stop early and keep what they found


def _q(name):
    return '"' + name.replace('"', '""') + '"'


def _show(v):
    """A SQL literal. Long text is cut and marked, so it is never copied as exact."""
    if isinstance(v, str):
        cut = len(v) > VALUE_CHARS
        lit = "'" + v[:VALUE_CHARS].replace("'", "''").replace("\n", "\\n") + "'"
        notes = (["\\n is a line break"] if "\n" in v[:VALUE_CHARS] else []) + (["truncated"] if cut else [])
        return lit + (f" ({', '.join(notes)})" if notes else "")
    return repr(v)


def _distinct(con, table, col):
    """Up to ALL_VALUES_MAX + 1 distinct non-null values, partial on timeout."""
    deadline = time.monotonic() + EXAMPLE_DEADLINE_S
    con.set_progress_handler(lambda: time.monotonic() > deadline, 1000)
    found = []
    try:
        cur = con.execute(
            f"SELECT DISTINCT {_q(col)} FROM {_q(table)} "
            f"WHERE {_q(col)} IS NOT NULL AND typeof({_q(col)}) != 'blob' "
            f"LIMIT {ALL_VALUES_MAX + 1}"
        )
        for (v,) in cur:
            found.append(v)
        complete = True
    except sqlite3.OperationalError:
        complete = False
    finally:
        con.set_progress_handler(None, 0)
    return found, complete


def _examples(con, table):
    lines = []
    for col in [r[1] for r in con.execute(f"PRAGMA table_info({_q(table)})")]:
        vals, complete = _distinct(con, table, col)
        if not vals:
            continue
        if complete and len(vals) <= ALL_VALUES_MAX:
            label, shown = "all values", vals
        else:
            label, shown = "e.g.", vals[:EXAMPLES]
        line = f"--   {col} ({label}): " + ", ".join(_show(v) for v in shown)
        cap = ALL_LINE_CHARS if label == "all values" else LINE_CHARS
        if len(line) > cap:
            line = line[:cap] + " ... (list cut)"
        lines.append(line)
    return lines


@functools.lru_cache(maxsize=None)
def _schema(db_path):
    con = _connect(db_path)
    try:
        tables = con.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
        ).fetchall()
        parts = []
        for name, sql in tables:
            ex = _examples(con, name)
            parts.append(sql + ("\n-- Example values:\n" + "\n".join(ex) if ex else ""))
        return "\n\n".join(parts)
    finally:
        con.close()


def schema_ddl(db_path):
    """CREATE TABLE statements, each followed by example values from the data.

    Values show real formats (leading zeros, text vs number, category names),
    which the DDL alone does not. Computed once per database.
    """
    return _schema(str(db_path))
