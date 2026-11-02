from pathlib import Path

# Unzipped Mini-Dev layout: questions JSON plus dev_databases/<db_id>/<db_id>.sqlite.
DATA_DIR = Path("data/MINIDEV")
QUESTIONS = DATA_DIR / "mini_dev_sqlite.json"
DB_DIR = DATA_DIR / "dev_databases"

# Tier 1, cheap model. NVIDIA Nemotron 3 Ultra 550B A55B, reasoning off.
# Was nemotron-lightning-3p5-30b-a3b: ~6 min per call on 2 Nov, see CHANGELOG.
CHEAP = "accounts/fireworks/models/nemotron-3-ultra-nvfp4"
# Tier 1 backup. OpenAI GPT OSS 120B.
CHEAP_BACKUP = "accounts/fireworks/models/gpt-oss-120b"
# Tier 2, large model. Kimi K3.
LARGE = "accounts/fireworks/models/kimi-k3"
# Tier 2 backup. GLM 5.3.
LARGE_BACKUP = "accounts/fireworks/models/glm-5p3"

# $ per 1M tokens: input, output. Confirmed against Fireworks on 1 Nov 2026.
PRICE = {
    CHEAP: (0.60, 2.40),
    CHEAP_BACKUP: (0.15, 0.60),
    LARGE: (3.00, 15.00),
    LARGE_BACKUP: (1.40, 4.40),
}

# reasoning_effort per model. Models not listed use their default reasoning.
REASONING = {CHEAP: "none", CHEAP_BACKUP: "low"}
MAX_TOKENS = 8192

K = 3  # cheap samples per question
TEMP_A = 0.6  # pass A temperature; 0 gives identical samples and a flat curve
TIMEOUT_S = 5.0  # per generated query
GOLD_TIMEOUT_S = 30.0  # reference queries can be slow
MAX_ROWS = 10_000
EMPTY_IS_FAILURE = True
SEED = 42
CONCURRENCY = 16
TAU = 2  # placeholder until the tune sweep. Restart the service after changing it.


def db_path(db_id):
    return DB_DIR / db_id / f"{db_id}.sqlite"
