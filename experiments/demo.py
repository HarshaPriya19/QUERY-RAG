"""Show one helpful rewrite and one harmful rewrite through all three levels.

Usage (from the project root):

    python -m experiments.demo
    python -m experiments.demo "NB Pro warrenty length"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.rag_baseline import run_baseline  # noqa: E402
from src.rag_judge import run_judge  # noqa: E402
from src.rag_rewrite import run_rewrite  # noqa: E402
from src.system import build_runtime  # noqa: E402

DEFAULTS = [
    "NB Pro warrenty length",
    "What is the NovaBook Air warranty, not the Pro",
]


def _show(runtime, query: str) -> None:
    produced = runtime.rewriter.rewrite(query)
    baseline = run_baseline(query, runtime.retriever, runtime.generator)
    rewritten = run_rewrite(
        query, runtime.retriever, runtime.generator, runtime.rewriter, rewrite=produced
    )
    judged = run_judge(
        query,
        runtime.retriever,
        runtime.generator,
        runtime.rewriter,
        runtime.judge,
        rewrite=produced,
    )
    print("=" * 72)
    print(f"Original:  {produced.original_query}")
    print(f"Rewritten: {produced.rewritten_query}")
    print(f"Failure:   {produced.failure_mode or 'none'}")
    print("Judge:")
    print(json.dumps(judged.judge_decision, indent=2))
    print(f"Level 3 retrieval query: {judged.retrieval_query}")
    print(f"Fallback: {judged.used_fallback}")
    for label, result in (
        ("Level 1", baseline),
        ("Level 2", rewritten),
        ("Level 3", judged),
    ):
        top = result.retrieved[0].chunk.doc_id if result.retrieved else "none"
        preview = " ".join(result.answer.split())
        if len(preview) > 180:
            preview = preview[:179] + "…"
        print(f"{label} top={top}")
        print(f"  {preview}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import os

    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    queries = sys.argv[1:] or DEFAULTS
    print("Loading embedding model and building the FAISS index...")
    runtime = build_runtime()
    for query in queries:
        _show(runtime, query)


if __name__ == "__main__":
    main()
