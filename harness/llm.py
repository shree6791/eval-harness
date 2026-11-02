"""Cached, metered Fireworks calls.

The cache key holds model, prompt, temperature, sample index, and tag.
Without the sample index the three samples come back identical.
"""

import asyncio
import hashlib
import json
import os
import random
import re
import time
from pathlib import Path

from openai import AsyncOpenAI

from harness.config import CONCURRENCY, MAX_TOKENS, MAX_TOKENS_BY_MODEL, PRICE, REASONING

CACHE = Path("cache")
CACHE.mkdir(exist_ok=True)
SEM = asyncio.Semaphore(CONCURRENCY)

_client = None


def get_client():
    """Open the client on the first live call so offline analysis imports cleanly."""
    global _client
    if _client is None:
        api_key = os.environ.get("FIREWORKS_API_KEY")
        if not api_key:
            raise RuntimeError("Set FIREWORKS_API_KEY before making a live model call.")
        _client = AsyncOpenAI(
            base_url="https://api.fireworks.ai/inference/v1",
            api_key=api_key,
            timeout=300,
        )
    return _client


def clean(text):
    """SQL from a fenced block, else from the first SELECT or WITH line, else ""."""
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    m = re.search(r"`{3}(?:sql)?\s*(.*?)`{3}", text, flags=re.S | re.I)
    if m:
        sql = m.group(1)
    else:
        m = re.search(r"^\s*(SELECT|WITH)\b.*", text, flags=re.S | re.I | re.M)
        sql = m.group(0).split(";")[0] if m else ""
    return sql.strip().rstrip(";").strip()


async def call(model, prompt, temperature, sample=0, tag="main", use_cache=True):
    effort = REASONING.get(model)
    max_tokens = MAX_TOKENS_BY_MODEL.get(model, MAX_TOKENS)
    key = hashlib.sha256(
        json.dumps([model, prompt, temperature, sample, tag, max_tokens, effort]).encode()
    ).hexdigest()
    extra = {"reasoning_effort": effort} if effort else {}
    path = CACHE / f"{key}.json"
    if use_cache and path.exists():
        return json.loads(path.read_text())
    client = get_client()
    for attempt in range(8):
        try:
            async with SEM:
                t0 = time.monotonic()
                r = await client.chat.completions.create(
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                    **extra,
                )
                ms = (time.monotonic() - t0) * 1000
            break
        except Exception:
            if attempt == 7:
                raise
            # Backoff up to 60 s so rate limits (HTTP 429) clear instead of failing the question.
            await asyncio.sleep(min(60, 2 ** attempt) + random.random())
    choice = r.choices[0]
    content = choice.message.content
    rec = {
        "model": model,
        "sql": clean(content),
        "ms": ms,
        "tin": r.usage.prompt_tokens,
        "tout": r.usage.completion_tokens,
        "finish": choice.finish_reason,
        # Reasoning tokens count as output; record them to see what used the budget.
        "treason": getattr(getattr(r.usage, "completion_tokens_details", None), "reasoning_tokens", None),
    }
    if not rec["sql"]:
        rec["raw"] = (content or "")[:2000]
    if choice.finish_reason == "length":
        print(f"warning: {model} hit max_tokens={max_tokens}")
    if use_cache:
        path.write_text(json.dumps(rec))
    return rec


def usd(rec):
    pin, pout = PRICE[rec["model"]]
    return (rec["tin"] * pin + rec["tout"] * pout) / 1e6
