from collections import Counter

from config import EMPTY_IS_FAILURE
from sqlrun import as_set


def signature(res, i):
    """Only successful result sets form groups.

    A crash, timeout, oversize result, or empty result never agrees with
    anything, including another failure of the same kind.
    """
    kind, payload = res
    if kind != "ok":
        return ("fail", i)
    if not payload and EMPTY_IS_FAILURE:
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
