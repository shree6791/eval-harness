"""Live /ask service and demo page.

Live calls skip the cache. Set TAU in harness/config.py and restart.
"""

import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from harness.cascade import live_answer
from harness.config import DB_DIR, K, TAU, db_path

app = FastAPI()
PAGE = (Path(__file__).parent / "page.html").read_text()


class Ask(BaseModel):
    db_id: str
    question: str
    evidence: str = ""


def resolve_db(db_id):
    if not db_id or db_id != Path(db_id).name or db_id in {".", ".."}:
        raise HTTPException(status_code=400, detail="unknown database")
    path = db_path(db_id)
    if not path.is_file():
        raise HTTPException(status_code=400, detail="unknown database")
    return path


@app.post("/ask")
async def ask(req: Ask):
    t0 = time.monotonic()
    db = resolve_db(req.db_id)
    pick, tier, c, cost = await live_answer(db, req.question, req.evidence, TAU, uuid.uuid4().hex)
    kind, payload = pick["res"]
    return {
        "sql": pick["sql"],
        "tier": tier,
        "agreement": f"{c}/{K}",
        "usd": round(cost, 5),
        "seconds": round(time.monotonic() - t0, 2),
        "rows": [[str(v) for v in r] for r in payload[:20]] if kind == "ok" else [],
        "error": None if kind == "ok" else (payload or "more than 10,000 rows"),
    }


@app.get("/dbs")
def dbs():
    if not DB_DIR.is_dir():
        return []
    return sorted(p.name for p in DB_DIR.iterdir() if p.is_dir())


@app.get("/", response_class=HTMLResponse)
def page():
    return PAGE
