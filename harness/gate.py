from collections import Counter

from harness.config import EMPTY_IS_FAILURE
from harness.sql import as_set


def is_empty(payload):
    """No rows, or only NULLs (e.g. AVG over nothing). No reference answer is all-NULL."""
    return not payload or all(v is None for row in payload for v in row)


def signature(res, i):
    """Only successful result sets form groups.

    A crash, timeout, oversize result, or empty or all-NULL result never
    agrees with anything, including another failure of the same kind.
    """
    kind, payload = res
    if kind != "ok":
        return ("fail", i)
    if EMPTY_IS_FAILURE and is_empty(payload):
        return ("empty", i)
    return ("rows", frozenset(as_set(payload)))


def gate(results, tau):
    """Returns (escalate, index of the answer to keep, c).

    c is the size of the largest group that returned real rows (0-3).
    Escalate when c < tau.
    """
    sigs = [signature(r, i) for i, r in enumerate(results)]
    good = [s for s in sigs if s[0] == "rows"]
    if not good:
        return 0 < tau, 0, 0
    sig, c = Counter(good).most_common(1)[0]
    return c < tau, sigs.index(sig), c
