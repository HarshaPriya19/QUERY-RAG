"""Paths and environment settings.

API keys are read from the environment or a local .env file. They are never
hard-coded. The default provider is local so the experiment runs without a key.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
EXPERIMENTS_DIR = ROOT / "experiments"

load_dotenv(ROOT / ".env")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "local").strip().lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

JUDGE_BACKEND = os.getenv("JUDGE_BACKEND", "rules").strip().lower()
REWRITER_FAILURES = os.getenv("REWRITER_FAILURES", "1").strip() not in {"0", "false", "False"}

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
).strip()

# Top-3 is reported as Recall@3. The answer uses the highest-ranked chunk so a
# swapped document changes the answer on this small catalog.
RETRIEVE_K = int(os.getenv("RETRIEVE_K", "3"))
ANSWER_K = int(os.getenv("ANSWER_K", "1"))
