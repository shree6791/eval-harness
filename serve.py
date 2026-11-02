"""Live /ask service and demo page.

Live calls skip the cache. Set TAU to the value chosen on the tune split and restart.
"""

import asyncio
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from config import CHEAP, DB_DIR, K, LARGE, TEMP_A, db_path
from gate import gate
from llm import call, usd
from prompts import cheap_prompt, repair_prompt
from sqlrun import execute, schema_ddl

TAU = 2
app = FastAPI()


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
    ddl = await asyncio.to_thread(schema_ddl, db)
    q = {"question": req.question, "evidence": req.evidence}
    p, tag = cheap_prompt(q, ddl), uuid.uuid4().hex
    samples = await asyncio.gather(
        *[
            call(CHEAP, p, TEMP_A, sample=i, tag=tag, use_cache=False)
            for i in range(K)
        ]
    )
    for s in samples:
        s["res"] = await asyncio.to_thread(execute, db, s["sql"])
    esc, best, c = gate([s["res"] for s in samples], TAU)
    pick, tier, cost = samples[best], "cheap", sum(usd(s) for s in samples)
    if esc:
        pick = await call(
            LARGE,
            repair_prompt(q, ddl, samples, c),
            0.0,
            tag=tag,
            use_cache=False,
        )
        pick["res"] = await asyncio.to_thread(execute, db, pick["sql"])
        tier, cost = "large (repair)", cost + usd(pick)
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


PAGE = """<!doctype html>
<meta name="viewport" content="width=device-width">
<title>Ask your data</title>
<style>
body{font:16px system-ui;max-width:860px;margin:32px auto;padding:0 16px}
select,textarea,input{width:100%;font:inherit;margin:6px 0;padding:8px;box-sizing:border-box}
button{font:inherit;padding:10px 24px}
.badge{display:inline-block;padding:4px 12px;border-radius:12px;color:#fff;margin-right:8px}
.cheap{background:#15803d}.large{background:#b45309}
pre{background:#f4f4f5;padding:12px;white-space:pre-wrap}
table{border-collapse:collapse}td{border:1px solid #ddd;padding:4px 8px}
</style>
<h1>Ask your data</h1>
<select id="db"></select>
<textarea id="q" rows="3" placeholder="Question in plain English"></textarea>
<input id="h" placeholder="Hint (optional)">
<button onclick="go()">Ask</button>
<div id="out"></div>
<script>
function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
fetch('/dbs').then(r => r.json()).then(d => {
  db.innerHTML = d.map(x => `<option>${esc(x)}</option>`).join('');
});
async function go() {
  out.textContent = 'Working...';
  const resp = await fetch('/ask', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({db_id: db.value, question: q.value, evidence: h.value})
  });
  const r = await resp.json();
  if (!resp.ok) {
    out.textContent = r.detail || 'Request failed';
    return;
  }
  const badge = r.tier === 'cheap' ? 'cheap' : 'large';
  const rows = r.error
    ? `<p>${esc(r.error)}</p>`
    : '<table>' + r.rows.map(x => '<tr>' + x.map(v => `<td>${esc(v)}</td>`).join('') + '</tr>').join('') + '</table>';
  out.innerHTML = `<p><span class="badge ${badge}">${esc(r.tier)}</span>agreement ${esc(r.agreement)} · $${esc(r.usd)} · ${esc(r.seconds)} s</p><pre>${esc(r.sql)}</pre>` + rows;
}
</script>
"""
