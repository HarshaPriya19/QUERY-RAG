"""Level 1: embed the original query, retrieve, then answer. No rewriting."""

from __future__ import annotations

from src.config import RETRIEVE_K
from src.generator import Generator
from src.retriever import FaissRetriever
from src.types import RAGResult


def run_baseline(
    query: str,
    retriever: FaissRetriever,
    generator: Generator,
    retrieve_k: int = RETRIEVE_K,
) -> RAGResult:
    original = query.strip()
    hits = retriever.search(original, k=retrieve_k)
    answer = generator.generate(original, hits)
    return RAGResult(
        level="baseline",
        original_query=original,
        rewritten_query=None,
        retrieval_query=original,
        judge_decision=None,
        used_fallback=False,
        failure_mode=None,
        retrieved=hits,
        answer=answer,
    )
