"""150/350 split, stratified by database x difficulty.

Run once, commit split.json, and do not run again. Regenerating the split
after baselines invalidates every number.
"""

import json
import random
from collections import defaultdict

from config import QUESTIONS, SEED


def build_split(questions):
    groups = defaultdict(list)
    for q in questions:
        groups[(q["db_id"], q["difficulty"])].append(q["question_id"])
    rng = random.Random(SEED)
    tune = set()
    for key in sorted(groups):
        ids = sorted(groups[key])
        rng.shuffle(ids)
        tune.update(ids[: round(len(ids) * 150 / len(questions))])
    return {
        str(q["question_id"]): ("tune" if q["question_id"] in tune else "test")
        for q in questions
    }


def main():
    questions = json.load(open(QUESTIONS))
    split = build_split(questions)
    json.dump(split, open("split.json", "w"), indent=1)
    n_tune = sum(v == "tune" for v in split.values())
    print(n_tune, "tune /", len(questions) - n_tune, "test")


if __name__ == "__main__":
    main()
