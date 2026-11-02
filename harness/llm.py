"""Cached, metered Fireworks calls.

The cache key holds model, prompt, temperature, sample index, and tag.
Without the sample index the three samples come back identical.
"""

import asyncio
import hashlib
import json
import os
import re
import time
from pathlib import Path

from openai import AsyncOpenAI

from harness.config import CONCURRENCY, PRICE

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
        )
    return _client


def clean(text):
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    m = re.search(r"`{3}(?:sql)?\s*(.*?)`{3}", text, flags=re.S | re.I)
    return (m.group(1) if m else text).strip().rstrip(";").strip()


async def call(model, prompt, temperature, sample=0, tag="main", use_cache=True):
    key = hashlib.sha256(
        json.dumps([model, prompt, temperature, sample, tag]).encode()
    ).hexdigest()
    path = CACHE / f"{key}.json"
    if use_cache and path.exists():
        return json.loads(path.read_text())
    client = get_client()
    for attempt in range(4):
        try:
            async with SEM:
                t0 = time.monotonic()
                r = await client.chat.completions.create(
                    model=model,
                    temperature=temperature,
                    max_tokens=2048,
                    messages=[{"role": "user", "content": prompt}],
                )
                ms = (time.monotonic() - t0) * 1000
            break
        except Exception:
            if attempt == 3:
                raise
            await asyncio.sleep(2 ** attempt)
    rec = {
        "model": model,
        "sql": clean(r.choices[0].message.content),
        "ms": ms,
        "tin": r.usage.prompt_tokens,
        "tout": r.usage.completion_tokens,
    }
    if use_cache:
        path.write_text(json.dumps(rec))
    return rec


def usd(rec):
    pin, pout = PRICE[rec["model"]]
    return (rec["tin"] * pin + rec["tout"] * pout) / 1e6
